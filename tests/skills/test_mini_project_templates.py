"""Tests for mini-project templates and rubrics."""

import pytest

from src.modules.skills.evaluation.template_registry import MiniProjectTemplateRegistry


@pytest.fixture
def registry():
    return MiniProjectTemplateRegistry()


def test_registry_lists_default_templates(registry):
    templates = registry.list_templates()
    ids = {template.template_id for template in templates}
    assert "fullstack-rest-api" in ids
    assert "data-pipeline-etl" in ids


def test_template_deliverables_cover_core_artifacts(registry):
    template = registry.get_template("fullstack-rest-api")
    required_names = {d.name for d in template.deliverables if d.required}
    assert {"API Source Code", "API Tests", "README"}.issubset(required_names)
    assert template.expected_artifacts, "expected_artifacts must not be empty"


def test_rubric_weights_sum_to_one(registry):
    template = registry.get_template("data-pipeline-etl")
    total_weight = sum(criterion.weight for criterion in template.rubric)
    assert pytest.approx(total_weight, rel=1e-3) == 1.0


def test_telemetry_hooks_include_confidence(registry):
    template = registry.get_template("fullstack-rest-api")
    hook_names = {hook.name for hook in template.telemetry_hooks}
    assert "runtime-metrics" in hook_names
    assert any("confidence" in metric for hook in template.telemetry_hooks for metric in hook.metrics)
