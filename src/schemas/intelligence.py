"""Intelligence module schemas for API requests/responses."""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
from enum import Enum


class CareerStageEnum(str, Enum):
    """Career stage enumeration."""
    EXPLORER = "explorer"
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class ExplanationTypeEnum(str, Enum):
    """Explanation type enumeration."""
    FEATURE_IMPORTANCE = "feature_importance"
    CAREER_PATH = "career_path"
    SKILL_GAP = "skill_gap"
    ASSESSMENT_IMPACT = "assessment_impact"
    RECOMMENDATION_REASONING = "recommendation_reasoning"


class ExperienceLevelEnum(str, Enum):
    """Experience level enumeration."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class IntelligenceAssessmentRequest(BaseModel):
    """Request for comprehensive intelligence assessment."""
    industry: Optional[str] = Field(None, description="Target industry for weight adjustment")
    career_goals: Optional[List[str]] = Field(None, description="List of career goals")
    custom_weights: Optional[Dict[str, float]] = Field(None, description="Custom KASH weight overrides")
    
    @validator('custom_weights')
    def validate_weights(cls, v):
        if v is None:
            return v
        
        # Ensure weights sum to 1.0
        total_weight = sum(v.values())
        if abs(total_weight - 1.0) > 0.1:
            raise ValueError("Custom weights must sum to approximately 1.0")
        
        # Validate weight values
        for key, weight in v.items():
            if not 0.0 <= weight <= 1.0:
                raise ValueError(f"Weight for {key} must be between 0.0 and 1.0")
        
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "industry": "technology",
                "career_goals": ["software_engineer", "data_scientist"],
                "custom_weights": {
                    "knowledge": 0.3,
                    "abilities": 0.2,
                    "skills": 0.4,
                    "experience": 0.1
                }
            }
        }


class FeatureImportance(BaseModel):
    """Feature importance with SHAP values."""
    feature_name: str
    feature_value: float
    shap_value: float
    contribution_percentage: float
    direction: str = Field(..., pattern="^(positive|negative|neutral)$")
    explanation: str
    
    class Config:
        from_attributes = True


class CareerPathExplanation(BaseModel):
    """Explanation for career path recommendation."""
    career_path: str
    match_score: float = Field(..., ge=0.0, le=100.0, description="Career match score (0-100)")
    key_factors: List[str]
    skill_gaps: List[str]
    alignment_reasons: List[str]
    development_needs: List[str]
    
    class Config:
        from_attributes = True


class SkillGapAnalysis(BaseModel):
    """Analysis of skill gaps for target role."""
    target_role: str
    experience_level: ExperienceLevelEnum
    current_skills: Dict[str, float]
    required_skills: Dict[str, float]
    skill_gaps: Dict[str, float]
    priority_gaps: List[str]
    development_timeline: Dict[str, str]
    
    class Config:
        from_attributes = True


class AssessmentImpact(BaseModel):
    """Impact of specific assessment on overall score."""
    assessment_type: str
    assessment_name: str
    score_contribution: float
    confidence_impact: float
    improvement_potential: float
    
    class Config:
        from_attributes = True


class RecommendationExplanation(BaseModel):
    """Explanation for a specific recommendation."""
    recommendation: str
    type: str
    explanation: str
    priority: str = Field(..., pattern="^(high|medium|low)$")
    expected_impact: Dict[str, float]
    
    class Config:
        from_attributes = True


class KASHScore(BaseModel):
    """KASH domain scores."""
    overall_score: float = Field(..., ge=0.0, le=100.0)
    knowledge_score: float = Field(..., ge=0.0, le=100.0)
    abilities_score: float = Field(..., ge=0.0, le=100.0)
    skills_score: float = Field(..., ge=0.0, le=100.0)
    experience_score: float = Field(..., ge=0.0, le=100.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    career_stage: CareerStageEnum
    strengths: List[str]
    improvement_areas: List[str]
    recommendations: List[str]
    
    class Config:
        from_attributes = True


class IntelligenceAssessmentResults(BaseModel):
    """Complete intelligence assessment results."""
    assessment_id: str
    assessment_name: str
    status: str
    created_at: datetime
    completed_at: datetime
    
    # KASH scoring
    kash_score: KASHScore
    
    # SHAP explanations
    feature_importance: List[FeatureImportance]
    career_explanations: List[CareerPathExplanation]
    skill_gap_analysis: List[Dict[str, Any]]
    assessment_impacts: List[AssessmentImpact]
    recommendation_explanations: Dict[str, RecommendationExplanation]
    
    # Input parameters
    industry: Optional[str]
    career_goals: Optional[List[str]]
    custom_weights: Optional[Dict[str, float]]
    
    class Config:
        from_attributes = True


class IntelligenceAssessmentSummary(BaseModel):
    """Summary of intelligence assessment for list views."""
    assessment_id: str
    assessment_name: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime]
    
    # Quick KASH scores
    overall_score: Optional[float]
    confidence: Optional[float]
    career_stage: Optional[str]
    
    # Quick stats
    industry: Optional[str]
    career_goals_count: int
    strengths_count: int
    recommendations_count: int
    
    class Config:
        from_attributes = True


class IntelligenceProfileResponse(BaseModel):
    """Complete intelligence profile for a user."""
    user_id: str
    total_assessments: int
    current_kash_score: Optional[Dict[str, float]]
    kash_trend: List[Dict[str, Any]]
    career_insights: Dict[str, Any]
    feature_importance_trends: Dict[str, Any]
    recommendation_history: List[Dict[str, Any]]
    skill_development_progress: Dict[str, Any]
    last_assessment: Optional[str]
    career_stage: Optional[str]
    confidence: Optional[float]
    
    class Config:
        from_attributes = True


class CareerPathRequest(BaseModel):
    """Request for career path explanation."""
    target_career: str = Field(..., min_length=1, description="Target career path")
    
    class Config:
        schema_extra = {
            "example": {
                "target_career": "software_engineer"
            }
        }


class CareerPathResponse(BaseModel):
    """Career path explanation response."""
    career_path: str
    explanation: Dict[str, Any]
    generated_at: str
    
    class Config:
        from_attributes = True


class SkillGapRequest(BaseModel):
    """Request for skill gap analysis."""
    target_role: str = Field(..., min_length=1, description="Target role name")
    experience_level: ExperienceLevelEnum = Field(ExperienceLevelEnum.INTERMEDIATE, description="Required experience level")
    
    class Config:
        schema_extra = {
            "example": {
                "target_role": "data_scientist",
                "experience_level": "intermediate"
            }
        }


class SkillGapResponse(BaseModel):
    """Skill gap analysis response."""
    target_role: str
    experience_level: ExperienceLevelEnum
    analysis: Dict[str, Any]
    generated_at: str
    
    class Config:
        from_attributes = True


class KASHDomainScore(BaseModel):
    """Individual KASH domain score."""
    domain: str
    score: float
    confidence: float
    weight: float
    breakdown: Dict[str, float]
    evidence: List[str]
    
    class Config:
        from_attributes = True


class FeatureTrend(BaseModel):
    """Feature importance trend over time."""
    feature_name: str
    current_importance: float
    trend_direction: str = Field(..., pattern="^(increasing|decreasing|stable)$")
    historical_values: List[Dict[str, Any]]
    
    class Config:
        from_attributes = True


class RecommendationHistory(BaseModel):
    """Historical recommendations."""
    date: str
    recommendations: List[str]
    career_stage: str
    implemented_count: Optional[int]
    
    class Config:
        from_attributes = True


class SkillProgress(BaseModel):
    """Skill development progress."""
    skill_name: str
    current_level: float
    target_level: float
    progress_percentage: float
    estimated_completion_date: Optional[str]
    
    class Config:
        from_attributes = True


class CareerInsight(BaseModel):
    """Career insight and recommendation."""
    insight_type: str
    title: str
    description: str
    supporting_data: Dict[str, Any]
    actionable: bool
    priority: str = Field(..., pattern="^(high|medium|low)$")
    
    class Config:
        from_attributes = True


class IndustryBenchmark(BaseModel):
    """Industry benchmark comparison."""
    industry: str
    user_score: float
    industry_average: float
    percentile_rank: float
    top_performers_score: float
    improvement_potential: float
    
    class Config:
        from_attributes = True


class LearningPath(BaseModel):
    """Personalized learning path."""
    path_id: str
    title: str
    description: str
    estimated_weeks: int
    difficulty_level: ExperienceLevelEnum
    required_skills: List[str]
    learning_modules: List[Dict[str, Any]]
    milestones: List[str]
    resources: List[Dict[str, Any]]
    
    class Config:
        from_attributes = True


class IntelligenceMetrics(BaseModel):
    """Intelligence system metrics."""
    total_assessments: int
    average_kash_score: float
    career_stage_distribution: Dict[str, int]
    top_industries: List[str]
    common_career_goals: List[str]
    feature_importance_summary: Dict[str, float]
    
    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "error": "assessment_not_found",
                "message": "Intelligence assessment not found",
                "details": {
                    "assessment_id": "123e4567-e89b-12d3-a456-426614174000"
                }
            }
        }


class BulkIntelligenceRequest(BaseModel):
    """Request for bulk intelligence assessment."""
    user_ids: List[str] = Field(..., min_items=1, max_items=50, description="List of user IDs")
    assessment_config: Optional[IntelligenceAssessmentRequest] = Field(None, description="Assessment configuration")
    
    @validator('user_ids')
    def validate_user_ids(cls, v):
        if not v:
            raise ValueError('At least one user ID must be provided')
        return v


class BulkIntelligenceResponse(BaseModel):
    """Response for bulk intelligence assessment."""
    assessment_ids: List[str]
    total_users: int
    successful_assessments: int
    failed_assessments: List[Dict[str, str]]
    processing_time_seconds: float
    
    class Config:
        from_attributes = True


class ComparisonRequest(BaseModel):
    """Request for intelligence score comparison."""
    comparison_type: str = Field(..., pattern="^(industry|career_stage|time_period)$")
    comparison_value: str
    user_group: Optional[List[str]] = Field(None, description="Specific user group for comparison")
    
    class Config:
        schema_extra = {
            "example": {
                "comparison_type": "industry",
                "comparison_value": "technology",
                "user_group": ["user1", "user2"]
            }
        }


class ComparisonResponse(BaseModel):
    """Intelligence score comparison response."""
    comparison_type: str
    comparison_value: str
    user_scores: Dict[str, float]
    benchmark_scores: Dict[str, float]
    insights: List[str]
    recommendations: List[str]
    
    class Config:
        from_attributes = True


class PredictionRequest(BaseModel):
    """Request for career prediction."""
    prediction_type: str = Field(..., pattern="^(career_success|skill_development|time_to_promotion)$")
    target_role: Optional[str]
    time_horizon_months: int = Field(default=12, ge=1, le=60, description="Prediction time horizon in months")
    
    class Config:
        schema_extra = {
            "example": {
                "prediction_type": "career_success",
                "target_role": "software_engineer",
                "time_horizon_months": 12
            }
        }


class PredictionResponse(BaseModel):
    """Career prediction response."""
    prediction_type: str
    prediction_score: float
    confidence_interval: Tuple[float, float]
    key_factors: List[str]
    recommendations: List[str]
    generated_at: str
    
    class Config:
        from_attributes = True
