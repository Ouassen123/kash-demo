"""Job profile models for KASH → Job mapping system."""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


class JobSectorEnum(str, Enum):
    """Job sector enumeration."""
    TECHNOLOGY = "technology"
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    EDUCATION = "education"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    GOVERNMENT = "government"
    CONSULTING = "consulting"
    MEDIA = "media"
    NON_PROFIT = "non_profit"
    OTHER = "other"


class SeniorityLevelEnum(str, Enum):
    """Seniority level enumeration."""
    ENTRY_LEVEL = "entry_level"
    JUNIOR = "junior"
    MID_LEVEL = "mid_level"
    SENIOR = "senior"
    LEAD = "lead"
    MANAGER = "manager"
    DIRECTOR = "director"
    EXECUTIVE = "executive"


class RegionAvailabilityEnum(str, Enum):
    """Regional availability enumeration."""
    GLOBAL = "global"
    NORTH_AMERICA = "north_america"
    EUROPE = "europe"
    ASIA_PACIFIC = "asia_pacific"
    LATIN_AMERICA = "latin_america"
    MIDDLE_EAST = "middle_east"
    AFRICA = "africa"


class KASHDomainEnum(str, Enum):
    """KASH domain enumeration."""
    KNOWLEDGE = "knowledge"
    ABILITIES = "abilities"
    SKILLS = "skills"
    HABITS = "habits"


class CompetencyLevel(str, Enum):
    """Competency level enumeration."""
    NONE = "none"
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class KASHCompetency(BaseModel):
    """Individual KASH competency requirement."""
    domain: KASHDomainEnum
    category: str = Field(..., description="Competency category within domain")
    name: str = Field(..., description="Competency name")
    required_level: CompetencyLevel = Field(..., description="Required proficiency level")
    weight: float = Field(..., ge=0, le=1, description="Weight in overall matching score")
    description: str = Field(..., description="What this competency entails")
    success_signals: List[str] = Field(default_factory=list, description="Signals of success in this competency")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "domain": "skills",
                "category": "programming",
                "name": "python_programming",
                "required_level": "intermediate",
                "weight": 0.8,
                "description": "Proficiency in Python programming language",
                "success_signals": [
                    "Can build complex applications",
                    "Understands OOP concepts",
                    "Can debug and optimize code"
                ]
            }
        }
    }


class JobMetadata(BaseModel):
    """Job profile metadata."""
    sectors: List[JobSectorEnum] = Field(..., description="Primary sectors for this role")
    seniority_levels: List[SeniorityLevelEnum] = Field(..., description="Applicable seniority levels")
    regional_availability: List[RegionAvailabilityEnum] = Field(..., description="Geographic availability")
    typical_experience_years: Optional[str] = Field(None, description="Typical years of experience required")
    education_requirements: Optional[str] = Field(None, description="Typical education requirements")
    salary_range: Optional[Dict[str, Any]] = Field(None, description="Salary range information")
    growth_potential: Optional[str] = Field(None, description="Career growth potential")
    demand_level: Optional[str] = Field(None, description="Current market demand")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "sectors": ["technology", "finance"],
                "seniority_levels": ["mid_level", "senior"],
                "regional_availability": ["global"],
                "typical_experience_years": "3-5 years",
                "education_requirements": "Bachelor's degree in Computer Science or related field",
                "salary_range": {"min": 80000, "max": 150000, "currency": "USD"},
                "growth_potential": "High - can progress to senior developer or architect roles",
                "demand_level": "Very High"
            }
        }
    }


