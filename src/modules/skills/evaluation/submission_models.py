"""Submission models for mini-project evaluation pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import fnmatch


@dataclass
class SubmissionArtifact:
    """Represents an artifact submitted by a learner for evaluation."""

    path: str
    artifact_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    content_hash: Optional[str] = None
    size_bytes: Optional[int] = None

    def matches_pattern(self, pattern: str) -> bool:
        """Return True if artifact path matches glob pattern."""
        return fnmatch.fnmatch(self.path, pattern)


@dataclass
class MiniProjectSubmission:
    """Full submission payload for evaluation."""

    submission_id: str
    learner_id: str
    template_id: str
    artifacts: List[SubmissionArtifact]
    telemetry: Dict[str, Any] = field(default_factory=dict)
    submitted_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    notes: Optional[str] = None

    def artifact_summary(self) -> Dict[str, int]:
        summary: Dict[str, int] = {}
        for artifact in self.artifacts:
            summary[artifact.artifact_type] = summary.get(artifact.artifact_type, 0) + 1
        return summary
