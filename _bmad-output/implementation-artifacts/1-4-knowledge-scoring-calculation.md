# Story 1.4: Knowledge scoring calculation

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Knowledge architect, I want to compute a transparent, multi-signal knowledge score that combines the NLP CV analysis, taxonomy enrichment, and adaptive quiz confidence so stakeholders see a single metric for placement decisions.

## Acceptance Criteria

1. Design a scoring formula that weights structured CV insights, taxonomy confidence, and quiz mastery while remaining configurable for future signal additions.
2. The score calculation records component-level contributions and confidence intervals to aid downstream analytics and QA.
3. Expose scoring outputs via an API so intelligence and frontend stories can pull the latest knowledge scores without duplicating logic.

## Tasks / Subtasks

- [ ] Task 1 (AC 1): Define modular scoring pipeline that consumes normalized attributes, taxonomy enrichments, and quiz results.
  - [ ] Subtask 1.1: Create configuration layer to tune weights per signal and preserve a audit log for weight changes.
- [ ] Task 2 (AC 2): Instrument scoring pipeline to emit component breakdowns, confidence flags, and raw inputs for auditing.
  - [ ] Subtask 2.1: Store these diagnostics alongside the final score for analysis by QA and analytics teams.
- [ ] Task 3 (AC 3): Build a REST/GraphQL endpoint for other services to request knowledge scores with cache-friendly parameters.
  - [ ] Subtask 3.1: Provide fallback behavior when quiz or taxonomy data are temporarily unavailable, logging the gap.

## Dev Notes

- Align scoring weights with the Knowledge scoring data model so adaptive quiz and intelligence modules consume consistent values.
- Keep scoring logic separate from data ingestion to simplify future experimentation and versioning.
- Document how each signal (CV, taxonomy, quiz) influences scores to help product communicate fairness.

### Project Structure Notes

- Place scoring services in `yes/modules/knowledge/scoring` with clear interfaces for signal inputs.
- Store weight configurations and audit logs in `yes/modules/knowledge/scoring/config` so changes stay centralized.
- Expose scoring dashboards or logs for QA stories and future analytics consumption.

### References

- [Source: planning-artifacts/epic-knowledge.md#Stories]
- [Source: implementation-artifacts/sprint-status.yaml#development_status]

## Dev Agent Record

### Agent Model Used

gpt-4o

### Debug Log References

- Synthesized scoring requirements from Knowledge epic and sprint status

### Completion Notes List

- Captured multi-signal scoring expectations
- Included diagnostics and API connectivity notes

### File List

- 1-4-knowledge-scoring-calculation.md
