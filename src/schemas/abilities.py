"""Abilities module schemas for API requests/responses."""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum


class QuizTypeEnum(str, Enum):
    """Quiz type enumeration."""
    COGNITIVE = "cognitive"
    BEHAVIORAL = "behavioral"
    TECHNICAL = "technical"


class CognitiveDomainEnum(str, Enum):
    """Cognitive domain enumeration."""
    MEMORY = "memory"
    ATTENTION = "attention"
    PROCESSING_SPEED = "processing_speed"
    EXECUTIVE_FUNCTION = "executive_function"
    LANGUAGE = "language"
    VISUAL_SPATIAL = "visual_spatial"
    PROBLEM_SOLVING = "problem_solving"
    CREATIVITY = "creativity"


class DifficultyLevelEnum(str, Enum):
    """Difficulty level enumeration."""
    VERY_EASY = "1"
    EASY = "2"
    MEDIUM = "3"
    HARD = "4"
    VERY_HARD = "5"


class QuestionTypeEnum(str, Enum):
    """Question type enumeration."""
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    PATTERN_RECOGNITION = "pattern_recognition"
    LOGICAL_REASONING = "logical_reasoning"
    NUMERICAL_REASONING = "numerical_reasoning"
    VERBAL_REASONING = "verbal_reasoning"


class StartAssessmentRequest(BaseModel):
    """Request to start a new assessment."""
    quiz_type: QuizTypeEnum = Field(..., description="Type of quiz")
    domain: CognitiveDomainEnum = Field(..., description="Cognitive domain to assess")
    num_questions: int = Field(default=20, ge=5, le=50, description="Number of questions")
    adaptive: bool = Field(default=True, description="Use adaptive difficulty")
    
    class Config:
        schema_extra = {
            "example": {
                "quiz_type": "cognitive",
                "domain": "memory",
                "num_questions": 20,
                "adaptive": True
            }
        }


class QuestionResponse(BaseModel):
    """Question response schema."""
    id: str
    type: QuestionTypeEnum
    domain: CognitiveDomainEnum
    difficulty: DifficultyLevelEnum
    question_text: str
    options: List[str]
    time_limit_seconds: int
    points_possible: float
    
    class Config:
        from_attributes = True


class AssessmentStartResponse(BaseModel):
    """Response when starting an assessment."""
    assessment_id: str
    session_id: str
    quiz_type: QuizTypeEnum
    domain: CognitiveDomainEnum
    total_questions: int
    adaptive: bool
    current_question: Optional[QuestionResponse]
    question_number: int
    time_limit_seconds: int
    
    class Config:
        schema_extra = {
            "example": {
                "assessment_id": "123e4567-e89b-12d3-a456-426614174000",
                "session_id": "quiz_user_123_1642147200",
                "quiz_type": "cognitive",
                "domain": "memory",
                "total_questions": 20,
                "adaptive": True,
                "current_question": {
                    "id": "mem_001",
                    "type": "multiple_choice",
                    "domain": "memory",
                    "difficulty": "2",
                    "question_text": "What is the capital of France?",
                    "options": ["London", "Berlin", "Paris", "Madrid"],
                    "time_limit_seconds": 30,
                    "points_possible": 10.0
                },
                "question_number": 1,
                "time_limit_seconds": 30
            }
        }


class SubmitAnswerRequest(BaseModel):
    """Request to submit an answer."""
    session_id: str = Field(..., description="Quiz session ID")
    question_id: str = Field(..., description="Question being answered")
    answer: Union[str, int, float, List[str]] = Field(..., description="User's answer")
    response_time_ms: float = Field(..., ge=0, description="Time taken in milliseconds")
    
    @validator('response_time_ms')
    def validate_response_time(cls, v):
        if v <= 0 or v > 300000:  # Max 5 minutes
            raise ValueError('Response time must be between 0 and 300000 milliseconds')
        return v


class SubmitAnswerResponse(BaseModel):
    """Response after submitting an answer."""
    is_correct: bool
    question_number: int
    total_questions: int
    progress: float = Field(..., ge=0.0, le=1.0, description="Progress as percentage")
    quiz_completed: bool
    next_question: Optional[QuestionResponse]
    time_limit_seconds: Optional[int]
    results: Optional[Dict[str, Any]]  # Only included when quiz is completed


class DifficultyPerformance(BaseModel):
    """Performance by difficulty level."""
    correct: int
    total: int
    percentage: float


class DomainScore(BaseModel):
    """Score for a cognitive domain."""
    score: float
    correct: int
    total: int
    avg_response_time_ms: float


class AdaptiveResults(BaseModel):
    """Results from adaptive algorithm."""
    final_ability_estimate: float
    ability_uncertainty: float
    difficulty_progression: List[str]


