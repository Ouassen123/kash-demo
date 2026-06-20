"""Skills module schemas for API requests/responses."""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum


class SourceTypeEnum(str, Enum):
    """Source type enumeration."""
    GITHUB = "github"
    UPLOAD = "upload"
    URL = "url"


class ProficiencyLevelEnum(str, Enum):
    """Proficiency level enumeration."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class GitHubAnalysisRequest(BaseModel):
    """Request for GitHub repository analysis."""
    owner: str = Field(..., min_length=1, description="Repository owner username")
    repo: str = Field(..., min_length=1, description="Repository name")
    github_token: Optional[str] = Field(None, description="GitHub access token for private repos")
    
    @validator('owner', 'repo')
    def validate_names(cls, v):
        if not v or len(v.strip()) < 1:
            raise ValueError('Repository owner and name cannot be empty')
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "owner": "octocat",
                "repo": "Hello-World",
                "github_token": "ghp_xxxxxxxxxxxx"
            }
        }


class GitHubLinkRequest(BaseModel):
    """Request payload to register a learner→GitHub repository link."""

    repository_full_name: str = Field(..., min_length=3)
    project_id: Optional[str] = None
    github_handle: Optional[str] = None
    metadata: Dict[str, str] = Field(default_factory=dict)


class GitHubLinkResponse(GitHubLinkRequest):
    """Response containing the registered link with metadata."""

    learner_id: str
    last_refreshed_at: datetime

    class Config:
        from_attributes = True


class GitHubSyncRequest(BaseModel):
    """Request payload to sync a mini-project submission with GitHub."""

    submission_id: str = Field(..., min_length=1)
    template_id: str = Field(..., min_length=1)
    project_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GitHubSyncResultResponse(BaseModel):
    """Response describing a GitHub sync result."""

    submission_id: str
    synced_at: datetime
    reliability: Dict[str, Any]
    repository: Optional[Dict[str, Any]]
    contributions_count: int
    pull_requests_count: int
    errors: List[str]


class GitHubSyncLogEntryResponse(BaseModel):
    """Audit-friendly GitHub sync log entry."""

    learner_id: str
    submission_id: str
    template_id: str
    project_id: Optional[str]
    metadata: Dict[str, Any]
    recorded_at: datetime
    result: GitHubSyncResultResponse


class CodeFile(BaseModel):
    """Code file for upload analysis."""
    path: str = Field(..., description="File path")
    content: str = Field(..., min_length=10, description="File content")
    
    @validator('content')
    def validate_content(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('File content must be at least 10 characters long')
        return v


class CodeUploadRequest(BaseModel):
    """Request for code upload analysis."""
    files: List[CodeFile] = Field(..., min_items=1, max_items=50, description="Code files to analyze")
    project_name: str = Field(default="Uploaded Project", description="Project name")
    
    @validator('files')
    def validate_files(cls, v):
        if not v:
            raise ValueError('At least one file must be provided')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "files": [
                    {
                        "path": "src/main.py",
                        "content": "def hello():\n    print('Hello, World!')\n"
                    }
                ],
                "project_name": "My Python Project"
            }
        }


class TechnicalSkill(BaseModel):
    """Technical skill with confidence."""
    name: str
    category: str
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    evidence: List[str] = Field(default_factory=list, description="Evidence of skill usage")
    proficiency_level: ProficiencyLevelEnum
    
    class Config:
        from_attributes = True


class CodePattern(BaseModel):
    """Code pattern or practice."""
    name: str
    type: str = Field(..., pattern="^(design_pattern|anti_pattern|best_practice|framework)$")
    description: str
    locations: List[str] = Field(default_factory=list)
    frequency: int = Field(..., ge=0, description="Pattern frequency")
    
    class Config:
        from_attributes = True


class CodeMetric(BaseModel):
    """Code quality metric."""
    name: str
    value: float
    description: str
    threshold: float
    is_good: bool
    
    class Config:
        from_attributes = True


class RepositoryInfo(BaseModel):
    """GitHub repository information."""
    name: str
    description: Optional[str]
    language: Optional[str]
    languages: Dict[str, int]
    stars: int
    forks: int
    open_issues: int
    created_at: str
    updated_at: str
    size_kb: int
    topics: List[str]
    is_private: bool
    default_branch: str
    
    class Config:
        from_attributes = True


class SkillsAssessmentStartResponse(BaseModel):
    """Response when starting a skills assessment."""
    assessment_id: str
    source_type: SourceTypeEnum
    source_url: Optional[str]
    project_name: str
    status: str
    created_at: datetime
    
    class Config:
        schema_extra = {
            "example": {
                "assessment_id": "123e4567-e89b-12d3-a456-426614174000",
                "source_type": "github",
                "source_url": "https://github.com/octocat/Hello-World",
                "project_name": "Hello-World",
                "status": "completed",
                "created_at": "2024-01-01T00:00:00Z"
            }
        }


class SkillsAssessmentSummary(BaseModel):
    """Summary of skills assessment for list views."""
    assessment_id: str
    assessment_name: str
    status: str
    source_type: SourceTypeEnum
    source_url: Optional[str]
    normalized_score: Optional[float]
    confidence_score: Optional[float]
    created_at: datetime
    completed_at: Optional[datetime]
    
    # Quick stats
    project_name: Optional[str]
    languages_detected: List[str]
    technical_skills_count: int
    project_complexity: Optional[float]
    
    class Config:
        from_attributes = True


class SkillsAssessmentResults(BaseModel):
    """Complete skills assessment results."""
    assessment_id: str
    source_type: SourceTypeEnum
    source_url: Optional[str]
    project_name: str
    status: str
    created_at: datetime
    completed_at: datetime
    
    # Repository analysis (if GitHub)
    repository_info: Optional[RepositoryInfo]
    
    # Code analysis
    code_summary: Dict[str, Any]
    technical_skills: List[TechnicalSkill]
    patterns: List[CodePattern]
    quality_metrics: List[CodeMetric]
    
    # Scores
    skills_scores: Dict[str, Any]
    overall_scores: Dict[str, float]
    
    # Additional details
    collaboration_indicators: Optional[Dict[str, Any]]
    learning_trajectory: Optional[List[Dict[str, Any]]]
    
    class Config:
        from_attributes = True


class SkillsProfileResponse(BaseModel):
    """Complete skills profile for a user."""
    user_id: str
    total_assessments: int
    technical_skills: Dict[str, Any]
    programming_languages: Dict[str, int]
    overall_performance: Dict[str, Any]
    project_complexity_trend: List[Dict[str, Any]]
    recommendations: List[str]
    recent_activity: List[Dict[str, Any]]
    last_assessment: Optional[str]
    
    class Config:
        from_attributes = True


class GitHubRepositoryResponse(BaseModel):
    """GitHub repository information response."""
    name: str
    description: Optional[str]
    language: Optional[str]
    languages: Dict[str, int]
    stars: int
    forks: int
    open_issues: int
    created_at: str
    updated_at: str
    size_kb: int
    topics: List[str]
    is_private: bool
    default_branch: str
    
    class Config:
        schema_extra = {
            "example": {
                "name": "octocat/Hello-World",
                "description": "My first repository on GitHub!",
                "language": "Python",
                "languages": {"Python": 1024, "HTML": 256},
                "stars": 42,
                "forks": 8,
                "open_issues": 2,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-15T00:00:00Z",
                "size_kb": 128,
                "topics": ["python", "hello-world"],
                "is_private": False,
                "default_branch": "main"
            }
        }


class SkillCategory(BaseModel):
    """Skill category with skills."""
    category: str
    skills: List[TechnicalSkill]
    total_skills: int
    avg_confidence: float


class ProficiencyDistribution(BaseModel):
    """Distribution of skill proficiency levels."""
    beginner: int
    intermediate: int
    advanced: int
    expert: int
    total: int


class SkillRecommendation(BaseModel):
    """Personalized skill recommendation."""
    type: str = Field(..., pattern="^(learn|practice|project|career)$")
    priority: str = Field(..., pattern="^(high|medium|low)$")
    skill: Optional[str]
    estimated_time_hours: Optional[int]
    resources: List[str] = Field(default_factory=list)


class LearningPath(BaseModel):
    """Personalized learning path for skill development."""
    path_id: str
    title: str
    description: str
    target_skills: List[str]
    current_level: ProficiencyLevelEnum
    target_level: ProficiencyLevelEnum
    estimated_weeks: int
    milestones: List[str]
    recommendations: List[SkillRecommendation]


class SkillsInsight(BaseModel):
    """Insight about user's technical skills."""
    insight_type: str
    title: str
    description: str
    supporting_data: Dict[str, Any]
    confidence: float = Field(..., ge=0.0, le=1.0)
    actionable: bool
    recommendations: List[str]


