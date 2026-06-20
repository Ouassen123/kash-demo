"""Redis caching service for KASH platform performance optimization."""

import json
import pickle
import hashlib
from typing import Any, Optional, Dict, List, Union, Callable
from datetime import datetime, timedelta
import logging
from functools import wraps
import asyncio
from dataclasses import dataclass

# Optional Redis import
try:
    import redis.asyncio as redis
    import redis.exceptions
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from pydantic import BaseModel, Field


@dataclass
class CacheConfig:
    """Configuration for Redis caching."""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    ssl: bool = False
    connection_pool_size: int = 10
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    max_connections: int = 50
    
    # Default TTL settings (in seconds)
    default_ttl: int = 3600  # 1 hour
    short_ttl: int = 300     # 5 minutes
    long_ttl: int = 86400    # 24 hours
    static_ttl: int = 604800 # 1 week
    
    # Cache key prefixes
    prefix: str = "kash:"
    esco_prefix: str = "esco:"
    onet_prefix: str = "onet:"
    prediction_prefix: str = "pred:"
    compatibility_prefix: str = "comp:"
    user_prefix: str = "user:"


class CacheEntry(BaseModel):
    """Cache entry with metadata."""
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    size_bytes: int = 0
    tags: List[str] = Field(default_factory=list)
    version: str = "1.0"
    
    class Config:
        arbitrary_types_allowed = True


