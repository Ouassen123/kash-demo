- **Skills Deep Dive UI**
  - `frontend/app/(dashboard)/skills/deep-dive` exposes the end-to-end view backed by `GET /skills/profile` with fallbacks.
  - Dashboard CTA (“View Skills Deep Dive”) links into the module for seamless navigation.
  - Helper utilities live in `frontend/lib/skills-view.ts` to normalize `SkillsProfile` responses for the UI.
- **Knowledge Deep Dive UI**
  - `frontend/app/(dashboard)/knowledge/deep-dive` shows CV/ESCO insights sourced from `GET /knowledge/profile`.
  - Includes hero, skill categories, top skills, gap analysis, and learning plan components.
- **Abilities Deep Dive UI**
  - `frontend/app/(dashboard)/abilities/deep-dive` visualizes adaptive quiz analytics via `GET /abilities/profile`.
  - Features domain score grid, recommendations, and assessment activity panels.
- **Intelligence Insights UI**
  - `frontend/app/(dashboard)/intelligence/insights` aggregates `/intelligence/profile` + assessments for SHAP explainability.
  - Includes hero, trend chart, feature importance, career insights, recommendation history, and assessment feed.

## 🔭 Observability

- Metrics & traces are wired via OpenTelemetry + Prometheus.
- Enable/disable with env vars in `.env`:
  ```env
  ENABLE_TRACING=true
  ENABLE_METRICS=true
  OTEL_SERVICE_NAME=kash-platform
  OTEL_EXPORTER_ENDPOINT=http://jaeger:4318/v1/traces
  ```
- Local stack (Prometheus, Grafana, Jaeger) is defined in `docker/dev-compose.yml`.
  ```bash
  docker compose -f docker/dev-compose.yml up prometheus grafana jaeger
  ```
- Prometheus scrapes the API at `/metrics` (port 8000); Grafana ships with a preprovisioned Prometheus datasource; Jaeger collects OTLP spans (http://localhost:16686 UI).

# KASH Career Intelligence Platform

A comprehensive platform for analyzing and developing student career intelligence through Knowledge, Abilities, Skills, and Intelligence (KASH) assessment.

## 🏗️ Architecture

Built with a modular monolith architecture using:
- **Backend**: Python 3.11, FastAPI, SQLAlchemy, PostgreSQL, Redis
- **Frontend**: Next.js 14, Tailwind CSS, React Query
- **ML**: LightGBM, SHAP, spaCy, NLTK
- **Infrastructure**: Docker, Celery, RabbitMQ

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend)

### Development Setup

1. **Clone and setup environment**
```bash
git clone <repository-url>
cd yes
cp .env.example .env
# Edit .env with your configuration
```

2. **Start development environment**
```bash
# Start all services (PostgreSQL, Redis, RabbitMQ, API, Workers)
docker-compose -f docker/dev-compose.yml up -d

# View logs
docker-compose -f docker/dev-compose.yml logs -f api
```

3. **Access services**
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Flower (Celery monitoring): http://localhost:5555
- RabbitMQ Management: http://localhost:15672 (user: kash_user, pass: kash_password)

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Setup environment
export PYTHONPATH=./src

# Start API server
uvicorn src.main:app --reload

# Start Celery worker (separate terminal)
celery -A src.jobs.celery_app worker --loglevel=info

# Start Celery beat (separate terminal)
celery -A src.jobs.celery_app beat --loglevel=info
```

## 📁 Project Structure

```
yes/
├── src/
│   ├── api/                  # FastAPI routers and endpoints
│   │   └── v1/
│   │       ├── knowledge/    # CV analysis, ESCO integration
│   │       ├── abilities/    # Adaptive assessments
│   │       ├── skills/       # GitHub integration, code analysis
│   │       └── intelligence/ # KASH scoring, predictions
│   ├── core/                 # Shared utilities
│   │   ├── config.py         # Configuration management
│   │   ├── database.py       # Database setup and sessions
│   │   └── logging.py        # Structured logging
│   ├── modules/              # Domain-specific services
│   │   ├── knowledge/
│   │   ├── abilities/
│   │   ├── skills/
│   │   └── intelligence/
│   ├── models/               # SQLAlchemy models
│   ├── schemas/              # Pydantic contracts
│   ├── integration/          # External API clients
│   ├── ml/                   # ML models and feature store
│   └── jobs/                 # Celery tasks
├── frontend/                 # Next.js application
├── docker/                   # Docker configurations
├── tests/                    # Test suites
├── data/                     # Data files and features
├── models/                   # Trained ML models
├── logs/                     # Application logs
└── requirements.txt          # Python dependencies
```

## 🔧 Configuration

Key environment variables (see `.env.example`):

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection for caching
- `FIREBASE_PROJECT_ID`: For Google/LinkedIn authentication
- `SECRET_KEY`: JWT signing key
- `DEBUG`: Enable development features

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific module tests
pytest tests/modules/knowledge/
```

## 📊 Monitoring

- **Health Check**: `GET /health`
- **Application Logs**: Structured JSON logging in `logs/`
- **Celery Monitoring**: Flower UI at http://localhost:5555
- **Database**: PostgreSQL metrics available via connection

## 🚀 Deployment

The architecture supports both development and production deployments:

- **Development**: Docker Compose with local services
- **Production**: Kubernetes with managed databases
- **CI/CD**: GitHub Actions for automated testing and deployment

## 🤝 Contributing

1. Follow the established code patterns in `src/core/`
2. Add tests for new features
3. Update documentation
4. Use the provided development environment

## 📄 License

[Add your license here]

## 🆘 Support

For issues and questions:
- Check the API documentation at `/docs`
- Review logs in the `logs/` directory
- Check service health via `/health` endpoint
