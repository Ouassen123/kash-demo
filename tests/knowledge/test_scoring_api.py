import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from modules.knowledge.scoring.api import ScoringAPI
from modules.knowledge.scoring.scorer import KnowledgeScorer


@pytest.fixture
def sample_inputs():
    return {
        "cv_insights": {"score": 0.8},
        "taxonomy_confidence": {"confidence": 0.7},
        "quiz_mastery": {"score": 0.9, "mastery": "high"},
    }


class TestScoringAPI:
    def setup_method(self):
        self.api = ScoringAPI(cache_ttl_seconds=60)  # short TTL for testing

    def test_cache_hit_and_miss(self, sample_inputs):
        # First call should compute and cache
        result1 = self.api.get_score(**sample_inputs, user_id=1)
        assert "knowledge_score" in result1

        # Second call within TTL should hit cache
        result2 = self.api.get_score(**sample_inputs, user_id=1)
        assert result1["knowledge_score"] == result2["knowledge_score"]

        # Force refresh should recompute
        result3 = self.api.get_score(**sample_inputs, user_id=1, force_refresh=True)
        # Still valid; just ensures code path runs
        assert "knowledge_score" in result3

    def test_fallback_on_error(self):
        # Simulate missing/invalid inputs
        bad_inputs = {"cv_insights": None, "taxonomy_confidence": None, "quiz_mastery": None}
        result = self.api.get_score(**bad_inputs, user_id=999)

        # Should return safe fallback
        assert result["knowledge_score"] == 0.0
        assert "error" in result["diagnostics"]

    def test_clear_cache_and_stats(self, sample_inputs):
        # Populate cache
        self.api.get_score(**sample_inputs, user_id=1)
        assert self.api.get_stats()["cache_size"] > 0

        # Clear cache
        self.api.clear_cache()
        assert self.api.get_stats()["cache_size"] == 0

        stats = self.api.get_stats()
        assert "cache_ttl_seconds" in stats
        assert "weights" in stats
