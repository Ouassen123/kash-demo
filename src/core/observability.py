"""Observability utilities for tracing and metrics."""

import time

from fastapi import FastAPI, Request, Response
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
)

TRACING_CONFIGURED = False


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware recording Prometheus metrics for HTTP requests."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        start_time = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start_time

        path = request.url.path
        method = request.method
        status = response.status_code

        REQUEST_COUNT.labels(method=method, path=path, status=status).inc()
        REQUEST_LATENCY.labels(method=method, path=path).observe(elapsed)

        return response


def _configure_tracing() -> None:
    global TRACING_CONFIGURED

    if TRACING_CONFIGURED:
        return

    resource = Resource.create({"service.name": settings.otel_service_name})
    provider = TracerProvider(resource=resource)

    exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_endpoint)
    provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)
    TRACING_CONFIGURED = True


def setup_observability(app: FastAPI) -> None:
    """Configure tracing and metrics for the FastAPI app."""

    if settings.enable_tracing:
        _configure_tracing()
        FastAPIInstrumentor.instrument_app(app)

    if settings.enable_metrics:
        app.add_middleware(MetricsMiddleware)

        @app.get("/metrics", include_in_schema=False)
        async def metrics_endpoint():  # pragma: no cover - simple passthrough
            return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
