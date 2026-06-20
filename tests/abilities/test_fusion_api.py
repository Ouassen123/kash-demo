import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from modules.abilities.fusion.api import MultimodalFusionAPI


class TestMultimodalFusionAPI:
    def setup_method(self):
        self.api = MultimodalFusionAPI()

    def test_create_fusion_session(self):
        result = self.api.create_fusion_session(user_id=42)
        assert result["session_id"] is not None
        assert result["user_id"] == 42
        assert result["status"] == "initialized"
        assert "created_at" in result

    def test_create_fusion_session_no_user_id(self):
        result = self.api.create_fusion_session()
        assert result["session_id"] is not None
        assert result["user_id"] is None

    def test_add_text_data(self):
        # Create session first
        create_result = self.api.create_fusion_session(user_id=42)
        session_id = create_result["session_id"]
        
        text_responses = [
            {"response_text": "Test response 1", "prompt_id": "prompt1"},
            {"response_text": "Test response 2", "prompt_id": "prompt2"},
        ]
        
        result = self.api.add_text_data(session_id, text_responses)
        assert result["session_id"] == session_id
        assert result["status"] == "text_added"
        assert result["responses_count"] == 2

    def test_add_text_data_session_not_found(self):
        result = self.api.add_text_data("nonexistent", [])
        assert "error" in result
        assert result["error"] == "Session not found"

    def test_add_audio_data(self):
        # Create session and add text data first
        create_result = self.api.create_fusion_session(user_id=42)
        session_id = create_result["session_id"]
        
        self.api.add_text_data(session_id, [
            {"response_text": "Test response", "prompt_id": "prompt1"},
        ])
        
        audio_segments = [
            {"duration_seconds": 5.0, "prompt_id": "prompt1"},
            {"duration_seconds": 3.0, "prompt_id": "prompt2"},
        ]
        
        result = self.api.add_audio_data(session_id, audio_segments)
        assert result["session_id"] == session_id
        assert result["status"] in ["audio_added", "text_added"]
        assert result["segments_count"] == 2

    def test_add_behavioral_tags(self):
        # Create session and add other modalities first
        create_result = self.api.create_fusion_session(user_id=42)
        session_id = create_result["session_id"]
        
        self.api.add_text_data(session_id, [
            {"response_text": "Test response", "prompt_id": "prompt1"},
        ])
        self.api.add_audio_data(session_id, [
            {"duration_seconds": 5.0, "prompt_id": "prompt1"},
        ])
        
        behavioral_tags = [
            {"tag_type": "engagement", "value": 0.8, "confidence": 0.9},
            {"tag_type": "persistence", "value": 0.7, "confidence": 0.8},
        ]
        
        result = self.api.add_behavioral_tags(session_id, behavioral_tags)
        assert result["session_id"] == session_id
        assert result["status"] in ["tags_added", "partial"]
        assert result["tags_count"] == 2

    def test_synchronize_session(self):
        # Create session and add all modalities
        create_result = self.api.create_fusion_session(user_id=42)
        session_id = create_result["session_id"]
        
        self.api.add_text_data(session_id, [
            {"response_text": "Response 1", "prompt_id": "prompt1", "timestamp": "2023-01-01T10:00:00"},
            {"response_text": "Response 2", "prompt_id": "prompt2", "timestamp": "2023-01-01T10:05:00"},
        ])
        self.api.add_audio_data(session_id, [
            {"duration_seconds": 5.0, "prompt_id": "prompt1", "timestamp": "2023-01-01T10:00:00"},
            {"duration_seconds": 3.0, "prompt_id": "prompt2", "timestamp": "2023-01-01T10:05:00"},
        ])
        self.api.add_behavioral_tags(session_id, [
            {"tag_type": "engagement", "value": 0.8, "confidence": 0.9},
        ])
        
        result = self.api.synchronize_session(session_id)
        assert result["session_id"] == session_id
        assert result["text_count"] == 2
        assert result["audio_count"] == 2
        assert result["tags_count"] == 1
        assert result["aligned_pairs"] == 2

    def test_handle_partial_session(self):
        # Create session with only text data
        create_result = self.api.create_fusion_session(user_id=42)
        session_id = create_result["session_id"]
        
        self.api.add_text_data(session_id, [
            {"response_text": "Only text response", "prompt_id": "prompt1"},
        ])
        
        result = self.api.handle_partial_session(session_id)
        assert result["session_id"] == session_id
        assert result["available_modalities"] == ["text"]
        assert result["missing_modalities"] == ["audio", "behavioral"]
        assert result["fallback_strategy"] == "single_modality"

    def test_fuse_session_features(self):
        # Create complete session
        create_result = self.api.create_fusion_session(user_id=42)
        session_id = create_result["session_id"]
        
        self.api.add_text_data(session_id, [
            {"response_text": "Complex response", "prompt_id": "prompt1"},
            {"response_text": "Creative response", "prompt_id": "prompt2"},
        ])
        self.api.add_audio_data(session_id, [
            {"duration_seconds": 8.0, "prompt_id": "prompt1"},
            {"duration_seconds": 6.0, "prompt_id": "prompt2"},
        ])
        self.api.add_behavioral_tags(session_id, [
            {"tag_type": "engagement", "value": 0.8, "confidence": 0.9},
            {"tag_type": "persistence", "value": 0.7, "confidence": 0.8},
        ])
        
        result = self.api.fuse_session_features(session_id)
        assert result["session_id"] == session_id
        assert result["status"] == "fused"
        assert "feature_vector" in result
        assert "cognitive_features" in result
        assert "behavioral_indicators" in result
        assert "confidence" in result

    def test_fuse_session_features_session_not_found(self):
        result = self.api.fuse_session_features("nonexistent")
        assert "error" in result
        assert result["error"] == "Session not found"

    def test_get_session_result(self):
        # Create and populate session
        create_result = self.api.create_fusion_session(user_id=42)
        session_id = create_result["session_id"]
        
        self.api.add_text_data(session_id, [
            {"response_text": "Test response", "prompt_id": "prompt1"},
        ])
        self.api.fuse_session_features(session_id)
        
        result = self.api.get_session_result(session_id)
        assert result is not None
        assert result["session_id"] == session_id
        assert "session_metadata" in result
        assert "fusion_result" in result
        assert "diagnostics" in result

    def test_get_session_result_not_found(self):
        result = self.api.get_session_result("nonexistent")
        assert result is None

    def test_get_session_diagnostics(self):
        # Create and populate session
        create_result = self.api.create_fusion_session(user_id=42)
        session_id = create_result["session_id"]
        
        self.api.add_text_data(session_id, [
            {"response_text": "Test response", "prompt_id": "prompt1"},
        ])
        self.api.fuse_session_features(session_id)
        
        diagnostics = self.api.get_session_diagnostics(session_id)
        assert diagnostics is not None
        assert diagnostics["session_id"] == session_id
        assert "fusion_confidence" in diagnostics

    def test_get_system_health(self):
        # Add some sessions
        for i in range(3):
            create_result = self.api.create_fusion_session(user_id=i)
            self.api.add_text_data(create_result["session_id"], [
                {"response_text": f"Response {i}", "prompt_id": f"prompt{i}"},
            ])
            self.api.fuse_session_features(create_result["session_id"])
        
        health = self.api.get_system_health()
        assert "system_status" in health
        assert health["total_sessions"] == 3
        assert "average_confidence" in health

    def test_get_alert_summary(self):
        # Add sessions with varying confidence levels
        for i in range(3):
            create_result = self.api.create_fusion_session(user_id=i)
            confidence = 0.3 + i * 0.2
            fusion_result = {
                "confidence_metadata": {"overall_confidence": confidence},
                "feature_vector": [0.1, 0.2, 0.3],
            }
            session_data = {
                "session_id": create_result["session_id"],
                "text_data": {"responses": [{"response_text": f"Response {i}", "prompt_id": f"prompt{i}"}]},
            }
            self.api.diagnostics.record_session_diagnostics(create_result["session_id"], fusion_result, session_data)
        
        summary = self.api.get_alert_summary()
        assert summary["total_sessions"] == 3
        assert "alerts_by_type" in summary
        assert "alerts_by_severity" in summary

    def test_get_modality_drift_report(self):
        # Add sessions over multiple days
        for day in range(3):
            create_result = self.api.create_fusion_session(user_id=day)
            availability = {
                "text": day % 2 != 0,
                "audio": day % 3 != 0,
                "behavioral": day % 1 != 0,
            }
            session_data = {
                "session_id": create_result["session_id"],
                "modality_availability": availability,
                "recorded_at": f"2023-01-{day+1:02d}:00:00",
            }
            self.api.diagnostics.session_diagnostics[create_result["session_id"]] = {
                "recorded_at": f"2023-01-{day+1:02d}:00:00",
                "modality_availability": availability,
            }
        
        drift_report = self.api.get_modality_drift_report(days=3)
        assert drift_report["timeframe_days"] == 3
        assert "modality_trends" in drift_report

    def test_export_diagnostics_report(self):
        # Add session data
        create_result = self.api.create_fusion_session(user_id=42)
        self.api.add_text_data(create_result["session_id"], [
            {"response_text": "Test response", "prompt_id": "prompt1"},
        ])
        self.api.fuse_session_features(create_result["session_id"])
        
        report = self.api.export_diagnostics_report()
        assert "report_metadata" in report
        assert "system_health" in report
        assert "session_diagnostics" in report

    def test_update_modality_weights(self):
        # Get current weights
        current_weights = self.api.get_modality_weights()
        assert current_weights == {"text": 0.4, "audio": 0.4, "behavioral": 0.2}

        # Update weights
        new_weights = {"text": 0.5, "audio": 0.3, "behavioral": 0.2}
        result = self.api.update_modality_weights(new_weights)
        assert result["updated_weights"] == new_weights
        assert result["previous_weights"] == current_weights

    def test_update_modality_weights_invalid_sum(self):
        # Invalid weights (sum > 1.0)
        invalid_weights = {"text": 0.6, "audio": 0.5}  # Sum = 1.1
        result = self.api.update_modality_weights(invalid_weights)
        assert "error" in result
        assert "Weights must sum to 1.0" in result["error"]

    def test_get_modality_weights(self):
        weights = self.api.get_modality_weights()
        assert isinstance(weights, dict)
        assert "text" in weights
        assert "audio" in weights
        assert "behavioral" in weights
        assert sum(weights.values()) == 1.0

    def test_get_feature_version(self):
        version = self.api.get_feature_version()
        assert isinstance(version, str)
        assert version == "1.0"

    def test_delete_session(self):
        # Create session first
        create_result = self.api.create_fusion_session(user_id=42)
        session_id = create_result["session_id"]
        
        # Delete session
        result = self.api.delete_session(session_id)
        assert result["session_id"] == session_id
        assert result["deleted"] is True
        assert "deleted_at" in result

    def test_delete_session_not_found(self):
        result = self.api.delete_session("nonexistent")
        assert result["session_id"] == "nonexistent"
        assert result["deleted"] is False
        assert "error" in result

    def test_list_sessions(self):
        # Create multiple sessions
        session_ids = []
        for i in range(3):
            create_result = self.api.create_fusion_session(user_id=i)
            session_ids.append(create_result["session_id"])
        
        # List all sessions
        all_sessions = self.api.list_sessions()
        assert len(all_sessions) == 3
        assert set(all_sessions) == set(session_ids)

        # List by status
        initialized_sessions = self.api.list_sessions(status="initialized")
        assert len(initialized_sessions) == 3

        # List by user
        user42_sessions = self.api.list_sessions(user_id=42)
        assert len(user42_sessions) == 3

        # Non-existent filters
        empty_sessions = self.api.list_sessions(status="nonexistent")
        assert len(empty_sessions) == 0

    def test_list_sessions_with_filters(self):
        # Create sessions with different statuses
        create_result1 = self.api.create_fusion_session(user_id=1)
        create_result2 = self.api.create_fusion_session(user_id=2)
        
        # Add data to first session
        self.api.add_text_data(create_result1["session_id"], [
            {"response_text": "Response", "prompt_id": "prompt1"},
        ])
        
        # Add data to second session
        self.api.add_text_data(create_result2["session_id"], [
            {"response_text": "Response", "prompt_id": "prompt1"},
        ])
        
        # Filter by status
        text_added_sessions = self.api.list_sessions(status="text_added")
        assert len(text_added_sessions) == 2
        assert all(s in text_added_sessions for s in [create_result1["session_id"], create_result2["session_id"]])

        # Filter by user
        user1_sessions = self.api.list_sessions(user_id=1)
        assert len(user1_sessions) == 1
        assert user1_sessions[0] == create_result1["session_id"]

        # Filter by both status and user
        user1_text_added = self.api.list_sessions(status="text_added", user_id=1)
        assert len(user1_text_added) == 1
        assert user1_text_added[0] == create_result1["session_id"]

    def test_list_sessions_no_filters(self):
        # Create sessions
        for i in range(3):
            self.api.create_fusion_session(user_id=i)
        
        # List without filters
        all_sessions = self.api.list_sessions()
        assert len(all_sessions) == 3
