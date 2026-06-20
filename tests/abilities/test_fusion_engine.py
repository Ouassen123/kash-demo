import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from modules.abilities.fusion.fusion_engine import MultimodalFusionEngine


class TestMultimodalFusionEngine:
    def setup_method(self):
        self.engine = MultimodalFusionEngine()

    def test_initialization_default_weights(self):
        engine = MultimodalFusionEngine()
        assert engine.modality_weights == {"text": 0.4, "audio": 0.4, "behavioral": 0.2}
        assert engine.feature_version == "1.0"

    def test_initialization_custom_weights(self):
        custom_weights = {"text": 0.5, "audio": 0.3, "behavioral": 0.2}
        engine = MultimodalFusionEngine(custom_weights)
        assert engine.modality_weights == custom_weights

    def test_initialization_invalid_weights(self):
        invalid_weights = {"text": 0.5, "audio": 0.6}  # Sum > 1.0
        engine = MultimodalFusionEngine(invalid_weights)
        assert engine.modality_weights == invalid_weights

    def test_fuse_session_features_full_session(self):
        session_data = {
            "session_id": "test-session",
            "text_data": {
                "responses": [
                    {"response_text": "This is a complex response with detailed analysis", "prompt_id": "prompt1"},
                    {"response_text": "Another response showing creativity", "prompt_id": "prompt2"},
                ]
            },
            "audio_data": {
                "segments": [
                    {"duration_seconds": 10.0, "prompt_id": "prompt1", "transcript": "This is a transcript of the audio"},
                    {"duration_seconds": 8.0, "prompt_id": "prompt2", "transcript": "Another transcript"},
                ]
            },
            "behavioral_tags": [
                {"tag_type": "engagement", "value": 0.8, "confidence": 0.9},
                {"tag_type": "persistence", "value": 0.7, "confidence": 0.8},
            ],
        }
        
        result = self.engine.fuse_session_features(session_data)
        
        assert result["session_id"] == "test-session"
        assert "feature_vector" in result
        assert "cognitive_features" in result
        assert "behavioral_indicators" in result
        assert "confidence_metadata" in result
        assert "interpretability" in result
        assert result["feature_version"] == "1.0"

    def test_fuse_session_features_text_only(self):
        session_data = {
            "session_id": "test-session",
            "text_data": {
                "responses": [
                    {"response_text": "Simple response", "prompt_id": "prompt1"},
                ]
            },
            "audio_data": None,
            "behavioral_tags": [],
        }
        
        result = self.engine.fuse_session_features(session_data)
        
        assert result["session_id"] == "test-session"
        assert len(result["feature_vector"]) > 0
        assert result["confidence_metadata"]["overall_confidence"] < 1.0
        assert result["modality_contributions"]["text"] > 0
        assert result["modality_contributions"]["audio"] == 0.0
        assert result["modality_contributions"]["behavioral"] == 0.0

    def test_fuse_session_features_audio_only(self):
        session_data = {
            "session_id": "test-session",
            "text_data": None,
            "audio_data": {
                "segments": [
                    {"duration_seconds": 5.0, "prompt_id": "prompt1", "transcript": "Audio transcript"},
                ]
            },
            "behavioral_tags": [],
        }
        
        result = self.engine.fuse_session_features(session_data)
        
        assert result["session_id"] == "test-session"
        assert len(result["feature_vector"]) > 0
        assert result["confidence_metadata"]["overall_confidence"] < 1.0
        assert result["modality_contributions"]["text"] == 0.0
        assert result["modality"]["audio"] > 0
        assert result["modality_contributions"]["behavioral"] == 0.0

    def test_fuse_session_features_behavioral_only(self):
        session_data = {
            "session_id": "test-session",
            "text_data": None,
            "audio_data": None,
            "behavioral_tags": [
                {"tag_type": "engagement", "value": 0.8, "confidence": 0.9},
                {"tag_type": "persistence", "value": 0.7, "confidence": 0.8},
            ],
        }
        
        result = self.engine.fuse_session_features(session_data)
        
        assert result["session_id"] == "test-session"
        assert len(result["feature_vector"]) > 0
        assert result["confidence_metadata"]["overall_confidence"] < 1.0
        assert result["modality_contributions"]["text"] == 0.0
        assert result["modality_contributions"]["audio"] == 0.0
        assert result["modality_contributions"]["behavioral"] > 0

    def test_fuse_session_features_no_data(self):
        session_data = {
            "session_id": "test-session",
            "text_data": None,
            "audio_data": None,
            "behavioral_tags": [],
        }
        
        result = self.engine.fuse_session_features(session_data)
        
        assert result["session_id"] == "test-session"
        assert len(result["feature_vector"]) == 0  # No features available
        assert result["confidence_metadata"]["overall_confidence"] == 0.0

    def test_extract_text_features(self):
        text_data = {
            "responses": [
                {"response_text": "This is a test response with some content", "prompt_id": "prompt1"},
                {"response_text": "Another response with different content", "prompt_id": "prompt2"},
                {"response_text": "Short", "prompt_id": "prompt3"},
            ]
        }
        
        features = self.engine._extract_text_features(text_data)
        
        assert features["available"] is True
        assert features["response_count"] == 3
        assert features["avg_response_length"] > 0
        assert "lexical_diversity" in features
        assert "response_time_variance" in features
        assert "content_complexity" in features

    def test_extract_text_features_empty(self):
        features = self.engine._extract_text_features(None)
        assert features["available"] is False

    def test_extract_audio_features(self):
        audio_data = {
            "segments": [
                {"duration_seconds": 10.0, "prompt_id": "prompt1", "transcript": "Audio transcript here"},
                {"duration_seconds": 5.0, "prompt_id": "prompt2", "transcript": "Another transcript"},
            ]
        }
        
        features = self.engine._extract_audio_features(audio_data)
        
        assert features["available"] is True
        assert features["segment_count"] == 2
        assert features["total_duration"] == 15.0
        assert "avg_speaking_rate" in features
        assert "voice_stability" in features
        assert "prosody_variance" in features
        assert "audio_quality" in features

    def test_extract_audio_features_empty(self):
        features = self.engine._extract_audio_features(None)
        assert features["available"] is False

    def test_extract_behavioral_features(self):
        behavioral_tags = [
            {"tag_type": "engagement", "value": 0.8, "confidence": 0.9},
            {"tag_type": "persistence", "value": 0.7, "confidence": 0.8},
            {"tag_type": "adaptability", "value": 0.6, "confidence": 0.7},
        ]
        
        features = self.engine._extract_behavioral_features(behavioral_tags)
        
        assert features["available"] is True
        assert features["tag_count"] == 3
        assert "engagement_level" in features
        assert "persistence_score" in features
        assert "adaptability_score" in features
        assert "emotional_regulation" in features

    def test_extract_behavioral_features_empty(self):
        features = self.engine._extract_behavioral_features([])
        assert features["available"] is False

    def test_generate_cognitive_dimensions(self):
        weighted_features = {
            "text": {
                "available": True,
                "features": {
                    "content_complexity": 0.8,
                    "avg_response_length": 0.6,
                    "lexical_diversity": 0.7,
                }
            },
            "audio": {
                "available": True,
                "features": {
                    "voice_stability": 0.7,
                    "avg_speaking_rate": 0.6,
                    "prosody_variance": 0.5,
                }
            },
            "behavioral": {
                "available": True,
                "features": {
                    "engagement_level": 0.8,
                    "persistence_score": 0.7,
                    "adaptability_score": 0.6,
                }
            },
        }
        
        dimensions = self.engine._generate_cognitive_dimensions(weighted_features)
        
        assert "reasoning" in dimensions
        assert "comprehension" in dimensions
        assert "creativity" in dimensions
        assert "memory" in dimensions
        assert "attention" in dimensions
        assert "executive_function" in dimensions
        
        # All dimensions should be between 0 and 1
        for dimension, value in dimensions.items():
            assert 0.0 <= value <= 1.0

    def test_generate_behavioral_indicators(self):
        weighted_features = {
            "text": {
                "available": True,
                "features": {
                    "content_complexity": 0.8,
                    "avg_response_length": 0.6,
                }
            },
            "audio": {
                "available": True,
                "features": {
                    "voice_stability": 0.7,
                    "audio_quality": 0.8,
                }
            },
            "behavioral": {
                "available": True,
                "features": {
                    "engagement_level": 0.8,
                    "persistence_score": 0.7,
                }
            },
        }
        
        indicators = self.engine._generate_behavioral_indicators(weighted_features)
        
        assert "task_engagement" in indicators
        assert "social_collaboration" in indicators
        assert "self_regulation" in indicators
        assert "problem_solving" in indicators
        assert "communication" in indicators
        
        # All indicators should be between 0 and 1
        for indicator, value in indicators.items():
            assert 0.0 <= value <= 1.0

    def test_apply_modality_weights(self):
        text_features = {"available": True, "features": {"complexity": 0.8}}
        audio_features = {"available": True, "features": {"stability": 0.7}}
        behavioral_features = {"available": True, "features": {"engagement": 0.6}}
        
        weighted = self.engine._apply_modality_weights(text_features, audio_features, behavioral_features)
        
        # Check that weights were applied
        assert weighted["text"]["features"]["complexity"] == 0.8 * 0.4  # text weight
        assert weighted["audio"]["features"]["stability"] == 0.7 * 0.4  # audio weight
        assert weighted["behavioral"]["features"]["engagement"] == 0.6 * 0.2  # behavioral weight

    def test_calculate_confidence(self):
        text_features = {"available": True, "features": {"complexity": 0.8}}
        audio_features = {"available": True, "features": {"stability": 0.7}}
        behavioral_features = {"available": True, "features": {"engagement": 0.6}}
        
        # Good alignment
        alignment_data = {"alignment_confidence": 0.9}
        confidence = self.engine._calculate_confidence(
            text_features, audio_features, behavioral_features, alignment_data, None
        )
        
        assert confidence["overall_confidence"] > 0.7
        assert len(confidence["modality_confidence"]) == 3
        assert confidence["alignment_confidence"] == 0.9

    def test_calculate_confidence_with_fallback(self):
        text_features = {"available": True, "features": {"complexity": 0.8}}
        audio_features = {"available": False}
        behavioral_features = {"available": True, "features": {"engagement": 0.6}}
        
        fallback_data = {"confidence_adjustment": -0.1}
        confidence = self.engine._calculate_confidence(
            text_features, audio_features, behavioral_features, None, fallback_data
        )
        
        assert confidence["overall_confidence"] < 0.8
        assert "fallback adjustment" in confidence["adjustments"][0]

    def test_create_feature_vector(self):
        cognitive_features = {
            "reasoning": 0.8,
            "comprehension": 0.7,
            "creativity": 0.6,
        }
        behavioral_indicators = {
            "task_engagement": 0.8,
            "social_collaboration": 0.7,
        }
        weighted_features = {
            "text": {"available": True, "features": {"complexity": 0.8}},
            "audio": {"available": True, "features": {"stability": 0.7}},
            "behavioral": {"available": True, "features": {"engagement": 0.6}},
        }
        
        vector = self.engine._create_feature_vector(
            cognitive_features, behavioral_indicators, weighted_features
        )
        
        assert len(vector) > 0
        # Should contain cognitive dimensions
        assert 0.8 in vector  # reasoning
        assert 0.7 in vector  # comprehension
        assert 0.6 in vector  # creativity
        # Should contain behavioral indicators
        assert 0.8 in vector  # task_engagement
        assert 0.7 in vector  # social_collaboration

    def test_generate_interpretability(self):
        text_features = {"available": True, "features": {"complexity": 0.8}}
        audio_features = {"available": True, "features": {"stability": 0.7}}
        behavioral_features = {"available": True, "features": {"engagement": 0.6}}
        cognitive_features = {"reasoning": 0.8, "comprehension": 0.7}
        behavioral_indicators = {"task_engagement": 0.8, "social_collaboration": 0.7}
        
        interpretability = self.engine._generate_interpretability(
            text_features, audio_features, behavioral_features,
            cognitive_features, behavioral_indicators
        )
        
        assert "feature_importance" in interpretability
        assert "dimension_explanations" in interpretability
        assert "indicator_explanations" in interpretability
        assert "modality_contributions" in interpretability

    def test_get_modality_contribution(self):
        features = {"available": True, "features": {"complexity": 0.8, "stability": 0.7}}
        contribution = self.engine._get_modality_contribution(features)
        assert contribution == 0.75  # (0.8 + 0.7) / 2

    def test_get_modality_contribution_unavailable(self):
        features = {"available": False, "features": {}}
        contribution = self.engine._get_modality_contribution(features)
        assert contribution == 0.0