class ProjectComplexityTrend(BaseModel):
    """Project complexity over time."""
    complexity: float
    date: str
    project_name: str


class RecentActivity(BaseModel):
    """Recent skills assessment activity."""
    assessment_id: str
    project_name: str
    source_type: SourceTypeEnum
    score: float
    languages: List[str]
    completed_at: Optional[str]


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "error": "repository_not_found",
                "message": "GitHub repository not found or inaccessible",
                "details": {
                    "owner": "octocat",
                    "repo": "nonexistent-repo"
                }
            }
        }


class AnalysisProgress(BaseModel):
    """Analysis progress information."""
    assessment_id: str
    status: str
    progress_percentage: float = Field(..., ge=0.0, le=100.0)
    current_step: str
    estimated_remaining_seconds: Optional[int]
    files_processed: int
    total_files: int


class BulkAnalysisRequest(BaseModel):
    """Request for bulk repository analysis."""
    repositories: List[Dict[str, str]] = Field(..., min_items=1, max_items=10, description="List of repositories to analyze")
    github_token: Optional[str] = Field(None, description="GitHub access token")
    
    @validator('repositories')
    def validate_repositories(cls, v):
        if not v:
            raise ValueError('At least one repository must be provided')
        
        for repo in v:
            if 'owner' not in repo or 'repo' not in repo:
                raise ValueError('Each repository must have "owner" and "repo" fields')
        
        return v


class BulkAnalysisResponse(BaseModel):
    """Response for bulk analysis."""
    assessment_ids: List[str]
    total_repositories: int
    successful_analyses: int
    failed_analyses: List[Dict[str, str]]
    processing_time_seconds: float
