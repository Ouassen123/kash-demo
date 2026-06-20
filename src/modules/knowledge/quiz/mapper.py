"""Quiz mapping utilities to convert CV-derived skills to question prompts."""

from typing import List, Dict, Any, Optional
import uuid


class QuizMapper:
    """Map CV-derived skills to adaptive quiz questions."""

    def __init__(self):
        self.templates = {
            "python": "Describe a situation where you used Python to solve a complex problem.",
            "team leadership": "How do you handle conflicts within a development team?",
            "generic": "What is your experience level with {skill_name}?"
        }

    def generate_questions(self, skills: List[Dict[str, Any]], difficulty_override: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Generate quiz questions from a list of skills.

        Args:
            skills: List of skill dictionaries from CV analysis.
            difficulty_override: Force a specific difficulty for all questions.

        Returns:
            List of question dictionaries with metadata.
        """
        questions = []
        for skill in skills:
            skill_name = skill.get("name", "").lower()
            template = self.templates.get(skill_name, self.templates["generic"])
            question_text = template.format(skill_name=skill.get("name", "the skill"))

            difficulty = difficulty_override or self._infer_difficulty(skill)

            question = {
                "question_id": str(uuid.uuid4()),
                "skill_name": skill.get("name"),
                "question_text": question_text,
                "difficulty": difficulty,
                "taxonomy_links": {
                    "esco_uri": skill.get("taxonomy", {}).get("esco_uri"),
                    "onet_code": skill.get("taxonomy", {}).get("onet_code")
                }
            }
            questions.append(question)
        return questions

    def _infer_difficulty(self, skill: Dict[str, Any]) -> str:
        """Infer difficulty from proficiency or fallback to medium."""
        proficiency = skill.get("proficiency", "").lower()
        mapping = {
            "beginner": "easy",
            "intermediate": "medium",
            "advanced": "hard"
        }
        return mapping.get(proficiency, "medium")
