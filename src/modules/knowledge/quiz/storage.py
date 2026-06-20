"""Storage utilities for quiz interactions and analytics tracking."""

from typing import List, Dict, Any


class QuizStorage:
    """Simple in-memory storage for quiz results and stats (mock for tests)."""

    def __init__(self):
        self._results: List[Dict[str, Any]] = []

    def save_results(self, results: Dict[str, Any]) -> bool:
        """
        Save a single quiz result.

        Args:
            results: Dict containing user_id, score, answers, etc.

        Returns:
            True if saved successfully.
        """
        self._results.append(results)
        return True

    def get_stats(self) -> Dict[str, Any]:
        """
        Retrieve aggregated stats.

        Returns:
            Dict with basic statistics.
        """
        total_attempts = len(self._results)
        if total_attempts == 0:
            return {"total_attempts": 0, "average_score": 0.0}

        total_score = sum(r.get("score", 0) for r in self._results)
        average_score = total_score / total_attempts

        return {"total_attempts": total_attempts, "average_score": average_score}
