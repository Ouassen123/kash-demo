"""Dashboard summaries for mini-project evaluations."""

from __future__ import annotations

from typing import Dict, Any, List

from .manager import MiniProjectEvaluationManager


class MiniProjectDashboard:
    """Provides digestible summaries for Skills dashboards."""

    def __init__(self, manager: MiniProjectEvaluationManager) -> None:
        self.manager = manager

    def overview(self, limit: int = 10) -> Dict[str, Any]:
        reports = self.manager.list_recent_reports(limit)
        if not reports:
            return {
                "recent_reports": [],
                "average_score": 0.0,
                "flagged_submissions": 0,
                "total": 0,
            }

        total_score = sum(report["total_score"] for report in reports)
        flagged = len([report for report in reports if report.get("flags")])

        return {
            "recent_reports": reports,
            "average_score": round(total_score / len(reports), 3),
            "flagged_submissions": flagged,
            "total": len(reports),
        }

    def submission_detail(self, submission_id: str) -> Dict[str, Any]:
        report = self.manager.get_report(submission_id)
        if not report:
            return {"error": "report_not_found", "submission_id": submission_id}
        return report

    def learner_history(self, learner_id: str, limit: int = 5) -> Dict[str, Any]:
        reports = self.manager.list_reports_for_learner(learner_id, limit)
        return {
            "learner_id": learner_id,
            "reports": reports,
        }
