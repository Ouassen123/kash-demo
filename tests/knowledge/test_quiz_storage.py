import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from modules.knowledge.quiz.storage import QuizStorage


class TestQuizStorage:
    def setup_method(self):
        self.storage = QuizStorage()

    def test_save_quiz_results(self):
        data = {
            "user_id": 1,
            "score": 0.8,
            "answers": []
        }

        result = self.storage.save_results(data)

        assert result is True

    def test_load_stats(self):
        stats = self.storage.get_stats()

        assert isinstance(stats, dict)
