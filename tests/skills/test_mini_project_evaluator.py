"""Tests for mini-project evaluation pipeline."""

import uuid

from src.modules.skills.evaluation import (
    MiniProjectTemplateRegistry,
    MiniProjectEvaluator,
    MiniProjectSubmission,
    SubmissionArtifact,
)


def _build_submission(template_id: str) -> MiniProjectSubmission:
    artifacts = [
        SubmissionArtifact(path="src/api/app.py", artifact_type="code"),
        SubmissionArtifact(path="tests/test_api.py", artifact_type="tests"),
        SubmissionArtifact(path="README.md", artifact_type="docs"),
        SubmissionArtifact(path="Dockerfile", artifact_type="infra"),
    ]
    return MiniProjectSubmission(
        submission_id=str(uuid.uuid4()),
        learner_id="learner-1",
        template_id=template_id,
        artifacts=artifacts,
    )


def test_evaluator_scores_submission():
    registry = MiniProjectTemplateRegistry()
    evaluator = MiniProjectEvaluator(registry)
    submission = _build_submission("fullstack-rest-api")

    result = evaluator.evaluate_submission(submission)

    assert result.template_id == "fullstack-rest-api"
    assert 0 <= result.total_score <= 1
    assert result.missing_deliverables == []
    assert result.rubric_scores, "rubric scores must exist"
    assert result.telemetry, "telemetry should be populated"


def test_missing_deliverables_flagged():
    registry = MiniProjectTemplateRegistry()
    evaluator = MiniProjectEvaluator(registry)
    submission = _build_submission("data-pipeline-etl")
    # drop docs deliverable
    submission.artifacts = [art for art in submission.artifacts if art.artifact_type != "docs"]

    result = evaluator.evaluate_submission(submission)

    assert result.missing_deliverables
    assert any("Missing required deliverables" in flag for flag in result.flags)


def test_low_coverage_triggers_flag():
    registry = MiniProjectTemplateRegistry()
    evaluator = MiniProjectEvaluator(registry)
    submission = MiniProjectSubmission(
        submission_id=str(uuid.uuid4()),
        learner_id="learner-2",
        template_id="fullstack-rest-api",
        artifacts=[SubmissionArtifact(path="src/app.py", artifact_type="code")],
    )

    result = evaluator.evaluate_submission(submission)

    assert any("Low test coverage" in flag for flag in result.flags)
