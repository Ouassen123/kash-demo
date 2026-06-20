import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from modules.knowledge.quiz.scoring import QuizScorer


class TestQuizScorer:
    def setup_method(self):
        self.scorer = QuizScorer()

    def test_score_calculation(self):
        answers = [
            {"correct": True},
            {"correct": True},
            {"correct": False},
        ]

        result = self.scorer.calculate_score(answers)

        assert result["score"] > 0
        assert result["confidence"] <= 1.0

    def test_mastery_level(self):
        answers = [{"correct": True}] * 5

        result = self.scorer.calculate_score(answers)

        assert result["mastery"] in {"low", "medium", "high"}

    def test_confidence_increases_with_correct_answers(self):
        answers_low = [{"correct": True}, {"correct": False}]
        answers_high = [{"correct": True}] * 4

        result_low = self.scorer.calculate_score(answers_low)
        result_high = self.scorer.calculate_score(answers_high)

        assert result_high["confidence"] >= result_low["confidence"]
