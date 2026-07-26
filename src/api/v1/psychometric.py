"""Psychometric API endpoints — Habits (H) questionnaire assessment."""

from __future__ import annotations

from typing import Dict, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.core.logging import get_logger
from src.modules.habits.psychometric.scorer import PsychometricScorer
from src.modules.habits.psychometric.questions import PSYCHOMETRIC_QUESTIONS, DIMENSION_DESCRIPTIONS

logger = get_logger(__name__)

router = APIRouter(prefix="/habits/psychometric", tags=["habits-psychometric"])


class PsychometricResponse(BaseModel):
    question_id: str
    answer: int = Field(ge=1, le=5, description="Likert scale: 1=Strongly Disagree, 5=Strongly Agree")


class PsychometricSubmitRequest(BaseModel):
    responses: List[PsychometricResponse]


@router.get("/questions")
async def get_psychometric_questions():
    """Get the psychometric questionnaire (20 questions across 7 dimensions)."""
    return [
        {
            "id": q["id"],
            "text": q["text"],
            "dimension": q["dimension"],
            "subscale": q["subscale"],
            "reverse": q["reverse"],
            "scale": {"min": 1, "max": 5, "labels": ["Pas du tout d'accord", "Pas d'accord", "Neutre", "D'accord", "Tout à fait d'accord"]},
        }
        for q in PSYCHOMETRIC_QUESTIONS
    ]


@router.get("/dimensions")
async def get_psychometric_dimensions():
    """Get description of all psychometric dimensions."""
    return DIMENSION_DESCRIPTIONS


@router.post("/submit")
async def submit_psychometric_questionnaire(request: PsychometricSubmitRequest):
    """Submit and score the psychometric questionnaire.

    Returns a comprehensive habits profile with:
    - Overall habits score (0-100)
    - Discipline level (excellent/strong/moderate/developing/weak)
    - Per-dimension scores (Big Five + Grit + Self-Discipline)
    - Strengths and improvement areas
    - Personalized habit recommendations
    """
    if len(request.responses) < 10:
        raise HTTPException(status_code=422, detail="At least 10 responses are required")

    scorer = PsychometricScorer()
    profile = scorer.score_questionnaire([r.model_dump() for r in request.responses])

    return {
        "overall_habits_score": profile.overall_habits_score,
        "discipline_level": profile.discipline_level,
        "routine_strength": profile.routine_strength,
        "perseverance_score": profile.perseverance_score,
        "stress_management_capacity": profile.stress_management_capacity,
        "learning_openness": profile.learning_openness,
        "social_engagement": profile.social_engagement,
        "dimension_scores": profile.dimension_scores,
        "strengths": profile.strengths,
        "improvement_areas": profile.improvement_areas,
        "habit_recommendations": profile.habit_recommendations,
        "recommendation": profile.recommendation,
    }
