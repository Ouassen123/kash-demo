"""Adaptive quiz scoring utilities for confidence and mastery metrics."""

from typing import List, Dict, Any


class QuizScorer:
    """Calculate quiz scores, confidence, and mastery metrics."""

    def calculate_score(self, answers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate score, confidence, and mastery from a list of answers.

        Args:
            answers: List of answer dicts with 'correct' boolean.

        Returns:
            Dict with 'score', 'confidence', and 'mastery' fields.
        """
        total = len(answers)
        if total == 0:
            return {"score": 0.0, "confidence": 0.0, "mastery": "low"}

        correct = sum(1 for a in answers if a.get("correct"))
        score = correct / total

        # Simple confidence model: boost slightly above raw score
        confidence = min(score + 0.1, 1.0)

        # Mastery thresholds
        if score > 0.8:
            mastery = "high"
        elif score > 0.5:
            mastery = "medium"
        else:
            mastery = "low"

        return {"score": score, "confidence": confidence, "mastery": mastery}
