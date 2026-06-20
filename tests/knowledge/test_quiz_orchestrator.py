import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from modules.knowledge.quiz.orchestrator import QuizOrchestrator


@pytest.fixture
def sample_skills():
    return [
        {
            "name": "Python",
            "skill_type": "technical",
            "proficiency": "advanced",
            "taxonomy": {
                "esco_uri": "http://data.europa.eu/esco/skill/python",
                "onet_code": "15-1252.00"
            }
        },
        {
            "name": "Team Leadership",
            "skill_type": "behavioral",
            "proficiency": "intermediate",
            "taxonomy": {
                "esco_uri": "http://data.europa.eu/esco/skill/leadership",
                "onet_code": "11-1021.00"
            }
        }
    ]


class TestQuizOrchestrator:
    def setup_method(self):
        self.orchestrator = QuizOrchestrator()

    def test_run_quiz_full_pipeline(self, sample_skills):
        answers = [{"correct": True}, {"correct": False}]

        result = self.orchestrator.run_quiz(sample_skills, answers, user_id=42)

        # Verify structure
        assert "questions" in result
        assert "scoring" in result
        assert "stored" in result
        assert result["user_id"] == 42

        # Verify questions generated
        assert len(result["questions"]) == len(sample_skills)
        assert all("question_text" in q for q in result["questions"])

        # Verify scoring
        scoring = result["scoring"]
        assert "score" in scoring
        assert "confidence" in scoring
        assert "mastery" in scoring
        assert 0 <= scoring["score"] <= 1

        # Verify storage
        assert result["stored"] is True

    def test_run_quiz_without_user_id_no_storage(self, sample_skills):
        answers = [{"correct": True}]

        result = self.orchestrator.run_quiz(sample_skills, answers, user_id=None)

        assert result["stored"] is False
        assert result["user_id"] is None

    def test_get_quiz_stats(self):
        stats = self.orchestrator.get_quiz_stats()
        assert isinstance(stats, dict)
        assert "total_attempts" in stats
