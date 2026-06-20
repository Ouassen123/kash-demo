"""API performance optimization service for KASH platform."""

import asyncio
import json
import gzip
import time
import logging
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from functools import wraps
import hashlib
import pickle

from fastapi import Request, Response
from fastapi.responses import JSONResponse

# Optional orjson import for faster JSON serialization
try:
    import orjson
    ORJSON_AVAILABLE = True
except ImportError:
    ORJSON_AVAILABLE = False

from ...shared.cache.redis_cache import get_redis_cache, CacheConfig


@dataclass
class APIPerformanceConfig:
    """Configuration for API performance optimization."""
    # Response caching
    enable_response_cache: bool = True
    default_cache_ttl: int = 300  # 5 minutes
    max_cache_size: int = 10000
    cache_key_prefix: str = "api:"
    
    # Serialization optimization
    use_orjson: bool = ORJSON_AVAILABLE,  # Faster JSON serialization if available
    enable_compression: bool = True
    compression_threshold: int = 1024  # Compress responses > 1KB
    compression_level: int = 6
    
    # Rate limiting
    enable_rate_limiting: bool = True
    default_rate_limit: int = 100  # requests per minute
    rate_limit_window: int = 60  # seconds
    
    # Request optimization
    enable_request_validation_cache: bool = True
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    request_timeout: int = 30  # seconds
    
    # Response optimization
    enable_response_optimization: bool = True
    exclude_null_fields: bool = True
    optimize_datetime_format: bool = True
    max_response_size: int = 50 * 1024 * 1024  # 50MB


