"""Scoring pipeline for text-based cognitive tests."""

from typing import List, Dict, Any, Optional
import re
from datetime import datetime

from src.core.logging import get_logger

logger = get_logger(__name__)


class CognitiveScorer:
    """Maps answers to cognitive dimensions, flags low-confidence/inconsistent responses."""

    def __init__(self):
        # Simple rubric keywords per dimension (can be extended)
        self.dimension_keywords = {
            "logic": ["because", "therefore", "since", "thus", "reason", "pattern", "sequence", "rule"],
            "reasoning": ["step", "first", "next", "then", "conclude", "solve", "approach"],
            "creativity": ["imagine", "story", "unique", "different", "new", "invent", "design"],
            "originality": ["original", "novel", "fresh", "unusual", "innovative"],
            "persistence": ["try", "retry", "keep", "continue", "effort", "practice", "learn"],
            "metacognition": ["think", "reflect", "understand", "monitor", "plan", "strategy"],
        }

    def score_response(self, prompt_id: str, response_text: str, time_taken_seconds: int, expected_dimensions: List[str]) -> Dict[str, Any]:
        """
        Score a single response across expected dimensions.

        Args:
            prompt_id: ID of the prompt.
            response_text: User's free-form response.
            time_taken_seconds: Time spent on this prompt.
            expected_dimensions: List of dimensions this prompt targets.

        Returns:
            Scoring dict with dimension scores, confidence, and flags.
        """
        scores = {}
        for dim in expected_dimensions:
            scores[dim] = self._compute_dimension_score(dim, response_text)

        overall_score = sum(scores.values()) / len(scores) if scores else 0.0
        confidence = self._estimate_confidence(scores, response_text, time_taken_seconds)
        flags = self._detect_flags(scores, response_text, time_taken_seconds)

        return {
            "prompt_id": prompt_id,
            "dimension_scores": scores,
            "overall_score": overall_score,
            "confidence": confidence,
            "flags": flags,
            "response_length": len(response_text.split()),
            "time_taken_seconds": time_taken_seconds,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _compute_dimension_score(self, dimension: str, response_text: str) -> float:
        """Compute a 0-1 score for a dimension based on keyword presence and length."""
        keywords = self.dimension_keywords.get(dimension.lower(), [])
        text = response_text.lower()
        matches = sum(1 for kw in keywords if kw in text)
        # Simple heuristic: proportion of keywords found, capped at 1
        keyword_score = min(matches / max(len(keywords), 1), 1.0)
        # Length factor: very short responses get penalized
        length_factor = min(len(response_text.split()) / 20, 1.0)
        # Combine: 70% keywords, 30% length
        return keyword_score * 0.7 + length_factor * 0.3

    def _estimate_confidence(self, dimension_scores: Dict[str, float], response_text: str, time_taken_seconds: int) -> float:
        """Estimate scoring confidence based on score variance and response quality."""
        if not dimension_scores:
            return 0.0
        # Low variance across dimensions increases confidence
        scores = list(dimension_scores.values())
        variance = max(scores) - min(scores)
        variance_factor = 1.0 - min(variance, 1.0)
        # Very short or very long responses reduce confidence
        word_count = len(response_text.split())
        length_factor = 1.0
        if word_count < 5:
            length_factor = 0.5
        elif word_count > 200:
            length_factor = 0.8
        # Extremely fast responses reduce confidence
        time_factor = 1.0
        if time_taken_seconds < 10:
            time_factor = 0.6
        # Combine factors
        confidence = (variance_factor * 0.4 + length_factor * 0.4 + time_factor * 0.2)
        return max(0.0, min(1.0, confidence))

    def _detect_flags(self, dimension_scores: Dict[str, float], response_text: str, time_taken_seconds: int) -> List[str]:
        """Flag low-confidence or inconsistent responses."""
        flags = []
        # Low overall score
        overall = sum(dimension_scores.values()) / len(dimension_scores) if dimension_scores else 0.0
        if overall < 0.3:
            flags.append("low_score")
        # High variance (inconsistent)
        if dimension_scores:
            variance = max(dimension_scores.values()) - min(dimension_scores.values())
            if variance > 0.7:
                flags.append("inconsistent")
        # Very short response
        if len(response_text.split()) < 5:
            flags.append("too_short")
        # Extremely fast response
        if time_taken_seconds < 10:
            flags.append("too_fast")
        # No keywords detected for any dimension
        if all(score < 0.1 for score in dimension_scores.values()):
            flags.append("no_keywords")
        return flags

    def score_session(self, session_transcript: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Score an entire session transcript.

        Args:
            session_transcript: List of response dicts from orchestrator.

        Returns:
            Session-level scoring summary with confidence bands.
        """
        if not session_transcript:
            return {"error": "Empty transcript"}

        response_scores = []
        for entry in session_transcript:
            prompt_id = entry.get("prompt_id")
            response_text = entry.get("response_text", "")
            time_taken = entry.get("time_taken_seconds", 0)
            # Expected dimensions would come from prompt metadata; here we infer from prompt_id
            expected = self._infer_expected_dimensions(prompt_id)
            score = self.score_response(prompt_id, response_text, time_taken, expected)
            response_scores.append(score)

        # Aggregate
        dimension_totals: Dict[str, List[float]] = {}
        for rs in response_scores:
            for dim, val in rs["dimension_scores"].items():
                dimension_totals.setdefault(dim, []).append(val)

        dimension_means = {dim: sum(vals) / len(vals) for dim, vals in dimension_totals.items()}
        overall_mean = sum(dimension_means.values()) / len(dimension_means) if dimension_means else 0.0
        overall_confidence = sum(rs["confidence"] for rs in response_scores) / len(response_scores)

        # Confidence bands (simple heuristic)
        margin = 0.1 * (1 - overall_confidence)
        lower = max(0.0, overall_mean - margin)
        upper = min(1.0, overall_mean + margin)

        return {
            "session_id": session_transcript[0].get("session_id"),
            "dimension_means": dimension_means,
            "overall_score": overall_mean,
            "overall_confidence": overall_confidence,
            "confidence_band": {"lower": lower, "upper": upper},
            "response_scores": response_scores,
            "flags": [flag for rs in response_scores for flag in rs["flags"]],
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _infer_expected_dimensions(self, prompt_id: str) -> List[str]:
        """Infer expected dimensions from prompt ID (fallback)."""
        mapping = {
            "logic_sequence": ["logic", "reasoning"],
            "creativity_story": ["creativity", "originality"],
            "persistence_puzzle": ["persistence", "metacognition"],
        }
        return mapping.get(prompt_id, ["logic"])
