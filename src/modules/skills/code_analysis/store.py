"""In-memory storage for code analysis results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, List

from .models import AnalysisResult


@dataclass
class StoredAnalysis:
    submission_id: str
    learner_id: str
    template_id: str
    result: AnalysisResult


class CodeAnalysisStore:
    """Keeps the latest analysis results for auditing and dashboards."""

    def __init__(self) -> None:
        self._by_submission: Dict[str, StoredAnalysis] = {}
        self._by_learner: Dict[str, List[StoredAnalysis]] = {}

    def save(self, payload: StoredAnalysis) -> None:
        self._by_submission[payload.submission_id] = payload
        history = self._by_learner.setdefault(payload.learner_id, [])
        history.insert(0, payload)

    def get(self, submission_id: str) -> Optional[StoredAnalysis]:
        return self._by_submission.get(submission_id)

    def list_by_learner(self, learner_id: str, limit: int = 10) -> List[StoredAnalysis]:
        history = self._by_learner.get(learner_id, [])
        return history[: max(limit, 0)]