class CacheStats(BaseModel):
    """Cache statistics."""
    total_keys: int = 0
    hit_count: int = 0
    miss_count: int = 0
    hit_rate: float = 0.0
    memory_usage_bytes: int = 0
    eviction_count: int = 0
    connection_count: int = 0
    avg_response_time_ms: float = 0.0
    
    # Detailed stats by prefix
    stats_by_prefix: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class RedisCacheService:
    """High-performance Redis caching service for KASH platform."""
    
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self.redis_client: Optional[redis.Redis] = None
        self.connection_pool: Optional[redis.ConnectionPool] = None
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.stats = CacheStats()
        self._start_time = datetime.utcnow()
        
        # Initialize Redis connection
        self._initialize_redis()
        
        self.logger.info("Redis cache service initialized")
    
    def _initialize_redis(self):
        """Initialize Redis connection pool and client."""
        if not REDIS_AVAILABLE:
            self.logger.warning("Redis not available, cache will be disabled")
            return
        
        try:
            # Create connection pool
            self.connection_pool = redis.ConnectionPool(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password,
                ssl=self.config.ssl,
                max_connections=self.config.max_connections,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                retry_on_timeout=True,
                decode_responses=False  # Keep binary for pickle
            )
            
            # Create Redis client
            self.redis_client = redis.Redis(connection_pool=self.connection_pool)
            
            # Test connection
            asyncio.create_task(self._test_connection())
            
            self.logger.info(f"Redis connection established: {self.config.host}:{self.config.port}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Redis: {e}")
            self.redis_client = None
    
    async def _test_connection(self):
        """Test Redis connection."""
        if self.redis_client:
            try:
                await self.redis_client.ping()
                self.logger.info("Redis connection test successful")
            except Exception as e:
                self.logger.error(f"Redis connection test failed: {e}")
    
    def _generate_key(self, prefix: str, key_parts: List[str]) -> str:
        """Generate cache key with prefix and parts."""
        key = self.config.prefix + prefix + ":" + ":".join(str(part) for part in key_parts)
        return key
    
    def _hash_key(self, key: str) -> str:
        """Generate hash for long keys."""
        if len(key) > 200:
            return hashlib.md5(key.encode()).hexdigest()
        return key
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        if not self.redis_client:
            return default
        
        start_time = datetime.utcnow()
        
        try:
            # Generate full key
            full_key = self._generate_key("", [key])
            full_key = self._hash_key(full_key)
            
            # Get from Redis
            data = await self.redis_client.get(full_key)
            
            if data is None:
                self.stats.miss_count += 1
                return default
            
            # Deserialize
            cache_entry = pickle.loads(data)
            
            # Update access stats
            cache_entry.access_count += 1
            cache_entry.last_accessed = datetime.utcnow()
            
            # Update cache entry
            await self.redis_client.set(full_key, pickle.dumps(cache_entry))
            
            # Update stats
            self.stats.hit_count += 1
            self._update_hit_rate()
            
            # Track response time
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self._update_response_time(response_time)
            
            return cache_entry.value
            
        except Exception as e:
            self.logger.error(f"Cache get error for key {key}: {e}")
            return default
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None, 
                  tags: Optional[List[str]] = None) -> bool:
        """Set value in cache."""
        if not self.redis_client:
            return False
        
        try:
            # Generate full key
            full_key = self._generate_key("", [key])
            full_key = self._hash_key(full_key)
            
            # Create cache entry
            now = datetime.utcnow()
            cache_entry = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                expires_at=now + timedelta(seconds=ttl or self.config.default_ttl),
                size_bytes=len(pickle.dumps(value)),
                tags=tags or []
            )
            
            # Serialize and store
            data = pickle.dumps(cache_entry)
            await self.redis_client.setex(
                full_key, 
                ttl or self.config.default_ttl, 
                data
            )
            
            # Update stats
            self.stats.total_keys += 1
            
            return True
            
        except Exception as e:
            self.logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.redis_client:
            return False
        
        try:
            full_key = self._generate_key("", [key])
            full_key = self._hash_key(full_key)
            
            result = await self.redis_client.delete(full_key)
            
            if result:
                self.stats.total_keys = max(0, self.stats.total_keys - 1)
            
            return result > 0
            
        except Exception as e:
            self.logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def clear_prefix(self, prefix: str) -> int:
        """Clear all keys with given prefix."""
        if not self.redis_client:
            return 0
        
        try:
            full_prefix = self._generate_key(prefix, [])
            pattern = full_prefix + "*"
            
            # Get all keys with pattern
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)
            
            # Delete keys
            if keys:
                deleted = await self.redis_client.delete(*keys)
                self.stats.total_keys = max(0, self.stats.total_keys - deleted)
                return deleted
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Cache clear prefix error for {prefix}: {e}")
            return 0
    
    async def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        if not self.redis_client:
            return self.stats
        
        try:
            # Get Redis info
            info = await self.redis_client.info()
            
            # Update basic stats
            self.stats.memory_usage_bytes = info.get('used_memory', 0)
            self.stats.eviction_count = info.get('evicted_keys', 0)
            self.stats.connection_count = info.get('connected_clients', 0)
            
            # Calculate hit rate
            self._update_hit_rate()
            
            return self.stats
            
        except Exception as e:
            self.logger.error(f"Error getting cache stats: {e}")
            return self.stats
    
    def _update_hit_rate(self):
        """Update hit rate calculation."""
        total_requests = self.stats.hit_count + self.stats.miss_count
        if total_requests > 0:
            self.stats.hit_rate = self.stats.hit_count / total_requests
    
    def _update_response_time(self, response_time_ms: float):
        """Update average response time."""
        if self.stats.avg_response_time_ms == 0:
            self.stats.avg_response_time_ms = response_time_ms
        else:
            # Simple moving average
            alpha = 0.1
            self.stats.avg_response_time_ms = (
                alpha * response_time_ms + 
                (1 - alpha) * self.stats.avg_response_time_ms
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for cache service."""
        health = {
            "status": "unhealthy",
            "redis_available": REDIS_AVAILABLE,
            "connection_status": "disconnected",
            "stats": self.stats.model_dump(),
            "uptime_seconds": (datetime.utcnow() - self._start_time).total_seconds()
        }
        
        if self.redis_client:
            try:
                # Test Redis connection
                await self.redis_client.ping()
                health["status"] = "healthy"
                health["connection_status"] = "connected"
            except Exception as e:
                health["connection_status"] = f"error: {str(e)}"
        
        return health
    
    def cache_decorator(self, ttl: Optional[int] = None, 
                       key_prefix: str = "", 
                       tags: Optional[List[str]] = None):
        """Decorator for caching function results."""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                key_parts = [key_prefix, func.__name__]
                
                # Add args to key
                for arg in args:
                    if isinstance(arg, (str, int, float, bool)):
                        key_parts.append(str(arg))
                    else:
                        key_parts.append(str(hash(str(arg))))
                
                # Add kwargs to key
                for k, v in sorted(kwargs.items()):
                    key_parts.append(f"{k}:{v}")
                
                cache_key = ":".join(key_parts)
                
                # Try to get from cache
                cached_result = await self.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Cache result
                await self.set(cache_key, result, ttl=ttl, tags=tags)
                
                return result
            
            return wrapper
        return decorator
    
    async def close(self):
        """Close Redis connections."""
        if self.connection_pool:
            await self.connection_pool.disconnect()
            self.logger.info("Redis connections closed")


# Specialized cache services for different data types

class ESCOCacheService:
    """Specialized cache for ESCO taxonomy data."""
    
    def __init__(self, redis_cache: RedisCacheService):
        self.cache = redis_cache
        self.config = redis_cache.config
        self.logger = logging.getLogger(__name__)
    
    async def get_occupation(self, occupation_id: str) -> Optional[Dict[str, Any]]:
        """Get occupation data from cache."""
        key = self._generate_key(["occupation", occupation_id])
        return await self.cache.get(key)
    
    async def set_occupation(self, occupation_id: str, data: Dict[str, Any]) -> bool:
        """Set occupation data in cache."""
        key = self._generate_key(["occupation", occupation_id])
        return await self.cache.set(key, data, ttl=self.config.long_ttl, tags=["esco", "occupation"])
    
    async def get_skills(self, skill_ids: List[str]) -> Dict[str, Any]:
        """Get multiple skills from cache."""
        result = {}
        for skill_id in skill_ids:
            skill_data = await self.get_skill(skill_id)
            if skill_data:
                result[skill_id] = skill_data
        return result
    
    async def get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """Get skill data from cache."""
        key = self._generate_key(["skill", skill_id])
        return await self.cache.get(key)
    
    async def set_skill(self, skill_id: str, data: Dict[str, Any]) -> bool:
        """Set skill data in cache."""
        key = self._generate_key(["skill", skill_id])
        return await self.cache.set(key, data, ttl=self.config.long_ttl, tags=["esco", "skill"])
    
    async def search_occupations(self, query: str, limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """Get search results from cache."""
        key = self._generate_key(["search", "occupations", query, str(limit)])
        return await self.cache.get(key)
    
    async def set_search_occupations(self, query: str, limit: int, results: List[Dict[str, Any]]) -> bool:
        """Set search results in cache."""
        key = self._generate_key(["search", "occupations", query, str(limit)])
        return await self.cache.set(key, results, ttl=self.config.short_ttl, tags=["esco", "search"])
    
    def _generate_key(self, parts: List[str]) -> str:
        """Generate ESCO cache key."""
        return self.cache._generate_key(self.config.esco_prefix, parts)


class PredictionCacheService:
    """Specialized cache for ML predictions."""
    
    def __init__(self, redis_cache: RedisCacheService):
        self.cache = redis_cache
        self.config = redis_cache.config
        self.logger = logging.getLogger(__name__)
    
    async def get_prediction(self, model_id: str, feature_hash: str) -> Optional[Dict[str, Any]]:
        """Get prediction from cache."""
        key = self._generate_key(["prediction", model_id, feature_hash])
        return await self.cache.get(key)
    
    async def set_prediction(self, model_id: str, feature_hash: str, prediction: Dict[str, Any]) -> bool:
        """Set prediction in cache."""
        key = self._generate_key(["prediction", model_id, feature_hash])
        return await self.cache.set(key, prediction, ttl=self.config.default_ttl, tags=["prediction", model_id])
    
    async def get_batch_predictions(self, model_id: str, batch_hash: str) -> Optional[List[Dict[str, Any]]]:
        """Get batch predictions from cache."""
        key = self._generate_key(["batch", model_id, batch_hash])
        return await self.cache.get(key)
    
    async def set_batch_predictions(self, model_id: str, batch_hash: str, predictions: List[Dict[str, Any]]) -> bool:
        """Set batch predictions in cache."""
        key = self._generate_key(["batch", model_id, batch_hash])
        return await self.cache.set(key, predictions, ttl=self.config.default_ttl, tags=["prediction", "batch", model_id])
    
    async def get_feature_importance(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get feature importance from cache."""
        key = self._generate_key(["feature_importance", model_id])
        return await self.cache.get(key)
    
    async def set_feature_importance(self, model_id: str, importance: Dict[str, Any]) -> bool:
        """Set feature importance in cache."""
        key = self._generate_key(["feature_importance", model_id])
        return await self.cache.set(key, importance, ttl=self.config.long_ttl, tags=["prediction", "features", model_id])
    
    def _generate_key(self, parts: List[str]) -> str:
        """Generate prediction cache key."""
        return self.cache._generate_key(self.config.prediction_prefix, parts)


class CompatibilityCacheService:
    """Specialized cache for compatibility scores."""
    
    def __init__(self, redis_cache: RedisCacheService):
        self.cache = redis_cache
        self.config = redis_cache.config
        self.logger = logging.getLogger(__name__)
    
    async def get_compatibility_score(self, learner_id: str, job_family: str) -> Optional[Dict[str, Any]]:
        """Get compatibility score from cache."""
        key = self._generate_key(["score", learner_id, job_family])
        return await self.cache.get(key)
    
    async def set_compatibility_score(self, learner_id: str, job_family: str, score: Dict[str, Any]) -> bool:
        """Set compatibility score in cache."""
        key = self._generate_key(["score", learner_id, job_family])
        return await self.cache.set(key, score, ttl=self.config.default_ttl, tags=["compatibility", "score"])
    
    async def get_learner_profile(self, learner_id: str) -> Optional[Dict[str, Any]]:
        """Get learner profile from cache."""
        key = self._generate_key(["profile", learner_id])
        return await self.cache.get(key)
    
    async def set_learner_profile(self, learner_id: str, profile: Dict[str, Any]) -> bool:
        """Set learner profile in cache."""
        key = self._generate_key(["profile", learner_id])
        return await self.cache.set(key, profile, ttl=self.config.short_ttl, tags=["compatibility", "profile"])
    
    async def get_job_family_data(self, job_family: str) -> Optional[Dict[str, Any]]:
        """Get job family data from cache."""
        key = self._generate_key(["job_family", job_family])
        return await self.cache.get(key)
    
    async def set_job_family_data(self, job_family: str, data: Dict[str, Any]) -> bool:
        """Set job family data in cache."""
        key = self._generate_key(["job_family", job_family])
        return await self.cache.set(key, data, ttl=self.config.long_ttl, tags=["compatibility", "job_family"])
    
    def _generate_key(self, parts: List[str]) -> str:
        """Generate compatibility cache key."""
        return self.cache._generate_key(self.config.compatibility_prefix, parts)


# Global cache instances
_redis_cache: Optional[RedisCacheService] = None
_esco_cache: Optional[ESCOCacheService] = None
_prediction_cache: Optional[PredictionCacheService] = None
_compatibility_cache: Optional[CompatibilityCacheService] = None


def get_redis_cache() -> RedisCacheService:
    """Get global Redis cache instance."""
    global _redis_cache
    if _redis_cache is None:
        _redis_cache = RedisCacheService()
    return _redis_cache


def get_esco_cache() -> ESCOCacheService:
    """Get global ESCO cache instance."""
    global _esco_cache
    if _esco_cache is None:
        _esco_cache = ESCOCacheService(get_redis_cache())
    return _esco_cache


def get_prediction_cache() -> PredictionCacheService:
    """Get global prediction cache instance."""
    global _prediction_cache
    if _prediction_cache is None:
        _prediction_cache = PredictionCacheService(get_redis_cache())
    return _prediction_cache


def get_compatibility_cache() -> CompatibilityCacheService:
    """Get global compatibility cache instance."""
    global _compatibility_cache
    if _compatibility_cache is None:
        _compatibility_cache = CompatibilityCacheService(get_redis_cache())
    return _compatibility_cache


# Cache initialization function
async def initialize_cache(config: Optional[CacheConfig] = None) -> bool:
    """Initialize cache services."""
    try:
        global _redis_cache, _esco_cache, _prediction_cache, _compatibility_cache
        
        _redis_cache = RedisCacheService(config)
        _esco_cache = ESCOCacheService(_redis_cache)
        _prediction_cache = PredictionCacheService(_redis_cache)
        _compatibility_cache = CompatibilityCacheService(_redis_cache)
        
        # Test connection
        health = await _redis_cache.health_check()
        
        return health["status"] == "healthy"
        
    except Exception as e:
        logging.error(f"Failed to initialize cache: {e}")
        return False


# Cache cleanup function
async def cleanup_cache():
    """Cleanup cache connections."""
    global _redis_cache, _esco_cache, _prediction_cache, _compatibility_cache
    
    if _redis_cache:
        await _redis_cache.close()
    
    _redis_cache = None
    _esco_cache = None
    _prediction_cache = None
    _compatibility_cache = None
