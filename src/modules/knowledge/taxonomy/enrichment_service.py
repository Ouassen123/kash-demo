"""Enrichment service for CV analysis with taxonomy data."""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.core.logging import get_logger
from .taxonomy_service import TaxonomyService

logger = get_logger(__name__)


class EnrichmentService:
    """Service for enriching CV analysis with taxonomy data."""
    
    def __init__(self, taxonomy_service: Optional[TaxonomyService] = None):
        """
        Initialize enrichment service.
        
        Args:
            taxonomy_service: Taxonomy service instance (optional)
        """
        self.taxonomy_service = taxonomy_service or TaxonomyService()
        
        # Enrichment configuration
        self.enable_async_processing = True
        self.batch_size = 10
        self.confidence_threshold = 0.7
    
    async def enrich_cv_analysis(self, cv_analysis: Dict[str, Any], language: str = "en") -> Dict[str, Any]:
        """
        Enrich CV analysis with taxonomy data.
        
        Args:
            cv_analysis: CV analysis result from NLP pipeline
            language: Language code for taxonomy lookup
            
        Returns:
            Enriched CV analysis with taxonomy data
        """
        logger.info(f"Starting CV analysis enrichment for {len(cv_analysis.get('skills', []))} skills")
        
        try:
            # Use taxonomy service for enrichment
            enriched_analysis = await self.taxonomy_service.enrich_cv_analysis(cv_analysis)
            
            # Add enrichment metadata
            enriched_analysis["enrichment_metadata"] = {
                "service": "enrichment_service",
                "language": language,
                "confidence_threshold": self.confidence_threshold,
                "enriched_at": datetime.now().isoformat(),
                "enriched_sections": self._get_enriched_sections(enriched_analysis)
            }
            
            logger.info("CV analysis enrichment completed successfully")
            return enriched_analysis
            
        except Exception as e:
            logger.error(f"Error during CV analysis enrichment: {e}")
            raise
    
    def _get_enriched_sections(self, analysis: Dict[str, Any]) -> List[str]:
        """Get list of enriched sections."""
        enriched_sections = []
        
        for section in ["skills", "education", "experience", "certifications"]:
            if section in analysis and analysis[section]:
                # Check if section has taxonomy data
                for item in analysis[section]:
                    if any(key.startswith(("esco_", "onet_")) for key in item.keys()):
                        enriched_sections.append(section)
                        break
        
        return list(set(enriched_sections))
    
    async def enrich_skills_batch(self, skills_list: List[Dict[str, Any]], language: str = "en") -> List[Dict[str, Any]]:
        """
        Enrich multiple skills in batch.
        
        Args:
            skills_list: List of skill dictionaries
            language: Language code
            
        Returns:
            Enriched skills with taxonomy data
        """
        if not self.enable_async_processing:
            # Process sequentially
            enriched = []
            for skill in skills_list:
                enriched.append(await self._enrich_single_skill(skill, language))
            return enriched
        
        # Process in batches
        enriched_skills = []
        
        for i in range(0, len(skills_list), self.batch_size):
            batch = skills_list[i:i + self.batch_size]
            
            tasks = [self._enrich_single_skill(skill, language) for skill in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Error enriching skill: {result}")
                    # Return original skill without enrichment
                    original_skill = batch[batch_results.index(result)]
                    enriched_skills.append(original_skill)
                else:
                    enriched_skills.append(result)
        
        return enriched_skills
    
    async def _enrich_single_skill(self, skill: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Enrich a single skill with taxonomy data."""
        enriched_skill = skill.copy()
        skill_name = skill.get("name", "")
        
        if not skill_name:
            return enriched_skill
        
        try:
            # Map to ESCO
            esco_match = await self.taxonomy_service.map_skill_to_esco(skill_name, language=language)
            
            if esco_match and esco_match["confidence"] >= self.confidence_threshold:
                enriched_skill.update({
                    "esco_uri": esco_match["uri"],
                    "esco_label": esco_match["label"],
                    "esco_confidence": esco_match["confidence"],
                    "esco_language": esco_match["language"]
                })
            else:
                enriched_skill.update({
                    "esco_uri": None,
                    "esco_label": None,
                    "esco_confidence": 0.0,
                    "esco_language": language
                })
            
            # Add enrichment metadata
            enriched_skill["enriched_at"] = datetime.now().isoformat()
            
        except Exception as e:
            logger.error(f"Error enriching skill '{skill_name}': {e}")
            # Add default values
            enriched_skill.update({
                "esco_uri": None,
                "esco_label": None,
                "esco_confidence": 0.0,
                "esco_language": language,
                "enriched_at": datetime.now().isoformat()
            })
        
        return enriched_skill
    
    async def enrich_experience_batch(self, experience_list: List[Dict[str, Any]], language: str = "en") -> List[Dict[str, Any]]:
        """
        Enrich multiple experience entries in batch.
        
        Args:
            experience_list: List of experience dictionaries
            language: Language code
            
        Returns:
            Enriched experience with O*NET data
        """
        if not self.enable_async_processing:
            # Process sequentially
            enriched = []
            for exp in experience_list:
                enriched.append(await self._enrich_single_experience(exp, language))
            return enriched
        
        # Process in batches
        enriched_experience = []
        
        for i in range(0, len(experience_list), self.batch_size):
            batch = experience_list[i:i + self.batch_size]
            
            tasks = [self._enrich_single_experience(exp, language) for exp in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Error enriching experience: {result}")
                    # Return original experience without enrichment
                    original_exp = batch[batch_results.index(result)]
                    enriched_experience.append(original_exp)
                else:
                    enriched_experience.append(result)
        
        return enriched_experience
    
    async def _enrich_single_experience(self, experience: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Enrich a single experience entry with O*NET data."""
        enriched_exp = experience.copy()
        job_title = experience.get("title", "")
        
        if not job_title:
            return enriched_exp
        
        try:
            # Map to O*NET
            onet_match = await self.taxonomy_service.map_occupation_to_onet(job_title)
            
            if onet_match and onet_match["confidence"] >= self.confidence_threshold:
                enriched_exp.update({
                    "onet_code": onet_match["code"],
                    "onet_title": onet_match["title"],
                    "onet_confidence": onet_match["confidence"],
                    "onet_zone": onet_match["zone"]
                })
            else:
                enriched_exp.update({
                    "onet_code": None,
                    "onet_title": None,
                    "onet_confidence": 0.0,
                    "onet_zone": None
                })
            
            # Add enrichment metadata
            enriched_exp["enriched_at"] = datetime.now().isoformat()
            
        except Exception as e:
            logger.error(f"Error enriching experience '{job_title}': {e}")
            # Add default values
            enriched_exp.update({
                "onet_code": None,
                "onet_title": None,
                "onet_confidence": 0.0,
                "onet_zone": None,
                "enriched_at": datetime.now().isoformat()
            })
        
        return enriched_exp
    
    def calculate_enrichment_quality_score(self, enriched_analysis: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate quality scores for enrichment.
        
        Args:
            enriched_analysis: Enriched CV analysis
            
        Returns:
            Dictionary with quality scores by section
        """
        scores = {}
        
        # Skills enrichment quality
        if "skills" in enriched_analysis:
            skills = enriched_analysis["skills"]
            if skills:
                esco_matches = sum(1 for skill in skills if skill.get("esco_confidence", 0) > 0)
                total_skills = len(skills)
                scores["skills"] = esco_matches / total_skills if total_skills > 0 else 0.0
            else:
                scores["skills"] = 0.0
        
        # Experience enrichment quality
        if "experience" in enriched_analysis:
            experience = enriched_analysis["experience"]
            if experience:
                onet_matches = sum(1 for exp in experience if exp.get("onet_confidence", 0) > 0)
                total_experience = len(experience)
                scores["experience"] = onet_matches / total_experience if total_experience > 0 else 0.0
            else:
                scores["experience"] = 0.0
        
        # Overall quality score
        if scores:
            scores["overall"] = sum(scores.values()) / len(scores)
        else:
            scores["overall"] = 0.0
        
        return scores
    
    def get_enrichment_summary(self, enriched_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get summary of enrichment results.
        
        Args:
            enriched_analysis: Enriched CV analysis
            
        Returns:
            Enrichment summary
        """
        summary = {
            "total_skills": len(enriched_analysis.get("skills", [])),
            "skills_with_esco": 0,
            "total_experience": len(enriched_analysis.get("experience", [])),
            "experience_with_onet": 0,
            "taxonomy_versions": enriched_analysis.get("taxonomy_metadata", {}),
            "quality_scores": self.calculate_enrichment_quality_score(enriched_analysis)
        }
        
        # Count enriched items
        for skill in enriched_analysis.get("skills", []):
            if skill.get("esco_confidence", 0) > 0:
                summary["skills_with_esco"] += 1
        
        for exp in enriched_analysis.get("experience", []):
            if exp.get("onet_confidence", 0) > 0:
                summary["experience_with_onet"] += 1
        
        return summary
    
    async def validate_enrichment_quality(self, enriched_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate enrichment quality against standards.
        
        Args:
            enriched_analysis: Enriched CV analysis
            
        Returns:
            Validation results
        """
        validation = {
            "valid": True,
            "issues": [],
            "warnings": [],
            "quality_score": 0.0
        }
        
        # Calculate quality scores
        scores = self.calculate_enrichment_quality_score(enriched_analysis)
        validation["quality_score"] = scores.get("overall", 0.0)
        
        # Check minimum quality thresholds
        min_skill_quality = 0.5
        min_experience_quality = 0.3
        
        if scores.get("skills", 0.0) < min_skill_quality:
            validation["valid"] = False
            validation["issues"].append(f"Skills enrichment quality ({scores['skills']:.2f}) below threshold ({min_skill_quality})")
        
        if scores.get("experience", 0.0) < min_experience_quality:
            validation["warnings"].append(f"Experience enrichment quality ({scores['experience']:.2f}) below recommended threshold ({min_experience_quality})")
        
        # Check for missing metadata
        if "taxonomy_metadata" not in enriched_analysis:
            validation["issues"].append("Missing taxonomy metadata")
            validation["valid"] = False
        
        # Check for enrichment timestamps
        for section in ["skills", "experience"]:
            if section in enriched_analysis:
                for item in enriched_analysis[section]:
                    if "enriched_at" not in item:
                        validation["warnings"].append(f"Missing enrichment timestamp in {section}")
        
        return validation
    
    async def close(self):
        """Close enrichment service and cleanup resources."""
        if self.taxonomy_service:
            await self.taxonomy_service.close()
    
    def __del__(self):
        """Cleanup when service is destroyed."""
        if hasattr(self, 'taxonomy_service'):
            asyncio.create_task(self.close())
