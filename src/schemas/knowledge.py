"""Knowledge module schemas for API requests/responses."""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Any, Optional
from datetime import datetime


class CVAnalysisRequest(BaseModel):
    """Request schema for CV analysis."""
    cv_text: str = Field(..., min_length=100, description="Raw CV text content")
    cv_filename: Optional[str] = Field(None, description="Original filename")
    
    @validator('cv_text')
    def validate_cv_text(cls, v):
        if not v or len(v.strip()) < 100:
            raise ValueError('CV text must be at least 100 characters long')
        return v.strip()


class SkillMatchResponse(BaseModel):
    """Skill matching response schema."""
    user_skill: str
    esco_skill: Dict[str, Any]
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    match_type: str = Field(..., pattern="^(exact|partial|semantic)$")


class OccupationMatchResponse(BaseModel):
    """Occupation matching response schema."""
    occupation: Dict[str, Any]
    match_score: float = Field(..., ge=0.0, le=1.0)
    required_skills: List[str]
    missing_skills: List[str]
    skill_coverage: float = Field(..., ge=0.0, le=1.0)


class KnowledgeScoreResponse(BaseModel):
    """Knowledge score breakdown response."""
    raw_score: float = Field(..., ge=0.0, le=1.0)
    normalized_score: float = Field(..., ge=0.0, le=100.0)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    domain_breakdown: Dict[str, float]


class CVAnalysisResponse(BaseModel):
    """Complete CV analysis response."""
    assessment_id: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime]
    
    # Parsed CV data
    contact_info: Dict[str, Any]
    experience: List[Dict[str, Any]]
    education: List[Dict[str, Any]]
    skills: List[Dict[str, Any]]
    projects: List[Dict[str, Any]]
    certifications: List[str]
    languages: List[Dict[str, Any]]
    
    # Analysis results
    skill_matches: List[SkillMatchResponse]
    occupation_matches: List[OccupationMatchResponse]
    knowledge_scores: KnowledgeScoreResponse
    
    # Metrics
    total_experience_years: float
    skill_diversity: int
    processing_time_ms: float
    confidence_score: float
    
    class Config:
        from_attributes = True


class KnowledgeAssessmentSummary(BaseModel):
    """Knowledge assessment summary for list views."""
    assessment_id: str
    assessment_name: str
    status: str
    normalized_score: Optional[float]
    confidence_score: Optional[float]
    created_at: datetime
    completed_at: Optional[datetime]
    
    # Quick stats
    total_skills_found: int
    occupations_suggested: int
    experience_years: float
    
    class Config:
        from_attributes = True


class SkillGapResponse(BaseModel):
    """Skill gap analysis response."""
    occupation: str
    missing_skills: List[str]
    skill_coverage: float
    priority: str = Field(..., pattern="^(high|medium|low)$")


class KnowledgeProfileResponse(BaseModel):
    """Complete knowledge profile response."""
    user_id: str
    total_assessments: int
    latest_assessment: Optional[KnowledgeAssessmentSummary]
    
    # Aggregated metrics
    average_knowledge_score: Optional[float]
    skill_categories: Dict[str, int]  # Skills by category
    top_skills: List[str]  # Top 10 skills
    career_suggestions: List[str]  # Top 5 career suggestions
    
    # Progress tracking
    skill_gaps: List[SkillGapResponse]
    learning_recommendations: List[str]


class ESCOSkillResponse(BaseModel):
    """ESCO skill response."""
    uri: str
    preferred_label: str
    description: str
    skill_type: str
    concept_uri: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class ESCOOccupationResponse(BaseModel):
    """ESCO occupation response."""
    uri: str
    preferred_label: str
    description: str
    concept_uri: str
    isco_code: Optional[str]
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class ESCOSearchRequest(BaseModel):
    """ESCO search request."""
    query: str = Field(..., min_length=2, description="Search query")
    type: str = Field(..., pattern="^(skill|occupation)$", description="Search type")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum results")


class ESCOSearchResponse(BaseModel):
    """ESCO search response."""
    query: str
    type: str
    total_found: int
    results: List[Dict[str, Any]]


class SkillMappingRequest(BaseModel):
    """Skill mapping request."""
    skills: List[str] = Field(..., min_items=1, description="List of user skills")
    
    @validator('skills')
    def validate_skills(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one skill must be provided')
        # Remove duplicates and empty strings
        return list(set(skill.strip() for skill in v if skill.strip()))


class SkillMappingResponse(BaseModel):
    """Skill mapping response."""
    user_skills: List[str]
    matches: List[SkillMatchResponse]
    total_matched: int
    match_rate: float = Field(..., ge=0.0, le=1.0)


class OccupationSuggestionRequest(BaseModel):
    """Occupation suggestion request."""
    skill_matches: List[SkillMatchResponse]
    limit: int = Field(default=10, ge=1, le=20, description="Maximum suggestions")


class OccupationSuggestionResponse(BaseModel):
    """Occupation suggestion response."""
    suggestions: List[OccupationMatchResponse]
    total_suggestions: int
    based_on_skills: int


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "error": "cv_parsing_failed",
                "message": "Failed to parse CV text",
                "details": {
                    "parsing_errors": ["Invalid date format", "Missing experience section"]
                }
            }
        }
