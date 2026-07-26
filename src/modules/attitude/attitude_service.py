"""Attitude service — orchestrates video interview analysis for Attitude (A) assessment.

This module replaces the cognitive quiz approach with a behavioral interview
analysis pipeline that detects mindset, comportment, and stress management
through text responses, optional video emotion analysis, and optional voice
stress analysis.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid

from src.core.logging import get_logger
from src.modules.attitude.questions import INTERVIEW_QUESTIONS
from src.modules.attitude.attitude_scorer import AttitudeScorer, AttitudeProfile

logger = get_logger(__name__)


class AttitudeService:
    """Service for Attitude (A) assessment via behavioral interview analysis."""

    def __init__(self, db=None, nlp=None):
        self.db = db
        self.nlp = nlp
        self.scorer = AttitudeScorer(nlp=nlp)

    def get_questions(self) -> List[Dict]:
        """Return the list of attitude interview questions."""
        return [
            {
                "id": q["id"],
                "text": q["text"],
                "category": q["category"],
                "expected_signals": q["expected_signals"],
            }
            for q in INTERVIEW_QUESTIONS
        ]

    async def analyze_interview(
        self,
        user_id: str,
        answers: List[Dict[str, str]],
        video_frames_base64: Optional[List[str]] = None,
        audio_base64: str = "",
        industry: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze attitude interview responses.

        Args:
            user_id: User UUID
            answers: List of {question_id, question_text, answer_text}
            video_frames_base64: Optional captured video frames (base64 JPEG)
            audio_base64: Optional audio recording (base64)
            industry: Optional industry context for tuning

        Returns:
            Complete attitude assessment results
        """
        logger.info(f"Starting attitude interview analysis for user {user_id}")
        start_time = datetime.now()

        answer_map = {a["question_id"]: a for a in answers}
        responses = []

        for q in INTERVIEW_QUESTIONS:
            ans = answer_map.get(q["id"])
            if ans and ans.get("answer_text", "").strip():
                responses.append({
                    "category": q["category"],
                    "question_text": q["text"],
                    "answer_text": ans["answer_text"],
                    "expected_signals": q["expected_signals"],
                })

        if not responses:
            return {
                "error": "No valid answers provided",
                "overall_attitude_score": 0,
            }

        face_emotions = None
        if video_frames_base64:
            face_emotions = self._analyze_face_emotions(video_frames_base64)

        voice_metrics = None
        if audio_base64:
            voice_metrics = self._analyze_voice(audio_base64)

        profile = self.scorer.compute_profile(responses, face_emotions, voice_metrics)

        processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000

        result = {
            "user_id": user_id,
            "assessment_type": "attitude",
            "overall_attitude_score": profile.overall_attitude_score,
            "stress_resistance": profile.stress_resistance,
            "emotional_regulation": profile.emotional_regulation,
            "adaptability": profile.adaptability,
            "self_awareness": profile.self_awareness,
            "communication_style": profile.communication_style,
            "motivation_level": profile.motivation_level,
            "decision_making_style": profile.decision_making_style,
            "dimension_scores": profile.dimension_scores,
            "strengths": profile.strengths,
            "improvement_areas": profile.improvement_areas,
            "recommendation": profile.recommendation,
            "modalities_used": ["text"] + (["face"] if face_emotions else []) + (["voice"] if voice_metrics else []),
            "industry": industry,
            "processing_time_ms": round(processing_time_ms, 1),
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(
            f"Attitude analysis completed for user {user_id} in {processing_time_ms:.0f}ms "
            f"(score={profile.overall_attitude_score:.1f})"
        )
        return result

    def _analyze_face_emotions(self, frames_base64: List[str]) -> List[Dict]:
        """Analyze face emotions from video frames.

        Placeholder: in production, use OpenCV + face emotion model.
        Returns simulated emotions for now.
        """
        emotions = []
        for i, frame in enumerate(frames_base64[:5]):
            emotions.append({
                "frame": i,
                "emotion": "neutral",
                "confidence": 0.7,
            })
        logger.debug(f"Face emotion analysis: {len(emotions)} frames analyzed")
        return emotions

    def _analyze_voice(self, audio_base64: str) -> Dict:
        """Analyze voice stress metrics from audio.

        Placeholder: in production, use librosa for pitch/volume/speech rate.
        Returns default metrics for now.
        """
        return {
            "pitch_variation": 22.0,
            "volume_db": -19.0,
            "speech_rate": 155.0,
        }
