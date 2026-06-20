import pytest
import sys
import tempfile
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from modules.abilities.text_tests.api import TextTestAPI


class TestTextTestAPI:
    def setup_method(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.temp_file.close()
        self.api = TextTestAPI(storage_path=self.temp_file.name)

    def teardown_method(self):
        os.unlink(self.temp_file.name)

    def test_list_templates(self):
        templates = self.api.list_templates()
        assert isinstance(templates, list)
        assert len(templates) >= 3
        ids = {t["id"] for t in templates}
        assert "logic_sequence" in ids
        assert "creativity_story" in ids
        assert "persistence_puzzle" in ids

    def test_start_test(self):
        result = self.api.start_test(["logic_sequence", "creativity_story"], user_id=5)
        assert "session_id" in result
        assert result["user_id"] == 5
        assert result["status"] == "in_progress"
        assert result["next_prompt"] is not None
        assert result["next_prompt"]["id"] == "logic_sequence"

    def test_get_next_prompt(self):
        start = self.api.start_test(["logic_sequence"], user_id=1)
        session_id = start["session_id"]
        prompt = self.api.get_next_prompt(session_id)
        assert prompt is not None
        assert prompt["id"] == "logic_sequence"

        # Submit response to complete
        self.api.submit_response(session_id, "32 because it doubles", 30)
        prompt_after = self.api.get_next_prompt(session_id)
        assert prompt_after is None

    def test_submit_response_and_complete(self):
        start = self.api.start_test(["logic_sequence"], user_id=2)
        session_id = start["session_id"]
        result = self.api.submit_response(session_id, "32 because it doubles", 30)
        assert result["session_id"] == session_id
        assert result["status"] == "completed"
        assert "metrics" in result
        assert result["next_prompt"] is None
        # Metrics should include overall_score and confidence_band
        assert "overall_score" in result["metrics"]
        assert "confidence_band" in result["metrics"]

    def test_submit_response_multi_step(self):
        start = self.api.start_test(["logic_sequence", "creativity_story"], user_id=3)
        session_id = start["session_id"]

        # First response
        result1 = self.api.submit_response(session_id, "32 because it doubles", 30)
        assert result1["status"] == "in_progress"
        assert result1["next_prompt"] is not None
        assert result1["next_prompt"]["id"] == "creativity_story"

        # Second response (completes)
        result2 = self.api.submit_response(session_id, "A robot found a secret in the forest.", 60)
        assert result2["status"] == "completed"
        assert "metrics" in result2
        assert result2["next_prompt"] is None

    def test_get_session_summary(self):
        start = self.api.start_test(["logic_sequence"], user_id=4)
        session_id = start["session_id"]
        self.api.submit_response(session_id, "32 because it doubles", 30)

        summary = self.api.get_session_summary(session_id)
        assert summary is not None
        assert "session" in summary
        assert "transcript" in summary
        assert "metrics" in summary
        assert summary["session"]["session_id"] == session_id
        assert len(summary["transcript"]) == 1
        assert summary["metrics"]["overall_score"] is not None

    def test_list_user_sessions(self):
        self.api.start_test(["logic_sequence"], user_id=10)
        self.api.start_test(["creativity_story"], user_id=11)
        self.api.start_test(["persistence_puzzle"], user_id=10)

        user10_sessions = self.api.list_user_sessions(10)
        assert len(user10_sessions) == 2
        user11_sessions = self.api.list_user_sessions(11)
        assert len(user11_sessions) == 1

    def test_delete_session(self):
        start = self.api.start_test(["logic_sequence"], user_id=20)
        session_id = start["session_id"]
        self.api.submit_response(session_id, "32 because it doubles", 30)

        # Verify exists
        assert self.api.get_session_summary(session_id) is not None

        # Delete
        assert self.api.delete_session(session_id) is True
        assert self.api.get_session_summary(session_id) is None