class AssessmentResults(BaseModel):
    """Complete assessment results."""
    session_id: str
    quiz_type: QuizTypeEnum
    domain: CognitiveDomainEnum
    total_score: float
    percentage: float
    correct_answers: int
    total_questions: int
    time_spent_seconds: float
    avg_response_time_ms: float
    domain_scores: Dict[str, DomainScore]
    difficulty_performance: Dict[str, DifficultyPerformance]
    adaptive_results: Optional[AdaptiveResults]
    recommendations: List[str]
    completed_at: Optional[str]
    
    class Config:
        from_attributes = True


class AssessmentStatus(BaseModel):
    """Assessment status information."""
    assessment_id: str
    status: str
    quiz_type: QuizTypeEnum
    domain: CognitiveDomainEnum
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    current_question_number: Optional[int]
    total_questions: Optional[int]
    progress: Optional[float]
    time_spent_seconds: Optional[float]
    adaptive_difficulty: Optional[str]
    results: Optional[AssessmentResults]
    
    class Config:
        from_attributes = True


class AbilitiesAssessmentSummary(BaseModel):
    """Summary of abilities assessment for list views."""
    assessment_id: str
    assessment_name: str
    status: str
    quiz_type: QuizTypeEnum
    domain: CognitiveDomainEnum
    normalized_score: Optional[float]
    confidence_score: Optional[float]
    created_at: datetime
    completed_at: Optional[datetime]
    
    # Quick stats
    correct_answers: Optional[int]
    total_questions: Optional[int]
    time_spent_minutes: Optional[float]
    
    class Config:
        from_attributes = True


class CognitiveScores(BaseModel):
    """Detailed cognitive scores."""
    short_term_memory: Optional[float]
    working_memory: Optional[float]
    long_term_memory: Optional[float]
    selective_attention: Optional[float]
    divided_attention: Optional[float]
    sustained_attention: Optional[float]
    visual_processing: Optional[float]
    auditory_processing: Optional[float]
    cognitive_processing: Optional[float]
    analytical_reasoning: Optional[float]
    creative_problem_solving: Optional[float]
    critical_thinking: Optional[float]


class AbilitiesProfileResponse(BaseModel):
    """Complete abilities profile for a user."""
    user_id: str
    total_assessments: int
    domain_scores: Dict[str, float]
    overall_performance: Dict[str, Any]
    recommendations: List[str]
    recent_activity: List[Dict[str, Any]]
    last_assessment: Optional[str]
    
    class Config:
        from_attributes = True


class AvailableAssessment(BaseModel):
    """Information about available assessments."""
    domain: CognitiveDomainEnum
    display_name: str
    description: str
    estimated_time_minutes: int
    question_count: int
    adaptive: bool
    difficulty_levels: List[str]
    
    class Config:
        schema_extra = {
            "example": {
                "domain": "memory",
                "display_name": "Memory & Recall",
                "description": "Assesses short-term, working, and long-term memory capabilities",
                "estimated_time_minutes": 15,
                "question_count": 20,
                "adaptive": True,
                "difficulty_levels": ["1", "2", "3", "4", "5"]
            }
        }


class AvailableAssessmentsResponse(BaseModel):
    """Response with list of available assessments."""
    assessments: List[AvailableAssessment]
    total_count: int


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "error": "session_not_found",
                "message": "Quiz session not found or expired",
                "details": {
                    "session_id": "quiz_user_123_1642147200"
                }
            }
        }


class QuizSessionInfo(BaseModel):
    """Information about an active quiz session."""
    session_id: str
    assessment_id: str
    domain: CognitiveDomainEnum
    current_question_number: int
    total_questions: int
    progress: float
    time_spent_seconds: float
    adaptive_difficulty: DifficultyLevelEnum
    is_completed: bool
    
    class Config:
        from_attributes = True


class Recommendation(BaseModel):
    """Personalized recommendation."""
    type: str = Field(..., pattern="^(practice|study|assessment|career)$")
    priority: str = Field(..., pattern="^(high|medium|low)$")
    domain: Optional[CognitiveDomainEnum]
    estimated_time_minutes: Optional[int]
    resources: List[str] = []


class LearningPath(BaseModel):
    """Personalized learning path."""
    path_id: str
    title: str
    description: str
    target_domains: List[CognitiveDomainEnum]
    estimated_duration_weeks: int
    difficulty_progression: List[DifficultyLevelEnum]
    milestones: List[str]
    recommendations: List[Recommendation]


class AbilitiesInsight(BaseModel):
    """Insight about user's abilities."""
    insight_type: str
    title: str
    description: str
    supporting_data: Dict[str, Any]
    confidence: float = Field(..., ge=0.0, le=1.0)
    actionable: bool
    recommendations: List[str]
