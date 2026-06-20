# Story 3.1: Mini-projects evaluation

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Skills coach, I want structured mini-project evaluations that capture real developer outputs against competence rubrics so we can measure hands-on ability and feed those signals into the Skills Module to complement Abilities data.

## Acceptance Criteria

1. Mini-project templates include defined success criteria, expected code artifacts, and telemetry hooks so judges can rate submissions objectively.
2. Evaluation pipelines automatically compare submissions to the rubric, highlight discrepancies, and store scoring rationale for transparency.
3. Collected artifacts integrate with Skills dashboards so reviewers can replay or inspect submissions alongside summary metrics.

## Tasks / Subtasks

- [x] Task 1: Define project templates and scoring rubrics aligned with the Skills competency matrix.
  - [x] Subtask 1.1: Capture required deliverables (code file list, documentation, tests) for each mini-project.
- [x] Task 2: Build evaluation automation that ingests submitted artifacts, runs static analysis, and populates rubric scores.
  - [x] Subtask 2.1: Emit structured summary reports and flag items requiring human re-review.
- [x] Task 3: Surface evaluations in Skills dashboards with artifact links and reviewer notes.
  - [x] Subtask 3.1: Persist evaluation metadata so Intelligence stories can reference them later.

## Dev Notes

- Keep project templates and rubrics versioned near scoring logic to avoid drift.
- Coordinate with the GitHub API integration story so submissions and evidence can be retrieved automatically.
- Include traceability metadata (e.g., project ID, reviewer, timestamp) for QA and audits.

### Project Structure Notes

- Host evaluation services under `yes/modules/skills/evaluation` with template storage and scoring helpers.
- Store rubric definitions alongside mini-project fixtures in `yes/modules/skills/evaluation/templates`.
- Use shared telemetry and logging utilities from Abilities stories to keep metrics comparable.

### References

- [Source: planning-artifacts/epic-skills.md#Stories]
- [Source: implementation-artifacts/sprint-status.yaml#development_status]

## Dev Agent Record

### Agent Model Used

gpt-4o

### Debug Log References

- Implemented template registry, evaluator pipeline, and dashboard integration for mini-project assessments.

### Completion Notes List

- Built template registry with deliverables, rubrics, and telemetry hooks.
- Added submission models, static analyzer, evaluator, reporting, store, manager, and dashboard helpers.
- Integrated `MiniProjectEvaluationManager` into `SkillsService` with submission + dashboard APIs.
- Verified new Skills tests (`test_mini_project_templates`, `test_mini_project_evaluator`) pass.

### Change Log

- Added `src/modules/skills/evaluation/` package (templates, submissions, analyzer, evaluator, reporting, store, manager, dashboard).
- Created tests `tests/skills/test_mini_project_templates.py` and `tests/skills/test_mini_project_evaluator.py`.
- Updated `src/modules/skills/skills_service.py` to expose mini-project evaluation APIs.

### File List

- src/modules/skills/evaluation/__init__.py
- src/modules/skills/evaluation/template_models.py
- src/modules/skills/evaluation/template_registry.py
- src/modules/skills/evaluation/submission_models.py
- src/modules/skills/evaluation/static_analyzer.py
- src/modules/skills/evaluation/evaluator.py
- src/modules/skills/evaluation/reporting.py
- src/modules/skills/evaluation/evaluation_store.py
- src/modules/skills/evaluation/manager.py
- src/modules/skills/evaluation/dashboard.py
- tests/skills/test_mini_project_templates.py
- tests/skills/test_mini_project_evaluator.py
- src/modules/skills/skills_service.py
- 3-1-mini-projects-evaluation.md
