import pytest
import sys
import tempfile
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from modules.abilities.text_tests.storage import TextTestStorage


class TestTextTestStorage:
    def setup_method(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.temp_file.close()
        self.storage = TextTestStorage(storage_path=self.temp_file.name)

    def teardown_method(self):
        os.unlink(self.temp_file.name)

    def test_save_and_get_session(self):
        session = {
            "session_id": "sess-123",
            "user_id": 42,
            "status": "in_progress",
            "templates": [],
            "responses": [],
        }
        assert self.storage.save_session(session) is True
        retrieved = self.storage.get_session("sess-123")
        assert retrieved["session_id"] == "sess-123"
        assert retrieved["user_id"] == 42

    def test_save_and_get_transcript(self):
        transcript = [
            {"prompt_id": "logic_sequence", "response_text": "32", "time_taken_seconds": 30},
            {"prompt_id": "creativity_story", "response_text": "A robot story.", "time_taken_seconds": 60},
        ]
        assert self.storage.save_transcript("sess-123", transcript) is True
        retrieved = self.storage.get_transcript("sess-123")
        assert len(retrieved) == 2
        assert retrieved[0]["response_text"] == "32"

    def test_save_and_get_metrics(self):
        metrics = {
            "overall_score": 0.78,
            "overall_confidence": 0.85,
            "dimension_means": {"logic": 0.8, "creativity": 0.75},
        }
        assert self.storage.save_metrics("sess-123", metrics) is True
        retrieved = self.storage.get_metrics("sess-123")
        assert retrieved["overall_score"] == 0.78
        assert retrieved["dimension_means"]["logic"] == 0.8

    def test_list_sessions(self):
        # Save sessions for two users
        self.storage.save_session({"session_id": "s1", "user_id": 1, "status": "done", "templates": [], "responses": []})
        self.storage.save_session({"session_id": "s2", "user_id": 2, "status": "done", "templates": [], "responses": []})
        self.storage.save_session({"session_id": "s3", "user_id": 1, "status": "done", "templates": [], "responses": []})
        all_ids = self.storage.list_sessions()
        assert set(all_ids) == {"s1", "s2", "s3"}
        user1_ids = self.storage.list_sessions(user_id=1)
        assert set(user1_ids) == {"s1", "s3"}

    def test_delete_session(self):
        self.storage.save_session({"session_id": "s1", "user_id": 1, "status": "done", "templates": [], "responses": []})
        self.storage.save_transcript("s1", [{"prompt_id": "p1", "response_text": "ok", "time_taken_seconds": 10}])
        self.storage.save_metrics("s1", {"overall_score": 0.5})
        assert self.storage.get_session("s1") is not None
        assert self.storage.get_transcript("s1") is not None
        assert self.storage.get_metrics("s1") is not None

        assert self.storage.delete_session("s1") is True
        assert self.storage.get_session("s1") is None
        assert self.storage.get_transcript("s1") is None
        assert self.storage.get_metrics("s1") is None

    def test_export_session(self):
        session = {"session_id": "s1", "user_id": 1, "status": "done", "templates": [], "responses": []}
        transcript = [{"prompt_id": "p1", "response_text": "ok", "time_taken_seconds": 10}]
        metrics = {"overall_score": 0.5}
        self.storage.save_session(session)
        self.storage.save_transcript("s1", transcript)
        self.storage.save_metrics("s1", metrics)

        exported = self.storage.export_session("s1")
        assert exported["session"]["session_id"] == "s1"
        assert exported["transcript"] == transcript
        assert exported["metrics"] == metrics
        assert "exported_at" in exported

        # Non-existent session returns None
        assert self.storage.export_session("unknown") is None
