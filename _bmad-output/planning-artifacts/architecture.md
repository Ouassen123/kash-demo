---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
inputDocuments: []
workflowType: 'architecture'
project_name: 'yes'
user_name: 'rida'
date: '2026-02-14'
lastStep: 8
---

# KASH Architecture Blueprint

## Objective
Clarify the end-to-end technical architecture that powers Knowledge, Abilities, Skills, and Intelligence workflows, ensuring NLP CV analysis, adaptive testing, predictive scoring, and integrations (ESCO/O*NET, GitHub) are orchestrated reliably and observably.

## Technical Stack
- **Backend:** Python 3.11, FastAPI, SQLAlchemy, Pydantic, PostgreSQL, Redis for caching, LightGBM for prediction, SHAP for explainability, Celery/RabbitMQ for async workloads.
- **Frontend:** Next.js 14, Tailwind CSS, React Query (data orchestration), Recharts/D3 for visualizations.
- **Infrastructure:** Dockerised services orchestrated via docker-compose/k8s (depending on environment), environment-based configuration, modular monolith with clear service boundaries, CI/CD via GitHub Actions, Terraform for infra as code.

## Project Structure (yes/src)
```
yes/
├── src/
│   ├── api/                  # FastAPI entrypoints and routers
│   │   └── v1/
│   │       ├── knowledge/
│   │       ├── abilities/
│   │       ├── skills/
│   │       └── intelligence/
│   ├── core/
│   │   ├── config.py          # env handling (pydantic BaseSettings)
│   │   ├── database.py        # SQLAlchemy session factory
│   │   └── logging.py         # structured logging/telemetry
│   ├── modules/               # domain-specific services
│   │   ├── knowledge/
│   │   ├── abilities/
│   │   ├── skills/
│   │   └── intelligence/
│   ├── models/                # SQLAlchemy/LightGBM artifacts
│   ├── schemas/               # Pydantic contracts for APIs/events
│   ├── integration/           # ESCO/O*NET/GitHub clients
│   ├── ml/                    # training + feature store connectors
│   └── jobs/                  # Celery tasks (ingestion, scoring)
├── frontend/                  # Next.js app
├── tests/                     # pytest suites (unit + integration)
├── docker/
│   ├── dev-compose.yml
│   └── prod-compose.yml
├── requirements.txt
├── Dockerfile
├── architecture.md           # this file (for ongoing refinement)
└── README.md
```

## Service Boundaries
- **Knowledge Module** handles NLP CV parsing, taxonomy enrichment, ESCO/O*NET lookups, and intermediate knowledge scoring pipelines.
- **Abilities Module** owns cognitive and behavioral assessment flows, including adaptive quizzes, speech-to-text checkers, and multimodal scoring.
- **Skills Module** evaluates project artifacts via GitHub integration, runs the code-analysis algorithm, and reports skill-level insights and badges.
- **Intelligence Module** maps domain-weighted KASH vectors, combines component scores for compatibility/predictive models, and exposes explainability dashboards (SHAP outputs).
- Shared services: Authentication, Rate Limiting, Monitoring (OpenTelemetry/Prometheus), Logging, and ML Lifecycle tooling (model registry, data drift alerts).

## API Conventions
- Base path: `/api/v1/<module>` with consistent verbs for actions.
  - `POST /api/v1/knowledge/analyze-cv` – ingest CV, return knowledge profile.
  - `POST /api/v1/abilities/start-quiz` – launch adaptive quiz session.
  - `POST /api/v1/skills/evaluate` – push code sample or GitHub repo snapshot.
  - `POST /api/v1/intelligence/predict` – combine inputs, apply LightGBM scoring, return SHAP summary.
- Use OpenAPI/JSON Schema for contracts, automatic docs via Swagger UI.
- Employ request/response middleware for correlation IDs, tracing.

## Non-Functional Requirements
- Response time <200 ms for scoring endpoints; 5 s for heavy ML pipelines (async + polling).
- Modular monolith architecture enabling independent team ownership.
- Strict separation between API layer and business logic, with domain services instantiating via dependency injection.
- 80%+ test coverage (pytest + Playwright for UI flows). Nightly regression runs via GitHub Actions.
- Structured logging, metrics, and alerting (Grafana dashboards + PagerDuty).
- Secrets via environment variables, validated via Pydantic and GitHub Secrets in CI.

## ML & Integration Strategy
- Feature store persists CV, quiz, repo signals; LightGBM models retrained on schedules, tracked via MLflow.
- SHAP-based explainability delivered alongside predictions for transparency in intelligence dashboards.
- ESCO/O*NET clients cache responses (Redis) with TTLs and fallback to local taxonomy mirror when rate limited.
- GitHub integration uses OAuth apps for repo access, analyzes code via the existing code-analysis algorithm, and emits signals into the skills module.

## Output Requirements / Workflow Confirmation
1. Stack selection confirmed.
2. Folder structure documented.
3. Service boundaries defined.
4. API conventions spelled out.
5. ML + integration approach described.
6. Architecture document stored under `_bmad-output/planning-artifacts/architecture.md` for traceability.

## Completion Checklist
- [x] architecture.md exists
- [x] Stack defined
- [x] Project structure detailed
- [x] Modules/services described
- [x] API conventions explained
- [x] ML & integration strategy articulated
