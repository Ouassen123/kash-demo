"""Prompt orchestration service for text-based cognitive tests."""

from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

from src.core.logging import get_logger

logger = get_logger(__name__)


class PromptOrchestrator:
    """Loads scenario templates, executes them in order, tracks time and metadata."""

    def __init__(self, templates_dir: Optional[str] = None):
        """
        Initialize orchestrator with optional templates directory.

        Args:
            templates_dir: Path to prompt templates (defaults to internal).
        """
        self.templates_dir = templates_dir or "modules/abilities/text-tests/templates"
        self.templates: Dict[str, Dict[str, Any]] = {}
        self._load_templates()

    def _load_templates(self):
        """Load prompt templates from disk or fallback to in-memory defaults."""
        # In-memory fallback templates for demo
        self.templates = {
            "logic_sequence": {
                "id": "logic_sequence",
                "prompt": "You are given a sequence: 2, 4, 8, 16, __. What is the next number and why?",
                "expected_dimensions": ["logic", "reasoning"],
                "time_limit_seconds": 120,
                "localizable": True,
                "version": "1.0",
            },
            "creativity_story": {
                "id": "creativity_story",
                "prompt": "Write a short story (3-5 sentences) that includes a robot, a forest, and a secret.",
                "expected_dimensions": ["creativity", "originality"],
                "time_limit_seconds": 180,
                "localizable": True,
                "version": "1.0",
            },
            "persistence_puzzle": {
                "id": "persistence_puzzle",
                "prompt": "Describe how you would approach solving a complex problem you have never seen before.",
                "expected_dimensions": ["persistence", "metacognition"],
                "time_limit_seconds": 150,
                "localizable": True,
                "version": "1.0",
            },
        }

    def list_templates(self) -> List[Dict[str, Any]]:
        """List available templates with metadata."""
        return [
            {
                "id": tmpl["id"],
                "expected_dimensions": tmpl["expected_dimensions"],
                "time_limit_seconds": tmpl["time_limit_seconds"],
                "localizable": tmpl["localizable"],
                "version": tmpl["version"],
            }
            for tmpl in self.templates.values()
        ]

    def start_session(self, template_ids: List[str], user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Start a new test session with ordered templates.

        Args:
            template_ids: Ordered list of template IDs to run.
            user_id: Optional user identifier.

        Returns:
            Session dict with session_id, ordered prompts, and metadata.
        """
        session_id = str(uuid.uuid4())
        ordered_templates = [self.templates[tid] for tid in template_ids if tid in self.templates]
        if len(ordered_templates) != len(template_ids):
            missing = set(template_ids) - set(self.templates.keys())
            logger.warning(f"Missing templates: {missing}")

        session = {
            "session_id": session_id,
            "user_id": user_id,
            "started_at": datetime.utcnow().isoformat(),
            "templates": ordered_templates,
            "status": "in_progress",
            "current_index": 0,
            "responses": [],
        }
        return session

    def get_next_prompt(self, session: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get the next prompt for a session.

        Args:
            session: Current session dict.

        Returns:
            Next prompt dict or None if finished.
        """
        idx = session.get("current_index", 0)
        templates = session.get("templates", [])
        if idx >= len(templates):
            return None
        prompt = templates[idx].copy()
        prompt["session_id"] = session["session_id"]
        prompt["prompt_index"] = idx
        return prompt

    def record_response(self, session: Dict[str, Any], response_text: str, time_taken_seconds: int) -> Dict[str, Any]:
        """
        Record a response and advance the session.

        Args:
            session: Current session dict.
            response_text: User's free-form response.
            time_taken_seconds: Time spent on this prompt.

        Returns:
            Updated session dict.
        """
        idx = session.get("current_index", 0)
        templates = session.get("templates", [])
        if idx >= len(templates):
            raise ValueError("No more prompts in this session")

        prompt = templates[idx]
        response = {
            "prompt_id": prompt["id"],
            "prompt_index": idx,
            "response_text": response_text,
            "time_taken_seconds": time_taken_seconds,
            "timestamp": datetime.utcnow().isoformat(),
        }
        session.setdefault("responses", []).append(response)
        session["current_index"] = idx + 1

        # Mark complete if all prompts answered
        if session["current_index"] >= len(templates):
            session["status"] = "completed"
            session["completed_at"] = datetime.utcnow().isoformat()

        return session

    def get_session_summary(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """
        Summarize a session for persistence/scoring.

        Args:
            session: Completed or in-progress session.

        Returns:
            Summary dict with transcript and metadata.
        """
        return {
            "session_id": session["session_id"],
            "user_id": session.get("user_id"),
            "started_at": session["started_at"],
            "completed_at": session.get("completed_at"),
            "status": session["status"],
            "prompts_count": len(session.get("templates", [])),
            "responses_count": len(session.get("responses", [])),
            "total_time_seconds": sum(r.get("time_taken_seconds", 0) for r in session.get("responses", [])),
            "transcript": session.get("responses", []),
        }
