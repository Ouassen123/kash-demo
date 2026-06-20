# Story 1.2: ESCO/O*NET integration

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Knowledge analyst, I want the CV analysis pipeline to enrich extracted skills and roles with ESCO/O*NET taxonomy links so that our scoring engine can reason over standardized job and skill identifiers for better benchmarking.

## Acceptance Criteria

1. Every normalized skill/role extracted from CVs includes a reference to the ESCO or O*NET canonical entry whenever a confident match exists.
2. Mappings are versioned and documented, enabling traceability back to specific taxonomies used for scoring.
3. Integration exposes an API or enrichment hook so downstream scoring and intelligence stories can consume taxonomy-augmented profiles without additional lookup layers.

## Tasks / Subtasks

- [ ] Task 1: Implement taxonomy lookup service that matches normalized CV attributes to ESCO/O*NET references.
  - [ ] Subtask 1.1: Cache taxonomy data locally and refresh from official sources.
- [ ] Task 2: Emit metadata (confidence, taxonomy URI, matched labels) alongside analysis results.
  - [ ] Subtask 2.1: Log mismatches and fallback strategies.
- [ ] Task 3: Provide documentation and sample dataset showing enriched output for knowledge scoring.

## Dev Notes

- Align taxonomy enrichment with the Knowledge scoring calculation so they speak the same data contract.
- Reuse language detection from Story 1.1 to ensure taxonomy mappings respect CV locale differences.
- Default to ESCO when both taxonomies match; document fallbacks explicitly.

### Project Structure Notes

- Encapsulate taxonomy logic under `yes/modules/knowledge/taxonomy` with well-documented entry points.
- Keep enrichment metadata close to the NLP pipeline outputs so scoring, quiz, and intelligence modules can pick it up easily.

### References

- [Source: planning-artifacts/epic-knowledge.md#Stories]
- [Source: implementation-artifacts/sprint-status.yaml#development_status]

## Dev Agent Record

### Agent Model Used

gpt-4o

### Debug Log References

- Created story from epic context and sprint status

### Completion Notes List

- Captured ESCO/O*NET integration expectations in detail
- Ensured references to taxonomy data for downstream consumers

### File List

- 1-2-esco-onet-integration.md
