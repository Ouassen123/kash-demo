"""Educational feedback and scoring schemas for API responses."""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


class MetricCategoryEnum(str, Enum):
    """Metric category enumeration."""
    COMPLEXITY = "complexity"
    MAINTAINABILITY = "maintainability"
    SECURITY = "security"
    STYLE = "style"
    PERFORMANCE = "performance"
    RELIABILITY = "reliability"
    DOCUMENTATION = "documentation"


class FeedbackTypeEnum(str, Enum):
    """Feedback type enumeration."""
    IMMEDIATE = "immediate"
    LEARNING = "learning"
    IMPROVEMENT = "improvement"
    ENCOURAGEMENT = "encouragement"


class LearningPathEnum(str, Enum):
    """Learning path enumeration."""
    BEGINNER_FOCUS = "beginner_focus"
    INTERMEDIATE_GROWTH = "intermediate_growth"
    ADVANCED_MASTERY = "advanced_mastery"
    MIXED_LEVEL = "mixed_level"


class SeverityDistribution(BaseModel):
    """Severity distribution for findings."""
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0


class QualityMetricResponse(BaseModel):
    """Quality metric response."""
    name: str
    category: MetricCategoryEnum
    score: float = Field(..., ge=0, le=100, description="Score from 0-100")
    weight: float = Field(..., ge=0, le=1, description="Importance weight")
    description: str
    findings_count: int
    severity_distribution: SeverityDistribution
    details: Dict[str, Any]


class QualityScoreResponse(BaseModel):
    """Quality score response."""
    overall_score: float = Field(..., ge=0, le=100, description="Overall quality score 0-100")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in the score")
    grade: str = Field(..., description="Letter grade A-F")
    metrics: List[QualityMetricResponse]
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]


class FeedbackItemResponse(BaseModel):
    """Feedback item response."""
    type: FeedbackTypeEnum
    title: str
    message: str
    priority: int = Field(..., ge=1, le=10, description="Priority 1-10")
    actionable: bool
    estimated_effort: str = Field(..., description="quick/moderate/significant")
    related_findings: List[str]
    learning_resources: List[str]
    next_steps: List[str]


class LearningResourceResponse(BaseModel):
    """Learning resource response."""
    title: str
    url: str


class LearningRecommendationResponse(BaseModel):
    """Learning recommendation response."""
    skill_area: str
    current_level: str
    target_level: str
    description: str
    resources: List[LearningResourceResponse]
    practice_exercises: List[str]
    estimated_time: str
    prerequisites: List[str]


class ProgressIndicatorsResponse(BaseModel):
    """Progress indicators response."""
    total_issues: int
    severity_breakdown: SeverityDistribution
    quality_score: float
    grade: str
    categories_analyzed: int
    improvement_potential: float = Field(..., ge=0, le=100, description="Potential improvement 0-100")
    next_milestone: str


class EducationalFeedbackResponse(BaseModel):
    """Educational feedback response."""
    overall_summary: str
    grade: str
    strengths: List[str]
    improvement_areas: List[str]
    feedback_items: List[FeedbackItemResponse]
    learning_path: LearningPathEnum
    recommendations: List[LearningRecommendationResponse]
    progress_indicators: ProgressIndicatorsResponse
    motivational_message: str


class EducationalAnalysisRequest(BaseModel):
    """Request for educational code analysis."""
    analysis_profile: str = Field("educational", description="Analysis profile to use")
    include_quality_metrics: bool = Field(True, description="Include quality metrics calculation")
    include_educational_feedback: bool = Field(True, description="Include educational feedback")
    language_hint: Optional[str] = Field(None, description="Optional language hint for better analysis")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "analysis_profile": "educational",
                "include_quality_metrics": True,
                "include_educational_feedback": True,
                "language_hint": "java"
            }
        }
    }


class EducationalAnalysisResponse(BaseModel):
    """Educational analysis response."""
    submission_id: str
    learner_id: str
    analysis_profile: str
    overall_score: float
    confidence: float
    summary: str
    analyzed_at: datetime
    quality_score: Optional[QualityScoreResponse] = None
    educational_feedback: Optional[EducationalFeedbackResponse] = None
    analyzer_reports: List[Dict[str, Any]]


class LearningPathRequest(BaseModel):
    """Request for personalized learning path."""
    current_skills: Dict[str, str] = Field(..., description="Current skill levels")
    target_skills: Dict[str, str] = Field(..., description="Target skill levels")
    preferred_learning_style: Optional[str] = Field(None, description="Preferred learning style")
    time_commitment: Optional[str] = Field(None, description="Weekly time commitment")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "current_skills": {
                    "python": "intermediate",
                    "java": "beginner"
                },
                "target_skills": {
                    "python": "advanced",
                    "java": "intermediate"
                },
                "preferred_learning_style": "visual",
                "time_commitment": "5-10 hours"
            }
        }
    }


class LearningStepResponse(BaseModel):
    """Learning step response."""
    step_number: int
    title: str
    description: str
    skill_area: str
    resources: List[LearningResourceResponse]
    practice_exercises: List[str]
    estimated_time: str
    prerequisites: List[str]
    completion_criteria: str


class LearningPathResponse(BaseModel):
    """Personalized learning path response."""
    path_id: str
    learner_id: str
    current_level: str
    target_level: str
    estimated_duration: str
    steps: List[LearningStepResponse]
    progress_indicators: Dict[str, Any]
    milestones: List[str]


class SkillAssessmentRequest(BaseModel):
    """Request for skill assessment."""
    code_samples: List[Dict[str, Any]] = Field(..., description="Code samples to assess")
    focus_areas: Optional[List[str]] = Field(None, description="Specific skill areas to focus on")
    depth_level: str = Field("standard", description="Assessment depth: basic/standard/comprehensive")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "code_samples": [
                    {
                        "language": "python",
                        "code": "def hello_world():\n    print('Hello, World!')",
                        "filename": "hello.py"
                    }
                ],
                "focus_areas": ["syntax", "style", "best_practices"],
                "depth_level": "standard"
            }
        }
    }


class SkillAssessmentResponse(BaseModel):
    """Skill assessment response."""
    assessment_id: str
    learner_id: str
    overall_score: float
    skill_breakdown: Dict[str, float]
    strengths: List[str]
    improvement_areas: List[str]
    recommendations: List[str]
    next_assessment_date: Optional[datetime] = None
    assessed_at: datetime
