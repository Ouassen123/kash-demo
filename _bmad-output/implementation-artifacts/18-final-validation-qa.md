# Story 18: Final validation & QA

Status: completed

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a QA lead, I want a final validation workspace that runs end-to-end checks against pilot criteria so we can certify readiness before deployment and surface any regressions.

## Acceptance Criteria

1. Run automated test suites covering knowledge, abilities, skills, and intelligence signals to ensure data flow integrity.
2. Provide manual QA checklists for the pilot team with traceable outcomes tied to each epic story.
3. Log validation results with timestamps and responsible reviewers so compliance reporting captures approvals.

## Tasks / Subtasks

- [x] Task 1: Define test suites and automation scripts aligned with each module’s deliverables.
  - [x] Subtask 1.1: Include regression detection for Story 1-5, 2-1 through 2-4, 3-1 through 3-3, and 4-1 through 4-4.
- [x] Task 2: Collect manual pilot validation notes and link them to sprint-status readiness markers.
  - [x] Subtask 2.1: Provide reviewer annotations for any blocked checks before deployment.
- [x] Task 3: Output validation dashboards/reports that connect to the Admin Panel reporting story.

## Dev Notes

- Write reusable QA helpers in `yes/modules/operations/qa`, sharing dataset references with intelligence, skills, and abilities stories.
- Capture environment metadata (pilot site, dataset snapshot) each time validation runs.
- Integrate regression alerts with admin reporting for transparency.

### Project Structure Notes

- Host QA automation under `yes/modules/operations/qa/validation` with dedicated dashboards in `yes/modules/operations/qa/dashboard`.
- Align artifacts with admin reporting exports to keep pilot oversight consistent.
- Document compliance requirements directly inside QA scripts for auditability.

### References

- [Source: planning-artifacts/epic-finalisation.md#Stories]
- [Source: implementation-artifacts/sprint-status.yaml#development_status]

## Dev Agent Record

### Agent Model Used

gpt-4o

### Debug Log References

- Derived final validation story from epic and sprint metadata

### Completion Notes List

- Implemented operations QA module with reusable validation runner and dataclasses
- Added automated export pipeline for validation JSON/CSV evidence artifacts
- Added manual checklist + audit exporters for pilot reviewer sign-off
- Added scripted entrypoint for final validation workflow (`scripts/run_final_validation.py`)
- Added pilot manual QA and automation documentation for deployment teams

### File List

- 18-final-validation-qa.md
- src/modules/operations/qa/__init__.py
- src/modules/operations/qa/validation/__init__.py
- src/modules/operations/qa/validation/validation_runner.py
- src/modules/operations/qa/dashboard/__init__.py
- src/modules/operations/qa/dashboard/reporting.py
- src/modules/operations/__init__.py
- scripts/run_final_validation.py
- docs/pilot-deployment/manual-qa-checklist.md
- docs/pilot-deployment/qa-automation.md
- test_final_validation_qa.py
