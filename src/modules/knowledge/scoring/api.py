"""API layer for knowledge scoring calculation."""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from .scorer import KnowledgeScorer
from src.core.logging import get_logger

logger = get_logger(__name__)


class ScoringAPI:
    """Cache-friendly API for knowledge scores."""

    def __init__(self, scorer: Optional[KnowledgeScorer] = None, cache_ttl_seconds: int = 300):
        """
        Initialize API with optional scorer and cache TTL.

        Args:
            scorer: KnowledgeScorer instance (creates default if None).
            cache_ttl_seconds: Cache TTL in seconds (default 5 minutes).
        """
        self.scorer = scorer or KnowledgeScorer()
        self.cache_ttl = timedelta(seconds=cache_ttl_seconds)
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get_score(
        self,
        cv_insights: Dict[str, Any],
        taxonomy_confidence: Dict[str, Any],
        quiz_mastery: Dict[str, Any],
        user_id: Optional[int] = None,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """
        Get knowledge score with caching and fallback behavior.

        Args:
            cv_insights: CV analysis output.
            taxonomy_confidence: Taxonomy enrichment confidence.
            quiz_mastery: Quiz scoring output.
            user_id: Optional user identifier.
            force_refresh: Skip cache and recompute.

        Returns:
            Unified knowledge score with diagnostics.
        """
        cache_key = self._make_cache_key(cv_insights, taxonomy_confidence, quiz_mastery, user_id)

        if not force_refresh and cache_key in self._cache:
            entry = self._cache[cache_key]
            if datetime.utcnow() - entry["timestamp"] < self.cache_ttl:
                logger.debug(f"Cache hit for user {user_id}")
                return entry["result"]
            else:
                logger.debug(f"Cache expired for user {user_id}")
                del self._cache[cache_key]

        # Compute score
        try:
            result = self.scorer.calculate_score(
                cv_insights=cv_insights,
                taxonomy_confidence=taxonomy_confidence,
                quiz_mastery=quiz_mastery,
                user_id=user_id,
            )
            # Cache result
            self._cache[cache_key] = {"timestamp": datetime.utcnow(), "result": result}
            return result
        except Exception as e:
            logger.error(f"Scoring calculation failed for user {user_id}: {e}")
            # Fallback: return minimal safe response
            return self._fallback_response(user_id, str(e))

    def _make_cache_key(self, cv_insights: Dict[str, Any], taxonomy_confidence: Dict[str, Any], quiz_mastery: Dict[str, Any], user_id: Optional[int]) -> str:
        """Create a deterministic cache key."""
        # Simplified: hash of concatenated scores + user_id
        import hashlib
        cv_score = cv_insights.get('score', '') if cv_insights else ''
        tax_conf = taxonomy_confidence.get('confidence', '') if taxonomy_confidence else ''
        quiz_score = quiz_mastery.get('score', '') if quiz_mastery else ''
        key_data = f"{cv_score}|{tax_conf}|{quiz_score}|{user_id}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    def _fallback_response(self, user_id: Optional[int], error_msg: str) -> Dict[str, Any]:
        """Return a safe fallback when scoring fails."""
        return {
            "knowledge_score": 0.0,
            "breakdown": {"cv_insights": {"score": 0.0, "weight": 0.35}, "taxonomy_confidence": {"score": 0.0, "weight": 0.25}, "quiz_mastery": {"score": 0.0, "weight": 0.40}},
            "confidence_interval": {"lower": 0.0, "upper": 0.0},
            "diagnostics": {
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "error": error_msg,
                "weights_used": self.scorer.weights.copy(),
            },
        }

    def clear_cache(self):
        """Clear the scoring cache."""
        self._cache.clear()
        logger.info("Scoring cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Return simple cache statistics."""
        return {
            "cache_size": len(self._cache),
            "cache_ttl_seconds": int(self.cache_ttl.total_seconds()),
            "weights": self.scorer.weights.copy(),
        }
