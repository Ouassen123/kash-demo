"""API client for frontend evaluation interface."""

from typing import Dict, Any, Optional, List
import json
from datetime import datetime

from src.core.logging import get_logger

logger = get_logger(__name__)


class EvaluationAPIClient:
    """Client to fetch and post data to Knowledge backend services."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")

    def fetch_cv_analysis(self, cv_text: str) -> Dict[str, Any]:
        """Fetch CV analysis from NLP backend."""
        # Placeholder: in real app, this would POST to /api/cv/analyze
        return {"mock": "cv_analysis", "timestamp": datetime.utcnow().isoformat()}

    def fetch_taxonomy_enrichment(self, skills: List[str]) -> Dict[str, Any]:
        """Fetch taxonomy enrichment for given skills."""
        # Placeholder: in real app, this would POST to /api/taxonomy/enrich
        return {"mock": "taxonomy_enrichment", "skills": skills, "timestamp": datetime.utcnow().isoformat()}

    def fetch_quiz_questions(self, skills: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fetch quiz questions for given skills."""
        # Placeholder: in real app, this would POST to /api/quiz/generate
        return {"mock": "quiz_questions", "skills": skills, "timestamp": datetime.utcnow().isoformat()}

    def submit_quiz_answers(self, answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Submit quiz answers and get scoring."""
        # Placeholder: in real app, this would POST to /api/quiz/score
        return {"mock": "quiz_scoring", "answers": answers, "timestamp": datetime.utcnow().isoformat()}

    def fetch_knowledge_score(
        self,
        cv_insights: Dict[str, Any],
        taxonomy_confidence: Dict[str, Any],
        quiz_mastery: Dict[str, Any],
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Fetch unified knowledge score."""
        # Placeholder: in real app, this would POST to /api/scoring/compute
        return {
            "mock": "knowledge_score",
            "cv_insights": cv_insights,
            "taxonomy_confidence": taxonomy_confidence,
            "quiz_mastery": quiz_mastery,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def flag_for_qa(self, entity_type: str, entity_id: str, reason: str) -> Dict[str, Any]:
        """Flag an entity for QA review."""
        # Placeholder: in real app, this would POST to /api/qa/flag
        return {"mock": "flagged", "entity_type": entity_type, "entity_id": entity_id, "reason": reason, "timestamp": datetime.utcnow().isoformat()}

    def rerun_nlp(self, cv_text: str) -> Dict[str, Any]:
        """Trigger NLP re-analysis."""
        # Placeholder: in real app, this would POST to /api/cv/rerun
        return {"mock": "rerun_nlp", "timestamp": datetime.utcnow().isoformat()}
