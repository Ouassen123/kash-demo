"""Quiz orchestrator coordinating mapping, scoring, and storage."""

from typing import List, Dict, Any, Optional
from .mapper import QuizMapper
from .scoring import QuizScorer
from .storage import QuizStorage


class QuizOrchestrator:
    """Orchestrate the full adaptive quiz workflow."""

    def __init__(self):
        self.mapper = QuizMapper()
        self.scorer = QuizScorer()
        self.storage = QuizStorage()

    def run_quiz(self, skills: List[Dict[str, Any]], answers: List[Dict[str, Any]], user_id: Optional[int] = None, difficulty_override: Optional[str] = None) -> Dict[str, Any]:
        """
        Run the full quiz pipeline: generate questions, score answers, store results.

        Args:
            skills: List of skill dictionaries from CV analysis.
            answers: List of answer dicts with 'correct' boolean.
            user_id: Optional user identifier for storage.
            difficulty_override: Force a specific difficulty for all questions.

        Returns:
            Dict with questions, scoring results, and storage confirmation.
        """
        # Step 1: Generate questions from skills
        questions = self.mapper.generate_questions(skills, difficulty_override=difficulty_override)

        # Step 2: Score the answers
        scoring_result = self.scorer.calculate_score(answers)

        # Step 3: Store results (if user_id provided)
        stored = False
        if user_id is not None:
            payload = {
                "user_id": user_id,
                "score": scoring_result["score"],
                "confidence": scoring_result["confidence"],
                "mastery": scoring_result["mastery"],
                "answers": answers,
                "questions": questions
            }
            stored = self.storage.save_results(payload)

        # Step 4: Return consolidated result
        return {
            "questions": questions,
            "scoring": scoring_result,
            "stored": stored,
            "user_id": user_id
        }

    def get_quiz_stats(self) -> Dict[str, Any]:
        """Retrieve aggregated quiz statistics."""
        return self.storage.get_stats()
