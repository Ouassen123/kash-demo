"""Reusable UI components for Knowledge evaluation interface."""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class DataCard:
    """Reusable data card with confidence and drill-down."""
    title: str
    value: Any
    confidence: Optional[float] = None
    source: Optional[str] = None
    drill_down_data: Optional[Dict[str, Any]] = None
    help_text: Optional[str] = None


@dataclass
class MetricBadge:
    """Badge for metrics with color coding."""
    label: str
    value: str
    level: str  # 'high', 'medium', 'low'


@dataclass
class ActionButton:
    """Action button tied to backend API."""
    label: str
    endpoint: str
    method: str = "POST"
    payload: Optional[Dict[str, Any]] = None


class EvaluationPanel:
    """Main evaluation panel builder."""

    @staticmethod
    def cv_analysis_panel(cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build panel for CV analysis results."""
        cards = []
        for section, items in cv_data.items():
            if isinstance(items, list):
                for item in items:
                    cards.append(DataCard(
                        title=f"{section.title()}: {item.get('name', 'N/A')}",
                        value=item.get('value', item.get('name', 'N/A')),
                        confidence=item.get('confidence'),
                        source="CV Analyzer",
                        drill_down_data=item,
                        help_text=f"Extracted from CV with confidence {item.get('confidence', 'N/A')}"
                    ))
        return {"title": "CV Analysis", "cards": cards}

    @staticmethod
    def taxonomy_panel(taxonomy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build panel for taxonomy enrichment."""
        cards = []
        # Handle mock format where taxonomy_data may contain non-dict values
        for skill, matches in taxonomy_data.items():
            if isinstance(matches, list):
                for match in matches:
                    if isinstance(match, dict):
                        cards.append(DataCard(
                            title=f"Taxonomy: {skill}",
                            value=match.get("description", match.get("title", skill)),
                            confidence=match.get("confidence"),
                            source=match.get("source", "ESCO/O*NET"),
                            drill_down_data=match,
                            help_text=f"Matched via {match.get('source', 'taxonomy')}"
                        ))
        return {"title": "Taxonomy Enrichment", "cards": cards}

    @staticmethod
    def quiz_panel(quiz_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build panel for quiz diagnostics."""
        cards = []
        scoring = quiz_data.get("scoring", {})
        cards.append(DataCard(
            title="Quiz Score",
            value=f"{scoring.get('score', 0):.2f}",
            confidence=scoring.get("confidence"),
            source="Quiz Engine",
            drill_down_data=quiz_data,
            help_text="Overall quiz performance"
        ))
        cards.append(DataCard(
            title="Mastery Level",
            value=scoring.get("mastery", "unknown"),
            confidence=scoring.get("confidence"),
            source="Quiz Engine",
            drill_down_data=quiz_data,
            help_text="Mastery derived from quiz results"
        ))
        return {"title": "Quiz Diagnostics", "cards": cards}

    @staticmethod
    def knowledge_score_panel(score_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build panel for unified knowledge score."""
        score = score_data.get("knowledge_score", 0)
        ci = score_data.get("confidence_interval", {})
        cards = [
            DataCard(
                title="Knowledge Score",
                value=f"{score:.2f}",
                confidence=ci.get("upper", 1.0) - ci.get("lower", 0.0),
                source="Scoring Engine",
                drill_down_data=score_data,
                help_text="Unified score from CV, taxonomy, and quiz"
            ),
            DataCard(
                title="Confidence Interval",
                value=f"{ci.get('lower', 0):.2f} - {ci.get('upper', 1):.2f}",
                confidence=None,
                source="Scoring Engine",
                drill_down_data=score_data,
                help_text="Estimated range for the score"
            )
        ]
        return {"title": "Knowledge Score", "cards": cards}
