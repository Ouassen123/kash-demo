"""Structured logging configuration."""

import logging
import sys
from pathlib import Path
from typing import Dict, Any
import json
from datetime import datetime

from .config import settings, LOGS_DIR


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "getMessage"
            }:
                log_entry[key] = value
        
        return json.dumps(log_entry)


def setup_logging() -> None:
    """Setup application logging configuration."""
    # Ensure logs directory exists
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.log_level.upper()))
    
    # File handler
    file_handler = logging.FileHandler(LOGS_DIR / "app.log")
    file_handler.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Formatters
    if settings.log_format.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Add handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Specific logger configurations
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)


def log_request_info(request_id: str, method: str, path: str, **kwargs) -> None:
    """Log HTTP request information."""
    logger = get_logger("http")
    logger.info(
        "HTTP request",
        extra={
            "request_id": request_id,
            "method": method,
            "path": path,
            **kwargs
        }
    )


def log_performance(operation: str, duration_ms: float, **kwargs) -> None:
    """Log performance metrics."""
    logger = get_logger("performance")
    logger.info(
        f"Performance: {operation}",
        extra={
            "operation": operation,
            "duration_ms": duration_ms,
            **kwargs
        }
    )
