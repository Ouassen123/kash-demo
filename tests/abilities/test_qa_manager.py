import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from modules.abilities.audio.qa_manager import QAManager


class TestQAManager:
    def setup_method(self):
        self.qa_manager = QAManager()
        self.session_id = "test-session-123"
        self.audio_info = {
            "session_id": self.session_id,
            "prompt_id": "prompt-001",
            "audio_hash": "hash123",
            "metadata": {
                "duration_seconds": 25.5,
                "noise_level": 0.3,
            },
            "quality_score": 85.0,
        }

    def test_initialization(self):
        assert len(self.qa_manager.sessions) == 0
        assert len(self.qa_manager.flags) == 0
        assert len(self.qa_manager.annotations) == 0

    def test_register_session(self):
        result = self.qa_manager.register_session(self.session_id, self.audio_info)
        assert result["status"] == "registered"
        assert result["session_id"] == self.session_id
        assert result["qa_status"] == "pending_review"
        assert "registered_at" in result

    def test_get_session_for_review(self):
        # Register session first
        self.qa_manager.register_session(self.session_id, self.audio_info)
        
        session = self.qa_manager.get_session_for_review(self.session_id)
        assert session is not None
        assert session["session_id"] == self.session_id
        assert session["status"] == "pending_review"
        assert "audio_info" in session
        assert "flags" in session
        assert "annotations" in session

    def test_get_session_for_review_not_found(self):
        session = self.qa_manager.get_session_for_review("nonexistent")
        assert session is None

    def test_replay_audio(self):
        # Register session first
        self.qa_manager.register_session(self.session_id, self.audio_info)
        
        replay = self.qa_manager.replay_audio(self.session_id)
        assert replay["session_id"] == self.session_id
        assert replay["audio_available"] is True
        assert "audio_hash" in replay
        assert "duration_seconds" in replay
        assert "quality_score" in replay
        assert "replay_token" in replay

    def test_replay_audio_not_found(self):
        replay = self.qa_manager.replay_audio("nonexistent")
        assert "error" in replay
        assert replay["error"] == "Session not found"

    def test_flag_session(self):
        # Register session first
        self.qa_manager.register_session(self.session_id, self.audio_info)
        
        result = self.qa_manager.flag_session(
            self.session_id, "Poor audio quality", "high", "reviewer1"
        )
        assert result["status"] == "flagged"
        assert result["session_id"] == self.session_id
        assert result["reason"] == "Poor audio quality"
        assert result["severity"] == "high"
        assert result["flagged_by"] == "reviewer1" or result.get("flagged_by") == "unknown"
        assert "flag_id" in result
        assert "flagged_at" in result

    def test_flag_session_not_found(self):
        result = self.qa_manager.flag_session(
            "nonexistent", "Test reason", "medium"
        )
        assert "error" in result
        assert result["error"] == "Session not found"

    def test_flag_session_critical_updates_status(self):
        # Register session first
        self.qa_manager.register_session(self.session_id, self.audio_info)
        
        # Flag with critical severity
        self.qa_manager.flag_session(self.session_id, "Critical issue", "critical")
        
        session = self.qa_manager.get_session_for_review(self.session_id)
        assert session["status"] == "critical_issue"

    def test_annotate_session(self):
        # Register session first
        self.qa_manager.register_session(self.session_id, self.audio_info)
        
        result = self.qa_manager.annotate_session(
            self.session_id, "Good response quality", "quality", "reviewer1"
        )
        assert result["status"] == "annotated"
        assert result["session_id"] == self.session_id
        assert result["type"] == "quality"
        assert result["annotated_by"] == "reviewer1" or result.get("annotated_by") == "unknown"
        assert "annotation_id" in result
        assert "annotated_at" in result

    def test_annotate_session_not_found(self):
        result = self.qa_manager.annotate_session(
            "nonexistent", "Test annotation", "general"
        )
        assert "error" in result
        assert result["error"] == "Session not found"

    def test_approve_session(self):
        # Register session first
        self.qa_manager.register_session(self.session_id, self.audio_info)
        
        result = self.qa_manager.approve_session(
            self.session_id, "reviewer1", 88.5, "Looks good"
        )
        assert result["status"] == "approved"
        assert result["session_id"] == self.session_id
        assert result["reviewed_by"] == "reviewer1"
        assert result["final_score"] == 88.5
        assert "reviewed_at" in result

    def test_approve_session_not_found(self):
        result = self.qa_manager.approve_session(
            "nonexistent", "reviewer1", 90.0
        )
        assert "error" in result
        assert result["error"] == "Session not found"

    def test_reject_session(self):
        # Register session first
        self.qa_manager.register_session(self.session_id, self.audio_info)
        
        result = self.qa_manager.reject_session(
            self.session_id, "reviewer1", "Inaudible audio", "Needs re-recording"
        )
        assert result["status"] == "rejected"
        assert result["session_id"] == self.session_id
        assert result["reviewed_by"] == "reviewer1"
        assert result["rejection_reason"] == "Inaudible audio"
        assert "reviewed_at" in result

    def test_reject_session_not_found(self):
        result = self.qa_manager.reject_session(
            "nonexistent", "reviewer1", "Test reason"
        )
        assert "error" in result
        assert result["error"] == "Session not found"

    def test_get_qa_dashboard(self):
        # Register multiple sessions with different statuses
        self.qa_manager.register_session("session1", self.audio_info)
        self.qa_manager.register_session("session2", self.audio_info)
        self.qa_manager.register_session("session3", self.audio_info)
        
        # Approve one
        self.qa_manager.approve_session("session1", "reviewer1")
        
        # Reject one
        self.qa_manager.reject_session("session2", "reviewer1", "Test reason")
        
        # Flag one
        self.qa_manager.flag_session("session3", "Test flag", "medium")
        
        dashboard = self.qa_manager.get_qa_dashboard()
        assert dashboard["total_sessions"] == 3
        assert dashboard["pending_review"] == 1  # session3
        assert dashboard["approved"] == 1  # session1
        assert dashboard["rejected"] == 1  # session2
        assert "status_breakdown" in dashboard
        assert "flag_severity_breakdown" in dashboard
        assert "generated_at" in dashboard

    def test_list_sessions_by_status(self):
        # Register multiple sessions
        self.qa_manager.register_session("session1", self.audio_info)
        self.qa_manager.register_session("session2", self.audio_info)
        self.qa_manager.register_session("session3", self.audio_info)
        
        # Approve one
        self.qa_manager.approve_session("session1", "reviewer1")
        
        pending = self.qa_manager.list_sessions_by_status("pending_review")
        approved = self.qa_manager.list_sessions_by_status("approved")
        
        assert len(pending) == 2
        assert "session2" in pending
        assert "session3" in pending
        assert len(approved) == 1
        assert "session1" in approved

    def test_multiple_flags_and_annotations(self):
        # Register session
        self.qa_manager.register_session(self.session_id, self.audio_info)
        
        # Add multiple flags
        self.qa_manager.flag_session(self.session_id, "Issue 1", "low")
        self.qa_manager.flag_session(self.session_id, "Issue 2", "medium")
        
        # Add multiple annotations
        self.qa_manager.annotate_session(self.session_id, "Note 1", "general")
        self.qa_manager.annotate_session(self.session_id, "Note 2", "quality")
        
        session = self.qa_manager.get_session_for_review(self.session_id)
        assert len(session["flags"]) == 2
        assert len(session["annotations"]) == 2
        
        # Check flag severities
        severities = [flag["severity"] for flag in session["flags"]]
        assert "low" in severities
        assert "medium" in severities
        
        # Check annotation types
        types = [ann["type"] for ann in session["annotations"]]
        assert "general" in types
        assert "quality" in types
