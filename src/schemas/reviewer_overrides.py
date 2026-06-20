"""Reviewer interface schemas for manual overrides."""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


class OverrideReasonEnum(str, Enum):
    """Reason for manual override."""
    FALSE_POSITIVE = "false_positive"
    EDUCATIONAL_CONTEXT = "educational_context"
    ASSESSMENT_CRITERIA = "assessment_criteria"
    SPECIAL_CASE = "special_case"
    INSTRUCTOR_JUDGMENT = "instructor_judgment"
    TECHNICAL_LIMITATION = "technical_limitation"


class OverrideStatusEnum(str, Enum):
    """Override status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class SeverityLevelEnum(str, Enum):
    """Severity level for findings."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FindingOverride(BaseModel):
    """Individual finding override."""
    finding_id: str = Field(..., description="Original finding ID")
    original_severity: SeverityLevelEnum = Field(..., description="Original severity level")
    new_severity: Optional[SeverityLevelEnum] = Field(None, description="New severity level")
    original_score_impact: float = Field(..., description="Original score impact")
    new_score_impact: Optional[float] = Field(None, description="New score impact")
    reason: OverrideReasonEnum = Field(..., description="Reason for override")
    comment: str = Field(..., min_length=10, description="Detailed explanation for override")
    evidence: Optional[List[str]] = Field(None, description="Supporting evidence or references")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "finding_id": "JAVA001_123",
                "original_severity": "high",
                "new_severity": "medium",
                "original_score_impact": -5.0,
                "new_score_impact": -2.0,
                "reason": "educational_context",
                "comment": "This is a learning exercise where the student is experimenting with different approaches",
                "evidence": ["Learning objective: explore naming conventions", "Exercise allows creative solutions"]
            }
        }
    }


class ScoreOverride(BaseModel):
    """Overall score override."""
    original_score: float = Field(..., ge=0, le=100, description="Original score")
    new_score: float = Field(..., ge=0, le=100, description="New score")
    reason: OverrideReasonEnum = Field(..., description="Reason for override")
    comment: str = Field(..., min_length=10, description="Detailed explanation")
    calculation_method: Optional[str] = Field(None, description="How new score was calculated")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "original_score": 75.5,
                "new_score": 82.0,
                "reason": "educational_context",
                "comment": "Student showed creative problem-solving despite some style issues",
                "calculation_method": "Base score + bonus for creativity"
            }
        }
    }


class GradeOverride(BaseModel):
    """Grade override."""
    original_grade: str = Field(..., pattern="^[A-F]$", description="Original grade A-F")
    new_grade: str = Field(..., pattern="^[A-F]$", description="New grade A-F")
    reason: OverrideReasonEnum = Field(..., description="Reason for override")
    comment: str = Field(..., min_length=10, description="Detailed explanation")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "original_grade": "C",
                "new_grade": "B",
                "reason": "instructor_judgment",
                "comment": "Student demonstrated understanding of core concepts despite minor issues"
            }
        }
    }


class ReviewerOverrideRequest(BaseModel):
    """Request for reviewer overrides."""
    submission_id: str = Field(..., description="Submission ID to override")
    reviewer_id: str = Field(..., description="Reviewer user ID")
    reviewer_notes: str = Field(..., min_length=20, description="Overall review notes")
    finding_overrides: Optional[List[FindingOverride]] = Field(default_factory=list, description="Individual finding overrides")
    score_override: Optional[ScoreOverride] = Field(None, description="Overall score override")
    grade_override: Optional[GradeOverride] = Field(None, description="Grade override")
    additional_feedback: Optional[str] = Field(None, description="Additional feedback for student")
    is_final: bool = Field(False, description="Whether this is the final review")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "submission_id": "sub-123",
                "reviewer_id": "reviewer-456",
                "reviewer_notes": "Good effort with creative solutions. Some style issues need attention but core concepts are well understood.",
                "finding_overrides": [
                    {
                        "finding_id": "JAVA001_123",
                        "original_severity": "high",
                        "new_severity": "medium",
                        "original_score_impact": -5.0,
                        "new_score_impact": -2.0,
                        "reason": "educational_context",
                        "comment": "Learning exercise allows experimentation",
                        "evidence": ["Exercise permits creative naming"]
                    }
                ],
                "score_override": {
                    "original_score": 75.5,
                    "new_score": 82.0,
                    "reason": "educational_context",
                    "comment": "Bonus for creative problem-solving",
                    "calculation_method": "Base + creativity bonus"
                },
                "additional_feedback": "Focus on consistency in naming conventions in future assignments.",
                "is_final": True
            }
        }
    }


