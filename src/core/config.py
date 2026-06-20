"""Core configuration values."""

from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    app_name: str = "KASH Platform"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # Database
    database_url: str = "postgresql://user:password@localhost:5432/kash_db"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_ttl: int = 3600  # 1 hour default TTL
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Firebase
    firebase_project_id: Optional[str] = None
    firebase_private_key_id: Optional[str] = None
    firebase_private_key: Optional[str] = None
    firebase_client_email: Optional[str] = None
    firebase_client_id: Optional[str] = None
    
    # External APIs
    esco_api_url: str = "https://ec.europa.eu/esco/api"
    github_api_url: str = "https://api.github.com"
    github_access_token: Optional[str] = None
    github_test_repo: Optional[str] = None
    github_rate_limit_per_minute: int = 60
    github_token_encryption_key: Optional[str] = None
    
    # Celery
    celery_broker_url: str = "pyamqp://user:password@localhost:5672//"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # ML Models
    model_storage_path: str = "models"
    feature_store_path: str = "data/features"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    pythonpath: Optional[str] = None

    # Observability
    enable_tracing: bool = False
    enable_metrics: bool = True
    otel_service_name: str = "kash-platform"
    otel_exporter_endpoint: str = "http://localhost:4318/v1/traces"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
MODELS_DIR = BASE_DIR / "models"
