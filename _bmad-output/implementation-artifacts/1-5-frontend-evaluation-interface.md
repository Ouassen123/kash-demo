# Story 1.5: Frontend evaluation interface

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Knowledge facilitator, I want a unified frontend interface that surfaces NLP CV analysis results, taxonomy insights, and adaptive quiz performance so reviewers can inspect the Knowledge score with confidence and act on next steps.

## Acceptance Criteria

1. The interface displays normalized CV attributes, taxonomy matches, and confidence metadata in one view with clear source references.
2. Adaptive quiz feedback and knowledge scores surface alongside the analysis timeline so reviewers understand how each signal contributed.
3. UX flows include drill-downs to open the scoring calculation rationale and links to follow-up actions for scoring/quiz stories.

## Tasks / Subtasks

- [ ] Task 1: Wire frontend panels for CV analysis, taxonomy enrichment, and quiz diagnostics.
  - [ ] Subtask 1.1: Implement reusable data cards that highlight confidence levels and allow auditors to inspect raw inputs.
- [ ] Task 2: Provide contextual help and references explaining each metric and its derivation.
  - [ ] Subtask 2.1: Link help tooltips to documentation maintained alongside the Knowledge Module artifacts.
- [ ] Task 3: Enable action buttons (e.g., "Re-run NLP", "Flag for QA") tied to backend APIs for future automation.

## Dev Notes

- Align UI components with the Knowledge scoring data model so frontend and backend teams share terminology.
- Respect accessibility standards since reviewers will rely on this interface for high-stakes decisions.
- Optimize data loading to avoid redundant fetches of normalized CV results when multiple sections request them.

### Project Structure Notes

- Build components under `yes/modules/knowledge/ui/evaluation` and keep styles close to avoid drift.
- Document API contracts so the frontend knows which backend endpoints supply NLP, taxonomy, and quiz data.
- Coordinate release with Dev Story 1.1-1.4 to ensure backend endpoints exist by the time UI is wired.

### References

- [Source: planning-artifacts/epic-knowledge.md#Stories]
- [Source: implementation-artifacts/sprint-status.yaml#development_status]

## Dev Agent Record

### Agent Model Used

gpt-4o

### Debug Log References

- Generated frontend evaluation story aligned to Knowledge epic and sprint status

### Completion Notes List

- Defined interface requirements for Knowledge review workflows
- Ensured hooks exist for future automation actions

### File List

- 1-5-frontend-evaluation-interface.md
