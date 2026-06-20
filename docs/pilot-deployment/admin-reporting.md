# Admin Panel & Reporting Operations Guide

## Objectives
- Provide centralized readiness view for knowledge/abilities/skills/intelligence/operations
- Export pilot governance reports in JSON and CSV
- Enforce role-based access and maintain audit trail

## Services
- Admin readiness snapshot: `src/modules/operations/admin/panel.py`
- Report exporter: `src/modules/operations/reporting/exporter.py`
- Access control + audit: `src/modules/operations/admin/access_control.py`

## Typical flow
1. Build snapshot from `AdminPanelService`.
2. Generate periodic report from `PilotReportingService`.
3. Gate sensitive actions with `AccessControlService.authorize(...)`.
4. Preserve generated access logs for compliance review.

## Suggested weekly report job
```bash
python -c "from src.modules.operations.reporting import PilotReportingService, ReportRequest; print(PilotReportingService().generate_report(ReportRequest(report_type='weekly', pilot_site='combined', reviewer='ops-lead')))"
```

## Audit expectation
- Keep `reports/access_audit.jsonl` retained for pilot period.
- Investigate denied accesses and unusual spikes in denied actions.
