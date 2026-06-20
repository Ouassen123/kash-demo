"""Taxonomy service for ESCO and O*NET integration."""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from src.core.logging import get_logger
from .esco_client import ESCOClient
from .onet_client import ONETClient

logger = get_logger(__name__)


@dataclass
class TaxonomyMatch:
    """Taxonomy match result."""
    uri: str
    label: str
    confidence: float
    source: str  # "esco" or "onet"
    language: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class EnrichmentMetadata:
    """Metadata for taxonomy enrichment."""
    esco_version: str
    onet_version: str
    enrichment_timestamp: str
    confidence_threshold: float
    fallback_strategy: str


class TaxonomyService:
    """Service for taxonomy lookups and enrichment."""
    
    def __init__(self, cache_ttl: timedelta = timedelta(hours=24)):
        """
        Initialize taxonomy service.
        
        Args:
            cache_ttl: Cache time-to-live
        """
        self.cache_ttl = cache_ttl
        self.cache = {}
        
        # Initialize clients
        self.esco_client = ESCOClient()
        self.onet_client = ONETClient()
        
        # Confidence thresholds
        self.min_confidence = 0.7
        self.high_confidence = 0.9
        
        # Fallback strategy
        self.fallback_strategy = "esco_priority"
        
        # Statistics
        self.stats = {
            "total_lookups": 0,
            "cache_hits": 0,
            "esco_matches": 0,
            "onet_matches": 0,
            "no_matches": 0
        }
    
    def _get_cache_key(self, service: str, method: str, query: str, **kwargs) -> str:
        """Generate cache key."""
        key_parts = [service, method, query]
        
        # Add relevant parameters to key
        if "language" in kwargs:
            key_parts.append(f"lang={kwargs['language']}")
        if "skill_type" in kwargs:
            key_parts.append(f"type={kwargs['skill_type']}")
        
        return ":".join(key_parts)
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get data from cache if not expired."""
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_ttl:
                self.stats["cache_hits"] += 1
                return cached_data
            else:
                # Remove expired entry
                del self.cache[cache_key]
        
        return None
    
    def _set_cache(self, cache_key: str, data: Any) -> None:
        """Set data in cache."""
        self.cache[cache_key] = (data, datetime.now())
    
    async def map_skill_to_esco(self, skill: str, language: str = "en", min_confidence: float = None) -> Optional[Dict[str, Any]]:
        """
        Map a skill to ESCO taxonomy.
        
        Args:
            skill: Skill name to map
            language: Language code
            min_confidence: Minimum confidence threshold
            
        Returns:
            ESCO match result or None
        """
        self.stats["total_lookups"] += 1
        
        cache_key = self._get_cache_key("esco", "search_skills", skill, language=language)
        cached_result = self._get_from_cache(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            results = await self.esco_client.search_skills(skill, language=language)
            
            # Filter by confidence
            threshold = min_confidence or self.min_confidence
            filtered_results = [r for r in results if r["confidence"] >= threshold]
            
            if filtered_results:
                # Return the highest confidence match
                best_match = max(filtered_results, key=lambda x: x["confidence"])
                
                result = {
                    "uri": best_match["uri"],
                    "label": best_match["label"],
                    "confidence": best_match["confidence"],
                    "language": best_match["language"],
                    "mapping_timestamp": datetime.now().isoformat()
                }
                
                self._set_cache(cache_key, result)
                self.stats["esco_matches"] += 1
                
                return result
            else:
                self.stats["no_matches"] += 1
                self._log_fallback("skill", skill, "no_esco_match")
                return None
                
        except Exception as e:
            logger.error(f"Error mapping skill to ESCO: {e}")
            self.stats["no_matches"] += 1
            return None
    
    async def map_occupation_to_onet(self, occupation: str, min_confidence: float = None) -> Optional[Dict[str, Any]]:
        """
        Map an occupation to O*NET taxonomy.
        
        Args:
            occupation: Occupation name to map
            min_confidence: Minimum confidence threshold
            
        Returns:
            O*NET match result or None
        """
        self.stats["total_lookups"] += 1
        
        cache_key = self._get_cache_key("onet", "search_occupations", occupation)
        cached_result = self._get_from_cache(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            results = await self.onet_client.search_occupations(occupation)
            
            # Filter by confidence
            threshold = min_confidence or self.min_confidence
            filtered_results = [r for r in results if r["confidence"] >= threshold]
            
            if filtered_results:
                # Return the highest confidence match
                best_match = max(filtered_results, key=lambda x: x["confidence"])
                
                result = {
                    "code": best_match["code"],
                    "title": best_match["title"],
                    "confidence": best_match["confidence"],
                    "zone": best_match["zone"],
                    "mapping_timestamp": datetime.now().isoformat()
                }
                
                self._set_cache(cache_key, result)
                self.stats["onet_matches"] += 1
                
                return result
            else:
                self.stats["no_matches"] += 1
                self._log_fallback("occupation", occupation, "no_onet_match")
                return None
                
        except Exception as e:
            logger.error(f"Error mapping occupation to O*NET: {e}")
            self.stats["no_matches"] += 1
            return None
    
    async def map_skills_batch(self, skills: List[Dict[str, Any]], language: str = "en") -> List[Optional[Dict[str, Any]]]:
        """
        Map multiple skills to taxonomy in batch.
        
        Args:
            skills: List of skill dictionaries with 'name' and 'confidence'
            language: Language code
            
        Returns:
            List of taxonomy matches (None for no matches)
        """
        tasks = []
        
        for skill in skills:
            skill_name = skill.get("name", "")
            if skill_name:
                task = self.map_skill_to_esco(skill_name, language=language)
                tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error mapping skill {skills[i].get('name', 'unknown')}: {result}")
                processed_results.append(None)
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def enrich_cv_skills(self, cv_skills: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enrich CV skills with taxonomy information.
        
        Args:
            cv_skills: List of CV skills from NLP analysis
            
        Returns:
            Enriched skills with taxonomy data
        """
        enriched_skills = []
        
        for skill in cv_skills:
            enriched_skill = skill.copy()
            
            # Add ESCO mapping
            esco_match = await self.map_skill_to_esco(skill["name"])
            if esco_match:
                enriched_skill["esco_uri"] = esco_match["uri"]
                enriched_skill["esco_label"] = esco_match["label"]
                enriched_skill["esco_confidence"] = esco_match["confidence"]
            else:
                enriched_skill["esco_uri"] = None
                enriched_skill["esco_label"] = None
                enriched_skill["esco_confidence"] = 0.0
            
            # Add enrichment metadata
            enriched_skill["enrichment_timestamp"] = datetime.now().isoformat()
            
            enriched_skills.append(enriched_skill)
        
        return enriched_skills
    
    async def enrich_cv_analysis(self, cv_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich complete CV analysis with taxonomy information.
        
        Args:
            cv_analysis: CV analysis result from NLP pipeline
            
        Returns:
            Enriched CV analysis with taxonomy data
        """
        enriched_analysis = cv_analysis.copy()
        
        # Enrich skills
        if "skills" in cv_analysis:
            enriched_analysis["skills"] = await self.enrich_cv_skills(cv_analysis["skills"])
        
        # Enrich experience with occupation mapping
        if "experience" in cv_analysis:
            enriched_experience = []
            
            for exp in cv_analysis["experience"]:
                enriched_exp = exp.copy()
                
                # Try to map job title to O*NET
                title = exp.get("title", "")
                if title:
                    onet_match = await self.map_occupation_to_onet(title)
                    if onet_match:
                        enriched_exp["onet_code"] = onet_match["code"]
                        enriched_exp["onet_title"] = onet_match["title"]
                        enriched_exp["onet_confidence"] = onet_match["confidence"]
                    else:
                        enriched_exp["onet_code"] = None
                        enriched_exp["onet_title"] = None
                        enriched_exp["onet_confidence"] = 0.0
                
                enriched_exp["enrichment_timestamp"] = datetime.now().isoformat()
                enriched_experience.append(enriched_exp)
            
            enriched_analysis["experience"] = enriched_experience
        
        # Add taxonomy metadata
        versions = await self.get_taxonomy_versions()
        enriched_analysis["taxonomy_metadata"] = EnrichmentMetadata(
            esco_version=versions.get("esco", "unknown"),
            onet_version=versions.get("onet", "unknown"),
            enrichment_timestamp=datetime.now().isoformat(),
            confidence_threshold=self.min_confidence,
            fallback_strategy=self.fallback_strategy
        ).__dict__
        
        return enriched_analysis
    
    async def get_taxonomy_versions(self) -> Dict[str, str]:
        """
        Get versions of taxonomy APIs.
        
        Returns:
            Dictionary with version information
        """
        versions = {}
        
        try:
            versions["esco"] = await self.esco_client.get_version()
        except Exception as e:
            logger.error(f"Error getting ESCO version: {e}")
            versions["esco"] = "unknown"
        
        try:
            versions["onet"] = await self.onet_client.get_version()
        except Exception as e:
            logger.error(f"Error getting O*NET version: {e}")
            versions["onet"] = "unknown"
        
        return versions
    
    async def refresh_taxonomy_data(self) -> Dict[str, bool]:
        """
        Refresh taxonomy data from APIs.
        
        Returns:
            Dictionary with refresh status for each taxonomy
        """
        results = {}
        
        # Clear cache
        self.cache.clear()
        
        # Test ESCO connectivity
        try:
            esco_health = await self.esco_client.health_check()
            results["esco"] = esco_health["status"] == "healthy"
        except Exception as e:
            logger.error(f"Error refreshing ESCO data: {e}")
            results["esco"] = False
        
        # Test O*NET connectivity
        try:
            onet_health = await self.onet_client.health_check()
            results["onet"] = onet_health["status"] == "healthy"
        except Exception as e:
            logger.error(f"Error refreshing O*NET data: {e}")
            results["onet"] = False
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get taxonomy service statistics.
        
        Returns:
            Statistics dictionary
        """
        total = self.stats["total_lookups"]
        if total > 0:
            cache_hit_rate = self.stats["cache_hits"] / total
        else:
            cache_hit_rate = 0.0
        
        return {
            **self.stats,
            "cache_hit_rate": cache_hit_rate,
            "cache_size": len(self.cache)
        }
    
    def _log_fallback(self, entity_type: str, entity_value: str, reason: str) -> None:
        """Log fallback strategy usage."""
        logger.warning(f"Taxonomy fallback for {entity_type} '{entity_value}': {reason}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of taxonomy service and dependencies.
        
        Returns:
            Health check results
        """
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {}
        }
        
        # Check ESCO
        try:
            esco_health = await self.esco_client.health_check()
            health_status["services"]["esco"] = esco_health
        except Exception as e:
            health_status["services"]["esco"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        # Check O*NET
        try:
            onet_health = await self.onet_client.health_check()
            health_status["services"]["onet"] = onet_health
        except Exception as e:
            health_status["services"]["onet"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        # Add statistics
        health_status["statistics"] = self.get_statistics()
        
        return health_status
    
    async def close(self):
        """Close taxonomy service and cleanup resources."""
        await self.esco_client.close()
        await self.onet_client.close()
    
    def __del__(self):
        """Cleanup when service is destroyed."""
        if hasattr(self, 'esco_client') or hasattr(self, 'onet_client'):
            asyncio.create_task(self.close())
