import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from modules.abilities.fusion.monitoring.diagnostics import FusionDiagnostics


class TestFusionDiagnostics:
    def setup_method(self):
        self.diagnostics = FusionDiagnostics()

    def test_record_session_diagnostics(self):
        session_id = "test-session"
        
        # Mock fusion result
        fusion_result = {
            "session_id": session_id,
            "confidence_metadata": {
                "overall_confidence": 0.85,
                "modality_confidence": {"text": 0.8, "audio": 0.7, "behavioral": 0.6},
            },
            "feature_vector": [0.1, 0.2, 0.3, 0.4, 0.5],
        }
        
        # Mock session data
        session_data = {
            "session_id": session_id,
            "text_data": {
                "responses": [{"response_text": "Test response", "prompt_id": "prompt1"}],
            },
            "audio_data": {
                "segments": [{"duration_seconds": 5.0, "prompt_id": "prompt1"}],
            },
            "behavioral_tags": [{"tag_type": "engagement", "value": 0.8}],
        }
        
        result = self.diagnostics.record_session_diagnostics(session_id, fusion_result, session_data)
        
        assert result["session_id"] == session_id
        assert result["alerts_count"] >= 0
        assert result["recommendations_count"] >= 0
        assert "recorded_at" in result

        # Verify diagnostics were stored
        stored = self.diagnostics.session_diagnostics[session_id]
        assert stored["session_id"] == session_id
        assert "fusion_confidence" in stored
        assert "alerts" in stored
        assert "recommendations" in stored

    def test_record_session_diagnostics_low_confidence(self):
        session_id = "test-session-low"
        
        # Mock low confidence fusion result
        fusion_result = {
            "session_id": session_id,
            "confidence_metadata": {
                "overall_confidence": 0.3,  # Low confidence
                "modality_confidence": {"text": 0.5, "audio": 0.4, "behavioral": 0.3},
            },
            "feature_vector": [0.1, 0.2, 0.3],
        }
        
        session_data = {
            "session_id": session_id,
            "text_data": {
                "responses": [{"response_text": "Test response", "prompt_id": "prompt1"}],
            },
            "audio_data": {
                "segments": [{"duration_seconds": 5.0, "prompt_id": "prompt1"}],
            },
            "behavioral_tags": [{"tag_type": "engagement", "value": 0.8}],
        }
        
        result = self.diagnostics.record_session_diagnostics(session_id, fusion_result, session_data)
        
        # Should have low confidence alert
        alerts = result["alerts"]
        low_confidence_alerts = [a for a in alerts if a["type"] == "low_confidence"]
        assert len(low_confidence_alerts) > 0
        assert low_confidence_alerts[0]["severity"] == "high"

    def test_record_session_diagnostics_missing_modalities(self):
        session_id = "test-session-missing"
        
        # Mock fusion result
        fusion_result = {
            "session_id": session_id,
            "confidence_metadata": {"overall_confidence": 0.7},
            "feature_vector": [0.1, 0.2, 0.3],
        }
        
        # Session missing audio and behavioral data
        session_data = {
            "session_id": session_id,
            "text_data": {
                "responses": [{"response_text": "Test response", "prompt_id": "prompt1"}],
            },
            "audio_data": None,
            "behavioral_tags": [],
        }
        
        result = self.diagnostics.record_session_diagnostics(session_id, fusion_result, session_data)
        
        # Should have missing modalities alert
        alerts = result["alerts"]
        missing_modalities_alerts = [a for a in alerts if a["type"] == "missing_modalities"]
        assert len(missing_modalities_alerts) > 0
        assert "audio" in missing_modalities_alerts[0]["missing_modalities"]
        assert "behavioral" in missing_modalities_alerts[0]["missing_modalities"]

    def test_get_session_diagnostics(self):
        session_id = "test-session"
        
        # Record diagnostics first
        fusion_result = {
            "session_id": session_id,
            "confidence_metadata": {"overall_confidence": 0.85},
            "feature_vector": [0.1, 0.2, 0.3],
        }
        session_data = {
            "session_id": session_id,
            "text_data": {"responses": [{"response_text": "Test response", "prompt_id": "prompt1"}]},
        }
        
        self.diagnostics.record_session_diagnostics(session_id, fusion_result, session_data)
        
        # Retrieve diagnostics
        retrieved = self.diagnostics.get_session_diagnostics(session_id)
        assert retrieved is not None
        assert retrieved["session_id"] == session_id
        assert "fusion_confidence" in retrieved

    def test_get_session_diagnostics_not_found(self):
        result = self.diagnostics.get_session_diagnostics("nonexistent")
        assert result is None

    def test_get_system_health_no_data(self):
        health = self.diagnostics.get_system_health()
        assert health["status"] == "no_data"
        assert "message" in health

    def test_get_system_health_with_data(self):
        # Add some session diagnostics
        for i in range(5):
            session_id = f"test-session-{i}"
            fusion_result = {
                "session_id": session_id,
                "confidence_metadata": {"overall_confidence": 0.8 + i * 0.02},
                "feature_vector": [0.1, 0.2, 0.3],
            }
            session_data = {
                "session_id": session_id,
                "text_data": {"responses": [{"response_text": f"Response {i}", "prompt_id": f"prompt{i}"}]},
            }
            self.diagnostics.record_session_diagnostics(session_id, fusion_result, session_data)
        
        health = self.diagnostics.get_system_health()
        assert health["total_sessions"] == 5
        assert health["recent_sessions_24h"] == 5
        assert "system_status" in health
        assert "average_confidence" in health
        assert "alert_rate" in health

    def test_get_alert_summary(self):
        # Add some sessions with alerts
        for i in range(3):
            session_id = f"test-session-{i}"
            fusion_result = {
                "session_id": session_id,
                "confidence_metadata": {"overall_confidence": 0.3 + i * 0.1},
                "feature_vector": [0.1, 0.2, 0.3],
            }
            session_data = {
                "session_id": session_id,
                "text_data": {"responses": [{"response_text": f"Response {i}", "prompt_id": f"prompt{i}"}]},
            }
            self.diagnostics.record_session_diagnostics(session_id, fusion_result, session_data)
        
        summary = self.diagnostics.get_alert_summary()
        assert summary["total_sessions"] == 3
        assert "alerts_by_type" in summary
        assert "alerts_by_severity" in summary
        assert "timeframe_hours" in summary

    def test_get_modality_drift_report(self):
        # Add sessions over multiple days
        for day in range(5):
            session_id = f"test-session-{day}"
            availability = {
                "text": day % 3 != 0,
                "audio": day % 2 != 0,
                "behavioral": day % 1 != 0,
            }
            
            session_data = {
                "session_id": session_id,
                "modality_availability": availability,
                "recorded_at": f"2023-01-{day+1:02d}:00:00",
            }
            self.diagnostics.session_diagnostics[session_id] = {
                "recorded_at": f"2023-01-{day+1:02d}:00:00",
                "modality_availability": availability,
            }
        
        drift_report = self.diagnostics.get_modality_drift_report(days=5)
        assert drift_report["timeframe_days"] == 5
        assert "modality_trends" in drift_report
        assert "drift_detected" in drift_report

    def test_export_diagnostics_report_json(self):
        # Add some session data
        self.diagnostics.record_session_diagnostics("test-session", {
            "confidence_metadata": {"overall_confidence": 0.85},
            "feature_vector": [0.1, 0.2, 0.3],
        }, {
            "session_id": "test-session",
            "text_data": {"responses": [{"response_text": "Test response"}]},
        })
        
        report = self.diagnostics.export_diagnostics_report("json")
        assert "report_metadata" in report
        assert "system_health" in report
        assert "session_diagnostics" in report

    def test_export_diagnostics_report_invalid_format(self):
        report = self.diagnostics.export_diagnostics_report("xml")
        assert "error" in report
        assert "Unsupported format" in report["error"]

    def _calculate_data_quality_metrics(self):
        """Mock data quality metrics calculation."""
        return {
            "completeness": 0.8,
            "consistency": 0.7,
            "timeliness": 0.9,
        }

    def _calculate_performance_metrics(self, fusion_result):
        """Mock performance metrics calculation."""
        return {
            "fusion_speed": 0.95,
            "feature_vector_size": len(fusion_result.get("feature_vector", [])),
            "confidence_score": fusion_result["confidence_metadata"].get("overall_confidence", 0.0),
        }
