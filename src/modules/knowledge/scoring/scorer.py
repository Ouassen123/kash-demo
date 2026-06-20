"""Knowledge scoring calculation service."""

from typing import Dict, Any, List, Optional
import yaml
from datetime import datetime

from src.core.logging import get_logger

logger = get_logger(__name__)


class KnowledgeScorer:
    """Compute unified knowledge scores from CV, taxonomy, and quiz signals."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize scorer with configurable weights.

        Args:
            config_path: Path to weights.yaml (defaults to internal config).
        """
        self.config_path = config_path or "modules/knowledge/scoring/config/weights.yaml"
        self.weights = self._load_weights()
        self.audit_log = self._load_audit_log()

    def _load_weights(self) -> Dict[str, float]:
        """Load component weights from YAML config."""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                return config.get("components", {})
        except Exception as e:
            logger.error(f"Failed to load weights config: {e}")
            # Fallback default weights
            return {"cv_insights": 0.35, "taxonomy_confidence": 0.25, "quiz_mastery": 0.40}

    def _load_audit_log(self) -> List[Dict[str, Any]]:
        """Load audit log from config file."""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                return config.get("audit_log", [])
        except Exception as e:
            logger.error(f"Failed to load audit log: {e}")
            return []

    def calculate_score(
        self,
        cv_insights: Dict[str, Any],
        taxonomy_confidence: Dict[str, Any],
        quiz_mastery: Dict[str, Any],
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Compute unified knowledge score with diagnostics.

        Args:
            cv_insights: CV analysis output (e.g., skills, confidence).
            taxonomy_confidence: Taxonomy enrichment confidence (ESCO/O*NET).
            quiz_mastery: Quiz scoring output (score, mastery, confidence).
            user_id: Optional user identifier for audit.

        Returns:
            Dict with score, breakdown, confidence intervals, and diagnostics.
        """
        # Extract component scores (normalized 0-1)
        cv_score = self._normalize_component(cv_insights)
        taxonomy_score = self._normalize_component(taxonomy_confidence)
        quiz_score = self._normalize_component(quiz_mastery)

        # Weighted sum
        raw_score = (
            cv_score * self.weights.get("cv_insights", 0)
            + taxonomy_score * self.weights.get("taxonomy_confidence", 0)
            + quiz_score * self.weights.get("quiz_mastery", 0)
        )

        # Clamp to [0, 1]
        final_score = max(0.0, min(1.0, raw_score))

        # Build diagnostics
        breakdown = {
            "cv_insights": {"score": cv_score, "weight": self.weights.get("cv_insights", 0)},
            "taxonomy_confidence": {"score": taxonomy_score, "weight": self.weights.get("taxonomy_confidence", 0)},
            "quiz_mastery": {"score": quiz_score, "weight": self.weights.get("quiz_mastery", 0)},
        }

        # Simple confidence interval (bootstrap-like)
        confidence_interval = self._estimate_confidence_interval(final_score, cv_score, taxonomy_score, quiz_score)

        diagnostics = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "raw_inputs": {
                "cv_insights": cv_insights,
                "taxonomy_confidence": taxonomy_confidence,
                "quiz_mastery": quiz_mastery,
            },
            "weights_used": self.weights.copy(),
            "breakdown": breakdown,
            "confidence_interval": confidence_interval,
        }

        return {
            "knowledge_score": final_score,
            "breakdown": breakdown,
            "confidence_interval": confidence_interval,
            "diagnostics": diagnostics,
        }

    def _normalize_component(self, component: Dict[str, Any]) -> float:
        """Normalize any component dict to a 0-1 score."""
        if "score" in component:
            return float(component["score"])
        if "confidence" in component:
            return float(component["confidence"])
        if "mastery" in component:
            mastery_map = {"low": 0.25, "medium": 0.6, "high": 0.9}
            return mastery_map.get(component["mastery"].lower(), 0.5)
        # Fallback: assume 0.5
        return 0.5

    def _estimate_confidence_interval(self, final_score: float, *component_scores) -> Dict[str, float]:
        """Simple confidence interval estimate (can be replaced with proper bootstrap)."""
        # Very simple heuristic: wider interval if components diverge
        variance = max(component_scores) - min(component_scores)
        margin = min(0.1, variance / 2)
        return {"lower": max(0.0, final_score - margin), "upper": min(1.0, final_score + margin)}

    def update_weights(self, new_weights: Dict[str, float], author: str = "system"):
        """
        Update component weights and log the change.

        Args:
            new_weights: New weight mapping.
            author: Who made the change.
        """
        old_weights = self.weights.copy()
        self.weights.update(new_weights)
        # Normalize to sum to 1
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in self.weights.items()}

        # Persist and audit
        self._persist_weights()
        self._log_weight_change(old_weights, self.weights.copy(), author)

    def _persist_weights(self):
        """Persist current weights to YAML."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump({"components": self.weights, "audit_log": self.audit_log}, f, default_flow_style=False)
        except Exception as e:
            logger.error(f"Failed to persist weights: {e}")

    def _log_weight_change(self, old_weights: Dict[str, float], new_weights: Dict[str, float], author: str):
        """Append weight change to audit log."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "change": "Weight update",
            "author": author,
            "previous": old_weights,
            "new": new_weights,
        }
        self.audit_log.append(entry)
        logger.info(f"Weights updated by {author}: {old_weights} -> {new_weights}")
