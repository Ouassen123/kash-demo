"""ESCO API client for taxonomy integration."""

import json
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import httpx
from urllib.parse import quote
from difflib import SequenceMatcher

from src.core.logging import get_logger
from src.core.config import settings

logger = get_logger(__name__)


class ESCOClient:
    """Client for European Skills/Competences, Qualifications and Occupations (ESCO) API."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize ESCO client.
        
        Args:
            api_key: API key for ESCO API (optional)
            base_url: Base URL for ESCO API (optional)
        """
        self.api_key = api_key or getattr(settings, 'ESCO_API_KEY', None)
        self.base_url = base_url or "https://ec.europa.eu/esco/api"
        
        # Rate limiting
        self.rate_limit_delay = 0.1  # 100ms between requests
        self.last_request_time = datetime.min
        
        # Cache for API responses
        self.cache = {}
        self.cache_ttl = timedelta(hours=24)
        
        self._default_headers = self._get_default_headers()
    
    def _get_default_headers(self) -> Dict[str, str]:
        """Get default HTTP headers."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "KASH-Platform/1.0"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            headers["X-API-Key"] = self.api_key
        else:
            headers["X-API-Key"] = "test-key"
        return headers
    
    def _respect_rate_limit(self):
        elapsed = (datetime.now() - self.last_request_time).total_seconds()
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make HTTP request to ESCO API.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            API response data
        """
        self._respect_rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = httpx.get(url, params=params, headers=self._default_headers, timeout=30.0)
            response.raise_for_status()
            
            self.last_request_time = datetime.now()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"ESCO API error: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"ESCO API request error: {e}")
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
        
        # Query is substring of result (strong indication)
        if query_lower in result_lower:
            programming_terms = ("programming", "coding", "language", "skill")
            if any(term in result_lower for term in programming_terms):
                return 0.95
            return 0.8
        
        # Result is substring of query
        if result_lower in query_lower:
            return 0.8
        
        ratio = SequenceMatcher(None, query_lower, result_lower).ratio()
        if ratio >= 0.85:
            return 0.85
        if ratio >= 0.65:
            return 0.7
        
        # Word overlap
        query_words = set(query_lower.split())
        result_words = set(result_lower.split())
        
        if query_words and result_words:
            overlap = len(query_words.intersection(result_words))
            total_words = len(query_words.union(result_words))
            return overlap / total_words
        
        return 0.3
    
    def _validate_uri(self, uri: str) -> bool:
        """Validate ESCO URI format."""
        return uri.startswith("http://data.europa.eu/esco/")
    
    def _get_cache_key(self, resource: str, **kwargs) -> str:
        parts = [resource]
        for key in sorted(kwargs.keys()):
            parts.append(f"{key}={kwargs[key]}")
        return "|".join(parts)

    def _get_cached_value(self, cache_key: str) -> Optional[Any]:
        if cache_key in self.cache:
            data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_ttl:
                return data
            del self.cache[cache_key]
        return None

    def _set_cache_value(self, cache_key: str, data: Any) -> None:
        self.cache[cache_key] = (data, datetime.now())

    def _validate_skill_response(self, response: Dict[str, Any]) -> None:
        if "_embedded" not in response or "results" not in response.get("_embedded", {}):
            raise ValueError("Invalid ESCO response structure")

    def search_skills(self, query: str, language: str = "en", skill_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for skills in ESCO taxonomy.
        
        Args:
            query: Search query
            language: Language code (en, fr, de, es, etc.)
            skill_type: Filter by skill type (skill/competence, knowledge/skill)
            
        Returns:
            List of matching skills with confidence scores
        """
        params = {
            "text": quote(query),
            "language": language,
            "type": "skill"
        }
        
        if skill_type:
            params["skillType"] = skill_type
        
        cache_key = self._get_cache_key("skills", query=query, language=language, skill_type=skill_type)
        cached = self._get_cached_value(cache_key)
        if cached is not None:
            return cached

        response = self._make_request("resource", params)
        self._validate_skill_response(response)
        results = []
        
        if "_embedded" in response and "results" in response["_embedded"]:
            for item in response["_embedded"]["results"]:
                if skill_type and item.get("skillType") != skill_type:
                    continue
                if "preferredLabel" in item and language in item["preferredLabel"]:
                    label = item["preferredLabel"][language]
                    confidence = self._calculate_confidence(query, label)
                    
                    result = {
                        "uri": item.get("conceptUri", ""),
                        "label": label,
                        "description": item.get("description", {}).get(language, ""),
                        "skill_type": item.get("skillType", ""),
                        "confidence": confidence,
                        "language": language
                    }
                    
                    if self._validate_uri(result["uri"]):
                        results.append(result)
        
        self._set_cache_value(cache_key, results)
        return results
    
    def search_occupations(self, query: str, language: str = "en") -> List[Dict[str, Any]]:
        """
        Search for occupations in ESCO taxonomy.
        
        Args:
            query: Search query
            language: Language code
            
        Returns:
            List of matching occupations with confidence scores
        """
        params = {
            "text": quote(query),
            "language": language,
            "type": "occupation"
        }
        
        cache_key = self._get_cache_key("occupations", query=query, language=language)
        cached = self._get_cached_value(cache_key)
        if cached is not None:
            return cached

        response = self._make_request("resource", params)
        results = []
        
        if "_embedded" in response and "results" in response["_embedded"]:
            for item in response["_embedded"]["results"]:
                if "preferredLabel" in item and language in item["preferredLabel"]:
                    label = item["preferredLabel"][language]
                    confidence = self._calculate_confidence(query, label)
                    
                    result = {
                        "uri": item.get("conceptUri", ""),
                        "label": label,
                        "title": label,
                        "description": item.get("description", {}).get(language, ""),
                        "confidence": confidence,
                        "language": language
                    }
                    
                    if self._validate_uri(result["uri"]):
                        results.append(result)
        
        self._set_cache_value(cache_key, results)
        return results
    
    def get_skill_by_uri(self, uri: str, language: str = "en") -> Optional[Dict[str, Any]]:
        """
        Get skill details by URI.
        
        Args:
            uri: ESCO skill URI
            language: Language code
            
        Returns:
            Skill details or None if not found
        """
        if not self._validate_uri(uri):
            return None
        
        # Extract resource ID from URI
        resource_id = uri.split("/")[-1]
        
        cache_key = self._get_cache_key("skill_uri", uri=uri, language=language)
        cached = self._get_cached_value(cache_key)
        if cached is not None:
            return cached

        try:
            response = self._make_request(f"resource/{resource_id}")
            
            if "preferredLabel" in response and language in response["preferredLabel"]:
                result = {
                    "uri": uri,
                    "label": response["preferredLabel"][language],
                    "description": response.get("description", {}).get(language, ""),
                    "skill_type": response.get("skillType", ""),
                    "language": language
                }
                self._set_cache_value(cache_key, result)
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting ESCO skill by URI: {e}")
            return None
    
    def get_occupation_by_uri(self, uri: str, language: str = "en") -> Optional[Dict[str, Any]]:
        """
        Get occupation details by URI.
        
        Args:
            uri: ESCO occupation URI
            language: Language code
            
        Returns:
            Occupation details or None if not found
        """
        if not self._validate_uri(uri):
            return None
        
        # Extract resource ID from URI
        resource_id = uri.split("/")[-1]
        
        cache_key = self._get_cache_key("occupation_uri", uri=uri, language=language)
        cached = self._get_cached_value(cache_key)
        if cached is not None:
            return cached

        try:
            response = self._make_request(f"resource/{resource_id}")
            
            if "preferredLabel" in response and language in response["preferredLabel"]:
                result = {
                    "uri": uri,
                    "label": response["preferredLabel"][language],
                    "description": response.get("description", {}).get(language, ""),
                    "language": language
                }
                self._set_cache_value(cache_key, result)
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting ESCO occupation by URI: {e}")
            return None
    
    def get_version(self) -> str:
        """
        Get ESCO API version.
        
        Returns:
            API version string
        """
        try:
            response = self._make_request("version")
            return response.get("version", "unknown")
        except Exception as e:
            logger.error(f"Error getting ESCO version: {e}")
            return "unknown"
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check ESCO API health.
        
        Returns:
            Health check results
        """
        start_time = datetime.now()
        
        try:
            version = self.get_version()
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                "status": "healthy",
                "api_version": version,
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
    
    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported languages.
        
        Returns:
            List of language codes
        """
        return ["en", "fr", "de", "es", "it", "nl", "sv", "da", "fi", "no", "pl", "pt", "ro", "bg", "hr", "sl", "sk", "hu", "cs", "et", "lv", "lt", "mt", "el", "cy", "ga", "eu"]
    
    def search_skills_batch(self, skills: List[str], **kwargs) -> List[List[Dict[str, Any]]]:
        results = []
        for skill in skills:
            results.append(self.search_skills(skill, **kwargs))
        return results

    def get_api_version(self) -> str:
        version_data = self._make_request("version")
        return version_data.get("apiVersion") or version_data.get("version", "unknown")
