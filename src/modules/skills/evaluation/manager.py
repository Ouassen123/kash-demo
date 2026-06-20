"""High-level manager that runs evaluations and stores results."""

from __future__ import annotations

from typing import Dict, Any, List, Optional

from .template_registry import MiniProjectTemplateRegistry
from .submission_models import MiniProjectSubmission
from .evaluator import MiniProjectEvaluator
from .reporting import EvaluationReportBuilder
from .evaluation_store import EvaluationStore, StoredEvaluation
from .static_analyzer import StaticAnalyzer


class MiniProjectEvaluationManager:
    """Coordinates submission evaluation, reporting, and persistence."""

    def __init__(
        self,
        template_registry: Optional[MiniProjectTemplateRegistry] = None,
        evaluator: Optional[MiniProjectEvaluator] = None,
        report_builder: Optional[EvaluationReportBuilder] = None,
        store: Optional[EvaluationStore] = None,
    ) -> None:
        self.template_registry = template_registry or MiniProjectTemplateRegistry()
        self.evaluator = evaluator or MiniProjectEvaluator(
            template_registry=self.template_registry,
            static_analyzer=StaticAnalyzer(),
        )
        self.report_builder = report_builder or EvaluationReportBuilder()
        self.store = store or EvaluationStore()

    def process_submission(self, submission: MiniProjectSubmission) -> Dict[str, Any]:
        """Run evaluation pipeline and persist results."""
        evaluation = self.evaluator.evaluate_submission(submission)
        dashboard_report = self.report_builder.build_report(evaluation)

        stored_payload = StoredEvaluation(
            submission_id=evaluation.submission_id,
            learner_id=submission.learner_id,
            template_id=submission.template_id,
            template_title=self.template_registry.get_template(submission.template_id).title,
            total_score=evaluation.total_score,
            summary_report=evaluation.summary_report,
            report=dashboard_report,
        )
        self.store.save(stored_payload)

        return {
            "evaluation": evaluation,
            "report": dashboard_report,
        }

    def get_report(self, submission_id: str) -> Optional[Dict[str, Any]]:
        record = self.store.get(submission_id)
        return record.report if record else None

    def list_recent_reports(self, limit: int = 10) -> List[Dict[str, Any]]:
        return [record.report for record in self.store.list_recent(limit)]

    def list_reports_for_learner(self, learner_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        return [record.report for record in self.store.list_by_learner(learner_id, limit)]
