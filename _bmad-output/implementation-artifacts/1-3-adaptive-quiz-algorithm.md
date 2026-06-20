# Story 1.3: Adaptive quiz algorithm

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Knowledge contributor, I want the system to generate adaptive quiz questions from the normalized CV analysis output so that learners receive targeted challenges aligned with their knowledge profiles and the scoring model can validate knowledge signals.

## Acceptance Criteria

1. Questions are derived from normalized CV attributes and mapped to difficulty tiers, adapting in real time as learners provide answers.
2. The quiz algorithm exposes scoring hooks so outputs can be consumed by the Knowledge scoring calculation for calibration.
3. Learner responses feed back into the knowledge data model, enriching future recommendations and reinforcing confidence measures.

## Tasks / Subtasks

- [ ] Task 1 (AC 1): Design mapping from CV attributes to question templates and difficulty tiers.
  - [ ] Subtask 1.1: Annotate taxonomy links (ESCO/O*NET) so quiz questions stay grounded in validated skill definitions.
- [ ] Task 2 (AC 2): Implement scoring service that emits confidence and mastery metrics for downstream scoring.
  - [ ] Subtask 2.1: Provide API for scoring calculation to pull latest metrics without duplicating logic.
- [ ] Task 3 (AC 3): Store quiz interactions alongside learner profiles and update knowledge metadata for future stories.
  - [ ] Subtask 3.1: Track question usage and learner improvement to help QA and analytics.

## Dev Notes

- Reuse the preprocessing pipeline from the NLP CV analysis engine so quizzes always reflect the freshest data.
- Keep question templates versioned together with taxonomy enrichments to avoid drift in question semantics.
- Ensure the adaptive logic can toggle between exploratory and mastery paths based on knowledge confidence scores.

### Project Structure Notes

- Host quiz orchestration under `yes/modules/knowledge/quiz` next to the scoring services.
- Keep question templates and taxonomy maps under `yes/modules/knowledge/quiz/templates` for easy updates.
- Coordinate with the frontend evaluation interface to surface quiz prompts consistent with knowledge scoring UI.

### References

- [Source: planning-artifacts/epic-knowledge.md#Stories]
- [Source: implementation-artifacts/sprint-status.yaml#development_status]

## Dev Agent Record

### Agent Model Used

gpt-4o

### Debug Log References

- Crafted adaptive quiz story from Knowledge epic context and sprint status

### Completion Notes List

- Documented adaptive quiz requirements aligned with scoring data model
- Linked acceptance criteria to downstream scoring hooks

### File List

- 1-3-adaptive-quiz-algorithm.md
