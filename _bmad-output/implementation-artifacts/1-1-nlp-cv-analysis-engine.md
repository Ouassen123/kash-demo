# Story 1.1: NLP CV analysis engine

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a talent reviewer working within the Knowledge Module, I want an NLP-powered CV analysis engine so that we can consistently extract structured knowledge attributes (skills, education, experience, certifications) and feed them into the Knowledge scoring pipeline with an objective, repeatable signal.

## Acceptance Criteria

1. Given a batch of CVs/resumes with unstructured text, the NLP engine normalizes them into a shared schema that exposes academic history, certifications, skills, and career highlights for scoring.
2. The analysis assigns confidence levels to each extracted attribute and surfaces any ambiguities so the scoring algorithm can weight them appropriately.
3. The output is stored in the Knowledge Module data model with source references, ensuring downstream scoring and quiz components can consume the insight without manual cleanup.

## Tasks / Subtasks

- [x] Task 1 (AC 1): Build CV ingestion and NLP preprocessing pipeline (text extraction, language detection, sentence segmentation)
  - [x] Subtask 1.1: Implement skill/education pattern extraction and mapping to normalized taxonomy
- [x] Task 2 (AC 2): Add confidence scoring layer and flag ambiguous values for human review
  - [x] Subtask 2.1: Surface confidence metadata alongside each normalized attribute
- [x] Task 3 (AC 3): Persist analyzed output into the Knowledge Module structure and expose APIs for the scoring engine
  - [x] Subtask 3.1: Document data contracts expected by downstream components (adaptive quiz, scoring calculation)

## Dev Notes

- Align every data field with the Knowledge scoring data model defined in the Knowledge Module epic so that Quiz and Scoring stories can consume the same signals without transformations.
- Reuse existing NLP tooling from the Compatibility Score and explainability research when possible to avoid redundant pipelines.
- Include monitoring of extraction confidence to trigger future analytics on accuracy drift once integrated with the scoring calculation.

### Project Structure Notes

- Place ingestion services under `yes/modules/knowledge/nlp` to mirror other knowledge-related components.
- Keep configuration and taxonomy files together so that updates to the normalized schema stay adjacent to the extractor code.
- Coordinate with the `adaptive-quiz-algorithm` and `knowledge-scoring-calculation` stories so downstream consumers already expect the normalized schema and metadata fields.

### References

- [Source: planning-artifacts/epic-knowledge.md#Stories]
- [Source: implementation-artifacts/sprint-status.yaml#development_status]

## Dev Agent Record

### Agent Model Used

gpt-4o

### Debug Log References

- Generated story file after analyzing epics and sprint status

### Completion Notes List

- ✅ Implemented complete NLP CV analysis pipeline with text extraction, language detection, and sentence segmentation
- ✅ Created confidence scoring system with ambiguity detection for all extracted attributes
- ✅ Built taxonomy mapper for normalizing skills, education, and experience to standardized schema
- ✅ Developed comprehensive test suite with unit tests and integration tests (10/10 tests passing)
- ✅ Integrated with existing Knowledge Module architecture and data models
- ✅ **CRITICAL FIXES APPLIED:**
  - Implemented database persistence with SQLAlchemy integration (AC3 satisfied)
  - Created comprehensive data contracts documentation (Task 3.1 completed)
  - Fixed circular imports by creating utils.py module
- ✅ **HIGH PRIORITY FIXES APPLIED:**
  - Added proper NLP model management with setup script
  - Fixed all test imports and dependencies
  - Enhanced input validation with size limits and security checks
- ✅ **MEDIUM PRIORITY IMPROVEMENTS:**
  - Pre-compiled all regex patterns for performance
  - Refactored analyze_cv() into smaller, maintainable functions
  - Added comprehensive documentation and docstrings
- ✅ All acceptance criteria satisfied with structured output ready for downstream scoring

### File List

- 1-1-nlp-cv-analysis-engine.md
- src/modules/knowledge/nlp/__init__.py
- src/modules/knowledge/nlp/cv_analyzer.py
- src/modules/knowledge/nlp/confidence_scorer.py
- src/modules/knowledge/nlp/taxonomy_mapper.py
- src/modules/knowledge/nlp/utils.py
- docs/knowledge/data-contracts.md
- scripts/setup_nlp_models.py
- tests/knowledge/test_cv_analyzer.py
- tests/knowledge/test_confidence_scorer.py
- tests/knowledge/test_taxonomy_mapper.py
- tests/knowledge/test_nlp_isolated.py
- tests/knowledge/test_integration.py
