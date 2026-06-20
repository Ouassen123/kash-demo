import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from modules.abilities.text_tests.orchestrator import PromptOrchestrator


class TestPromptOrchestrator:
    def setup_method(self):
        self.orchestrator = PromptOrchestrator()

    def test_list_templates(self):
        templates = self.orchestrator.list_templates()
        assert isinstance(templates, list)
        assert len(templates) >= 3
        ids = {t["id"] for t in templates}
        assert "logic_sequence" in ids
        assert "creativity_story" in ids
        assert "persistence_puzzle" in ids

    def test_start_session(self):
        session = self.orchestrator.start_session(["logic_sequence", "creativity_story"], user_id=7)
        assert "session_id" in session
        assert session["user_id"] == 7
        assert session["status"] == "in_progress"
        assert session["current_index"] == 0
        assert len(session["templates"]) == 2

    def test_get_next_prompt(self):
        session = self.orchestrator.start_session(["logic_sequence"], user_id=1)
        prompt = self.orchestrator.get_next_prompt(session)
        assert prompt is not None
        assert prompt["id"] == "logic_sequence"
        assert "prompt" in prompt
        assert prompt["prompt_index"] == 0

        # After recording response, no more prompts
        updated = self.orchestrator.record_response(session, "32, because it doubles each time.", 45)
        next_prompt = self.orchestrator.get_next_prompt(updated)
        assert next_prompt is None

    def test_record_response(self):
        session = self.orchestrator.start_session(["logic_sequence"], user_id=1)
        updated = self.orchestrator.record_response(session, "32, because it doubles each time.", 45)
        assert updated["current_index"] == 1
        assert updated["status"] == "completed"
        assert "completed_at" in updated
        assert len(updated["responses"]) == 1
        assert updated["responses"][0]["response_text"] == "32, because it doubles each time."
        assert updated["responses"][0]["time_taken_seconds"] == 45

    def test_get_session_summary(self):
        session = self.orchestrator.start_session(["logic_sequence", "creativity_story"], user_id=3)
        self.orchestrator.record_response(session, "32, because it doubles each time.", 30)
        self.orchestrator.record_response(session, "A robot found a secret in the forest.", 60)

        summary = self.orchestrator.get_session_summary(session)
        assert summary["session_id"] == session["session_id"]
        assert summary["user_id"] == 3
        assert summary["status"] == "completed"
        assert summary["prompts_count"] == 2
        assert summary["responses_count"] == 2
        assert summary["total_time_seconds"] == 90
        assert len(summary["transcript"]) == 2
