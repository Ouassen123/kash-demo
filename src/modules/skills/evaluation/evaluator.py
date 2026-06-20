"""Evaluation pipeline for mini-project submissions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any

from .template_registry import MiniProjectTemplateRegistry
from .template_models import MiniProjectTemplate
from .submission_models import MiniProjectSubmission, SubmissionArtifact
from .static_analyzer import StaticAnalyzer


@dataclass
class CriterionScore:
    name: str
    weight: float
    raw_score: float
    weighted_score: float
    rationale: str


@dataclass
class EvaluationResult:
    submission_id: str
    template_id: str
    total_score: float
    rubric_scores: List[CriterionScore]
    missing_deliverables: List[str]
    flags: List[str]
    summary_report: Dict[str, Any]
    telemetry: Dict[str, Dict[str, Any]]


class MiniProjectEvaluator:
    """Evaluates submissions against mini-project templates and rubrics."""

    def __init__(
        self,
        template_registry: MiniProjectTemplateRegistry,
        static_analyzer: StaticAnalyzer | None = None,
    ) -> None:
        self.template_registry = template_registry
        self.static_analyzer = static_analyzer or StaticAnalyzer()

    def evaluate_submission(self, submission: MiniProjectSubmission) -> EvaluationResult:
        template = self.template_registry.get_template(submission.template_id)
        metrics = self.static_analyzer.run_checks(submission, template)
        deliverable_status = self._check_deliverables(submission, template)

        rubric_scores = self._score_rubric(template, metrics, deliverable_status)
        total_score = round(sum(item.weighted_score for item in rubric_scores), 3)
        flags = self._generate_flags(metrics, deliverable_status)

        summary_report = {
            "submission_id": submission.submission_id,
            "learner_id": submission.learner_id,
            "template_title": template.title,
            "artifact_summary": submission.artifact_summary(),
            "artifact_links": [
                {"path": artifact.path, "type": artifact.artifact_type}
                for artifact in submission.artifacts
            ],
            "metrics": metrics,
            "deliverables": deliverable_status,
            "reviewer_notes": [],
        }

        return EvaluationResult(
            submission_id=submission.submission_id,
            template_id=template.template_id,
            total_score=total_score,
            rubric_scores=rubric_scores,
            missing_deliverables=[
                name
                for name, status in deliverable_status.items()
                if not status["present"] and status["required"]
            ],
            flags=flags,
            summary_report=summary_report,
            telemetry=metrics.get("telemetry", {}),
        )

    # ------------------------------------------------------------------
    # Deliverables & rubric scoring
    # ------------------------------------------------------------------
    def _check_deliverables(
        self,
        submission: MiniProjectSubmission,
        template: MiniProjectTemplate,
    ) -> Dict[str, Dict[str, Any]]:
        results: Dict[str, Dict[str, Any]] = {}
        for deliverable in template.deliverables:
            present = self._artifact_matches(submission.artifacts, deliverable)
            results[deliverable.name] = {
                "present": present,
                "required": deliverable.required,
                "description": deliverable.description,
            }
        return results

    def _artifact_matches(
        self,
        artifacts: List[SubmissionArtifact],
        deliverable,
    ) -> bool:
        patterns = getattr(deliverable, "file_patterns", [])
        keywords = deliverable.name.lower()
        if not artifacts:
            return False

        for artifact in artifacts:
            path = artifact.path.lower()
            artifact_type = (artifact.artifact_type or "").lower()

            # Direct pattern match first
            if patterns:
                for pattern in patterns:
                    if artifact.matches_pattern(pattern):
                        return True

            # Fallback heuristics using artifact_type+keywords
            if artifact_type and artifact_type in keywords:
                return True
            if "test" in keywords and artifact_type == "tests":
                return True
            if "readme" in keywords and path.endswith("readme.md"):
                return True

        return False

    def _score_rubric(
        self,
        template: MiniProjectTemplate,
        metrics: Dict[str, Any],
        deliverables: Dict[str, Dict[str, Any]],
    ) -> List[CriterionScore]:
        scores: List[CriterionScore] = []
        for criterion in template.rubric:
            raw_score, rationale = self._score_criterion(criterion.name, metrics, deliverables)
            weighted_score = round(raw_score * criterion.weight, 3)
            scores.append(
                CriterionScore(
                    name=criterion.name,
                    weight=criterion.weight,
                    raw_score=round(raw_score, 3),
                    weighted_score=weighted_score,
                    rationale=rationale,
                )
            )
        return scores

    def _score_criterion(
        self,
        criterion_name: str,
        metrics: Dict[str, Any],
        deliverables: Dict[str, Dict[str, Any]],
    ) -> tuple[float, str]:
        key = criterion_name.lower()
        if "correctness" in key or "accuracy" in key:
            raw = metrics.get("correctness_signal", 0.5)
            rationale = f"Correctness signal={raw}"
        elif "quality" in key:
            lint = metrics.get("lint_warnings", 0)
            raw = max(0.0, 1.0 - min(lint, 20) / 20)
            rationale = f"Lint warnings={lint}"
        elif "test" in key or "coverage" in key:
            coverage = metrics.get("coverage", 0.0)
            raw = coverage
            rationale = f"Estimated coverage={coverage}"
        elif "operational" in key or "reliability" in key:
            raw = metrics.get("deployment_signal", 0.3)
            rationale = f"Deployment signal={raw}"
        elif "documentation" in key:
            raw = metrics.get("documentation_signal", 0.4)
            rationale = f"Documentation signal={raw}"
        elif "data quality" in key:
            raw = metrics.get("data_quality_signal", 0.5)
            rationale = f"Data quality signal={raw}"
        else:
            raw = 0.5
            rationale = "Default heuristic applied"

        if any(
            not status["present"] and status["required"]
            for status in deliverables.values()
        ):
            raw = max(raw - 0.1, 0.0)
            rationale += " | penalty for missing required deliverables"

        return raw, rationale

    # ------------------------------------------------------------------
    # Flagging & reporting
    # ------------------------------------------------------------------
    def _generate_flags(
        self,
        metrics: Dict[str, Any],
        deliverables: Dict[str, Dict[str, Any]],
    ) -> List[str]:
        flags: List[str] = []
        missing = [
            name
            for name, status in deliverables.items()
            if status["required"] and not status["present"]
        ]
        if missing:
            flags.append(f"Missing required deliverables: {', '.join(missing)}")

        coverage = metrics.get("coverage", 0.0)
        if coverage < 0.6:
            flags.append(f"Low test coverage detected ({coverage:.2f})")

        lint = metrics.get("lint_warnings", 0)
        if lint > 10:
            flags.append(f"High lint warning count ({lint})")

        return flags
