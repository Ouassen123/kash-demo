"""Celery application configuration for background tasks."""

from celery import Celery
from kombu import Queue
from src.core.config import settings

# Create Celery app
celery_app = Celery(
    "kash_platform",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "src.jobs.ml_tasks",
        "src.jobs.integration_tasks", 
        "src.jobs.notification_tasks"
    ]
)

# Configure Celery
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task routing
    task_routes={
        "src.jobs.ml_tasks.*": {"queue": "ml_processing"},
        "src.jobs.integration_tasks.*": {"queue": "integrations"},
        "src.jobs.notification_tasks.*": {"queue": "notifications"},
    },
    
    # Queue definitions
    task_queues=(
        Queue("ml_processing", routing_key="ml_processing"),
        Queue("integrations", routing_key="integrations"),
        Queue("notifications", routing_key="notifications"),
        Queue("default", routing_key="default"),
    ),
    
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    
    # Result settings
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
    },
    
    # Beat schedule for periodic tasks
    beat_schedule={
        "cleanup-expired-sessions": {
            "task": "src.jobs.notification_tasks.cleanup_expired_sessions",
            "schedule": 3600.0,  # Every hour
        },
        "update-ml-models": {
            "task": "src.jobs.ml_tasks.update_models",
            "schedule": 86400.0,  # Daily
        },
    },
)

# Optional: Configure monitoring
if settings.debug:
    celery_app.conf.update(
        worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
        worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",
    )
