"""Composite scorer for the Habits module."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from src.core.logging import get_logger

logger = get_logger(__name__)


class CompositeScorer:
    """Compute the final Habits score from multimodal metrics.

    The scorer dynamically selects the weighting table based on the modalities
    present in the request:
      - text only
      - text + voice
      - text + voice + face

    Industry-specific tuning can slightly rebalance the weights to favour
    clarity or engagement for technical / management contexts.
    """

    _WEIGHTS_TEXT_ONLY = {
        "clarity": 0.30,
        "relevance": 0.30,
        "engagement": 0.25,
        "confidence": 0.15,
    }

    _WEIGHTS_TEXT_VOICE = {
        "clarity": 0.25,
        "relevance": 0.25,
        "engagement": 0.20,
        "confidence": 0.20,
        "fluency": 0.10,
    }

    _WEIGHTS_TEXT_VOICE_FACE = {
        "clarity": 0.20,
        "relevance": 0.20,
        "engagement": 0.15,
        "confidence_voice": 0.20,
        "confidence_face": 0.15,
        "fluency": 0.10,
    }

    def compute_score(
        self,
        *,
        clarity_score: float,
        relevance_score: float,
        engagement_score: float,
        confidence_score: float,
        fluency_score: Optional[float] = None,
        face_confidence_score: Optional[float] = None,
        modalities_used: Optional[List[str]] = None,
        industry: Optional[str] = None,
    ) -> Tuple[float, Dict[str, float]]:
        """Compute the final composite score and a detailed breakdown.

        Args:
            clarity_score: Clarity score in [0, 100].
            relevance_score: Relevance score in [0, 100].
            engagement_score: Engagement score in [0, 100].
            confidence_score: Aggregated confidence score in [0, 100].
            fluency_score: Optional voice fluency score in [0, 100].
            face_confidence_score: Optional face confidence score in [0, 100].
            modalities_used: List of modalities present in the analysis.
            industry: Optional industry profile for lightweight reweighting.

        Returns:
            (composite_score, score_breakdown)
        """
        modalities_used = modalities_used or ["text"]
        weights = self._select_weights(modalities_used)
        weights = self._adjust_weights_for_industry(weights, industry)
        weights = self._normalize_weights(weights)

        breakdown: Dict[str, float] = {
            "clarity": round(clarity_score, 2),
            "relevance": round(relevance_score, 2),
            "engagement": round(engagement_score, 2),
            "confidence": round(confidence_score, 2),
        }

        if fluency_score is not None and "fluency" in weights:
            breakdown["fluency"] = round(fluency_score, 2)

        if face_confidence_score is not None and "confidence_face" in weights:
            breakdown["confidence_face"] = round(face_confidence_score, 2)

        composite = 0.0
        composite += clarity_score * weights.get("clarity", 0.0)
        composite += relevance_score * weights.get("relevance", 0.0)
        composite += engagement_score * weights.get("engagement", 0.0)

        if "confidence_face" in weights and face_confidence_score is not None:
            composite += confidence_score * weights.get("confidence_voice", 0.0)
            composite += face_confidence_score * weights.get("confidence_face", 0.0)
        else:
            # Text-only and text+voice modes use the aggregated confidence score.
            composite += confidence_score * weights.get("confidence", weights.get("confidence_voice", 0.0))

        if fluency_score is not None:
            composite += fluency_score * weights.get("fluency", 0.0)

        composite = round(max(0.0, min(100.0, composite)), 2)
        logger.debug("CompositeScorer: modalities=%s industry=%s score=%.2f", modalities_used, industry, composite)
        return composite, breakdown

    def _select_weights(self, modalities_used: List[str]) -> Dict[str, float]:
        has_voice = "voice" in modalities_used
        has_face = "face" in modalities_used

        if has_voice and has_face:
            return dict(self._WEIGHTS_TEXT_VOICE_FACE)
        if has_voice:
            return dict(self._WEIGHTS_TEXT_VOICE)
        return dict(self._WEIGHTS_TEXT_ONLY)

    @staticmethod
    def _adjust_weights_for_industry(weights: Dict[str, float], industry: Optional[str]) -> Dict[str, float]:
        """Slightly bias weights for technical/management contexts."""
        if not industry:
            return weights

        industry_key = industry.strip().lower()
        adjusted = dict(weights)

        if industry_key in {"technology", "tech", "it", "engineering", "data"}:
            # Favor clarity a little more, keep the total balanced later via normalization.
            adjusted = CompositeScorer._shift_weight(adjusted, "clarity", +0.03)
            adjusted = CompositeScorer._shift_weight(adjusted, "engagement", -0.02)
            adjusted = CompositeScorer._shift_weight(adjusted, "relevance", -0.01)
        elif industry_key in {"management", "business", "leadership"}:
            adjusted = CompositeScorer._shift_weight(adjusted, "engagement", +0.03)
            adjusted = CompositeScorer._shift_weight(adjusted, "clarity", -0.01)
            adjusted = CompositeScorer._shift_weight(adjusted, "relevance", -0.02)

        return adjusted

    @staticmethod
    def _shift_weight(weights: Dict[str, float], key: str, delta: float) -> Dict[str, float]:
        if key not in weights:
            return weights
        weights[key] = max(0.0, weights[key] + delta)
        return weights

    @staticmethod
    def _normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
        total = sum(weights.values())
        if total <= 0:
            return weights
        return {k: v / total for k, v in weights.items()}
