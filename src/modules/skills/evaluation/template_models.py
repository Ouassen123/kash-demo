"""Data models for mini-project templates, deliverables, rubrics, and telemetry hooks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import datetime as _dt


@dataclass
class Deliverable:
    """Represents a required artifact for a mini-project submission."""

    name: str
    description: str
    required: bool = True
    file_patterns: List[str] = field(default_factory=list)
    acceptance_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "required": self.required,
            "file_patterns": self.file_patterns,
            "acceptance_notes": self.acceptance_notes,
        }


@dataclass
class RubricCriterion:
    """Represents a rubric item with weight and scoring guidance."""

    name: str
    description: str
    weight: float
    scoring_scale: Dict[str, str]
    automation_hint: Optional[str] = None

    def __post_init__(self) -> None:
        if not 0 < self.weight <= 1:
            raise ValueError("Rubric criterion weight must be between 0 and 1")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "weight": self.weight,
            "scoring_scale": self.scoring_scale,
            "automation_hint": self.automation_hint,
        }


@dataclass
class TelemetryHook:
    """Defines telemetry metrics to collect during evaluation."""

    name: str
    description: str
    metrics: List[str]
    sampling_strategy: str = "per_submission"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "metrics": self.metrics,
            "sampling_strategy": self.sampling_strategy,
        }


@dataclass
class MiniProjectTemplate:
    """Full template definition for a mini-project evaluation."""

    template_id: str
    title: str
    difficulty: str
    summary: str
    expected_artifacts: List[str]
    deliverables: List[Deliverable]
    rubric: List[RubricCriterion]
    telemetry_hooks: List[TelemetryHook]
    success_criteria: List[str]
    version: str = "1.0"
    created_at: str = field(default_factory=lambda: _dt.datetime.utcnow().isoformat())
    competency_tags: List[str] = field(default_factory=list)
    analysis_profile: str = "default"

    def validate_weights(self) -> None:
        total = round(sum(criterion.weight for criterion in self.rubric), 3)
        if total != 1.0:
            raise ValueError(
                f"Rubric weights must sum to 1.0 for {self.template_id}, got {total}"
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_id": self.template_id,
            "title": self.title,
            "difficulty": self.difficulty,
            "summary": self.summary,
            "expected_artifacts": self.expected_artifacts,
            "deliverables": [d.to_dict() for d in self.deliverables],
            "rubric": [r.to_dict() for r in self.rubric],
            "telemetry_hooks": [h.to_dict() for h in self.telemetry_hooks],
            "success_criteria": self.success_criteria,
            "version": self.version,
            "created_at": self.created_at,
            "competency_tags": self.competency_tags,
        }
