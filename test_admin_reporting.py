"""Smoke tests for admin panel and reporting services."""

from src.modules.operations.admin import AccessControlService, AdminPanelService
from src.modules.operations.reporting import PilotReportingService, ReportRequest


def test_admin_snapshot_contains_modules() -> None:
    snapshot = AdminPanelService(pilot_site="combined").build_snapshot()
    assert snapshot["overall_status"] == "ready"
    assert len(snapshot["modules"]) >= 4


def test_reporting_service_generates_artifacts() -> None:
    service = PilotReportingService(output_dir="./reports-test")
    artifact = service.generate_report(
        ReportRequest(report_type="weekly", pilot_site="combined", reviewer="ops")
    )
    assert artifact["report_id"]
    assert artifact["json_path"].endswith(".json")
    assert artifact["csv_path"].endswith(".csv")


def test_access_control_logs_decisions() -> None:
    access = AccessControlService(audit_log_path="./reports-test/access_audit.jsonl")
    assert access.authorize("u-1", "admin", "view_sensitive_logs", "audit") is True
    assert access.authorize("u-2", "reviewer", "view_sensitive_logs", "audit") is False