class ReviewerOverrideResponse(BaseModel):
    """Response for reviewer overrides."""
    override_id: str = Field(..., description="Override record ID")
    submission_id: str
    reviewer_id: str
    status: OverrideStatusEnum
    original_analysis: Dict[str, Any] = Field(..., description="Original analysis results")
    modified_analysis: Dict[str, Any] = Field(..., description="Modified analysis results")
    changes_summary: Dict[str, Any] = Field(..., description="Summary of changes made")
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    approved_by: Optional[str] = None


class OverrideHistoryItem(BaseModel):
    """Item in override history."""
    override_id: str
    reviewer_id: str
    reviewer_name: Optional[str] = None
    changes_made: Dict[str, Any]
    reason: OverrideReasonEnum
    comment: str
    created_at: datetime
    status: OverrideStatusEnum


class OverrideHistoryResponse(BaseModel):
    """Override history for a submission."""
    submission_id: str
    total_overrides: int
    overrides: List[OverrideHistoryItem]
    current_analysis: Dict[str, Any]


class ReviewerDashboardRequest(BaseModel):
    """Request for reviewer dashboard data."""
    reviewer_id: Optional[str] = Field(None, description="Specific reviewer ID (admin only)")
    status_filter: Optional[List[OverrideStatusEnum]] = Field(None, description="Filter by status")
    date_from: Optional[datetime] = Field(None, description="Filter from date")
    date_to: Optional[datetime] = Field(None, description="Filter to date")
    limit: int = Field(default=50, ge=1, le=200, description="Results limit")
    offset: int = Field(default=0, ge=0, description="Results offset")


class ReviewerStats(BaseModel):
    """Reviewer statistics."""
    reviewer_id: str
    reviewer_name: Optional[str] = None
    total_reviews: int
    pending_reviews: int
    approved_overrides: int
    rejected_overrides: int
    average_score_adjustment: float
    most_common_reasons: List[Dict[str, Any]]
    recent_activity: List[OverrideHistoryItem]


class ReviewerDashboardResponse(BaseModel):
    """Reviewer dashboard response."""
    reviewer_stats: Optional[ReviewerStats] = None
    pending_submissions: List[Dict[str, Any]]
    recent_overrides: List[OverrideHistoryItem]
    summary_stats: Dict[str, Any]


class OverrideTemplate(BaseModel):
    """Template for common overrides."""
    template_id: str
    name: str
    description: str
    reason: OverrideReasonEnum
    comment_template: str
    common_findings: List[str] = Field(default_factory=list, description="Finding types this applies to")
    score_adjustment: Optional[float] = Field(None, description="Typical score adjustment")
    is_active: bool = True
    created_by: str
    created_at: datetime


class OverrideTemplateRequest(BaseModel):
    """Request to create override template."""
    name: str = Field(..., min_length=3, description="Template name")
    description: str = Field(..., min_length=10, description="Template description")
    reason: OverrideReasonEnum = Field(..., description="Override reason")
    comment_template: str = Field(..., min_length=20, description="Comment template with placeholders")
    common_findings: List[str] = Field(default_factory=list, description="Applicable finding types")
    score_adjustment: Optional[float] = Field(None, description="Typical score adjustment")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Educational Context - Learning Exercise",
                "description": "For learning exercises where strict rules don't apply",
                "reason": "educational_context",
                "comment_template": "This is a learning exercise where {student_action} is acceptable. The learning objective focuses on {learning_objective} rather than strict adherence to {rule_type}.",
                "common_findings": ["naming_conventions", "style_guidelines"],
                "score_adjustment": 2.0
            }
        }
    }


class OverrideValidationRequest(BaseModel):
    """Request to validate potential override."""
    submission_id: str
    proposed_overrides: List[FindingOverride]
    proposed_score_override: Optional[ScoreOverride] = None
    validation_context: Optional[Dict[str, Any]] = Field(None, description="Additional context for validation")


class OverrideValidationResponse(BaseModel):
    """Response for override validation."""
    is_valid: bool
    validation_errors: List[str] = Field(default_factory=list)
    validation_warnings: List[str] = Field(default_factory=list)
    estimated_impact: Dict[str, Any]
    recommendations: List[str] = Field(default_factory=list)
