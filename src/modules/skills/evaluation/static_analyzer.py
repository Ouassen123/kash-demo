"""Lightweight static analysis utilities for mini-project submissions."""

from __future__ import annotations

from typing import Dict, Any

from .submission_models import MiniProjectSubmission
from .template_models import MiniProjectTemplate


class StaticAnalyzer:
    """Runs heuristics over submitted artifacts to produce metrics for scoring."""

    def run_checks(self, submission: MiniProjectSubmission, template: MiniProjectTemplate) -> Dict[str, Any]:
        artifact_summary = submission.artifact_summary()
        tests = artifact_summary.get("tests", 0)
        docs = artifact_summary.get("docs", 0)
        infra = artifact_summary.get("infra", 0)
        code = artifact_summary.get("code", 0)

        metrics = {
            "files_analyzed": sum(artifact_summary.values()),
            "tests_count": tests,
            "docs_count": docs,
            "infra_count": infra,
            "code_count": code,
            "coverage": self._estimate_coverage(tests, code),
            "lint_warnings": self._estimate_lint_warnings(submission),
            "deployment_signal": 1.0 if infra else 0.5 if docs else 0.2,
            "documentation_signal": 1.0 if docs else 0.4,
            "correctness_signal": 0.8 if tests and code else 0.5,
        }

        # Map telemetry hooks to metric names for downstream usage
        telemetry = {}
        for hook in template.telemetry_hooks:
            telemetry[hook.name] = {metric: metrics.get(metric) for metric in hook.metrics}

        metrics["telemetry"] = telemetry
        return metrics

    def _estimate_coverage(self, tests: int, code: int) -> float:
        if not code:
            return 0.0
        ratio = min(tests / max(code, 1), 1.0)
        return round(0.6 + 0.4 * ratio, 3) if tests else 0.4

    def _estimate_lint_warnings(self, submission: MiniProjectSubmission) -> int:
        # Use artifact metadata hints if provided
        total_warnings = 0
        for artifact in submission.artifacts:
            total_warnings += int(artifact.metadata.get("lint_warnings", 0))
        return total_warnings
