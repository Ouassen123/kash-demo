"""Main FastAPI application entry point."""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import os
import time
import uuid
from contextlib import asynccontextmanager

from src.core.config import settings
from src.core.logging import setup_logging, get_logger, log_request_info, log_performance
from src.core.observability import setup_observability
from src.core.database import check_db_connection, create_tables

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting KASH Platform API")
    
    # Check database connection
    if not check_db_connection():
        logger.error("Failed to connect to database")
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    # Create database tables
    try:
        create_tables()
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise
    
    logger.info("KASH Platform API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down KASH Platform API")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="KASH Career Intelligence Platform API",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Setup observability integrations (metrics + tracing)
setup_observability(app)

def _parse_csv_env(name: str) -> list[str]:
    raw = os.getenv(name)
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


cors_origins = _parse_csv_env("CORS_ALLOW_ORIGINS") or _parse_csv_env("ALLOWED_ORIGINS")
allow_origins = cors_origins if cors_origins else ["*"]

allow_credentials = os.getenv("CORS_ALLOW_CREDENTIALS", "false").strip().lower() == "true"
if allow_origins == ["*"]:
    allow_credentials = False

trusted_hosts = _parse_csv_env("TRUSTED_HOSTS") or _parse_csv_env("ALLOWED_HOSTS")
allowed_hosts = trusted_hosts if trusted_hosts else ["*"]

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=allowed_hosts
)


@app.middleware("http")
async def add_request_id_and_timing(request: Request, call_next):
    """Add request ID and timing middleware."""
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Add request ID to request state
    request.state.request_id = request_id
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    # Add headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log request
    log_request_info(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        process_time_ms=process_time
    )
    
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(
        f"Unhandled exception: {exc}",
        extra={
            "request_id": request_id,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc)
        }
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "request_id": request_id,
            "message": "An unexpected error occurred. Please try again later."
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    start_time = time.time()
    
    # Check database
    db_healthy = check_db_connection()
    
    # Calculate response time
    response_time = (time.time() - start_time) * 1000
    
    health_status = {
        "status": "healthy" if db_healthy else "unhealthy",
        "version": settings.app_version,
        "database": "connected" if db_healthy else "disconnected",
        "response_time_ms": round(response_time, 2)
    }
    
    log_performance(
        operation="health_check",
        duration_ms=response_time,
        healthy=db_healthy
    )
    
    return health_status


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "KASH Career Intelligence Platform API",
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else "Documentation not available in production"
    }


# Include API routers
from src.api.v1 import api_router
app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
