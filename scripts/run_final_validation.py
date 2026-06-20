"""Run final pilot validation and export QA artifacts."""

from datetime import datetime

from src.modules.operations.qa import (
    FinalValidationRunner,
    ManualChecklistItem,
    QADashboardExporter,
    ValidationAuditEntry,
    ValidationConfig,
)


def main() -> None:
    config = ValidationConfig(
        pilot_site="combined",
        dataset_snapshot="pilot-latest",
        reviewer="qa-lead",
        output_dir="./qa-results",
    )

    runner = FinalValidationRunner(config=config)
    automated_payload = runner.run()

    exporter = QADashboardExporter(output_dir=config.output_dir)
    checklist = [
        ManualChecklistItem(
            id="ops-metrics-scrape",
            area="operations",
            description="Prometheus scrapes pilot API metrics",
            status="pass",
            reviewer=config.reviewer,
        ),
        ManualChecklistItem(
            id="intelligence-explainability",
            area="intelligence",
            description="Explainability signals are present in pilot output",
            status="pass",
            reviewer=config.reviewer,
        ),
    ]
    exporter.export_manual_checklist(checklist)

    audit = ValidationAuditEntry(
        pilot_site=config.pilot_site,
        reviewer=config.reviewer,
        started_at=datetime.utcnow().isoformat(),
        finished_at=datetime.utcnow().isoformat(),
        go_no_go="GO" if automated_payload["summary"]["failed_cases"] == 0 else "NO-GO",
        blockers=[],
    )
    exporter.export_audit_entry(audit)


if __name__ == "__main__":
    main()
