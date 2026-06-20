import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from modules.abilities.audio.processor import AudioProcessor


class TestAudioProcessor:
    def setup_method(self):
        self.processor = AudioProcessor(encryption_key="test_key")
        self.session_id = "test-session-123"
        self.audio_blob = b"mock_audio_data_test"
        self.metadata = {
            "session_id": self.session_id,
            "prompt_id": "prompt-001",
            "learner_id": 42,
            "duration_seconds": 25.5,
            "noise_level": 0.3,
        }

    def test_initialization(self):
        assert self.processor.encryption_key == "test_key"
        assert len(self.processor.storage) == 0
        assert len(self.processor.pipeline_triggers) == 0

    def test_process_audio_upload_success(self):
        result = self.processor.process_audio_upload(
            self.audio_blob, self.metadata, self.session_id
        )
        assert result["status"] == "success"
        assert result["session_id"] == self.session_id
        assert "audio_hash" in result
        assert result["size_bytes"] == len(self.audio_blob)
        assert "pipeline_status" in result
        assert "uploaded_at" in result

    def test_process_audio_upload_no_audio(self):
        result = self.processor.process_audio_upload(
            b"", self.metadata, self.session_id
        )
        assert "error" in result
        assert result["error"] == "No audio data provided"

    def test_process_audio_upload_invalid_metadata(self):
        result = self.processor.process_audio_upload(
            self.audio_blob, {}, self.session_id
        )
        assert "error" in result
        assert result["error"] == "Invalid metadata"

    def test_encrypt_audio(self):
        encrypted = self.processor._encrypt_audio(self.audio_blob)
        assert isinstance(encrypted, str)
        assert encrypted.startswith("encrypted_")

    def test_trigger_pipelines(self):
        result = self.processor._trigger_pipelines(self.session_id, self.metadata)
        assert "transcription" in result
        assert "scoring" in result
        assert "multimodal_fusion" in result
        assert result["transcription"]["status"] == "queued"
        assert result["scoring"]["status"] == "queued"
        assert result["multimodal_fusion"]["status"] == "queued"

    def test_get_audio_info(self):
        # First process audio
        self.processor.process_audio_upload(self.audio_blob, self.metadata, self.session_id)
        
        info = self.processor.get_audio_info(self.session_id)
        assert info is not None
        assert info["session_id"] == self.session_id
        assert info["prompt_id"] == "prompt-001"
        assert info["learner_id"] == 42
        assert "encrypted_audio" in info
        assert "uploaded_at" in info

    def test_get_audio_info_not_found(self):
        info = self.processor.get_audio_info("nonexistent")
        assert info is None

    def test_list_sessions(self):
        # Process multiple sessions
        self.processor.process_audio_upload(self.audio_blob, self.metadata, "session1")
        self.processor.process_audio_upload(self.audio_blob, self.metadata, "session2")
        
        all_sessions = self.processor.list_sessions()
        assert len(all_sessions) == 2
        assert "session1" in all_sessions
        assert "session2" in all_sessions

    def test_list_sessions_by_learner(self):
        # Process sessions for different learners
        metadata1 = self.metadata.copy()
        metadata1["learner_id"] = 1
        metadata2 = self.metadata.copy()
        metadata2["learner_id"] = 2
        
        self.processor.process_audio_upload(self.audio_blob, metadata1, "session1")
        self.processor.process_audio_upload(self.audio_blob, metadata2, "session2")
        
        learner1_sessions = self.processor.list_sessions(learner_id=1)
        assert len(learner1_sessions) == 1
        assert "session1" in learner1_sessions

    def test_get_pipeline_status(self):
        # Process audio to trigger pipelines
        self.processor.process_audio_upload(self.audio_blob, self.metadata, self.session_id)
        
        status = self.processor.get_pipeline_status(self.session_id)
        assert status is not None
        assert status["session_id"] == self.session_id
        assert "pipelines" in status
        assert "triggered_at" in status

    def test_get_pipeline_status_not_found(self):
        status = self.processor.get_pipeline_status("nonexistent")
        assert status is None

    def test_delete_session(self):
        # Process audio first
        self.processor.process_audio_upload(self.audio_blob, self.metadata, self.session_id)
        
        # Verify it exists
        assert self.processor.get_audio_info(self.session_id) is not None
        
        # Delete it
        deleted = self.processor.delete_session(self.session_id)
        assert deleted is True
        
        # Verify it's gone
        assert self.processor.get_audio_info(self.session_id) is None

    def test_delete_session_not_found(self):
        deleted = self.processor.delete_session("nonexistent")
        assert deleted is False

    def test_get_quality_metrics(self):
        # Process audio first
        self.processor.process_audio_upload(self.audio_blob, self.metadata, self.session_id)
        
        metrics = self.processor.get_quality_metrics(self.session_id)
        assert metrics is not None
        assert metrics["session_id"] == self.session_id
        assert "duration_seconds" in metrics
        assert "noise_level" in metrics
        assert "device_info" in metrics
        assert "audio_size_bytes" in metrics
        assert "quality_score" in metrics

    def test_get_quality_metrics_not_found(self):
        metrics = self.processor.get_quality_metrics("nonexistent")
        assert metrics is None

    def test_calculate_quality_score(self):
        # Test good quality
        good_metadata = {"duration_seconds": 30, "noise_level": 0.2}
        score = self.processor._calculate_quality_score(good_metadata)
        assert isinstance(score, float)
        assert 0 <= score <= 100
        
        # Test poor quality
        poor_metadata = {"duration_seconds": 5, "noise_level": 0.8}
        score = self.processor._calculate_quality_score(poor_metadata)
        assert isinstance(score, float)
        assert 0 <= score <= 100

    def test_retry_logic_max_retries(self):
        # Mock processing failure by passing invalid data
        result = self.processor.process_audio_upload(
            b"", self.metadata, self.session_id, retry_count=3
        )
        assert "error" in result
        assert result["error"] == "No audio data provided"

    def test_retry_logic_scheduled(self):
        # Mock processing failure with retry count below max
        # Use a different error that triggers retry
        result = self.processor.process_audio_upload(
            self.audio_blob, self.metadata, self.session_id, retry_count=1
        )
        # This should succeed since we're providing valid data
        assert result["status"] == "success"
