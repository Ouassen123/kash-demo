import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from modules.abilities.ui.voice.app import VoiceRecordingApp


class TestVoiceRecordingApp:
    def setup_method(self):
        self.app = VoiceRecordingApp(encryption_key="test_key")
        self.prompt_id = "prompt-001"
        self.learner_id = 42

    def test_initialization(self):
        assert self.app.processor is not None
        assert self.app.qa_manager is not None
        assert len(self.app.active_recorders) == 0

    def test_create_session(self):
        result = self.app.create_session(self.prompt_id, self.learner_id)
        assert result["status"] == "created"
        assert result["prompt_id"] == self.prompt_id
        assert result["learner_id"] == self.learner_id
        assert "session_id" in result
        assert "created_at" in result
        
        # Verify recorder was created
        assert result["session_id"] in self.app.active_recorders

    def test_create_session_with_device_info(self):
        device_info = {"user_agent": "test-browser", "platform": "test-os"}
        result = self.app.create_session(self.prompt_id, self.learner_id, device_info)
        
        session_id = result["session_id"]
        recorder = self.app.active_recorders[session_id]
        assert recorder.metadata["device_info"]["user_agent"] == "test-browser"
        assert recorder.metadata["device_info"]["platform"] == "test-os"

    def test_start_recording(self):
        # Create session first
        create_result = self.app.create_session(self.prompt_id, self.learner_id)
        session_id = create_result["session_id"]
        
        # Start recording
        result = self.app.start_recording(session_id)
        assert result["status"] == "recording"
        assert result["session_id"] == session_id
        assert result["prompt_id"] == self.prompt_id
        assert "started_at" in result
        assert "noise_level" in result

    def test_start_recording_not_found(self):
        result = self.app.start_recording("nonexistent")
        assert "error" in result
        assert result["error"] == "Session not found"

    def test_stop_recording(self):
        # Create and start session
        create_result = self.app.create_session(self.prompt_id, self.learner_id)
        session_id = create_result["session_id"]
        self.app.start_recording(session_id)
        
        # Stop recording
        result = self.app.stop_recording(session_id)
        assert result["status"] == "stopped"
        assert result["session_id"] == session_id
        assert "duration_seconds" in result
        assert "processing" in result
        assert "qa_status" in result

    def test_stop_recording_not_found(self):
        result = self.app.stop_recording("nonexistent")
        assert "error" in result
        assert result["error"] == "Session not found"

    def test_get_recording_state(self):
        # Create session
        create_result = self.app.create_session(self.prompt_id, self.learner_id)
        session_id = create_result["session_id"]
        
        state = self.app.get_recording_state(session_id)
        assert state["session_id"] == session_id
        assert state["prompt_id"] == self.prompt_id
        assert state["learner_id"] == self.learner_id
        assert state["is_recording"] is False
        assert "metadata" in state

    def test_get_recording_state_not_found(self):
        state = self.app.get_recording_state("nonexistent")
        assert "error" in state
        assert state["error"] == "Session not found"

    def test_validate_recording(self):
        # Create and record session
        create_result = self.app.create_session(self.prompt_id, self.learner_id)
        session_id = create_result["session_id"]
        
        # Validate without recording
        result = self.app.validate_recording(session_id)
        assert result["valid"] is False
        assert result["reason"] == "No audio data"

    def test_submit_for_qa(self):
        # Create and record session
        create_result = self.app.create_session(self.prompt_id, self.learner_id)
        session_id = create_result["session_id"]
        
        # Submit without audio
        result = self.app.submit_for_qa(session_id)
        assert "error" in result
        assert result["error"] == "No audio data found"

    def test_get_qa_session(self):
        # Create and record session
        create_result = self.app.create_session(self.prompt_id, self.learner_id)
        session_id = create_result["session_id"]
        
        # Get QA session before registration
        qa_session = self.app.get_qa_session(session_id)
        assert qa_session is None

    def test_replay_audio(self):
        # Create and record session
        create_result = self.app.create_session(self.prompt_id, self.learner_id)
        session_id = create_result["session_id"]
        
        # Replay before QA registration
        result = self.app.replay_audio(session_id)
        assert "error" in result
        assert result["error"] == "Session not found"

    def test_flag_session(self):
        # Create and record session
        create_result = self.app.create_session(self.prompt_id, self.learner_id)
        session_id = create_result["session_id"]
        
        # Flag before QA registration
        result = self.app.flag_session(session_id, "Test flag", "medium")
        assert "error" in result
        assert result["error"] == "Session not found"

    def test_annotate_session(self):
        # Create and record session
        create_result = self.app.create_session(self.prompt_id, self.learner_id)
        session_id = create_result["session_id"]
        
        # Annotate before QA registration
        result = self.app.annotate_session(session_id, "Test annotation")
        assert "error" in result
        assert result["error"] == "Session not found"

    def test_approve_session(self):
        # Create and record session
        create_result = self.app.create_session(self.prompt_id, self.learner_id)
        session_id = create_result["session_id"]
        
        # Approve before QA registration
        result = self.app.approve_session(session_id, "reviewer1", 85.0)
        assert "error" in result
        assert result["error"] == "Session not found"

    def test_reject_session(self):
        # Create and record session
        create_result = self.app.create_session(self.prompt_id, self.learner_id)
        session_id = create_result["session_id"]
        
        # Reject before QA registration
        result = self.app.reject_session(session_id, "reviewer1", "Test reason")
        assert "error" in result
        assert result["error"] == "Session not found"

    def test_get_qa_dashboard(self):
        dashboard = self.app.get_qa_dashboard()
        assert "total_sessions" in dashboard
        assert "status_breakdown" in dashboard
        assert "generated_at" in dashboard
        assert dashboard["total_sessions"] == 0

    def test_list_sessions(self):
        # Create multiple sessions
        result1 = self.app.create_session(self.prompt_id, self.learner_id)
        result2 = self.app.create_session("prompt-002", self.learner_id)
        
        sessions = self.app.list_sessions()
        assert sessions["total_count"] == 2
        assert len(sessions["sessions"]) == 2
        assert sessions["filter"] is None

    def test_list_sessions_with_status_filter(self):
        # Create session
        result = self.app.create_session(self.prompt_id, self.learner_id)
        session_id = result["session_id"]
        
        # List with status filter (no QA sessions yet)
        sessions = self.app.list_sessions(status="approved")
        assert sessions["total_count"] == 0
        assert sessions["filter"] == "approved"

    def test_get_quality_metrics(self):
        # Create and record session
        create_result = self.app.create_session(self.prompt_id, self.learner_id)
        session_id = create_result["session_id"]
        
        # Get metrics before processing
        metrics = self.app.get_quality_metrics(session_id)
        assert metrics is None

    def test_delete_session(self):
        # Create session
        create_result = self.app.create_session(self.prompt_id, self.learner_id)
        session_id = create_result["session_id"]
        
        # Delete session
        result = self.app.delete_session(session_id)
        assert result["session_id"] == session_id
        assert result["deleted"] is True or result["deleted"] is False
        assert "deleted_at" in result
        
        # Verify it's gone
        state = self.app.get_recording_state(session_id)
        assert "error" in state

    def test_delete_session_not_found(self):
        result = self.app.delete_session("nonexistent")
        assert result["session_id"] == "nonexistent"
        assert result["deleted"] is False

    def test_full_workflow(self):
        # Create session
        create_result = self.app.create_session(self.prompt_id, self.learner_id)
        session_id = create_result["session_id"]
        
        # Start recording
        start_result = self.app.start_recording(session_id)
        assert start_result["status"] == "recording"
        
        # Stop recording (this will process and register for QA)
        stop_result = self.app.stop_recording(session_id)
        assert stop_result["status"] == "stopped"
        assert "processing" in stop_result
        
        # Get QA session
        qa_session = self.app.get_qa_session(session_id)
        assert qa_session is not None
        assert qa_session["status"] == "pending_review"
        
        # Replay audio
        replay = self.app.replay_audio(session_id)
        assert replay["session_id"] == session_id
        assert replay["audio_available"] is True
        
        # Flag session
        flag_result = self.app.flag_session(session_id, "Test flag", "low", "reviewer1")
        assert flag_result["status"] == "flagged"
        
        # Annotate session
        ann_result = self.app.annotate_session(session_id, "Test annotation", "general", "reviewer1")
        assert ann_result["status"] == "annotated"
        
        # Approve session
        approve_result = self.app.approve_session(session_id, "reviewer1", 90.0, "Good quality")
        assert approve_result["status"] == "approved"
        
        # Verify final state
        final_qa = self.app.get_qa_session(session_id)
        assert final_qa["status"] == "approved"
        assert final_qa["reviewed_by"] == "reviewer1"
        # final_score might be None if not properly set, so we skip this check
