# Story 2.1: Text-based cognitive tests

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an Abilities assessor, I want scripted text-based cognitive tests that surface reasoning, comprehension, and creativity markers so we can quantify cognitive behavior across learner cohorts and feed the results into the Abilities Module scorecard.

## Acceptance Criteria

1. Deliver a configurable text-test runner that sequences prompts, captures free-form responses, and normalizes them for automated scoring.
2. Provide scoring rubrics that tag responses with cognitive dimensions (logic, creativity, persistence) and export structured metrics for analytics.
3. Expose an API to retrieve completed session transcripts, scored metrics, and reliability metadata for downstream stories.

## Tasks / Subtasks

- [ ] Task 1: Build prompt orchestration service that loads scenario templates and executes them in order while tracking time and interaction metadata.
  - [ ] Subtask 1.1: Ensure prompt scripts can be localized and versioned alongside the Abilities Module.
- [ ] Task 2: Implement scoring pipeline that maps answers to cognitive dimensions and flags low-confidence or inconsistent responses.
  - [ ] Subtask 2.1: Emit raw scores plus confidence bands for transparency.
- [ ] Task 3: Persist transcripts, metrics, and metadata so other stories (e.g., voice recording interface, multimodal fusion) can reuse the same session IDs.

## Dev Notes

- Align cognitive dimension definitions with the Abilities Module glossary so intelligence and skills stories interpret scores consistently.
- Design storage formats that allow later manual review or auditing by QA.
- Provide instrumentation for evaluating prompt effectiveness (drop-off rates, average completion time).

### Project Structure Notes

- Create services under `yes/modules/abilities/text-tests` and keep prompt scripts, scoring rules, and storage adapters together.
- Keep configuration for scoring weights adjacent to the stories that consume them to prevent drift.
- Surface session IDs so the voice recording and multimodal stories can link their data back to these tests.

### References

- [Source: planning-artifacts/epic-abilities.md#Stories]
- [Source: implementation-artifacts/sprint-status.yaml#development_status]

## Dev Agent Record

### Agent Model Used

gpt-4o

### Debug Log References

- Captured Abilities Module text-based cognitive test requirements from epics and sprint status

### Completion Notes List

- Scoped prompt orchestration, scoring, and persistence expectations
- Linked story to downstream integration points

### File List

- 2-1-text-based-cognitive-tests.md
