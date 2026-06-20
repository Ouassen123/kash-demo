"""Performance optimization module for KASH platform."""

from .database_optimization import (
    DatabaseConfig, DatabaseOptimizationService,
    get_database_service, initialize_database, cleanup_database,
    optimize_query
)

from .api_optimization import (
    APIPerformanceConfig, APIPerformanceService,
    get_api_performance_service, cache_response, rate_limit, optimize_response,
    PerformanceMiddleware
)

from .ml_optimization import (
    MLPerformanceConfig, MLPerformanceService,
    get_ml_performance_service, initialize_ml_performance, cleanup_ml_performance
)

__all__ = [
    # Database optimization
    "DatabaseConfig",
    "DatabaseOptimizationService", 
    "get_database_service",
    "initialize_database",
    "cleanup_database",
    "optimize_query",
    
    # API optimization
    "APIPerformanceConfig",
    "APIPerformanceService",
    "get_api_performance_service",
    "cache_response",
    "rate_limit", 
    "optimize_response",
    "PerformanceMiddleware",
    
    # ML optimization
    "MLPerformanceConfig",
    "MLPerformanceService",
    "get_ml_performance_service",
    "initialize_ml_performance",
    "cleanup_ml_performance"
]
