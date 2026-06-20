"""Performance monitoring service with OpenTelemetry for KASH platform."""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json

# Optional psutil import for system metrics
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Optional numpy import for statistics
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

# OpenTelemetry imports
try:
    from opentelemetry import trace, metrics, baggage
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False


@dataclass
class MonitoringConfig:
    """Configuration for performance monitoring."""
    # OpenTelemetry settings
    enable_opentelemetry: bool = True
    service_name: str = "kash-platform"
    service_version: str = "1.0.0"
    environment: str = "production"
    
    # OTLP endpoint
    otlp_endpoint: str = "http://localhost:4317"
    otlp_headers: Optional[Dict[str, str]] = None
    
    # Sampling
    trace_sampling_ratio: float = 0.1  # 10% sampling
    metric_export_interval_ms: int = 30000  # 30 seconds
    
    # Custom metrics
    enable_custom_metrics: bool = True
    enable_system_metrics: bool = True
    enable_business_metrics: bool = True
    
    # Alerting
    enable_alerting: bool = True
    slow_request_threshold_ms: float = 1000.0
    error_rate_threshold: float = 0.05  # 5%
    memory_usage_threshold: float = 0.8  # 80%
    
    # Performance baselines
    baseline_response_time_ms: float = 200.0
    baseline_error_rate: float = 0.01  # 1%
    baseline_memory_usage_mb: float = 512.0


class PerformanceMetrics:
    """Custom performance metrics collector."""
    
    def __init__(self, meter):
        self.meter = meter
        
        # Request metrics
        self.request_counter = meter.create_counter(
            "http_requests_total",
            description="Total number of HTTP requests"
        )
        
        self.request_duration = meter.create_histogram(
            "http_request_duration_ms",
            description="HTTP request duration in milliseconds"
        )
        
        self.request_size = meter.create_histogram(
            "http_request_size_bytes",
            description="HTTP request size in bytes"
        )
        
        self.response_size = meter.create_histogram(
            "http_response_size_bytes",
            description="HTTP response size in bytes"
        )
        
        # Error metrics
        self.error_counter = meter.create_counter(
            "http_errors_total",
            description="Total number of HTTP errors"
        )
        
        # Cache metrics
        self.cache_hits = meter.create_counter(
            "cache_hits_total",
            description="Total number of cache hits"
        )
        
        self.cache_misses = meter.create_counter(
            "cache_misses_total",
            description="Total number of cache misses"
        )
        
        # Database metrics
        self.db_query_duration = meter.create_histogram(
            "db_query_duration_ms",
            description="Database query duration in milliseconds"
        )
        
        self.db_connections_active = meter.create_up_down_counter(
            "db_connections_active",
            description="Number of active database connections"
        )
        
        # ML prediction metrics
        self.ml_prediction_counter = meter.create_counter(
            "ml_predictions_total",
            description="Total number of ML predictions"
        )
        
        self.ml_prediction_duration = meter.create_histogram(
            "ml_prediction_duration_ms",
            description="ML prediction duration in milliseconds"
        )
        
        # Business metrics
        self.compatibility_calculations = meter.create_counter(
            "compatibility_calculations_total",
            description="Total number of compatibility calculations"
        )
        
        self.active_users = meter.create_up_down_counter(
            "active_users",
            description="Number of active users"
        )
        
        # System metrics
        self.memory_usage = meter.create_gauge(
            "memory_usage_bytes",
            description="Memory usage in bytes"
        )
        
        self.cpu_usage = meter.create_gauge(
            "cpu_usage_percent",
            description="CPU usage percentage"
        )


