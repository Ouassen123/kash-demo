"""Data models for the Skills code analysis pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional


class SeverityLevel(str, Enum):
    """Severity levels used by analyzer findings."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AnalyzerFinding:
    """Single analyzer finding with context."""

    message: str
    severity: SeverityLevel
    category: str
    file_path: Optional[str] = None
    line: Optional[int] = None
    hint: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["severity"] = self.severity.value
        return payload


@dataclass
class AnalyzerReport:
    """Result emitted by each analyzer plugin."""

    analyzer_name: str
    analyzer_version: str
    execution_time_ms: int
    findings: List[AnalyzerFinding] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    @property
    def duration_ms(self) -> Optional[float]:
        if not self.completed_at:
            return None
        return (self.completed_at - self.started_at).total_seconds() * 1000

    def to_dict(self) -> Dict[str, Any]:
        return {
            "analyzer_name": self.analyzer_name,
            "analyzer_version": self.analyzer_version,
            "execution_time_ms": self.execution_time_ms,
            "findings": [finding.to_dict() for finding in self.findings],
            "warnings": self.warnings,
            "errors": self.errors,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
        }


@dataclass
class AnalysisResult:
    """Top-level structure describing a submission analysis run."""

    submission_id: str
    learner_id: str
    template_id: str
    analysis_profile: str
    overall_score: float
    confidence: float
    analyzer_reports: List[AnalyzerReport]
    summary: str
    analyzed_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "submission_id": self.submission_id,
            "learner_id": self.learner_id,
            "template_id": self.template_id,
            "analysis_profile": self.analysis_profile,
            "overall_score": self.overall_score,
            "confidence": self.confidence,
            "analyzer_reports": [report.to_dict() for report in self.analyzer_reports],
            "summary": self.summary,
            "analyzed_at": self.analyzed_at.isoformat(),
        }
