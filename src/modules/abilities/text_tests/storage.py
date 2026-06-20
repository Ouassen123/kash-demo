"""Storage for transcripts, metrics, and metadata for text-based cognitive tests."""

from typing import List, Dict, Any, Optional
import json
from datetime import datetime

from src.core.logging import get_logger

logger = get_logger(__name__)


class TextTestStorage:
    """Persist transcripts, metrics, and metadata for reuse across stories."""

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize storage with optional file path.

        Args:
            storage_path: Path to JSON file for persistence (defaults to in-memory).
        """
        self.storage_path = storage_path
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._transcripts: Dict[str, List[Dict[str, Any]]] = {}
        self._metrics: Dict[str, Dict[str, Any]] = {}
        if storage_path:
            self._load_from_disk()

    def _load_from_disk(self):
        """Load existing data from JSON file."""
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._sessions = data.get("sessions", {})
                self._transcripts = data.get("transcripts", {})
                self._metrics = data.get("metrics", {})
        except FileNotFoundError:
            logger.info(f"No existing storage file at {self.storage_path}, starting fresh.")
        except Exception as e:
            logger.error(f"Failed to load storage from {self.storage_path}: {e}")

    def _persist_to_disk(self):
        """Persist current data to JSON file."""
        if not self.storage_path:
            return
        try:
            data = {
                "sessions": self._sessions,
                "transcripts": self._transcripts,
                "metrics": self._metrics,
                "last_updated": datetime.utcnow().isoformat(),
            }
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to persist storage to {self.storage_path}: {e}")

    def save_session(self, session: Dict[str, Any]) -> bool:
        """
        Save a session (metadata only).

        Args:
            session: Session dict from orchestrator.

        Returns:
            True if saved successfully.
        """
        session_id = session["session_id"]
        self._sessions[session_id] = session
        self._persist_to_disk()
        return True

    def save_transcript(self, session_id: str, transcript: List[Dict[str, Any]]) -> bool:
        """
        Save a transcript for a session.

        Args:
            session_id: Session identifier.
            transcript: List of response entries.

        Returns:
            True if saved successfully.
        """
        self._transcripts[session_id] = transcript
        self._persist_to_disk()
        return True

    def save_metrics(self, session_id: str, metrics: Dict[str, Any]) -> bool:
        """
        Save scoring metrics for a session.

        Args:
            session_id: Session identifier.
            metrics: Scoring output from CognitiveScorer.

        Returns:
            True if saved successfully.
        """
        self._metrics[session_id] = metrics
        self._persist_to_disk()
        return True

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session metadata."""
        return self._sessions.get(session_id)

    def get_transcript(self, session_id: str) -> Optional[List[Dict[str, Any]]]:
        """Retrieve transcript for a session."""
        return self._transcripts.get(session_id)

    def get_metrics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve metrics for a session."""
        return self._metrics.get(session_id)

    def list_sessions(self, user_id: Optional[int] = None) -> List[str]:
        """
        List session IDs, optionally filtered by user.

        Args:
            user_id: Optional user filter.

        Returns:
            List of session IDs.
        """
        if user_id is None:
            return list(self._sessions.keys())
        return [sid for sid, sess in self._sessions.items() if sess.get("user_id") == user_id]

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and its related data.

        Args:
            session_id: Session identifier.

        Returns:
            True if deleted.
        """
        deleted = False
        if session_id in self._sessions:
            del self._sessions[session_id]
            deleted = True
        if session_id in self._transcripts:
            del self._transcripts[session_id]
            deleted = True
        if session_id in self._metrics:
            del self._metrics[session_id]
            deleted = True
        if deleted:
            self._persist_to_disk()
        return deleted

    def export_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Export a full session (metadata, transcript, metrics) for downstream use.

        Args:
            session_id: Session identifier.

        Returns:
            Combined dict or None if not found.
        """
        session = self.get_session(session_id)
        transcript = self.get_transcript(session_id)
        metrics = self.get_metrics(session_id)
        if not session:
            return None
        return {
            "session": session,
            "transcript": transcript,
            "metrics": metrics,
            "exported_at": datetime.utcnow().isoformat(),
        }
