---
stepsCompleted:
  - manual-prd
inputDocuments:
  - architecture.md
  - epic-knowledge.md
  - epic-abilities.md
  - epic-skills.md
  - epic-intelligence.md
  - epic-finalisation.md
workflowType: 'prd'
---

# Product Requirements Document · KASH Phase 1

## Executive Summary
KASH Career Intelligence Phase 1 helps students who are uncertain about academic or career direction gain clarity through Knowledge, Abilities, Skills, and Intelligence (KASH) scoring. The product blends automated CV analysis, adaptive quizzes, GitHub-code-based skill evaluation, and explainable intelligence models so each learner receives a personalized profile, compatibility score, and recommended pathways—while counselors/pilot schools gain visibility through an admin panel and reporting layer.

## Success Criteria
1. CV + academic history ingestion reliably produces Knowledge scores with ESCO/O*NET validation and SHAP explainability attached to Intelligence outcomes.
2. Abilities, Skills, and Intelligence modules surface actionable guidance (quiz results, mini-project evaluation, job mapping) that 80% of pilot students identify as “helps clarify my next move.”
3. Admin & pilot operations can view progress, QA flags, and deployment metrics through the admin panel/reporting stories to support two initial partner schools.
4. CI/CD pipeline ensures nightly tests, Lightspeed scoring responses (<200 ms), and monitored async ML jobs with observability.

## Product Scope
### MVP
- Ingest CVs and academic data to generate Knowledge scores with ESCO/O*NET enrichment (Story 1‑5).
- Deliver Abilities assessments via text, voice, and mini-project scoring APIs (Stories 6‑9), plus integrate the admin reporting interface for pilot readiness.
- Evaluate skills through GitHub integration, mini-project scoring, and compatibility calculations (Stories 10‑16).
- Expose Intelligence predictions, compatibility mappings to 50+ jobs, and SHAP-based explanation content for students and counselors.

### Growth
- Expand job coverage beyond 50 occupations, add counselor-facing insights, and enable LinkedIn/Firebase authentication flows for seamless access.
- Layer in adaptive coaching prompts, enhance recommendation personalization, and extend ML re-training automation with Drift detection dashboards.

### Vision
- Become the go-to student career intelligence platform that continuously correlates KASH scores with emerging labor market data, integrates with education systems, and guides holistic career paths end-to-end.

## User Journeys
1. **Self-Discovery Student:** Uploads CV, completes adaptive quiz (Abilities), reviews Knowledge + Skills analysis, and receives intelligence-backed job matches with explainability. Confidence metric and compatibility score are shared with an in-app growth plan.
2. **Pilot Admin / Counselor:** Monitors pilot deployment progress (Stories 17‑20), reviews QA / optimization flags, and shares summarized reports with partner schools to guide coaching sessions.

## Domain Requirements
- Maintain ESCO/O*NET taxonomy for consistent Knowledge scoring.
- Map KASH vectors to job roles and success predictors with explainability for each recommendation.
- Ensure data capture supports job mapping, compatibility, and admin reporting requirements.

## Innovation Analysis
- Combines NLP CV parsing, adaptive assessments, GitHub-based skills validation, and LightGBM intelligence predictions with SHAP explainability to surface both scores and narratives.
- Modular architecture allows independent evolution of Knowledge, Abilities, Skills, and Intelligence while sharing observable services (monitoring, logging, ML lifecycle tooling).

## Project-Type Requirements
- Backend (Python 3.11, FastAPI, SQLAlchemy, Celery/RabbitMQ) orchestrating scoring pipelines with Redis caching and PostgreSQL persistence.
- Frontend (Next.js 14 + Tailwind + Recharts/D3) exposing scoring dashboards, admin reporting, and interactive student journeys.
- Infrastructure with Docker, environment-based config, GitHub Actions CI/CD, Terraform-managed environments, and OpenTelemetry/Grafana observability.
- Integrations: ESCO/O*NET clients with Redis caching and GitHub OAuth for repository analysis.

## Functional Requirements (Capability Contract)
1. **Knowledge Module (Stories 1‑5):** Accept CV/API inputs, normalize taxonomy, compute Knowledge score, store in PostgreSQL, and emit enriched payload for Intelligence.
2. **Abilities Module (Stories 6‑9):** Launch adaptive quizzes, capture text/voice/miniproject responses, produce abilities vectors, and surface them via `/api/v1/abilities/*` endpoints.
3. **Skills Module (Stories 10‑12):** Pull GitHub repos via secure OAuth, run code analysis algorithms, and map results to skill badges and readiness signals.
4. **Intelligence Module (Stories 13‑16):** Combine KASH vectors, run LightGBM predictions, calculate compatibility with at least 50 jobs, and attach SHAP explainability summaries.
5. **Finalisation & Pilot (Stories 17‑20):** Admin panel + reporting, QA validation flows, performance tuning, and pilot deployment orchestration for two schools.
6. **APIs / Observability:** Provide consistent `/api/v1/knowledge`, `/abilities`, `/skills`, `/intelligence` routes with correlation IDs, tracing, and documentation via Swagger.

## Non-Functional Requirements
- Scoring endpoints respond within 200 ms; heavy ML jobs (LightGBM retrain, batch scoring) complete within 5 s for async requests with polling support.
- System maintains ≥80% test coverage (pytest + Playwright), nightly regression runs, and automated alerts via Grafana + PagerDuty.
- Secrets managed via environment variables and GitHub Secrets; configuration validated via Pydantic BaseSettings.
- Observability via structured logging, OpenTelemetry traces, and Prometheus/Grafana dashboards.
- Modular monolith architecture with clear service boundaries, DI, and caching via Redis for ESCO/O*NET and GitHub lookups.

## Implementation Notes
- Deploy via docker-compose or Kubernetes depending on environment, with Celery/RabbitMQ handling async workloads and LightGBM models versioned in MLflow.
- Emphasize data privacy for student CVs and pilot reporting; ensure pilot admins can access reporting without exposing raw student data.
- Plan for pilot feedback loops before scaling to wider student populations.
