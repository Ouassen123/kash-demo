# Story 3.3: Code analysis algorithm

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Skills automation engineer, I want a code analysis algorithm that evaluates repository submissions for structure, style, and correctness so we can surface objective metrics for each mini-project and feed them into Skills scoring and intelligence comparisons.

## Acceptance Criteria

1. Analyze learner repositories for code smells, complexity, and adherence to accepted patterns, emitting normalized scores and highlights.
2. Flag risky or insecure patterns while recording reviewer annotations for QA.
3. Output structured data that integrates with the GitHub API stories and Skills dashboards for transparency.

## Tasks / Subtasks

- [x] Task 1: Build static/dynamic analysis hooks that operate over git history or zipped submissions.
  - [x] Subtask 1.1: Support custom analyzers for different languages specified per mini-project.
- [x] Task 2: Produce scoring metadata (grades, severity buckets, reviewer notes) and push to Skills telemetry.
  - [x] Subtask 2.1: Allow reviewers to override automated scores with justification.

## Dev Story – Technical Implementation

Technical Story: Skills Code Analysis Pipeline
Module: Skills / Code Evaluation
Developer: Backend + Developer Productivity Engineer
Estimated Time: 4 days

### Technical Requirements
- Provide a pluggable analysis engine that can run static checks (complexity, lint, security) against GitHub snapshots or uploaded zips.
- Normalize analyzer outputs into the existing `MiniProjectEvaluationManager` metrics and ReliabilitySignals schema.
- Persist structured findings (category, severity, reviewer notes, remediation hints) for dashboards and downstream scoring.
- Support language-specific analyzers (Python, JS/TS, Java) with configuration per mini-project template.
- Expose API hooks so Skills reviewers can trigger re-analysis and override scores with audited comments.

### Implementation Details
- **Analyzer Orchestrator**: implement `CodeAnalysisEngine` service that accepts a `RepositorySnapshot` or artifact bundle, spins up async tasks per analyzer (Radon, Bandit, ESLint, Semgrep tree-sitter rules). Use asyncio + process pool for CPU heavy metrics.
- **Plugin Interface**: define `BaseAnalyzer` protocol (name, supported_languages, run(inputs)->AnalyzerReport). Ship built-in analyzers (complexity, lint, security, test-coverage stub) and allow registration via entrypoint table.
- **Metrics Aggregator**: convert raw analyzer findings into `CodeQualityMetric` dataclasses (score, severity, rationale, affected files). Aggregate to overall grades (A–D) and severity buckets for Task 2.
- **Reviewer Overrides**: extend `MiniProjectDashboard` store with override records (score_delta, justification, reviewer_id). Merge overrides downstream so telemetry carries both automated and manual scores.
- **Storage & APIs**: persist analyzer artifacts in `data/skills/code_analysis/<submission_id>.json` (or DB table when available). Add methods on `SkillsService` to fetch latest analysis, trigger re-run, and supply scoring metadata to GitHub audit APIs.
- **Language Configuration**: reuse template registry metadata (`analysis_profile`) to select analyzers + thresholds per project. Provide default config referencing rulesets stored under `src/modules/skills/code_rules/`.
- **Telemetry Hooks**: push summary metrics (score, risk_count, smell_count) to Skills telemetry bus (reuse existing logging/metrics client) so dashboards can chart trends.

### Acceptance Criteria
- Given a learner submission with Python + JS files, when the analysis service runs, then complexity/security/lint metrics are captured and stored with severity tags.
- Given a reviewer override, when telemetry is queried, then the override justification and adjusted scores are visible alongside automated metrics.
- Given a mini-project template with `analysis_profile="node-web"`, when a submission is analyzed, then only the configured analyzers (ESLint, Semgrep web rules) execute.

### Testing Strategy
- **Unit tests**: cover each built-in analyzer adapter (mock tool output), configuration parsing, severity bucketing logic, override merge logic (target 80% coverage for `code_analyzer` package).
- **Integration tests**: run the engine against a small fixture repository (Python + JS) to verify multi-language orchestration and persistence.
- **Performance tests**: benchmark analysis on repos up to 5k LOC to ensure runtime < 20s with concurrency capped.
- **Regression tests**: include fixture-based golden files for analyzer outputs so rule changes are detected in CI.

### Dependencies
- Python tooling: radon, bandit, semgrep, tree-sitter (per language), eslint via Node (invoked through subprocess), gitpython (for snapshot checkout), numpy/pandas for scoring.
- Existing Skills modules: `MiniProjectEvaluationManager`, `GitHubSyncManager`, telemetry/logging utilities.
- Infrastructure: access to repo artifacts (local checkout or GitHub snapshot), storage under `DATA_DIR/skills`, FastAPI endpoints in `/skills` router.

### Risks & Mitigations
- **Compilation / tooling availability**: Windows CI may lack native deps (semgrep/tree-sitter). Ship dockerized analyzer image or document tool installation; gate optional analyzers behind feature flags.
- **False positives overwhelming reviewers**: add severity thresholds + suppression config per template, and expose quick dismiss actions with justification.
- **Performance bottlenecks on large repos**: stream files, limit file types (exclude binaries/tests) and run analyzers concurrently with timeouts.
- **Version drift between analyzers**: lock tool versions in `requirements.txt`/`package.json` and add smoke tests to CI.
- [ ] Task 3: Expose an API that returns analysis artifacts, highlights, and confidence so downstream stories can reference them.

## Dev Notes

- Coordinate with GitHub integration to fetch the exact commit set under review.
- Keep analyzer outputs traceable to module definitions in `yes/modules/skills/code-analysis`.
- Document how security findings should be rebased into future QA stories.

### Project Structure Notes

- Host algorithm logic under `yes/modules/skills/code-analysis` with adapters for each static analysis tool.
- Include reviewer override interfaces in `yes/modules/skills/code-analysis/ui` so insights are accessible.
- Align exported schema with Skills scoring so dashboards can aggregate across mini-projects.

### References

- [Source: planning-artifacts/epic-skills.md#Stories]
- [Source: implementation-artifacts/sprint-status.yaml#development_status]

## Dev Agent Record

### Agent Model Used

gpt-4o

### Debug Log References

- Created code analysis story referencing Skills epic and sprint status

### Completion Notes List

- Documented analyzer hooks, scoring metadata, and override flows
- Connected story to downstream dashboards and GitHub integration

### File List

- 3-3-code-analysis-algorithm.md
