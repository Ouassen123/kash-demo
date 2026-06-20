"""Structured reporting utilities for mini-project evaluations."""

from __future__ import annotations

from typing import Dict, Any, List

from .evaluator import EvaluationResult


class EvaluationReportBuilder:
    """Converts evaluation results into dashboard-friendly payloads."""

    def build_report(self, result: EvaluationResult) -> Dict[str, Any]:
        rubric_rows = [
            {
                "criterion": score.name,
                "weight": score.weight,
                "raw_score": score.raw_score,
                "weighted_score": score.weighted_score,
                "rationale": score.rationale,
            }
            for score in result.rubric_scores
        ]

        discrepancies = self._find_discrepancies(result)

        return {
            "submission_id": result.submission_id,
            "template_id": result.template_id,
            "total_score": result.total_score,
            "rubric": rubric_rows,
            "flags": result.flags,
            "missing_deliverables": result.missing_deliverables,
            "needs_human_review": bool(result.flags or discrepancies),
            "discrepancies": discrepancies,
            "summary": {
                "score_percent": round(result.total_score * 100, 1),
                "flag_count": len(result.flags),
                "telemetry": result.telemetry,
            },
        }

    def _find_discrepancies(self, result: EvaluationResult) -> List[Dict[str, Any]]:
        discrepancies: List[Dict[str, Any]] = []
        for score in result.rubric_scores:
            if score.raw_score < 0.6:
                discrepancies.append(
                    {
                        "type": "low_score",
                        "criterion": score.name,
                        "raw_score": score.raw_score,
                        "rationale": score.rationale,
                    }
                )

        for missing in result.missing_deliverables:
            discrepancies.append(
                {
                    "type": "missing_deliverable",
                    "deliverable": missing,
                    "message": f"{missing} not submitted",
                }
            )
        return discrepancies