class JobProfile(BaseModel):
    """Complete job profile with KASH competency requirements."""
    job_id: str = Field(..., description="Unique job profile identifier")
    title: str = Field(..., description="Job title")
    description: str = Field(..., description="Job description")
    metadata: JobMetadata = Field(..., description="Job metadata")
    
    # KASH competency requirements
    knowledge_competencies: List[KASHCompetency] = Field(default_factory=list, description="Knowledge domain requirements")
    abilities_competencies: List[KASHCompetency] = Field(default_factory=list, description="Abilities domain requirements")
    skills_competencies: List[KASHCompetency] = Field(default_factory=list, description="Skills domain requirements")
    habits_competencies: List[KASHCompetency] = Field(default_factory=list, description="Habits domain requirements")
    
    # Success criteria and rationale
    success_criteria: List[str] = Field(..., description="Key success criteria for this role")
    rationale: str = Field(..., description="Why this role matters and career rationale")
    career_path: Optional[str] = Field(None, description="Typical career progression path")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(True, description="Whether this profile is active")
    version: str = Field(default="1.0", description="Profile version")
    
    @property
    def all_competencies(self) -> List[KASHCompetency]:
        """Get all competencies across all KASH domains."""
        return (
            self.knowledge_competencies +
            self.abilities_competencies +
            self.skills_competencies +
            self.habits_competencies
        )
    
    def get_competencies_by_domain(self, domain: KASHDomainEnum) -> List[KASHCompetency]:
        """Get competencies for a specific KASH domain."""
        domain_map = {
            KASHDomainEnum.KNOWLEDGE: self.knowledge_competencies,
            KASHDomainEnum.ABILITIES: self.abilities_competencies,
            KASHDomainEnum.SKILLS: self.skills_competencies,
            KASHDomainEnum.HABITS: self.habits_competencies,
        }
        return domain_map.get(domain, [])
    
    def get_total_weight_by_domain(self, domain: KASHDomainEnum) -> float:
        """Get total weight for a specific KASH domain."""
        competencies = self.get_competencies_by_domain(domain)
        return sum(comp.weight for comp in competencies)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "job_id": "software_developer_001",
                "title": "Software Developer",
                "description": "Design, develop, and maintain software applications",
                "metadata": {
                    "sectors": ["technology"],
                    "seniority_levels": ["mid_level"],
                    "regional_availability": ["global"]
                },
                "knowledge_competencies": [
                    {
                        "domain": "knowledge",
                        "category": "computer_science",
                        "name": "algorithms_and_data_structures",
                        "required_level": "intermediate",
                        "weight": 0.7,
                        "description": "Understanding of fundamental algorithms and data structures"
                    }
                ],
                "success_criteria": [
                    "Delivers high-quality code on time",
                    "Collaborates effectively with team members",
                    "Continuously learns new technologies"
                ],
                "rationale": "Software developers are essential for building digital solutions that drive business innovation and user experiences."
            }
        }
    }


class JobProfileCatalog(BaseModel):
    """Catalog of job profiles with search and filtering capabilities."""
    profiles: Dict[str, JobProfile] = Field(..., description="Job profiles indexed by job_id")
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    total_profiles: int = Field(..., description="Total number of profiles in catalog")
    version: str = Field(default="1.0", description="Catalog version")
    
    def get_profile_by_id(self, job_id: str) -> Optional[JobProfile]:
        """Get job profile by ID."""
        return self.profiles.get(job_id)
    
    def get_profiles_by_sector(self, sector: JobSectorEnum) -> List[JobProfile]:
        """Get all profiles in a specific sector."""
        return [
            profile for profile in self.profiles.values()
            if sector in profile.metadata.sectors
        ]
    
    def get_profiles_by_seniority(self, seniority: SeniorityLevelEnum) -> List[JobProfile]:
        """Get all profiles for a specific seniority level."""
        return [
            profile for profile in self.profiles.values()
            if seniority in profile.metadata.seniority_levels
        ]
    
    def search_profiles(self, query: str, limit: int = 10) -> List[JobProfile]:
        """Search profiles by title or description."""
        query_lower = query.lower()
        matching_profiles = []
        
        for profile in self.profiles.values():
            if (query_lower in profile.title.lower() or 
                query_lower in profile.description.lower()):
                matching_profiles.append(profile)
        
        return matching_profiles[:limit]
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "profiles": {},
                "last_updated": "2024-01-01T12:00:00Z",
                "total_profiles": 50,
                "version": "1.0"
            }
        }
    }
