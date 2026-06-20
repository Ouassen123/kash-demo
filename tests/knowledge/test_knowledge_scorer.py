import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from modules.knowledge.scoring.scorer import KnowledgeScorer


@pytest.fixture
def sample_inputs():
    return {
        "cv_insights": {"score": 0.8},
        "taxonomy_confidence": {"confidence": 0.7},
        "quiz_mastery": {"score": 0.9, "mastery": "high"},
    }


class TestKnowledgeScorer:
    def setup_method(self):
        self.scorer = KnowledgeScorer()

    def test_calculate_score_breakdown(self, sample_inputs):
        result = self.scorer.calculate_score(**sample_inputs, user_id=42)

        assert "knowledge_score" in result
        assert "breakdown" in result
        assert "confidence_interval" in result
        assert "diagnostics" in result

        # Verify score is in [0, 1]
        assert 0 <= result["knowledge_score"] <= 1

        # Verify breakdown structure
        breakdown = result["breakdown"]
        assert all(comp in breakdown for comp in ["cv_insights", "taxonomy_confidence", "quiz_mastery"])
        assert all("score" in breakdown[comp] and "weight" in breakdown[comp] for comp in breakdown)

    def test_fallback_normalization(self):
        # Test with missing/unknown fields
        inputs = {"cv_insights": {}, "taxonomy_confidence": {}, "quiz_mastery": {}}
        result = self.scorer.calculate_score(**inputs)

        # Should not crash and should produce a valid score
        assert 0 <= result["knowledge_score"] <= 1

    def test_update_weights_and_audit(self):
        new_weights = {"cv_insights": 0.5, "taxonomy_confidence": 0.3, "quiz_mastery": 0.2}
        old_weights = self.scorer.weights.copy()

        self.scorer.update_weights(new_weights, author="test_user")

        # Verify weights updated and normalized
        updated = self.scorer.weights
        assert updated["cv_insights"] == 0.5
        assert updated["taxonomy_confidence"] == 0.3
        assert updated["quiz_mastery"] == 0.2

        # Verify audit log entry
        assert len(self.scorer.audit_log) > 0
        last_entry = self.scorer.audit_log[-1]
        assert last_entry["author"] == "test_user"
        assert last_entry["previous"] == old_weights
        assert last_entry["new"] == updated

    def test_confidence_interval_estimation(self, sample_inputs):
        result = self.scorer.calculate_score(**sample_inputs)

        ci = result["confidence_interval"]
        assert "lower" in ci and "upper" in ci
        assert 0 <= ci["lower"] <= ci["upper"] <= 1
