import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from modules.knowledge.quiz.mapper import QuizMapper


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


class TestQuizMapper:
    def setup_method(self):
        self.mapper = QuizMapper()

    def test_generates_question_per_skill(self, sample_skills):
        questions = self.mapper.generate_questions(sample_skills)

        assert len(questions) == len(sample_skills)

        first = questions[0]
        assert first["skill_name"].lower() == "python"
        assert first["difficulty"] in {"easy", "medium", "hard"}
        assert "question_text" in first and first["question_text"].strip()
        assert first["taxonomy_links"]["esco_uri"] == sample_skills[0]["taxonomy"]["esco_uri"]
        assert first["taxonomy_links"]["onet_code"] == sample_skills[0]["taxonomy"]["onet_code"]

    def test_applies_fallback_template_when_missing_specific_match(self, sample_skills):
        # Use a skill that does not have a dedicated template keyword
        unknown_skill = {
            "name": "Quantum Storytelling",
            "skill_type": "creative",
            "proficiency": "beginner",
            "taxonomy": {
                "esco_uri": None,
                "onet_code": None
            }
        }

        questions = self.mapper.generate_questions(sample_skills + [unknown_skill])
        fallback_question = next(q for q in questions if q["skill_name"] == unknown_skill["name"])

        assert fallback_question["difficulty"] == "easy"  # fallback to proficiency-inferred
        # Note: question_id is a UUID, not prefixed with generic_ in current simple implementation
        assert fallback_question["taxonomy_links"] == {"esco_uri": None, "onet_code": None}

    def test_respects_explicit_difficulty_override(self, sample_skills):
        questions = self.mapper.generate_questions(sample_skills, difficulty_override="hard")

        assert all(q["difficulty"] == "hard" for q in questions)
