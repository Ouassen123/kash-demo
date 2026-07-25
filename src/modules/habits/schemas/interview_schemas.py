"""Pydantic v2 schemas for the Habits module — multimodal interview analysis."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Request schemas ───────────────────────────────────────────


class InterviewAnswer(BaseModel):
    """A single answer to an interview question."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question_id": "q1_motivation",
                "question_text": "Présente ton objectif académique ou professionnel principal.",
                "answer_text": "Je souhaite devenir ingénieur data scientist dans le secteur de l'énergie renouvelable.",
            }
        }
    )

    question_id: str = Field(..., description="Identifiant unique de la question")
    question_text: str = Field(..., description="Texte de la question posée")
    answer_text: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Réponse du candidat",
    )


class InterviewAnalysisRequest(BaseModel):
    """Payload for POST /interview/analyze."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "answers": [
                    {
                        "question_id": "q1_motivation",
                        "question_text": "Présente ton objectif académique ou professionnel principal.",
                        "answer_text": "Je souhaite devenir ingénieur data scientist...",
                    },
                    {
                        "question_id": "q2_challenge",
                        "question_text": "Décris un défi que tu as résolu et ce que tu as appris.",
                        "answer_text": "Lors de mon projet de fin d'études, j'ai dû optimiser...",
                    },
                ],
                "audio_base64": None,
                "video_frames_base64": None,
                "industry": "technology",
            }
        }
    )

    answers: List[InterviewAnswer] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Liste des réponses aux questions d'entretien",
    )
    audio_base64: Optional[str] = Field(
        default=None,
        description="Audio encodé en base64 (webm/wav) pour analyse prosodique",
    )
    video_frames_base64: Optional[List[str]] = Field(
        default=None,
        max_length=30,
        description="Frames vidéo encodées en base64 (JPEG) pour analyse faciale",
    )
    industry: Optional[str] = Field(
        default="technology",
        description="Industrie cible pour ajustement des poids de scoring",
    )


# ── Sub-metric schemas ────────────────────────────────────────


class EmotionMetric(BaseModel):
    """A single detected emotion with confidence score."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "emotion": "happy",
                "confidence": 0.87,
                "timestamp_ms": 1500.0,
            }
        }
    )

    emotion: str = Field(
        ...,
        description="Nom de l'émotion: happy, sad, angry, surprise, neutral, fear, disgust",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Score de confiance de la détection",
    )
    timestamp_ms: Optional[float] = Field(
        default=None,
        description="Timestamp dans l'enregistrement vidéo (en millisecondes)",
    )


class VoiceMetrics(BaseModel):
    """Voice analysis metrics extracted from audio."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "speech_rate": 135.0,
                "volume_db": -18.5,
                "pitch_variation": 45.2,
                "pause_ratio": 0.15,
                "fluency_score": 78.0,
            }
        }
    )

    speech_rate: float = Field(
        ...,
        description="Vitesse de parole en mots par minute (normale: 120-150)",
    )
    volume_db: float = Field(
        ...,
        description="Volume moyen en décibels (dB)",
    )
    pitch_variation: float = Field(
        ...,
        description="Variation de la fréquence fondamentale en Hertz (Hz)",
    )
    pause_ratio: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Ratio silence/parole (0 = parole continue, 1 = silence total)",
    )
    fluency_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Score de fluence vocale globale",
    )


class BehavioralProfile(BaseModel):
    """Synthetic behavioral profile of the candidate."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "communication_style": "structured",
                "motivation_level": "high",
                "self_awareness": "medium",
                "stress_indicators": "low",
                "overall_recommendation": "recommended",
            }
        }
    )

    communication_style: str = Field(
        ...,
        description="Style de communication: structured, spontaneous, analytical, narrative",
    )
    motivation_level: str = Field(
        ...,
        description="Niveau de motivation: high, medium, low",
    )
    self_awareness: str = Field(
        ...,
        description="Niveau de connaissance de soi: high, medium, low",
    )
    stress_indicators: str = Field(
        ...,
        description="Indicateurs de stress: low, moderate, high",
    )
    overall_recommendation: str = Field(
        ...,
        description="Recommandation globale: recommended, borderline, not_recommended",
    )


# ── Response schema ───────────────────────────────────────────


class InterviewAnalysisResponse(BaseModel):
    """Response for POST /interview/analyze."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "assessment_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "clarity_score": 75.0,
                "relevance_score": 82.0,
                "confidence_score": 68.0,
                "engagement_score": 70.0,
                "emotions_detected": [
                    {"emotion": "happy", "confidence": 0.82, "timestamp_ms": 1200.0},
                    {"emotion": "neutral", "confidence": 0.65, "timestamp_ms": 3400.0},
                ],
                "voice_metrics": {
                    "speech_rate": 138.0,
                    "volume_db": -16.2,
                    "pitch_variation": 52.0,
                    "pause_ratio": 0.12,
                    "fluency_score": 80.0,
                },
                "composite_score": 73.5,
                "score_breakdown": {
                    "clarity": 75.0,
                    "relevance": 82.0,
                    "confidence": 68.0,
                    "engagement": 70.0,
                },
                "strengths": ["Structure claire des réponses", "Vocabulaire technique riche"],
                "improvement_areas": ["Manque d'exemples concrets", "Réponses parfois trop courtes"],
                "behavioral_profile": {
                    "communication_style": "structured",
                    "motivation_level": "high",
                    "self_awareness": "medium",
                    "stress_indicators": "low",
                    "overall_recommendation": "recommended",
                },
                "processing_time_ms": 1250.0,
                "modalities_used": ["text", "voice", "face"],
                "created_at": "2025-07-18T14:30:00Z",
            }
        }
    )

    assessment_id: str = Field(..., description="ID de l'assessment créé en base")
    status: str = Field(..., description="Statut de l'analyse: completed")

    # ── Dimension scores (0-100) ──────────────────────────────
    clarity_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Score de clarté (structure, cohérence, richesse vocabulaire)",
    )
    relevance_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Score de pertinence (alignement réponse/question)",
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Score de confiance (signaux vocaux + faciaux si disponibles)",
    )
    engagement_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Score d'engagement (longueur, profondeur, exemples concrets)",
    )

    # ── Multimodal data ───────────────────────────────────────
    emotions_detected: List[EmotionMetric] = Field(
        default_factory=list,
        description="Émotions détectées depuis l'analyse vidéo (si disponible)",
    )
    voice_metrics: Optional[VoiceMetrics] = Field(
        default=None,
        description="Métriques vocales (si audio fourni)",
    )

    # ── Composite score ───────────────────────────────────────
    composite_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Score final combiné pondérant toutes les dimensions",
    )
    score_breakdown: Dict[str, float] = Field(
        ...,
        description="Détail du calcul par dimension: {'clarity': 75.0, 'relevance': 80.0, ...}",
    )

    # ── Insights & feedback ───────────────────────────────────
    strengths: List[str] = Field(
        default_factory=list,
        description="Points forts identifiés",
    )
    improvement_areas: List[str] = Field(
        default_factory=list,
        description="Axes d'amélioration suggérés",
    )
    behavioral_profile: BehavioralProfile = Field(
        ...,
        description="Profil comportemental synthétique du candidat",
    )

    # ── Metadata ──────────────────────────────────────────────
    processing_time_ms: float = Field(
        ...,
        description="Temps de traitement en millisecondes",
    )
    modalities_used: List[str] = Field(
        ...,
        description="Modalités analysées: ['text'], ['text', 'voice'], ou ['text', 'voice', 'face']",
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp de création de l'analyse",
    )
