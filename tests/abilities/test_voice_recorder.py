import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from modules.abilities.ui.voice.recorder import VoiceRecorder


class TestVoiceRecorder:
    def setup_method(self):
        self.session_id = "test-session-123"
        self.prompt_id = "prompt-001"
        self.learner_id = 42
        self.recorder = VoiceRecorder(self.session_id, self.prompt_id, self.learner_id)

    def test_initialization(self):
        assert self.recorder.session_id == self.session_id
        assert self.recorder.prompt_id == self.prompt_id
        assert self.recorder.learner_id == self.learner_id
        assert not self.recorder.is_recording
        assert self.recorder.start_time is None
        assert self.recorder.audio_blob is None

    def test_start_recording(self):
        result = self.recorder.start_recording()
        assert result["status"] == "recording"
        assert result["session_id"] == self.session_id
        assert result["prompt_id"] == self.prompt_id
        assert "started_at" in result
        assert "noise_level" in result
        assert self.recorder.is_recording
        assert self.recorder.start_time is not None

    def test_start_recording_already_recording(self):
        self.recorder.start_recording()
        result = self.recorder.start_recording()
        assert "error" in result
        assert result["error"] == "Already recording"

    def test_stop_recording(self):
        self.recorder.start_recording()
        result = self.recorder.stop_recording()
        assert result["status"] == "stopped"
        assert result["session_id"] == self.session_id
        assert result["prompt_id"] == self.prompt_id
        assert "duration_seconds" in result
        assert "audio_size_bytes" in result
        assert "stopped_at" in result
        assert not self.recorder.is_recording
        assert self.recorder.audio_blob is not None

    def test_stop_recording_not_recording(self):
        result = self.recorder.stop_recording()
        assert "error" in result
        assert result["error"] == "Not recording"

    def test_get_recording_state(self):
        state = self.recorder.get_recording_state()
        assert state["is_recording"] is False
        assert state["session_id"] == self.session_id
        assert state["prompt_id"] == self.prompt_id
        assert state["learner_id"] == self.learner_id
        assert "metadata" in state
        assert state["has_audio"] is False

    def test_get_audio_data(self):
        # Before recording
        assert self.recorder.get_audio_data() is None
        
        # After recording
        self.recorder.start_recording()
        self.recorder.stop_recording()
        audio_data = self.recorder.get_audio_data()
        assert audio_data is not None
        assert isinstance(audio_data, bytes)

    def test_get_metadata(self):
        metadata = self.recorder.get_metadata()
        assert metadata["session_id"] == self.session_id
        assert metadata["prompt_id"] == self.prompt_id
        assert metadata["learner_id"] == self.learner_id
        assert "device_info" in metadata
        assert "created_at" in metadata

    def test_validate_recording_no_audio(self):
        result = self.recorder.validate_recording()
        assert result["valid"] is False
        assert result["reason"] == "No audio data"

    def test_validate_recording_good_quality(self):
        self.recorder.start_recording()
        # Mock good recording parameters
        self.recorder.metadata["duration_seconds"] = 25.0
        self.recorder.metadata["noise_level"] = 0.3
        self.recorder.audio_blob = b"mock_audio_data"
        
        result = self.recorder.validate_recording()
        assert result["valid"] is True
        assert len(result["issues"]) == 0

    def test_validate_recording_too_short(self):
        self.recorder.start_recording()
        self.recorder.metadata["duration_seconds"] = 0.5
        self.recorder.metadata["noise_level"] = 0.3
        self.recorder.audio_blob = b"mock_audio_data"
        
        result = self.recorder.validate_recording()
        assert result["valid"] is False
        assert "Too short" in result["issues"]
        assert "Record for at least 1 second" in result["recommendations"]

    def test_validate_recording_too_long(self):
        self.recorder.start_recording()
        self.recorder.metadata["duration_seconds"] = 350.0
        self.recorder.metadata["noise_level"] = 0.3
        self.recorder.audio_blob = b"mock_audio_data"
        
        result = self.recorder.validate_recording()
        assert result["valid"] is False
        assert "Too long" in result["issues"]
        assert "Keep recordings under 5 minutes" in result["recommendations"]

    def test_validate_recording_high_noise(self):
        self.recorder.start_recording()
        self.recorder.metadata["duration_seconds"] = 25.0
        self.recorder.metadata["noise_level"] = 0.8
        self.recorder.audio_blob = b"mock_audio_data"
        
        result = self.recorder.validate_recording()
        assert result["valid"] is False
        assert "High background noise" in result["issues"]
        assert "Reduce background noise" in result["recommendations"]

    def test_monitor_noise(self):
        noise_level = self.recorder._monitor_noise()
        assert isinstance(noise_level, float)
        assert 0.0 <= noise_level <= 1.0

    def test_get_device_info(self):
        device_info = self.recorder._get_device_info()
        assert "user_agent" in device_info
        assert "platform" in device_info
        assert "audio_context" in device_info
        assert "sample_rate" in device_info
        assert "channels" in device_info
