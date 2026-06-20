"""Simple in-memory persistence for mini-project evaluations."""

from __future__ import annotations

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class StoredEvaluation:
    submission_id: str
    learner_id: str
    template_id: str
    template_title: str
    total_score: float
    summary_report: Dict[str, Any]
    report: Dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class EvaluationStore:
    """Keeps evaluation artifacts for dashboards and downstream stories."""

    def __init__(self) -> None:
        self._by_submission: Dict[str, StoredEvaluation] = {}

    def save(self, payload: StoredEvaluation) -> None:
        self._by_submission[payload.submission_id] = payload

    def get(self, submission_id: str) -> Optional[StoredEvaluation]:
        return self._by_submission.get(submission_id)

    def list_recent(self, limit: int = 20) -> List[StoredEvaluation]:
        return sorted(
            self._by_submission.values(),
            key=lambda item: item.created_at,
            reverse=True,
        )[:limit]

    def list_by_learner(self, learner_id: str, limit: int = 20) -> List[StoredEvaluation]:
        items = [item for item in self._by_submission.values() if item.learner_id == learner_id]
        return sorted(items, key=lambda item: item.created_at, reverse=True)[:limit]
