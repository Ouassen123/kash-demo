import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from modules.abilities.text_tests.scoring import CognitiveScorer


class TestCognitiveScorer:
    def setup_method(self):
        self.scorer = CognitiveScorer()

    def test_score_response_logic(self):
        result = self.scorer.score_response(
            prompt_id="logic_sequence",
            response_text="The next number is 32 because the pattern doubles each time.",
            time_taken_seconds=45,
            expected_dimensions=["logic", "reasoning"]
        )
        assert "dimension_scores" in result
        assert "overall_score" in result
        assert "confidence" in result
        assert "flags" in result
        assert result["prompt_id"] == "logic_sequence"
        assert 0 <= result["overall_score"] <= 1
        assert 0 <= result["confidence"] <= 1
        assert isinstance(result["flags"], list)

    def test_score_response_creativity(self):
        result = self.scorer.score_response(
            prompt_id="creativity_story",
            response_text="In a quiet forest, a robot discovered a glowing secret that changed its world.",
            time_taken_seconds=60,
            expected_dimensions=["creativity", "originality"]
        )
        assert "dimension_scores" in result
        assert set(result["dimension_scores"].keys()) == {"creativity", "originality"}

    def test_low_confidence_flags(self):
        # Very short, fast response with no keywords
        result = self.scorer.score_response(
            prompt_id="logic_sequence",
            response_text="42",
            time_taken_seconds=5,
            expected_dimensions=["logic"]
        )
        assert "too_short" in result["flags"] or "too_fast" in result["flags"] or "no_keywords" in result["flags"]
        assert result["confidence"] < 0.8

    def test_score_session(self):
        transcript = [
            {"prompt_id": "logic_sequence", "response_text": "32 because it doubles", "time_taken_seconds": 30},
            {"prompt_id": "creativity_story", "response_text": "A robot found a secret in the forest.", "time_taken_seconds": 60},
        ]
        result = self.scorer.score_session(transcript)
        assert "session_id" in result
        assert "dimension_means" in result
        assert "overall_score" in result
        assert "overall_confidence" in result
        assert "confidence_band" in result
        assert "response_scores" in result
        assert "flags" in result
        assert "lower" in result["confidence_band"]
        assert "upper" in result["confidence_band"]
        assert result["confidence_band"]["lower"] <= result["overall_score"] <= result["confidence_band"]["upper"]

    def test_infer_expected_dimensions(self):
        dims = self.scorer._infer_expected_dimensions("logic_sequence")
        assert dims == ["logic", "reasoning"]
        dims = self.scorer._infer_expected_dimensions("creativity_story")
        assert dims == ["creativity", "originality"]
        dims = self.scorer._infer_expected_dimensions("unknown")
        assert dims == ["logic"]
