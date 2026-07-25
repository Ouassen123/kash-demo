import uuid
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from src.core.auth import get_current_user
from src.core.database import Base, SessionLocal, engine, get_db
from src.main import app
from src.models.assessment import HabitsAssessment, UserAssessment
from src.models.user import User
from src.modules.habits.habits_service import HabitsService
from src.modules.habits.schemas.interview_schemas import (
    BehavioralProfile,
    EmotionMetric,
    InterviewAnalysisResponse,
    VoiceMetrics,
)


@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def test_user(db_session):
    user = User(
        id=uuid.uuid4(),
        firebase_uid="test-firebase-uid",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        display_name="Test User",
        auth_provider="email",
        is_active=True,
        is_verified=True,
        is_admin=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def client(db_session, test_user):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def mock_habits_service(monkeypatch):
    def _analyze_interview(self, request, assessment_id):
        has_voice = bool(getattr(request, "audio_base64", None))
        has_face = bool(getattr(request, "video_frames_base64", None))
        emotions = []
        if has_face:
            emotions = [
                EmotionMetric(emotion="happy", confidence=0.72, timestamp_ms=100.0),
                EmotionMetric(emotion="neutral", confidence=0.64, timestamp_ms=220.0),
            ]
        return InterviewAnalysisResponse(
            assessment_id=assessment_id,
            status="completed",
            clarity_score=82.0,
            relevance_score=76.0,
            confidence_score=94.0 if has_voice and has_face else 92.0 if has_voice else 88.0,
            engagement_score=70.0,
            emotions_detected=emotions,
            voice_metrics=VoiceMetrics(
                speech_rate=136.0,
                volume_db=-18.4,
                pitch_variation=28.5,
                pause_ratio=0.14,
                fluency_score=81.0,
            ) if has_voice else None,
            composite_score=84.0 if has_voice and has_face else 82.0 if has_voice else 79.0,
            score_breakdown={
                "clarity": 82.0,
                "relevance": 76.0,
                "confidence": 94.0 if has_voice and has_face else 92.0 if has_voice else 88.0,
                "engagement": 70.0,
                **({"fluency": 81.0} if has_voice else {}),
                **({"face_stress": 12.0} if has_face else {}),
            },
            strengths=["Réponses structurées", "Bonne assurance"],
            improvement_areas=["Ajouter davantage d'exemples concrets"],
            behavioral_profile=BehavioralProfile(
                communication_style="structured",
                motivation_level="high",
                self_awareness="medium",
                stress_indicators="low" if has_face else "low",
                overall_recommendation="recommended",
            ),
            processing_time_ms=12.5,
            modalities_used=["text", "voice", "face"] if has_voice and has_face else ["text", "voice"] if has_voice else ["text"],
            created_at=datetime.utcnow(),
        )

    monkeypatch.setattr(HabitsService, "analyze_interview", _analyze_interview)


def test_post_interview_analyze_persists_habits_assessment(client, db_session, mock_habits_service):
    payload = {
        "answers": [
            {
                "question_id": "q1",
                "question_text": "Présente ton objectif principal.",
                "answer_text": "Je souhaite devenir data scientist et contribuer à des projets à fort impact.",
            }
        ],
        "industry": "technology",
    }

    response = client.post("/api/v1/habits/interview/analyze", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["assessment_id"]
    assert data["composite_score"] == 79.0
    assert data["behavioral_profile"]["overall_recommendation"] == "recommended"

    assessment = db_session.query(UserAssessment).filter_by(id=uuid.UUID(data["assessment_id"])).one_or_none()
    assert assessment is not None
    assert assessment.assessment_type == "habits"
    assert assessment.status == "completed"
    assert assessment.result_data is not None
    assert assessment.result_data["composite_score"] == 79.0

    habits_row = db_session.query(HabitsAssessment).filter_by(assessment_id=assessment.id).one_or_none()
    assert habits_row is not None
    assert habits_row.composite_score == 79.0
    assert habits_row.behavioral_profile["communication_style"] == "structured"
    assert habits_row.modalities_used == ["text"]


def test_post_interview_analyze_with_audio_persists_voice_metrics(client, db_session, mock_habits_service):
    payload = {
        "answers": [
            {
                "question_id": "q1",
                "question_text": "Présente ton objectif principal.",
                "answer_text": "Je souhaite devenir data scientist et contribuer à des projets à fort impact.",
            }
        ],
        "audio_base64": "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAESsAACJWAAACABAAZGF0YQAAAAA=",
        "industry": "technology",
    }

    response = client.post("/api/v1/habits/interview/analyze", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert "voice" in data["modalities_used"]
    assert data["voice_metrics"] is not None
    assert isinstance(data["voice_metrics"]["speech_rate"], (int, float))
    assert isinstance(data["voice_metrics"]["volume_db"], (int, float))
    assert isinstance(data["voice_metrics"]["pitch_variation"], (int, float))
    assert isinstance(data["voice_metrics"]["pause_ratio"], (int, float))
    assert isinstance(data["voice_metrics"]["fluency_score"], (int, float))
    assert data["voice_metrics"]["fluency_score"] >= 0

    assessment = db_session.query(UserAssessment).filter_by(id=uuid.UUID(data["assessment_id"])).one_or_none()
    assert assessment is not None
    assert assessment.result_data is not None
    assert assessment.result_data["voice_metrics"] is not None
    assert "voice" in assessment.result_data["modalities_used"]

    habits_row = db_session.query(HabitsAssessment).filter_by(assessment_id=assessment.id).one_or_none()
    assert habits_row is not None
    assert "voice" in habits_row.modalities_used


def test_post_interview_analyze_trimodal_persists_emotions_and_modalities(client, db_session, mock_habits_service):
    payload = {
        "answers": [
            {
                "question_id": "q1",
                "question_text": "Présente ton objectif principal.",
                "answer_text": "Je souhaite devenir data scientist et contribuer à des projets à fort impact.",
            },
            {
                "question_id": "q2",
                "question_text": "Décris un défi que tu as résolu.",
                "answer_text": "J'ai réduit les erreurs d'un pipeline de données en automatisant les vérifications qualité.",
            },
        ],
        "audio_base64": "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAESsAACJWAAACABAAZGF0YQAAAAA=",
        "video_frames_base64": [
            "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wCEAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAx",
            "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wCEAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAx",
        ],
        "industry": "technology",
    }

    response = client.post("/api/v1/habits/interview/analyze", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert data["modalities_used"] == ["text", "voice", "face"]
    assert data["voice_metrics"] is not None
    assert data["emotions_detected"]

    emotion_fields = ["emotion", "confidence", "timestamp_ms"]
    for emotion in data["emotions_detected"]:
        for field in emotion_fields:
            assert field in emotion
        assert isinstance(emotion["emotion"], str)
        assert isinstance(emotion["confidence"], (int, float))
        assert 0.0 <= emotion["confidence"] <= 1.0

    assessment = db_session.query(UserAssessment).filter_by(id=uuid.UUID(data["assessment_id"])).one_or_none()
    assert assessment is not None
    assert assessment.result_data is not None
    assert assessment.result_data["modalities_used"] == ["text", "voice", "face"]
    assert assessment.result_data["emotions_detected"]

    habits_row = db_session.query(HabitsAssessment).filter_by(assessment_id=assessment.id).one_or_none()
    assert habits_row is not None
    assert habits_row.modalities_used == ["text", "voice", "face"]
    assert habits_row.behavioral_profile["stress_indicators"] in {"low", "moderate", "high"}