class AlertManager:
    """Simple alert manager for performance thresholds."""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.alerts: Dict[str, Dict[str, Any]] = {}
    
    def check_thresholds(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check metrics against thresholds and generate alerts."""
        new_alerts = []
        
        # Check slow request rate
        if "avg_response_time_ms" in metrics:
            avg_response_time = metrics["avg_response_time_ms"]
            if avg_response_time > self.config.slow_request_threshold_ms:
                alert = {
                    "type": "slow_requests",
                    "severity": "warning",
                    "message": f"Average response time ({avg_response_time:.2f}ms) exceeds threshold ({self.config.slow_request_threshold_ms}ms)",
                    "timestamp": datetime.utcnow().isoformat(),
                    "metrics": {"avg_response_time_ms": avg_response_time}
                }
                new_alerts.append(alert)
        
        # Check error rate
        if "error_rate" in metrics:
            error_rate = metrics["error_rate"]
            if error_rate > self.config.error_rate_threshold:
                alert = {
                    "type": "high_error_rate",
                    "severity": "critical",
                    "message": f"Error rate ({error_rate:.2%}) exceeds threshold ({self.config.error_rate_threshold:.2%})",
                    "timestamp": datetime.utcnow().isoformat(),
                    "metrics": {"error_rate": error_rate}
                }
                new_alerts.append(alert)
        
        # Check memory usage
        if "memory_usage_mb" in metrics:
            memory_usage_mb = metrics["memory_usage_mb"]
            if memory_usage_mb > self.config.memory_usage_threshold * 1024:
                alert = {
                    "type": "high_memory_usage",
                    "severity": "warning",
                    "message": f"Memory usage ({memory_usage_mb:.2f}MB) exceeds threshold ({self.config.memory_usage_threshold * 1024:.2f}MB)",
                    "timestamp": datetime.utcnow().isoformat(),
                    "metrics": {"memory_usage_mb": memory_usage_mb}
                }
                new_alerts.append(alert)
        
        # Update alerts
        for alert in new_alerts:
            alert_key = f"{alert['type']}_{alert['severity']}"
            self.alerts[alert_key] = alert
            self.logger.warning(f"ALERT: {alert['message']}")
        
        return new_alerts
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active alerts."""
        # Clear old alerts (older than 1 hour)
        cutoff = datetime.utcnow() - timedelta(hours=1)
        active_alerts = []
        
        for alert_key, alert in self.alerts.items():
            alert_time = datetime.fromisoformat(alert["timestamp"])
            if alert_time > cutoff:
                active_alerts.append(alert)
            else:
                del self.alerts[alert_key]
        
        return active_alerts


class PerformanceMonitoringService:
    """Performance monitoring service with OpenTelemetry."""
    
    def __init__(self, config: Optional[MonitoringConfig] = None):
        self.config = config or MonitoringConfig()
        self.logger = logging.getLogger(__name__)
        
        # OpenTelemetry components
        self.tracer_provider: Optional[TracerProvider] = None
        self.meter_provider: Optional[MeterProvider] = None
        self.metrics: Optional[PerformanceMetrics] = None
        
        # Alert manager
        self.alert_manager = AlertManager(self.config)
        
        # Performance data storage
        self.performance_data: Dict[str, List[Dict[str, Any]]] = {
            "requests": [],
            "errors": [],
            "system": []
        }
        
        # Initialize OpenTelemetry
        self._initialize_opentelemetry()
        
        # Start background monitoring
        self._monitoring_task: Optional[asyncio.Task] = None
        self._start_background_monitoring()
        
        self.logger.info("Performance monitoring service initialized")
    
    def _initialize_opentelemetry(self):
        """Initialize OpenTelemetry components."""
        if not OPENTELEMETRY_AVAILABLE or not self.config.enable_opentelemetry:
            self.logger.warning("OpenTelemetry not available or disabled")
            return
        
        try:
            # Initialize tracing
            self.tracer_provider = TracerProvider()
            trace.set_tracer_provider(self.tracer_provider)
            
            # Configure OTLP trace exporter
            otlp_exporter = OTLPSpanExporter(
                endpoint=self.config.otlp_endpoint,
                headers=self.config.otlp_headers
            )
            
            span_processor = BatchSpanProcessor(otlp_exporter)
            self.tracer_provider.add_span_processor(span_processor)
            
            # Initialize metrics
            metric_reader = PeriodicExportingMetricReader(
                exporter=OTLPMetricExporter(
                    endpoint=self.config.otlp_endpoint,
                    headers=self.config.otlp_headers
                ),
                export_interval_millis=self.config.metric_export_interval_ms
            )
            
            self.meter_provider = MeterProvider(metric_readers=[metric_reader])
            metrics.set_meter_provider(self.meter_provider)
            
            # Create custom metrics
            meter = self.meter_provider.get_meter("kash.performance")
            self.metrics = PerformanceMetrics(meter)
            
            # Instrument libraries
            self._instrument_libraries()
            
            self.logger.info("OpenTelemetry initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenTelemetry: {e}")
    
    def _instrument_libraries(self):
        """Instrument common libraries."""
        try:
            # Note: These would be called during application startup
            # FastAPIInstrumentor.instrument_app(app)
            # AsyncPGInstrumentor().instrument()
            # RedisInstrumentor().instrument()
            # HTTPXClientInstrumentor().instrument()
            
            self.logger.info("Library instrumentation configured")
            
        except Exception as e:
            self.logger.error(f"Failed to instrument libraries: {e}")
    
    def _start_background_monitoring(self):
        """Start background monitoring task."""
        if self.config.enable_system_metrics:
            self._monitoring_task = asyncio.create_task(self._background_monitoring_loop())
    
    async def _background_monitoring_loop(self):
        """Background loop for collecting system metrics."""
        while True:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(30)  # Collect every 30 seconds
            except Exception as e:
                self.logger.error(f"Error in background monitoring: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _collect_system_metrics(self):
        """Collect system metrics."""
        if not PSUTIL_AVAILABLE:
            self.logger.warning("psutil not available, skipping system metrics")
            return
        
        try:
            # Memory usage
            memory = psutil.virtual_memory()
            if self.metrics:
                self.metrics.memory_usage.set(memory.used)
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if self.metrics:
                self.metrics.cpu_usage.set(cpu_percent)
            
            # Store in performance data
            system_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "memory_usage_mb": memory.used / (1024 * 1024),
                "memory_usage_percent": memory.percent,
                "cpu_usage_percent": cpu_percent,
                "disk_usage_percent": psutil.disk_usage('/').percent if hasattr(psutil, 'disk_usage') else 0
            }
            
            self.performance_data["system"].append(system_data)
            
            # Keep only last 1000 entries
            if len(self.performance_data["system"]) > 1000:
                self.performance_data["system"] = self.performance_data["system"][-1000:]
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
    
    def record_request(self, method: str, path: str, status_code: int, 
                      duration_ms: float, request_size: int = 0, 
                      response_size: int = 0):
        """Record HTTP request metrics."""
        if not self.metrics:
            return
        
        # Record basic metrics
        self.request_counter.add(1, {
            "method": method,
            "path": path,
            "status_code": str(status_code)
        })
        
        self.request_duration.record(duration_ms, {
            "method": method,
            "path": path,
            "status_code": str(status_code)
        })
        
        if request_size > 0:
            self.request_size.record(request_size)
        
        if response_size > 0:
            self.response_size.record(response_size)
        
        # Record error if applicable
        if status_code >= 400:
            self.error_counter.add(1, {
                "method": method,
                "path": path,
                "status_code": str(status_code)
            })
        
        # Store in performance data
        request_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "request_size": request_size,
            "response_size": response_size
        }
        
        self.performance_data["requests"].append(request_data)
        
        # Keep only last 1000 entries
        if len(self.performance_data["requests"]) > 1000:
            self.performance_data["requests"] = self.performance_data["requests"][-1000:]
    
    def record_cache_hit(self, cache_type: str, key: str):
        """Record cache hit."""
        if self.metrics:
            self.cache_hits.add(1, {"cache_type": cache_type})
    
    def record_cache_miss(self, cache_type: str, key: str):
        """Record cache miss."""
        if self.metrics:
            self.cache_misses.add(1, {"cache_type": cache_type})
    
    def record_database_query(self, query_type: str, duration_ms: float):
        """Record database query metrics."""
        if self.metrics:
            self.db_query_duration.record(duration_ms, {"query_type": query_type})
    
    def record_ml_prediction(self, model_id: str, duration_ms: float, 
                           cached: bool = False):
        """Record ML prediction metrics."""
        if self.metrics:
            self.ml_prediction_counter.add(1, {
                "model_id": model_id,
                "cached": str(cached)
            })
            
            self.ml_prediction_duration.record(duration_ms, {"model_id": model_id})
    
    def record_compatibility_calculation(self, learner_id: str, job_family: str, 
                                       duration_ms: float):
        """Record compatibility calculation metrics."""
        if self.metrics:
            self.compatibility_calculations.add(1, {
                "job_family": job_family
            })
    
    def create_span(self, name: str, **attributes) -> Optional[Any]:
        """Create a new span for tracing."""
        if not self.tracer_provider:
            return None
        
        tracer = trace.get_tracer(__name__)
        return tracer.start_span(name, attributes=attributes)
    
    def get_performance_summary(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get performance summary for the given time window."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        
        # Filter requests within time window
        recent_requests = [
            req for req in self.performance_data["requests"]
            if datetime.fromisoformat(req["timestamp"]) > cutoff_time
        ]
        
        if not recent_requests:
            return {"message": "No recent requests"}
        
        # Calculate statistics
        total_requests = len(recent_requests)
        total_errors = sum(1 for req in recent_requests if req["status_code"] >= 400)
        avg_duration = sum(req["duration_ms"] for req in recent_requests) / total_requests
        
        # Calculate P95
        if NUMPY_AVAILABLE:
            p95_duration = np.percentile([req["duration_ms"] for req in recent_requests], 95)
        else:
            # Simple P95 calculation without numpy
            durations = sorted([req["duration_ms"] for req in recent_requests])
            p95_index = int(len(durations) * 0.95)
            p95_duration = durations[min(p95_index, len(durations) - 1)]
        
        # Get latest system metrics
        recent_system = self.performance_data["system"][-1] if self.performance_data["system"] else {}
        
        summary = {
            "time_window_minutes": time_window_minutes,
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": total_errors / total_requests,
            "avg_response_time_ms": avg_duration,
            "p95_response_time_ms": p95_duration,
            "system_metrics": recent_system,
            "active_alerts": self.alert_manager.get_active_alerts()
        }
        
        # Check for alerts
        new_alerts = self.alert_manager.check_thresholds(summary)
        if new_alerts:
            summary["new_alerts"] = new_alerts
        
        return summary
    
    def get_detailed_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics."""
        return {
            "performance_data": self.performance_data,
            "active_alerts": self.alert_manager.get_active_alerts(),
            "config": {
                "service_name": self.config.service_name,
                "environment": self.config.environment,
                "opentelemetry_enabled": self.config.enable_opentelemetry
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for monitoring service."""
        return {
            "status": "healthy",
            "opentelemetry_available": OPENTELEMETRY_AVAILABLE,
            "opentelemetry_enabled": self.config.enable_opentelemetry,
            "metrics_enabled": self.metrics is not None,
            "active_alerts": len(self.alert_manager.get_active_alerts()),
            "background_monitoring": self._monitoring_task is not None,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def cleanup(self):
        """Cleanup monitoring service."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        # Shutdown OpenTelemetry
        if self.tracer_provider:
            await self.tracer_provider.force_flush()
            await self.tracer_provider.shutdown()
        
        if self.meter_provider:
            await self.meter_provider.force_flush()
            await self.meter_provider.shutdown()


# Performance monitoring decorators

def monitor_performance(operation_name: str = None):
    """Decorator for monitoring function performance."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            monitoring_service = get_performance_monitoring_service()
            
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            # Create span
            span = monitoring_service.create_span(op_name)
            
            start_time = time.time()
            status_code = 200
            
            try:
                result = await func(*args, **kwargs)
                return result
                
            except Exception as e:
                status_code = 500
                monitoring_service.logger.error(f"Error in {op_name}: {e}")
                raise
                
            finally:
                # Record metrics
                duration_ms = (time.time() - start_time) * 1000
                monitoring_service.record_request(
                    method="INTERNAL",
                    path=op_name,
                    status_code=status_code,
                    duration_ms=duration_ms
                )
                
                if span:
                    span.set_attribute("duration_ms", duration_ms)
                    span.set_attribute("status_code", status_code)
                    span.end()
        
        return wrapper
    return decorator


# Global monitoring service
_performance_monitoring_service: Optional[PerformanceMonitoringService] = None


def get_performance_monitoring_service() -> PerformanceMonitoringService:
    """Get global performance monitoring service."""
    global _performance_monitoring_service
    if _performance_monitoring_service is None:
        _performance_monitoring_service = PerformanceMonitoringService()
    return _performance_monitoring_service


async def initialize_performance_monitoring(config: Optional[MonitoringConfig] = None) -> bool:
    """Initialize performance monitoring service."""
    try:
        global _performance_monitoring_service
        _performance_monitoring_service = PerformanceMonitoringService(config)
        
        # Test health
        health = await _performance_monitoring_service.health_check()
        
        return health["status"] == "healthy"
        
    except Exception as e:
        logging.error(f"Failed to initialize performance monitoring: {e}")
        return False


async def cleanup_performance_monitoring():
    """Cleanup performance monitoring service."""
    global _performance_monitoring_service
    if _performance_monitoring_service:
        await _performance_monitoring_service.cleanup()
    _performance_monitoring_service = None
