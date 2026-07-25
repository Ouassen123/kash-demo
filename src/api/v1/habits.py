"""Habits module API endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.auth import get_current_user
from src.core.database import get_db
from src.core.logging import get_logger
from src.models.assessment import HabitsAssessment, UserAssessment
from src.models.user import User
from src.modules.habits.habits_service import HabitsService
from src.modules.habits.schemas.interview_schemas import (
    InterviewAnalysisRequest,
    InterviewAnalysisResponse,
)

router = APIRouter(prefix="/habits", tags=["habits"])
logger = get_logger(__name__)


@router.post("/interview/analyze", response_model=InterviewAnalysisResponse)
async def analyze_interview(
    request: InterviewAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Analyze an interview session and persist the Habits assessment.

    This endpoint is authenticated and stores both the parent assessment row
    and the Habits-specific results.
    """
    assessment = None
    try:
        service = HabitsService()

        # Create the parent assessment record first so we have an ID to persist.
        assessment = UserAssessment(
            id=uuid.uuid4(),
            user_id=current_user.id,
            assessment_type="habits",
            assessment_name="Habits Interview Assessment",
            assessment_version="1.0",
            status="in_progress",
            created_at=datetime.utcnow(),
            started_at=datetime.utcnow(),
            input_data={
                "answers": [answer.model_dump() for answer in request.answers],
                "audio_base64": request.audio_base64,
                "video_frames_base64": request.video_frames_base64,
                "industry": request.industry,
            },
        )
        db.add(assessment)
        db.flush()

        analysis = service.analyze_interview(request=request, assessment_id=str(assessment.id))
        serialized_result = analysis.model_dump(mode="json")

        habits_assessment = HabitsAssessment(
            id=uuid.uuid4(),
            assessment_id=assessment.id,
            user_id=current_user.id,
            composite_score=analysis.composite_score,
            score_breakdown=analysis.score_breakdown,
            strengths=analysis.strengths,
            improvement_areas=analysis.improvement_areas,
            behavioral_profile=analysis.behavioral_profile.model_dump(),
            modalities_used=analysis.modalities_used,
            clarity_score=analysis.clarity_score,
            relevance_score=analysis.relevance_score,
            engagement_score=analysis.engagement_score,
            confidence_score=analysis.confidence_score,
            processing_time_ms=analysis.processing_time_ms,
            created_at=analysis.created_at,
        )
        db.add(habits_assessment)

        assessment.result_data = serialized_result
        assessment.raw_score = analysis.composite_score
        assessment.normalized_score = analysis.composite_score
        assessment.confidence_score = analysis.confidence_score / 100.0
        assessment.status = "completed"
        assessment.completed_at = analysis.created_at

        db.commit()
        db.refresh(assessment)
        db.refresh(habits_assessment)

        return analysis

    except HTTPException:
        if assessment is not None:
            db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.error("Interview analysis failed for user %s: %s", current_user.id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Interview analysis failed",
        )
