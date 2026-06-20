"""Models package for KASH → Job mapping system."""

from .job_profile import (
    JobProfile,
    JobProfileCatalog,
    KASHCompetency,
    JobMetadata,
    JobSectorEnum,
    SeniorityLevelEnum,
    RegionAvailabilityEnum,
    KASHDomainEnum,
    CompetencyLevel,
)

from .matching_result import (
    JobMatchResult,
    JobMatchingRequest,
    JobMatchingResponse,
    CompetencyMatch,
    DomainMatchResult,
    ConfidenceMetrics,
    AlternativeSuggestion,
    MatchScoreType,
    ConfidenceLevel,
)

__all__ = [
    # Job profile models
    "JobProfile",
    "JobProfileCatalog", 
    "KASHCompetency",
    "JobMetadata",
    "JobSectorEnum",
    "SeniorityLevelEnum",
    "RegionAvailabilityEnum",
    "KASHDomainEnum",
    "CompetencyLevel",
    
    # Matching result models
    "JobMatchResult",
    "JobMatchingRequest",
    "JobMatchingResponse",
    "CompetencyMatch",
    "DomainMatchResult",
    "ConfidenceMetrics",
    "AlternativeSuggestion",
    "MatchScoreType",
    "ConfidenceLevel",
]
