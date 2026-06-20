"""Schemas package."""

from .auth import *
from .knowledge import *
from .abilities import *
from .skills import *
from .intelligence import *

__all__ = [
    # Auth schemas
    "FirebaseLoginRequest",
    "LoginResponse", 
    "UserResponse",
    "UserProfileUpdate",
    "UserSessionResponse",
    "LogoutResponse",
    
    # Knowledge schemas
    "CVAnalysisRequest",
    "CVAnalysisResponse",
    "KnowledgeAssessmentSummary",
    "KnowledgeProfileResponse",
    "ESCOSearchRequest",
    "ESCOSearchResponse",
    "SkillMappingRequest",
    "SkillMappingResponse",
    
    # Abilities schemas
    "StartAssessmentRequest",
    "AssessmentStartResponse",
    "SubmitAnswerRequest",
    "SubmitAnswerResponse",
    "AssessmentStatus",
    "AbilitiesAssessmentSummary",
    "AbilitiesProfileResponse",
    "AvailableAssessmentsResponse",
    "QuizSessionInfo",
    
    # Skills schemas
    "GitHubAnalysisRequest",
    "CodeUploadRequest",
    "SkillsAssessmentSummary",
    "SkillsAssessmentResults",
    "SkillsProfileResponse",
    "GitHubRepositoryResponse",
    
    # Intelligence schemas
    "IntelligenceAssessmentRequest",
    "IntelligenceAssessmentResults",
    "IntelligenceAssessmentSummary",
    "IntelligenceProfileResponse",
    "CareerPathRequest",
    "CareerPathResponse",
    "SkillGapRequest",
    "SkillGapResponse"
]