class APIPerformanceService:
    """API performance optimization service."""
    
    def __init__(self, config: Optional[APIPerformanceConfig] = None):
        self.config = config or APIPerformanceConfig()
        self.logger = logging.getLogger(__name__)
        
        # Cache service
        self.redis_cache = get_redis_cache()
        
        # Performance tracking
        self.performance_stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_response_time_ms": 0.0,
            "compression_savings_bytes": 0,
            "rate_limited_requests": 0,
            "slow_requests": 0,
            "error_requests": 0
        }
        
        # Rate limiting storage
        self.rate_limit_store: Dict[str, List[datetime]] = {}
        
        # Request validation cache
        self.validation_cache: Dict[str, Any] = {}
        
        self.logger.info("API performance service initialized")
    
    def generate_cache_key(self, request: Request, include_query_params: bool = True) -> str:
        """Generate cache key for request."""
        # Base key components
        key_parts = [
            self.config.cache_key_prefix,
            request.method.lower(),
            request.url.path
        ]
        
        # Add query parameters if included
        if include_query_params and request.query_params:
            sorted_params = sorted(request.query_params.items())
            key_parts.extend(f"{k}:{v}" for k, v in sorted_params)
        
        # Add user context if available
        if hasattr(request.state, 'user_id') and request.state.user_id:
            key_parts.append(f"user:{request.state.user_id}")
        
        # Generate key
        key_string = ":".join(key_parts)
        
        # Hash if key is too long
        if len(key_string) > 200:
            key_string = hashlib.md5(key_string.encode()).hexdigest()
        
        return key_string
    
    async def get_cached_response(self, request: Request) -> Optional[Response]:
        """Get cached response for request."""
        if not self.config.enable_response_cache:
            return None
        
        cache_key = self.generate_cache_key(request)
        
        try:
            cached_data = await self.redis_cache.get(cache_key)
            if cached_data:
                self.performance_stats["cache_hits"] += 1
                
                # Create response from cached data
                response_data = cached_data.get("response_data", {})
                headers = cached_data.get("headers", {})
                status_code = cached_data.get("status_code", 200)
                
                # Add cache headers
                headers["X-Cache"] = "HIT"
                headers["X-Cache-Key"] = cache_key
                
                return JSONResponse(
                    content=response_data,
                    status_code=status_code,
                    headers=headers
                )
            
            self.performance_stats["cache_misses"] += 1
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting cached response: {e}")
            return None
    
    async def cache_response(self, request: Request, response: Response, ttl: Optional[int] = None):
        """Cache response for future requests."""
        if not self.config.enable_response_cache:
            return
        
        # Don't cache error responses
        if response.status_code >= 400:
            return
        
        # Don't cache if no-cache header
        cache_control = response.headers.get("cache-control", "")
        if "no-cache" in cache_control.lower():
            return
        
        cache_key = self.generate_cache_key(request)
        
        try:
            # Extract response data
            if hasattr(response, 'body'):
                response_data = orjson.loads(response.body)
            else:
                response_data = response.get("content", {})
            
            # Prepare cache data
            cache_data = {
                "response_data": response_data,
                "headers": dict(response.headers),
                "status_code": response.status_code,
                "cached_at": datetime.utcnow().isoformat()
            }
            
            # Cache with TTL
            cache_ttl = ttl or self.config.default_cache_ttl
            await self.redis_cache.set(
                cache_key, 
                cache_data, 
                ttl=cache_ttl,
                tags=["api_response", request.method.lower(), request.url.path]
            )
            
        except Exception as e:
            self.logger.error(f"Error caching response: {e}")
    
    def optimize_response_data(self, data: Any) -> Any:
        """Optimize response data for faster transmission."""
        if not self.config.enable_response_optimization:
            return data
        
        try:
            if isinstance(data, dict):
                optimized = {}
                
                for key, value in data.items():
                    # Skip null fields if configured
                    if self.config.exclude_null_fields and value is None:
                        continue
                    
                    # Optimize datetime format
                    if self.config.optimize_datetime_format and isinstance(value, datetime):
                        optimized[key] = value.isoformat()
                    else:
                        optimized[key] = value
                
                return optimized
            
            elif isinstance(data, list):
                return [self.optimize_response_data(item) for item in data]
            
            else:
                return data
                
        except Exception as e:
            self.logger.error(f"Error optimizing response data: {e}")
            return data
    
    def serialize_response(self, data: Any) -> bytes:
        """Serialize response data with optimal format."""
        try:
            if self.config.use_orjson and ORJSON_AVAILABLE:
                # Use orjson for faster serialization
                serialized = orjson.dumps(data)
            else:
                # Fallback to standard json
                serialized = json.dumps(data).encode('utf-8')
            
            # Apply compression if enabled and threshold met
            if (self.config.enable_compression and 
                len(serialized) > self.config.compression_threshold):
                
                compressed = gzip.compress(serialized, compresslevel=self.config.compression_level)
                
                # Track compression savings
                savings = len(serialized) - len(compressed)
                self.performance_stats["compression_savings_bytes"] += savings
                
                return compressed, True  # (data, is_compressed)
            
            return serialized, False  # (data, is_compressed)
            
        except Exception as e:
            self.logger.error(f"Error serializing response: {e}")
            return json.dumps({"error": "Serialization failed"}).encode('utf-8'), False
    
    async def check_rate_limit(self, request: Request, limit: Optional[int] = None) -> bool:
        """Check if request is within rate limits."""
        if not self.config.enable_rate_limiting:
            return True
        
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Get rate limit
        rate_limit = limit or self.config.default_rate_limit
        window = self.config.rate_limit_window
        
        # Clean old entries
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=window)
        
        if client_id not in self.rate_limit_store:
            self.rate_limit_store[client_id] = []
        
        # Remove old requests
        self.rate_limit_store[client_id] = [
            req_time for req_time in self.rate_limit_store[client_id] 
            if req_time > cutoff
        ]
        
        # Check if under limit
        if len(self.rate_limit_store[client_id]) >= rate_limit:
            self.performance_stats["rate_limited_requests"] += 1
            return False
        
        # Add current request
        self.rate_limit_store[client_id].append(now)
        return True
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting."""
        # Try to get user ID first
        if hasattr(request.state, 'user_id') and request.state.user_id:
            return f"user:{request.state.user_id}"
        
        # Fall back to IP address
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return f"ip:{forwarded_for.split(',')[0].strip()}"
        
        return f"ip:{request.client.host}"
    
    def validate_request_size(self, request: Request) -> bool:
        """Validate request size."""
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.config.max_request_size:
                    return False
            except ValueError:
                pass
        
        return True
    
    async def get_cached_validation(self, validation_key: str) -> Optional[Any]:
        """Get cached validation result."""
        if not self.config.enable_request_validation_cache:
            return None
        
        return self.validation_cache.get(validation_key)
    
    def cache_validation(self, validation_key: str, result: Any):
        """Cache validation result."""
        if not self.config.enable_request_validation_cache:
            return
        
        # Simple LRU - limit cache size
        if len(self.validation_cache) >= 1000:
            # Remove oldest entries
            keys_to_remove = list(self.validation_cache.keys())[:100]
            for key in keys_to_remove:
                del self.validation_cache[key]
        
        self.validation_cache[validation_key] = result
    
    def update_performance_stats(self, response_time_ms: float, status_code: int):
        """Update performance statistics."""
        self.performance_stats["total_requests"] += 1
        
        # Update average response time
        if self.performance_stats["avg_response_time_ms"] == 0:
            self.performance_stats["avg_response_time_ms"] = response_time_ms
        else:
            alpha = 0.1
            self.performance_stats["avg_response_time_ms"] = (
                alpha * response_time_ms + 
                (1 - alpha) * self.performance_stats["avg_response_time_ms"]
            )
        
        # Track slow requests (> 1 second)
        if response_time_ms > 1000:
            self.performance_stats["slow_requests"] += 1
        
        # Track error requests
        if status_code >= 400:
            self.performance_stats["error_requests"] += 1
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics."""
        total_requests = self.performance_stats["total_requests"]
        
        # Calculate cache hit rate
        cache_total = self.performance_stats["cache_hits"] + self.performance_stats["cache_misses"]
        cache_hit_rate = (
            self.performance_stats["cache_hits"] / cache_total 
            if cache_total > 0 else 0
        )
        
        # Calculate error rate
        error_rate = (
            self.performance_stats["error_requests"] / total_requests 
            if total_requests > 0 else 0
        )
        
        # Calculate slow request rate
        slow_rate = (
            self.performance_stats["slow_requests"] / total_requests 
            if total_requests > 0 else 0
        )
        
        return {
            **self.performance_stats,
            "cache_hit_rate": cache_hit_rate,
            "error_rate": error_rate,
            "slow_request_rate": slow_rate,
            "compression_savings_mb": self.performance_stats["compression_savings_bytes"] / (1024 * 1024),
            "active_rate_limits": len(self.rate_limit_store),
            "validation_cache_size": len(self.validation_cache)
        }
    
    def reset_stats(self):
        """Reset performance statistics."""
        self.performance_stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_response_time_ms": 0.0,
            "compression_savings_bytes": 0,
            "rate_limited_requests": 0,
            "slow_requests": 0,
            "error_requests": 0
        }
    
    async def cleanup_expired_entries(self):
        """Clean up expired rate limit entries."""
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.config.rate_limit_window)
        
        for client_id, requests in list(self.rate_limit_store.items()):
            # Remove old requests
            self.rate_limit_store[client_id] = [
                req_time for req_time in requests 
                if req_time > cutoff
            ]
            
            # Remove empty entries
            if not self.rate_limit_store[client_id]:
                del self.rate_limit_store[client_id]


