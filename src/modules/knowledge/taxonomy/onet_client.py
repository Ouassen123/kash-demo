"""O*NET API client for taxonomy integration."""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import httpx
from urllib.parse import quote

from src.core.logging import get_logger
from src.core.config import settings

logger = get_logger(__name__)


class ONETClient:
    """Client for O*NET API for occupational information."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize O*NET client.
        
        Args:
            api_key: API key for O*NET API (optional)
            base_url: Base URL for O*NET API (optional)
        """
        self.api_key = api_key or getattr(settings, 'ONET_API_KEY', None)
        self.base_url = base_url or "https://services.onetcenter.org/ws/migrate"
        
        # Rate limiting
        self.rate_limit_delay = 0.2  # 200ms between requests (O*NET is stricter)
        self.last_request_time = datetime.min
        
        # Cache for API responses
        self.cache = {}
        self.cache_ttl = timedelta(hours=24)
        
        # HTTP client
        self.client = httpx.Client(
            timeout=30.0,
            headers=self._get_default_headers()
        )
    
    def _get_default_headers(self) -> Dict[str, str]:
        """Get default HTTP headers."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "KASH-Platform/1.0"
        }
        
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        
        return headers
    
    async def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make HTTP request to O*NET API.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            API response data
        """
        # Rate limiting
        time_since_last = datetime.now() - self.last_request_time
        if time_since_last.total_seconds() < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - time_since_last.total_seconds())
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            self.last_request_time = datetime.now()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"O*NET API error: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"O*NET API request error: {e}")
            raise
    
    def _calculate_confidence(self, query: str, result_text: str) -> float:
        """
        Calculate confidence score for a match.
        
        Args:
            query: Original search query
            result_text: Result text from API
            
        Returns:
            Confidence score (0.0-1.0)
        """
        query_lower = query.lower()
        result_lower = result_text.lower()
        
        # Exact match
        if query_lower == result_lower:
            return 1.0
        
        # Query is substring of result
        if query_lower in result_lower:
            return 0.9
        
        # Result is substring of query
        if result_lower in query_lower:
            return 0.8
        
        # Word overlap
        query_words = set(query_lower.split())
        result_words = set(result_lower.split())
        
        if query_words and result_words:
            overlap = len(query_words.intersection(result_words))
            total_words = len(query_words.union(result_words))
            return overlap / total_words
        
        return 0.3
    
    def _validate_code(self, code: str) -> bool:
        """Validate O*NET code format."""
        # O*NET codes follow pattern XX-XXXX.XX
        import re
        return bool(re.match(r'^\d{2}-\d{4}\.\d{2}$', code))
    
    async def search_occupations(self, query: str, keyword: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for occupations in O*NET database.
        
        Args:
            query: Search query
            keyword: Keyword filter (optional)
            
        Returns:
            List of matching occupations with confidence scores
        """
        params = {
            "keyword": query,
            "detail": "brief"
        }
        
        if keyword:
            params["keyword"] = keyword
        
        try:
            response = await self._make_request("online/occupations", params)
            results = []
            
            if "occupation" in response:
                occupations = response["occupation"]
                if not isinstance(occupations, list):
                    occupations = [occupations]
                
                for item in occupations:
                    title = item.get("title", "")
                    confidence = self._calculate_confidence(query, title)
                    
                    result = {
                        "code": item.get("code", ""),
                        "title": title,
                        "description": item.get("description", ""),
                        "zone": item.get("zone", ""),
                        "confidence": confidence
                    }
                    
                    if self._validate_code(result["code"]):
                        results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching O*NET occupations: {e}")
            return []
    
    async def get_occupation_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Get occupation details by O*NET code.
        
        Args:
            code: O*NET occupation code
            
        Returns:
            Occupation details or None if not found
        """
        if not self._validate_code(code):
            return None
        
        try:
            response = await self._make_request("online/occupations", {"code": code, "detail": "brief"})
            
            if "occupation" in response:
                item = response["occupation"]
                if not isinstance(item, list):
                    item = [item]
                
                if item:
                    occupation = item[0]
                    return {
                        "code": occupation.get("code", ""),
                        "title": occupation.get("title", ""),
                        "description": occupation.get("description", ""),
                        "zone": occupation.get("zone", "")
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting O*NET occupation by code: {e}")
            return None
    
    async def get_related_occupations(self, code: str, related_type: str = "bright") -> List[Dict[str, Any]]:
        """
        Get related occupations for a given O*NET code.
        
        Args:
            code: O*NET occupation code
            related_type: Type of related occupations (bright, bright_outlook, etc.)
            
        Returns:
            List of related occupations
        """
        if not self._validate_code(code):
            return []
        
        try:
            response = await self._make_request("online/occupations", {
                "code": code,
                "related": related_type
            })
            
            results = []
            if related_type in response:
                related = response[related_type]
                if not isinstance(related, list):
                    related = [related]
                
                for item in related:
                    result = {
                        "code": item.get("code", ""),
                        "title": item.get("title", ""),
                        "description": item.get("description", ""),
                        "zone": item.get("zone", ""),
                        "relation_type": related_type
                    }
                    
                    if self._validate_code(result["code"]):
                        results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting related O*NET occupations: {e}")
            return []
    
    async def get_occupation_skills(self, code: str) -> List[Dict[str, Any]]:
        """
        Get skills required for an occupation.
        
        Args:
            code: O*NET occupation code
            
        Returns:
            List of required skills
        """
        if not self._validate_code(code):
            return []
        
        try:
            response = await self._make_request("online/occupations", {
                "code": code,
                "element": "skills"
            })
            
            results = []
            if "element" in response:
                skills = response["element"]
                if not isinstance(skills, list):
                    skills = [skills]
                
                for item in skills:
                    result = {
                        "element_id": item.get("element_id", ""),
                        "name": item.get("name", ""),
                        "description": item.get("description", ""),
                        "category": item.get("category", ""),
                        "scale": item.get("scale", "")
                    }
                    
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting O*NET occupation skills: {e}")
            return []
    
    async def get_occupation_tasks(self, code: str) -> List[Dict[str, Any]]:
        """
        Get tasks for an occupation.
        
        Args:
            code: O*NET occupation code
            
        Returns:
            List of occupation tasks
        """
        if not self._validate_code(code):
            return []
        
        try:
            response = await self._make_request("online/occupations", {
                "code": code,
                "element": "tasks"
            })
            
            results = []
            if "element" in response:
                tasks = response["element"]
                if not isinstance(tasks, list):
                    tasks = [tasks]
                
                for item in tasks:
                    result = {
                        "element_id": item.get("element_id", ""),
                        "name": item.get("name", ""),
                        "description": item.get("description", ""),
                        "category": item.get("category", "")
                    }
                    
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting O*NET occupation tasks: {e}")
            return []
    
    async def get_version(self) -> str:
        """
        Get O*NET API version.
        
        Returns:
            API version string
        """
        try:
            # O*NET doesn't have a version endpoint, so we'll use a health check
            response = await self.health_check()
            return response.get("api_version", "unknown")
        except Exception as e:
            logger.error(f"Error getting O*NET version: {e}")
            return "unknown"
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check O*NET API health.
        
        Returns:
            Health check results
        """
        start_time = datetime.now()
        
        try:
            # Try a simple search to test connectivity
            await self.search_occupations("software", limit=1)
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                "status": "healthy",
                "api_version": "v1.0",
                "response_time_ms": response_time,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time_ms": response_time,
                "timestamp": datetime.now().isoformat()
            }
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
    
    def __del__(self):
        """Cleanup when client is destroyed."""
        if hasattr(self, 'client'):
            asyncio.create_task(self.close())
