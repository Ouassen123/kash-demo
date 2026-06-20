import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from modules.abilities.fusion.preprocessor import MultimodalPreprocessor


class TestMultimodalPreprocessor:
    def setup_method(self):
        self.preprocessor = MultimodalPreprocessor()
        self.session_id = "test-session-123"

    def test_register_session(self):
        result = self.preprocessor.register_session(self.session_id)
        assert result["session_id"] == self.session_id
        assert result["status"] == "initialized"
        assert "created_at" in result
        
        # Verify session was stored
        session = self.preprocessor.session_data[self.session_id]
        assert session["session_id"] == self.session_id
        assert session["status"] == "initialized"

    def test_add_text_data(self):
        # Register session first
        self.preprocessor.register_session(self.session_id)
        
        text_responses = [
            {"response_text": "This is a test response", "prompt_id": "prompt1", "timestamp": "2023-01-01T10:00:00"},
            {"response_text": "Another response", "prompt_id": "prompt2", "timestamp": "2023-01-01T10:05:00"},
        ]
        
        result = self.preprocessor.add_text_data(self.session_id, text_responses)
        assert result["session_id"] == self.session_id
        assert result["status"] == "text_added"
        assert result["responses_count"] == 2

        # Verify data was stored
        session = self.preprocessor.session_data[self.session_id]
        assert session["text_data"]["responses"] == text_responses

    def test_add_text_data_no_responses(self):
        # Register session first
        self.preprocessor.register_session(self.session_id)
        
        result = self.preprocessor.add_text_data(self.session_id, [])
        assert "error" in result
        assert result["error"] == "No text responses provided"

    def test_add_text_data_missing_fields(self):
        # Register session first
        self.preprocessor.register_session(self.session_id)
        
        # Response with missing fields
        text_responses = [
            {"response_text": "Test response"},  # missing prompt_id and timestamp
        ]
        
        result = self.preprocessor.add_text_data(self.session_id, text_responses)
        assert result["session_id"] == self.session_id
        assert result["status"] == "text_added"
        assert result["responses_count"] == 1

        # Verify fields were added
        session = self.preprocessor.session_data[self.session_id]
        response = session["text_data"]["responses"][0]
        assert response["prompt_id"] == "prompt_1"
        assert "timestamp" in response

    def test_add_audio_data(self):
        # Register session first
        self.preprocessor.register_session(self.session_id)
        
        audio_segments = [
            {"duration_seconds": 5.0, "prompt_id": "prompt1", "timestamp": "2023-01-01T10:00:00"},
            {"duration_seconds": 3.5, "prompt_id": "prompt2", "timestamp": "2023-01-01T10:05:00"},
        ]
        
        result = self.preprocessor.add_audio_data(self.session_id, audio_segments)
        assert result["session_id"] == self.session_id
        assert result["status"] in ["audio_added", "audio_only"]
        assert result["segments_count"] == 2

        # Verify data was stored
        session = self.preprocessor.session_data[self.session_id]
        assert session["audio_data"]["segments"] == audio_segments

    def test_add_audio_data_no_segments(self):
        # Register session first
        self.preprocessor.register_session(self.session_id)
        
        result = self.preprocessor.add_audio_data(self.session_id, [])
        assert "error" in result
        assert result["error"] == "No audio segments provided"

    def test_add_behavioral_tags(self):
        # Register session first
        self.preprocessor.register_session(self.session_id)
        
        behavioral_tags = [
            {"tag_type": "engagement", "value": 0.8, "confidence": 0.9, "timestamp": "2023-01-01T10:00:00"},
            {"tag_type": "persistence", "value": 0.7, "confidence": 0.8, "timestamp": "2023-01-01T10:05:00"},
        ]
        
        result = self.preprocessor.add_behavioral_tags(self.session_id, behavioral_tags)
        assert result["session_id"] == self.session_id
        assert result["status"] in ["tags_added", "partial"]
        assert result["tags_count"] == 2

        # Verify data was stored
        session = self.preprocessor.session_data[self.session_id]
        assert session["behavioral_tags"] == behavioral_tags

    def test_add_behavioral_tags_missing_fields(self):
        # Register session first
        self.preprocessor.register_session(self.session_id)
        
        # Tags with missing fields
        behavioral_tags = [
            {"value": 0.8},  # missing tag_type, confidence, timestamp
        ]
        
        result = self.preprocessor.add_behavioral_tags(self.session_id, behavioral_tags)
        assert result["session_id"] == self.session_id
        assert result["status"] in ["tags_added", "partial"]
        assert result["tags_count"] == 1

        # Verify fields were added
        session = self.preprocessor.session_data[self.session_id]
        tag = session["behavioral_tags"][0]
        assert tag["tag_type"] == "general"
        assert tag["confidence"] == 0.5
        assert "timestamp" in tag

    def test_synchronize_modalities_full_session(self):
        # Register session and add all modalities
        self.preprocessor.register_session(self.session_id)
        
        text_responses = [
            {"response_text": "Response 1", "prompt_id": "prompt1", "timestamp": "2023-01-01T10:00:00"},
            {"response_text": "Response 2", "prompt_id": "prompt2", "timestamp": "2023-01-01T10:05:00"},
        ]
        audio_segments = [
            {"duration_seconds": 5.0, "prompt_id": "prompt1", "timestamp": "2023-01-01T10:00:00"},
            {"duration_seconds": 3.5, "prompt_id": "prompt2", "timestamp": "2023-01-01T10:05:00"},
        ]
        behavioral_tags = [
            {"tag_type": "engagement", "value": 0.8, "confidence": 0.9, "timestamp": "2023-01-01T10:00:00"},
        ]
        
        self.preprocessor.add_text_data(self.session_id, text_responses)
        self.preprocessor.add_audio_data(self.session_id, audio_segments)
        self.preprocessor.add_behavioral_tags(self.session_id, behavioral_tags)
        
        result = self.preprocessor.synchronize_modalities(self.session_id)
        assert result["session_id"] == self.session_id
        assert result["text_count"] == 2
        assert result["audio_count"] == 2
        assert result["tags_count"] == 1
        assert result["aligned_pairs"] == 2
        assert len(result["misalignments"]) == 0
        assert len(result["missing_modalities"]) == 0
        assert result["alignment_confidence"] == 1.0

    def test_synchronize_modalities_partial_session(self):
        # Register session and add only text and behavioral data
        self.preprocessor.register_session(self.session_id)
        
        text_responses = [
            {"response_text": "Response 1", "prompt_id": "prompt1", "timestamp": "2023-01-01T10:00:00"},
        ]
        behavioral_tags = [
            {"tag_type": "engagement", "value": 0.8, "confidence": 0.9, "timestamp": "2023-01-01T10:00:00"},
        ]
        
        self.preprocessor.add_text_data(self.session_id, text_responses)
        self.preprocessor.add_behavioral_tags(self.session_id, behavioral_tags)
        
        result = self.preprocessor.synchronize_modalities(self.session_id)
        assert result["session_id"] == self.session_id
        assert result["text_count"] == 1
        assert result["audio_count"] == 0
        assert result["tags_count"] == 1
        assert result["aligned_pairs"] == 0
        assert len(result["missing_modalities"]) == 1  # Missing audio
        assert result["missing_modalities"][0]["missing"] == "audio"

    def test_synchronize_modalities_misaligned_timestamps(self):
        # Register session and add misaligned data
        self.preprocessor.register_session(self.session_id)
        
        text_responses = [
            {"response_text": "Response 1", "prompt_id": "prompt1", "timestamp": "2023-01-01T10:00:00"},
            {"response_text": "Response 2", "prompt_id": "prompt2", "timestamp": "2023-01-01T10:05:00"},
        ]
        audio_segments = [
            {"duration_seconds": 5.0, "prompt_id": "prompt1", "timestamp": "2023-01-01T10:02:00"},  # 2 minutes later
            {"duration_seconds": 3.5, "prompt_id": "prompt2", "timestamp": "2023-01-01T10:05:00"},
        ]
        
        self.preprocessor.add_text_data(self.session_id, text_responses)
        self.preprocessor.add_audio_data(self.session_id, audio_segments)
        
        result = self.preprocessor.synchronize_modalities(self.session_id)
        assert result["session_id"] == self.session_id
        assert result["text_count"] == 2
        assert result["audio_count"] == 2
        assert result["aligned_pairs"] == 2
        assert len(result["misalignments"]) == 1  # prompt1 is misaligned
        assert result["misalignments"][0]["issue"] == "time_difference"
        assert result["alignment_confidence"] <= 1.0

    def test_handle_partial_session_single_modality(self):
        # Register session and add only text data
        self.preprocessor.register_session(self.session_id)
        
        text_responses = [
            {"response_text": "Response 1", "prompt_id": "prompt1", "timestamp": "2023-01-01T10:00:00"},
        ]
        
        self.preprocessor.add_text_data(self.session_id, text_responses)
        
        result = self.preprocessor.handle_partial_session(self.session_id)
        assert result["session_id"] == self.session_id
        assert result["available_modalities"] == ["text"]
        assert result["missing_modalities"] == ["audio", "behavioral"]
        assert result["fallback_strategy"] == "single_modality"
        assert result["confidence_adjustment"] == -0.3

    def test_handle_partial_session_dual_modality(self):
        # Register session and add text and audio data
        self.preprocessor.register_session(self.session_id)
        
        text_responses = [
            {"response_text": "Response 1", "prompt_id": "prompt1", "timestamp": "2023-01-01T10:00:00"},
        ]
        audio_segments = [
            {"duration_seconds": 5.0, "prompt_id": "prompt1", "timestamp": "2023-01-01T10:00:00"},
        ]
        
        self.preprocessor.add_text_data(self.session_id, text_responses)
        self.preprocessor.add_audio_data(self.session_id, audio_segments)
        
        result = self.preprocessor.handle_partial_session(self.session_id)
        assert result["session_id"] == self.session_id
        assert result["available_modalities"] == ["text", "audio"]
        assert result["missing_modalities"] == ["behavioral"]
        assert result["fallback_strategy"] == "dual_modality"
        assert result["confidence_adjustment"] == -0.1

    def test_get_session_summary(self):
        # Register session and add data
        self.preprocessor.register_session(self.session_id)
        
        text_responses = [
            {"response_text": "Test response", "prompt_id": "prompt1", "timestamp": "2023-01-01T10:00:00"},
        ]
        
        self.preprocessor.add_text_data(self.session_id, text_responses)
        
        summary = self.preprocessor.get_session_summary(self.session_id)
        assert summary["session_id"] == self.session_id
        assert summary["status"] == "text_added"
        assert "text_data" in summary
        assert summary["text_data"]["responses"] == text_responses

    def test_get_session_summary_not_found(self):
        summary = self.preprocessor.get_session_summary("nonexistent")
        assert summary is None
