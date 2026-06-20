"""Shared cache module for KASH platform performance optimization."""

from .redis_cache import (
    CacheConfig, CacheEntry, CacheStats, RedisCacheService,
    ESCOCacheService, PredictionCacheService, CompatibilityCacheService,
    get_redis_cache, get_esco_cache, get_prediction_cache, get_compatibility_cache,
    initialize_cache, cleanup_cache
)

__all__ = [
    # Core classes
    "CacheConfig",
    "CacheEntry", 
    "CacheStats",
    "RedisCacheService",
    
    # Specialized services
    "ESCOCacheService",
    "PredictionCacheService",
    "CompatibilityCacheService",
    
    # Global functions
    "get_redis_cache",
    "get_esco_cache", 
    "get_prediction_cache",
    "get_compatibility_cache",
    "initialize_cache",
    "cleanup_cache"
]
