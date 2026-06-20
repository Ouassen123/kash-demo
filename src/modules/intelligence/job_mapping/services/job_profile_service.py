"""Job profile catalog service for managing KASH job profiles."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..models import (
    JobProfile, 
    JobProfileCatalog, 
    KASHDomainEnum,
    JobSectorEnum,
    SeniorityLevelEnum,
    RegionAvailabilityEnum
)


class JobProfileService:
    """Service for managing job profile catalog and operations."""
    
    def __init__(self, catalog_path: Optional[Path] = None):
        self.catalog_path = catalog_path or Path(__file__).parent.parent / "catalog" / "job_profiles_sample.json"
        self.catalog: Optional[JobProfileCatalog] = None
        self._load_catalog()
    
    def _load_catalog(self):
        """Load job profile catalog from JSON file."""
        try:
            if self.catalog_path.exists():
                with open(self.catalog_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Convert JSON data to JobProfile objects
                profiles = {}
                for job_id, profile_data in data.get("job_profiles", {}).items():
                    profile = JobProfile(**profile_data)
                    profiles[job_id] = profile
                
                self.catalog = JobProfileCatalog(
                    profiles=profiles,
                    last_updated=datetime.fromisoformat(data["metadata"]["last_updated"]),
                    total_profiles=len(profiles),
                    version=data["metadata"]["catalog_version"]
                )
                
                print(f"✅ Loaded {self.catalog.total_profiles} job profiles from catalog")
            else:
                print(f"⚠️ Catalog file not found at {self.catalog_path}")
                self.catalog = JobProfileCatalog(profiles={}, total_profiles=0, version="1.0")
                
        except Exception as e:
            print(f"❌ Error loading catalog: {e}")
            self.catalog = JobProfileCatalog(profiles={}, total_profiles=0, version="1.0")
    
    def get_all_profiles(self) -> List[JobProfile]:
        """Get all job profiles from catalog."""
        if not self.catalog:
            return []
        return list(self.catalog.profiles.values())
    
    def get_profile_by_id(self, job_id: str) -> Optional[JobProfile]:
        """Get job profile by ID."""
        if not self.catalog:
            return None
        return self.catalog.get_profile_by_id(job_id)
    
    def get_profiles_by_sector(self, sector: JobSectorEnum) -> List[JobProfile]:
        """Get all profiles in a specific sector."""
        if not self.catalog:
            return []
        return self.catalog.get_profiles_by_sector(sector)
    
    def get_profiles_by_seniority(self, seniority: SeniorityLevelEnum) -> List[JobProfile]:
        """Get all profiles for a specific seniority level."""
        if not self.catalog:
            return []
        return self.catalog.get_profiles_by_seniority(seniority)
    
    def get_profiles_by_region(self, region: RegionAvailabilityEnum) -> List[JobProfile]:
        """Get all profiles available in a specific region."""
        if not self.catalog:
            return []
        
        return [
            profile for profile in self.catalog.profiles.values()
            if region in profile.metadata.regional_availability
        ]
    
    def search_profiles(self, query: str, limit: int = 10) -> List[JobProfile]:
        """Search profiles by title or description."""
        if not self.catalog:
            return []
        return self.catalog.search_profiles(query, limit)
    
    def get_profiles_by_kash_domain(self, domain: KASHDomainEnum, min_weight: float = 0.5) -> List[JobProfile]:
        """Get profiles that have significant weight in a specific KASH domain."""
        if not self.catalog:
            return []
        
        matching_profiles = []
        for profile in self.catalog.profiles.values():
            domain_weight = profile.get_total_weight_by_domain(domain)
            if domain_weight >= min_weight:
                matching_profiles.append(profile)
        
        return matching_profiles
    
    def get_competency_statistics(self) -> Dict[str, Any]:
        """Get statistics about competencies across all job profiles."""
        if not self.catalog:
            return {}
        
        stats = {
            "total_profiles": self.catalog.total_profiles,
            "competency_counts": {
                "knowledge": 0,
                "abilities": 0,
                "skills": 0,
                "habits": 0
            },
            "sector_distribution": {},
            "seniority_distribution": {},
            "average_competencies_per_profile": 0,
            "most_common_competencies": {}
        }
        
        total_competencies = 0
        competency_frequency = {}
        
        for profile in self.catalog.profiles.values():
            # Count competencies by domain
            stats["competency_counts"]["knowledge"] += len(profile.knowledge_competencies)
            stats["competency_counts"]["abilities"] += len(profile.abilities_competencies)
            stats["competency_counts"]["skills"] += len(profile.skills_competencies)
            stats["competency_counts"]["habits"] += len(profile.habits_competencies)
            
            total_competencies += len(profile.all_competencies)
            
            # Track sector distribution
            for sector in profile.metadata.sectors:
                stats["sector_distribution"][sector.value] = stats["sector_distribution"].get(sector.value, 0) + 1
            
            # Track seniority distribution
            for seniority in profile.metadata.seniority_levels:
                stats["seniority_distribution"][seniority.value] = stats["seniority_distribution"].get(seniority.value, 0) + 1
            
            # Track competency frequency
            for competency in profile.all_competencies:
                comp_key = f"{competency.domain.value}:{competency.name}"
                competency_frequency[comp_key] = competency_frequency.get(comp_key, 0) + 1
        
        # Calculate averages
        if self.catalog.total_profiles > 0:
            stats["average_competencies_per_profile"] = total_competencies / self.catalog.total_profiles
        
        # Get most common competencies
        sorted_competencies = sorted(competency_frequency.items(), key=lambda x: x[1], reverse=True)
        stats["most_common_competencies"] = dict(sorted_competencies[:10])
        
        return stats
    
    def get_similar_profiles(self, job_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find profiles similar to the given job profile."""
        target_profile = self.get_profile_by_id(job_id)
        if not target_profile:
            return []
        
        similarities = []
        
        for profile in self.catalog.profiles.values():
            if profile.job_id == job_id:
                continue
            
            # Calculate similarity based on multiple factors
            similarity_score = 0.0
            
            # Sector overlap (40% weight)
            sector_overlap = len(set(target_profile.metadata.sectors) & set(profile.metadata.sectors))
            sector_similarity = sector_overlap / max(len(target_profile.metadata.sectors), len(profile.metadata.sectors))
            similarity_score += sector_similarity * 0.4
            
            # Seniority overlap (30% weight)
            seniority_overlap = len(set(target_profile.metadata.seniority_levels) & set(profile.metadata.seniority_levels))
            seniority_similarity = seniority_overlap / max(len(target_profile.metadata.seniority_levels), len(profile.metadata.seniority_levels))
            similarity_score += seniority_similarity * 0.3
            
            # Competency overlap (30% weight)
            target_competencies = {comp.name for comp in target_profile.all_competencies}
            profile_competencies = {comp.name for comp in profile.all_competencies}
            competency_overlap = len(target_competencies & profile_competencies)
            competency_similarity = competency_overlap / max(len(target_competencies), len(profile_competencies))
            similarity_score += competency_similarity * 0.3
            
            similarities.append({
                "profile": profile,
                "similarity_score": similarity_score,
                "sector_similarity": sector_similarity,
                "seniority_similarity": seniority_similarity,
                "competency_similarity": competency_similarity
            })
        
        # Sort by similarity score and return top matches
        similarities.sort(key=lambda x: x["similarity_score"], reverse=True)
        return similarities[:limit]
    
    def validate_profile(self, profile: JobProfile) -> Dict[str, Any]:
        """Validate a job profile for completeness and consistency."""
        validation_result = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "recommendations": []
        }
        
        # Check required fields
        if not profile.title or len(profile.title.strip()) < 3:
            validation_result["errors"].append("Title must be at least 3 characters long")
            validation_result["is_valid"] = False
        
        if not profile.description or len(profile.description.strip()) < 10:
            validation_result["errors"].append("Description must be at least 10 characters long")
            validation_result["is_valid"] = False
        
        if not profile.success_criteria:
            validation_result["errors"].append("Success criteria are required")
            validation_result["is_valid"] = False
        
        # Check competency balance
        total_competencies = len(profile.all_competencies)
        if total_competencies == 0:
            validation_result["errors"].append("At least one competency is required")
            validation_result["is_valid"] = False
        elif total_competencies < 5:
            validation_result["warnings"].append("Consider adding more competencies for better matching")
        
        # Check KASH domain balance
        domain_counts = {
            KASHDomainEnum.KNOWLEDGE: len(profile.knowledge_competencies),
            KASHDomainEnum.ABILITIES: len(profile.abilities_competencies),
            KASHDomainEnum.SKILLS: len(profile.skills_competencies),
            KASHDomainEnum.HABITS: len(profile.habits_competencies)
        }
        
        empty_domains = [domain.value for domain, count in domain_counts.items() if count == 0]
        if empty_domains:
            validation_result["warnings"].append(f"Empty KASH domains: {', '.join(empty_domains)}")
        
        # Check weight distribution
        total_weight = sum(comp.weight for comp in profile.all_competencies)
        if total_weight == 0:
            validation_result["errors"].append("Total competency weight cannot be zero")
            validation_result["is_valid"] = False
        elif abs(total_weight - 1.0) > 0.1:
            validation_result["warnings"].append(f"Total weight ({total_weight}) should sum to 1.0")
        
        # Check for duplicate competencies
        competency_names = [comp.name for comp in profile.all_competencies]
        duplicates = [name for name in competency_names if competency_names.count(name) > 1]
        if duplicates:
            validation_result["errors"].append(f"Duplicate competencies found: {', '.join(set(duplicates))}")
            validation_result["is_valid"] = False
        
        # Recommendations
        if len(profile.metadata.sectors) == 0:
            validation_result["recommendations"].append("Add at least one sector for better categorization")
        
        if len(profile.metadata.seniority_levels) == 0:
            validation_result["recommendations"].append("Add at least one seniority level")
        
        return validation_result
    
    def export_catalog_summary(self) -> Dict[str, Any]:
        """Export a summary of the job profile catalog."""
        if not self.catalog:
            return {"error": "No catalog loaded"}
        
        summary = {
            "catalog_info": {
                "version": self.catalog.version,
                "last_updated": self.catalog.last_updated.isoformat(),
                "total_profiles": self.catalog.total_profiles
            },
            "statistics": self.get_competency_statistics(),
            "sample_profiles": []
        }
        
        # Add sample profiles (first 5)
        for i, profile in enumerate(list(self.catalog.profiles.values())[:5]):
            summary["sample_profiles"].append({
                "job_id": profile.job_id,
                "title": profile.title,
                "sectors": [s.value for s in profile.metadata.sectors],
                "seniority_levels": [s.value for s in profile.metadata.seniority_levels],
                "total_competencies": len(profile.all_competencies),
                "competency_breakdown": {
                    "knowledge": len(profile.knowledge_competencies),
                    "abilities": len(profile.abilities_competencies),
                    "skills": len(profile.skills_competencies),
                    "habits": len(profile.habits_competencies)
                }
            })
        
        return summary
    
    def reload_catalog(self):
        """Reload the catalog from file."""
        self._load_catalog()
        print("🔄 Catalog reloaded")