# Performance optimization decorators

def cache_response(ttl_seconds: int = 300, include_query_params: bool = True):
    """Decorator for caching API responses."""
    def decorator(endpoint_func: Callable):
        @wraps(endpoint_func)
        async def wrapper(*args, **kwargs):
            # Get performance service
            perf_service = APIPerformanceService()
            
            # Try to get request from args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # Try to get from kwargs
                request = kwargs.get('request')
            
            if not request:
                # No request found, just execute function
                return await endpoint_func(*args, **kwargs)
            
            # Check cache
            cached_response = await perf_service.get_cached_response(request)
            if cached_response:
                return cached_response
            
            # Execute endpoint
            start_time = time.time()
            response = await endpoint_func(*args, **kwargs)
            response_time = (time.time() - start_time) * 1000
            
            # Cache response
            await perf_service.cache_response(request, response, ttl_seconds)
            
            # Update stats
            status_code = getattr(response, 'status_code', 200)
            perf_service.update_performance_stats(response_time, status_code)
            
            return response
        
        return wrapper
    return decorator


def rate_limit(requests_per_minute: int = 100):
    """Decorator for rate limiting endpoints."""
    def decorator(endpoint_func: Callable):
        @wraps(endpoint_func)
        async def wrapper(*args, **kwargs):
            # Get performance service
            perf_service = APIPerformanceService()
            
            # Try to get request from args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                request = kwargs.get('request')
            
            if not request:
                # No request found, just execute function
                return await endpoint_func(*args, **kwargs)
            
            # Check rate limit
            if not await perf_service.check_rate_limit(request, requests_per_minute):
                return JSONResponse(
                    status_code=429,
                    content={"error": "Rate limit exceeded"},
                    headers={
                        "Retry-After": str(perf_service.config.rate_limit_window),
                        "X-RateLimit-Limit": str(requests_per_minute),
                        "X-RateLimit-Window": str(perf_service.config.rate_limit_window)
                    }
                )
            
            # Execute endpoint
            return await endpoint_func(*args, **kwargs)
        
        return wrapper
    return decorator


