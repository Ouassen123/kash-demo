"""Registry for mini-project evaluation templates and rubrics."""

from __future__ import annotations

from typing import Dict, List, Optional

from .template_models import (
    Deliverable,
    RubricCriterion,
    TelemetryHook,
    MiniProjectTemplate,
)


class MiniProjectTemplateRegistry:
    """Provides access to registered mini-project templates."""

    def __init__(self) -> None:
        self._templates: Dict[str, MiniProjectTemplate] = {}
        self._load_default_templates()

    # ------------------------------------------------------------------
    # Template management
    # ------------------------------------------------------------------
    def list_templates(self) -> List[MiniProjectTemplate]:
        """Return all registered templates."""
        return list(self._templates.values())

    def get_template(self, template_id: str) -> MiniProjectTemplate:
        """Return template by ID or raise KeyError."""
        if template_id not in self._templates:
            raise KeyError(f"Template '{template_id}' not found")
        return self._templates[template_id]

    def register_template(self, template: MiniProjectTemplate) -> None:
        """Register or update a template definition."""
        template.validate_weights()
        self._templates[template.template_id] = template

    # ------------------------------------------------------------------
    # Default templates
    # ------------------------------------------------------------------
    def _load_default_templates(self) -> None:
        self.register_template(self._create_fullstack_rest_api_template())
        self.register_template(self._create_data_pipeline_etl_template())

    def _create_fullstack_rest_api_template(self) -> MiniProjectTemplate:
        deliverables = [
            Deliverable(
                name="API Source Code",
                description="Backend service implementing REST endpoints with business logic",
                file_patterns=["app/**/*.py", "src/**/*.py", "app/**/*.ts", "src/**/*.ts"],
            ),
            Deliverable(
                name="API Tests",
                description="Automated unit/integration tests covering endpoints and edge cases",
                file_patterns=["tests/**/*.py", "tests/**/*.ts"],
            ),
            Deliverable(
                name="README",
                description="Setup instructions, API contract, environment variables",
                file_patterns=["README.md"],
            ),
            Deliverable(
                name="Deployment Manifest",
                description="Container/Dockerfile or IaC manifest for deployment",
                required=False,
                file_patterns=["Dockerfile", "infra/**/*.tf"],
            ),
        ]

        rubric = [
            RubricCriterion(
                name="API Correctness",
                description="Endpoints satisfy contract, validation, and error handling",
                weight=0.35,
                scoring_scale={
                    "excellent": "All endpoints pass automated tests with strong validation",
                    "good": "Minor gaps discovered but overall correct",
                    "fair": "Multiple validation or logic issues detected",
                    "poor": "Fails to satisfy core contract",
                },
                automation_hint="Use contract tests + schema comparison",
            ),
            RubricCriterion(
                name="Code Quality",
                description="Code is modular, readable, and adheres to style guide",
                weight=0.25,
                scoring_scale={
                    "excellent": "Consistent patterns, clear abstractions, zero lint warnings",
                    "good": "Mostly clean with minor refactors suggested",
                    "fair": "Notable duplication or smells",
                    "poor": "Difficult to follow / lacks structure",
                },
                automation_hint="Run lint, cyclomatic complexity, duplication scan",
            ),
            RubricCriterion(
                name="Tests & Coverage",
                description="Automated tests cover key paths and edge cases",
                weight=0.2,
                scoring_scale={
                    "excellent": ">=90% coverage, integration tests pass",
                    "good": "70-90% coverage, few gaps",
                    "fair": "<70% coverage or flaky tests",
                    "poor": "Lacks automated testing",
                },
                automation_hint="Collect pytest/jest coverage report",
            ),
            RubricCriterion(
                name="Operational Readiness",
                description="Deployability, configuration, and observability",
                weight=0.2,
                scoring_scale={
                    "excellent": "Automated deploy + metrics and health checks",
                    "good": "Deploy guide exists, minimal ops hooks",
                    "fair": "Manual steps, missing metrics",
                    "poor": "Not deployable",
                },
                automation_hint="Inspect Dockerfile, health routes, logging",
            ),
        ]

        telemetry_hooks = [
            TelemetryHook(
                name="runtime-metrics",
                description="Capture API latency, error rates, and confidence",
                metrics=["latency_p95", "error_rate", "confidence_score"],
            ),
            TelemetryHook(
                name="static-analysis",
                description="Collect lint warnings, complexity, security flags",
                metrics=["lint_warnings", "cyclomatic_complexity", "security_findings"],
            ),
        ]

        success_criteria = [
            "Implements CRUD endpoints with pagination and filtering",
            "Includes automated test suite runnable via single command",
            "Provides deploy instructions + env variable schema",
        ]

        return MiniProjectTemplate(
            template_id="fullstack-rest-api",
            title="Full-stack REST API",
            difficulty="intermediate",
            summary="Build a production-ready REST API with tests and deployment metadata",
            expected_artifacts=["src/", "tests/", "README.md", "Dockerfile"],
            deliverables=deliverables,
            rubric=rubric,
            telemetry_hooks=telemetry_hooks,
            success_criteria=success_criteria,
            competency_tags=["backend", "api-design", "testing", "devops"],
        )

    def _create_data_pipeline_etl_template(self) -> MiniProjectTemplate:
        deliverables = [
            Deliverable(
                name="Pipeline DAG",
                description="Code/config describing ETL stages",
                file_patterns=["dags/**/*.py", "pipelines/**/*.yml"],
            ),
            Deliverable(
                name="Data Contracts",
                description="Schema definitions, validation rules, sample datasets",
                file_patterns=["schemas/**/*.json", "data/*.csv"],
            ),
            Deliverable(
                name="Monitoring Notebook",
                description="Explains data quality metrics, alert thresholds",
                required=False,
                file_patterns=["notebooks/**/*.ipynb"],
            ),
        ]

        rubric = [
            RubricCriterion(
                name="Pipeline Accuracy",
                description="Transforms meet spec and unit tests verify calculations",
                weight=0.4,
                scoring_scale={
                    "excellent": "All stages validated with golden datasets",
                    "good": "Minor rounding or formatting issues",
                    "fair": "Frequent mismatches detected",
                    "poor": "Fails to reproduce expected output",
                },
                automation_hint="Run golden dataset comparison + data diff",
            ),
            RubricCriterion(
                name="Reliability & Scheduling",
                description="Handles retries, backfills, and failure alerts",
                weight=0.25,
                scoring_scale={
                    "excellent": "Idempotent with retry/backoff and alerting hooks",
                    "good": "Basic retry behavior, limited alerting",
                    "fair": "Manual intervention required",
                    "poor": "No reliability features",
                },
                automation_hint="Inspect DAG metadata + config lint",
            ),
            RubricCriterion(
                name="Data Quality Telemetry",
                description="Captures quality metrics, anomaly detection",
                weight=0.2,
                scoring_scale={
                    "excellent": "Automated checks push metrics with confidence",
                    "good": "Checks exist but no alert thresholds",
                    "fair": "Manual quality validation",
                    "poor": "No telemetry",
                },
                automation_hint="Parse expectations configs (e.g., Great Expectations)",
            ),
            RubricCriterion(
                name="Documentation",
                description="Explains lineage, data contracts, runbook",
                weight=0.15,
                scoring_scale={
                    "excellent": "Complete runbook + diagrams",
                    "good": "Readable README with key info",
                    "fair": "Sparse documentation",
                    "poor": "Missing",
                },
                automation_hint="Check README sections + diagrams",
            ),
        ]

        telemetry_hooks = [
            TelemetryHook(
                name="data-quality",
                description="Capture null rates, schema drift confidence",
                metrics=["null_ratio", "schema_drift_score", "confidence_score"],
            ),
            TelemetryHook(
                name="pipeline-runtime",
                description="Track run duration, retries, resource usage",
                metrics=["run_time_seconds", "retry_count", "cpu_percent"],
            ),
        ]

        success_criteria = [
            "ETL job orchestrated via DAG/scheduler with documented triggers",
            "Data contracts stored with schema evolution notes",
            "Quality telemetry exported for dashboards",
        ]

        return MiniProjectTemplate(
            template_id="data-pipeline-etl",
            title="Data Pipeline ETL",
            difficulty="advanced",
            summary="Implement robust ETL workflows with quality telemetry",
            expected_artifacts=["dags/", "schemas/", "README.md"],
            deliverables=deliverables,
            rubric=rubric,
            telemetry_hooks=telemetry_hooks,
            success_criteria=success_criteria,
            competency_tags=["data-engineering", "etl", "observability"],
        )
