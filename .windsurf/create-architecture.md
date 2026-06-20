# CREATE ARCHITECTURE WORKFLOW – KASH PROJECT

## Objective
Generate the full technical architecture and initial project structure for the KASH platform.

The system must support:
- NLP CV analysis
- ESCO/O*NET integration
- Adaptive quizzes
- Cognitive tests
- GitHub integration
- Predictive ML scoring
- SHAP explainability
- REST API exposure
- Frontend dashboard

---

# STEP 1 – Define Technical Stack

Backend:
- Python 3.11
- FastAPI
- PostgreSQL
- SQLAlchemy
- Pydantic
- LightGBM
- SHAP

Frontend:
- Next.js
- TailwindCSS

Infrastructure:
- Docker
- Environment-based configuration
- Modular monolith architecture

---

# STEP 2 – Generate Project Structure

Create the following folder structure:

yes/
├── src/
│   ├── api/
│   │   └── main.py
│   ├── core/
│   │   ├── config.py
│   │   └── database.py
│   ├── modules/
│   │   ├── knowledge/
│   │   ├── abilities/
│   │   ├── skills/
│   │   ├── intelligence/
│   ├── models/
│   └── schemas/
├── tests/
├── docker/
├── requirements.txt
├── Dockerfile

---

# STEP 3 – Define Service Boundaries

Knowledge Module:
- CV NLP parsing
- Taxonomy integration
- Knowledge scoring

Abilities Module:
- Cognitive tests
- Speech-to-text processing
- Multimodal scoring

Skills Module:
- Mini-project evaluation
- GitHub API integration
- Code analysis algorithm

Intelligence Module:
- KASH vector mapping
- Compatibility scoring
- Predictive success model
- SHAP explainability

---

# STEP 4 – API Conventions

All endpoints must follow:

/api/v1/<module>/<action>

Example:
- /api/v1/knowledge/analyze-cv
- /api/v1/intelligence/predict
- /api/v1/skills/evaluate

---

# STEP 5 – Non-Functional Requirements

- Response time < 200ms for scoring
- Modular code organization
- Clear separation of business logic and API layer
- Test coverage required
- Logging enabled
- Environment variables for secrets

---

# STEP 6 – Output Requirements

When executed, this workflow must:

1. Generate architecture.md inside:
   _bmad-output/planning-artifacts/

2. Confirm stack selection
3. Confirm folder structure
4. Confirm service boundaries
5. Confirm API conventions
6. Confirm ML integration strategy

---

# Completion Criteria

Architecture is considered complete when:

- architecture.md exists
- Stack defined
- Project structure defined
- Modules defined
- API conventions defined
- ML strategy defined