def optimize_response():
    """Decorator for optimizing API responses."""
    def decorator(endpoint_func: Callable):
        @wraps(endpoint_func)
        async def wrapper(*args, **kwargs):
            # Get performance service
            perf_service = APIPerformanceService()
            
            # Execute endpoint
            start_time = time.time()
            response = await endpoint_func(*args, **kwargs)
            response_time = (time.time() - start_time) * 1000
            
            # Optimize response data
            if hasattr(response, 'content'):
                optimized_content = perf_service.optimize_response_data(response.content)
                response.content = optimized_content
            
            # Update stats
            status_code = getattr(response, 'status_code', 200)
            perf_service.update_performance_stats(response_time, status_code)
            
            return response
        
        return wrapper
    return decorator


# Global API performance service
_api_performance_service: Optional[APIPerformanceService] = None


def get_api_performance_service() -> APIPerformanceService:
    """Get global API performance service."""
    global _api_performance_service
    if _api_performance_service is None:
        _api_performance_service = APIPerformanceService()
    return _api_performance_service


# Middleware for FastAPI
class PerformanceMiddleware:
    """FastAPI middleware for performance optimization."""
    
    def __init__(self, app, config: Optional[APIPerformanceConfig] = None):
        self.app = app
        self.config = config or APIPerformanceConfig()
        self.perf_service = APIPerformanceService(self.config)
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Create request-like object for performance service
        class MockRequest:
            def __init__(self, scope):
                self.method = scope["method"]
                self.path = scope["path"]
                self.query_string = scope.get("query_string", b"").decode()
                self.headers = dict(scope.get("headers", []))
        
        request = MockRequest(scope)
        start_time = time.time()
        
        # Process request
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Calculate response time
                response_time = (time.time() - start_time) * 1000
                status_code = message.get("status", 200)
                
                # Update performance stats
                self.perf_service.update_performance_stats(response_time, status_code)
                
                # Add performance headers
                headers = list(message.get("headers", []))
                headers.append([b"x-response-time-ms", str(int(response_time)).encode()])
                headers.append([b"x-cache-status", b"MISS"])
                message["headers"] = headers
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)
