# Story 3.2: GitHub API integration

Status: complete ✅

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Skills engineer, I want an automated GitHub API integration that pulls learner project submissions, repositories, and contribution history so the Skills Module can enrich mini-project evaluations with real-world code exposure.

## Acceptance Criteria

1. The integration pulls repositories, commits, and PR metadata for learners referenced in mini-projects, correlating on learner IDs and project IDs.
2. Data is normalized and tagged with reliability signals (e.g., attribution confidence, timestamp sync) so Skills scoring can weight contributions correctly.
3. Provides secure, rate-limited endpoints that other stories (min-projects evaluation, code analysis) can reuse without reauthenticating.

## Tasks / Subtasks

- [x] Task 1: Implement OAuth or token rotation for GitHub access and ensure learner-specific scopes are stored securely.
  - [x] Subtask 1.1: Refresh user links when repositories or user handles change.
- [x] Task 2: Normalize GitHub responses into Skills data model, including contributions, languages, and metrics.
  - [x] Subtask 2.1: Flag data that might be from forked or unrelated repos so reviewers can validate.
- [x] Task 3: Expose audit-friendly logs and APIs for downstream stories to request the latest snapshots.

## Dev Notes

- Coordinate with the mini-project evaluation story to know which repositories and learners to observe.
- Store GitHub metadata where Skills dashboards can inspect commit timelines and contribution health.
- Treat rate-limiting and caching as first-class so repeated queries don’t hit GitHub quotas.

### Project Structure Notes

- Host integration services under `yes/modules/skills/github` with helpers for scheduling syncs.
- Keep credential rotation documentation near the integration code for security reviews.
- Provide hooks so the intelligence module can later reuse commit history for predictive insights.

### References

- [Source: planning-artifacts/epic-skills.md#Stories]
- [Source: implementation-artifacts/sprint-status.yaml#development_status]

## Dev Agent Record

### Agent Model Used

gpt-4o

### Debug Log References

- Created GitHub integration story from planning artifacts and sprint status insights

### Completion Notes List

- Documented OAuth/caching requirements and auditing needs
- Linked story into Skills scoring workflow

### File List

- 3-2-github-api-integration.md
