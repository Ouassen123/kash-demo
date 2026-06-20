"""API layer for text-based cognitive tests."""

from typing import List, Dict, Any, Optional
from datetime import datetime

from .orchestrator import PromptOrchestrator
from .scoring import CognitiveScorer
from .storage import TextTestStorage
from src.core.logging import get_logger

logger = get_logger(__name__)


class TextTestAPI:
    """Facade for orchestrating, scoring, and persisting text-based cognitive tests."""

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize API with optional storage path.

        Args:
            storage_path: Path to JSON storage file.
        """
        self.orchestrator = PromptOrchestrator()
        self.scorer = CognitiveScorer()
        self.storage = TextTestStorage(storage_path)

    def list_templates(self) -> List[Dict[str, Any]]:
        """List available prompt templates."""
        return self.orchestrator.list_templates()

    def start_test(self, template_ids: List[str], user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Start a new test session.

        Args:
            template_ids: Ordered list of template IDs.
            user_id: Optional user identifier.

        Returns:
            Session dict with session_id and first prompt (if any).
        """
        session = self.orchestrator.start_session(template_ids, user_id)
        self.storage.save_session(session)
        first_prompt = self.orchestrator.get_next_prompt(session)
        return {
            "session_id": session["session_id"],
            "user_id": session.get("user_id"),
            "status": session["status"],
            "next_prompt": first_prompt,
        }

    def get_next_prompt(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get the next prompt for a session."""
        session = self.storage.get_session(session_id)
        if not session:
            return None
        return self.orchestrator.get_next_prompt(session)

    def submit_response(self, session_id: str, response_text: str, time_taken_seconds: int) -> Dict[str, Any]:
        """
        Submit a response and advance the session.

        Args:
            session_id: Session identifier.
            response_text: User's response.
            time_taken_seconds: Time spent on this prompt.

        Returns:
            Updated session info and next prompt (if any).
        """
        session = self.storage.get_session(session_id)
        if not session:
            return {"error": "Session not found"}

        updated = self.orchestrator.record_response(session, response_text, time_taken_seconds)
        self.storage.save_session(updated)

        # If completed, score the session
        if updated["status"] == "completed":
            summary = self.orchestrator.get_session_summary(updated)
            transcript = summary["transcript"]
            self.storage.save_transcript(session_id, transcript)
            metrics = self.scorer.score_session(transcript)
            self.storage.save_metrics(session_id, metrics)
            return {
                "session_id": session_id,
                "status": "completed",
                "metrics": metrics,
                "next_prompt": None,
            }
        else:
            next_prompt = self.orchestrator.get_next_prompt(updated)
            return {
                "session_id": session_id,
                "status": updated["status"],
                "next_prompt": next_prompt,
            }

    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a full session summary (metadata, transcript, metrics)."""
        return self.storage.export_session(session_id)

    def list_user_sessions(self, user_id: int) -> List[str]:
        """List session IDs for a given user."""
        return self.storage.list_sessions(user_id=user_id)

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and its data."""
        return self.storage.delete_session(session_id)
