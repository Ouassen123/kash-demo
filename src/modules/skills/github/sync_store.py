"""Audit-friendly storage for GitHub submission syncs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from .models import SubmissionSyncResult


@dataclass
class SyncLogEntry:
    """Single GitHub sync log entry with metadata for auditing."""

    learner_id: str
    submission_id: str
    template_id: str
    project_id: Optional[str]
    metadata: Dict[str, Any]
    result: SubmissionSyncResult
    recorded_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "learner_id": self.learner_id,
            "submission_id": self.submission_id,
            "template_id": self.template_id,
            "project_id": self.project_id,
            "metadata": self.metadata,
            "recorded_at": self.recorded_at.isoformat(),
            "result": self.result.to_dict(),
        }
        return payload


class GitHubSyncStore:
    """In-memory log of GitHub sync activity for downstream consumers."""

    def __init__(self) -> None:
        self._by_submission: Dict[str, SyncLogEntry] = {}
        self._by_learner: Dict[str, List[SyncLogEntry]] = {}

    def record_sync(
        self,
        learner_id: str,
        submission_id: str,
        template_id: str,
        project_id: Optional[str],
        metadata: Dict[str, Any],
        result: SubmissionSyncResult,
    ) -> SyncLogEntry:
        entry = SyncLogEntry(
            learner_id=learner_id,
            submission_id=submission_id,
            template_id=template_id,
            project_id=project_id,
            metadata=metadata,
            result=result,
            recorded_at=result.synced_at,
        )
        self._by_submission[submission_id] = entry
        history = self._by_learner.setdefault(learner_id, [])
        history.insert(0, entry)
        return entry

    def get_latest_by_submission(self, submission_id: str) -> Optional[SyncLogEntry]:
        return self._by_submission.get(submission_id)

    def list_by_learner(self, learner_id: str, limit: int = 10) -> List[SyncLogEntry]:
        history = self._by_learner.get(learner_id, [])
        return history[: max(limit, 0)]

    def to_dict(self) -> Dict[str, List[Dict[str, Any]]]:
        return {
            learner_id: [entry.to_dict() for entry in entries]
            for learner_id, entries in self._by_learner.items()
        }
