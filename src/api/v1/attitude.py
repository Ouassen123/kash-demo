"""Attitude API endpoints — behavioral interview analysis for Attitude (A)."""

from __future__ import annotations

from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.core.logging import get_logger
from src.modules.attitude.attitude_service import AttitudeService

logger = get_logger(__name__)

router = APIRouter(prefix="/attitude", tags=["attitude"])


class AttitudeAnswerInput(BaseModel):
    question_id: str
    question_text: str = ""
    answer_text: str


class AttitudeAnalyzeRequest(BaseModel):
    answers: List[AttitudeAnswerInput]
    video_frames_base64: List[str] = Field(default_factory=list)
    audio_base64: str = ""
    industry: str = "technology"


class AttitudeQuestionResponse(BaseModel):
    id: str
    text: str
    category: str
    expected_signals: List[str]


@router.get("/questions")
async def get_attitude_questions():
    """Get the list of attitude interview questions."""
    service = AttitudeService()
    questions = service.get_questions()
    return questions


@router.post("/interview/analyze")
async def analyze_attitude_interview(request: AttitudeAnalyzeRequest):
    """Analyze attitude interview responses.

    Accepts text answers, optional video frames, and optional audio.
    Returns comprehensive attitude profile with stress resistance,
    emotional regulation, adaptability, and behavioral metrics.
    """
    service = AttitudeService()
    result = await service.analyze_interview(
        user_id="admin-test",
        answers=[a.model_dump() for a in request.answers],
        video_frames_base64=request.video_frames_base64 or None,
        audio_base64=request.audio_base64 or None,
        industry=request.industry,
    )
    return result
