# Story 17: Admin panel & reporting

Status: completed

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an operations lead, I want a centralized admin panel and reporting workspace so team leads can track pilot readiness, system health, and learner signals while aligning with compliance requirements.

## Acceptance Criteria

1. The panel surfaces real-time statuses for epics, readiness metrics for each module, and dashboards for learner progress with contextual annotations.
2. Reporting exports support CSV/JSON artifacts and scheduled summaries aligned with pilot milestones.
3. User permissions ensure only authorized stakeholders can access sensitive logs, with audit trails captured for each session.

## Tasks / Subtasks

- [x] Task 1: Build the admin portal layout with modules for knowledge, abilities, skills, and intelligence readiness.
  - [x] Subtask 1.1: Provide drill-down links into each story’s README, normalized data schema, and current status.
- [x] Task 2: Implement reporting pipelines that aggregate live metrics and export them per pilot requirements.
  - [x] Subtask 2.1: Schedule automated reports (e.g., weekly, pilot go/no-go) with email notifications.
- [x] Task 3: Harden access controls, session logging, and compliance-friendly reporting on data access.
  - [x] Subtask 3.1: Log role-based access and flag unusual activity for ops review.

## Dev Notes

- Mirror the Knowledge Module data model to ensure dashboards show the exact metrics developers emit.
- Reuse telemetry and audit utilities from other modules to avoid building duplicate logging.
- Align exports with pilot QA and analytics needs to reduce custom scripting.

### Project Structure Notes

- Place admin UI under `yes/modules/operations/admin` and report generators under `yes/modules/operations/reporting`.
- Keep permission schemes documented alongside the panel code so compliance reviews stay synchronized.
- Include connectors to pilot scheduling services for timeline visibility.

### References

- [Source: planning-artifacts/epic-finalisation.md#Stories]
- [Source: implementation-artifacts/sprint-status.yaml#development_status]

## Dev Agent Record

### Agent Model Used

gpt-4o

### Debug Log References

- Derived story from finalisation epic and sprint tracker

### Completion Notes List

- Implemented admin readiness service with module-level pilot status snapshots
- Implemented reporting exporter for JSON/CSV pilot governance reports
- Added RBAC access control service with JSONL audit logging
- Added admin/reporting operational guide and smoke tests

### File List

- 17-admin-panel-reporting.md
- src/modules/operations/admin/__init__.py
- src/modules/operations/admin/panel.py
- src/modules/operations/admin/access_control.py
- src/modules/operations/reporting/__init__.py
- src/modules/operations/reporting/exporter.py
- src/modules/operations/__init__.py
- docs/pilot-deployment/admin-reporting.md
- test_admin_reporting.py
