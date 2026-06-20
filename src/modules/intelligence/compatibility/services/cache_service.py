"""Cache service for compatibility scores with intelligent invalidation."""

import json
import hashlib
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from ..models import (
    CompatibilityScore,
    CompatibilityScoreResponse,
    CompatibilityScoreRequest,
    JobFamilyEnum,
    DataFreshness
)


class CacheHitStatus(str, Enum):
    """Cache hit status."""
    HIT = "hit"
    MISS = "miss"
    STALE = "stale"
    EXPIRED = "expired"


@dataclass
class CacheEntry:
    """Individual cache entry."""
    key: str
    value: CompatibilityScoreResponse
    created_at: datetime
    expires_at: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    # Cache metadata
    source_version: str = "1.0"
    signal_hashes: List[str] = None
    weight_config_hash: str = ""
    
    def __post_init__(self):
        if self.signal_hashes is None:
            self.signal_hashes = []
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_stale(self, max_age_minutes: int = 30) -> bool:
        """Check if cache entry is stale."""
        age = datetime.utcnow() - self.created_at
        return age > timedelta(minutes=max_age_minutes)
    
    @property
    def age_seconds(self) -> int:
        """Get age of cache entry in seconds."""
        return int((datetime.utcnow() - self.created_at).total_seconds())
    
    def mark_accessed(self):
        """Mark cache entry as accessed."""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()


@dataclass
class CacheStats:
    """Cache statistics."""
    total_entries: int = 0
    hit_count: int = 0
    miss_count: int = 0
    stale_count: int = 0
    expired_count: int = 0
    
    # Performance metrics
    avg_access_time_ms: float = 0.0
    total_access_time_ms: float = 0.0
    access_count: int = 0
    
    # Size metrics
    total_size_bytes: int = 0
    avg_entry_size_bytes: float = 0.0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total_requests = self.hit_count + self.miss_count
        return self.hit_count / total_requests if total_requests > 0 else 0.0
    
    @property
    def miss_rate(self) -> float:
        """Calculate cache miss rate."""
        return 1.0 - self.hit_rate
    
    def record_hit(self, access_time_ms: float):
        """Record a cache hit."""
        self.hit_count += 1
        self._record_access(access_time_ms)
    
    def record_miss(self, access_time_ms: float):
        """Record a cache miss."""
        self.miss_count += 1
        self._record_access(access_time_ms)
    
    def record_stale(self):
        """Record a stale cache hit."""
        self.stale_count += 1
    
    def record_expired(self):
        """Record an expired cache entry."""
        self.expired_count += 1
    
    def _record_access(self, access_time_ms: float):
        """Record cache access time."""
        self.access_count += 1
        self.total_access_time_ms += access_time_ms
        self.avg_access_time_ms = self.total_access_time_ms / self.access_count


class CacheInvalidationRule:
    """Rule for cache invalidation."""
    
    def __init__(self, rule_id: str, condition: str, action: str, priority: int = 0):
        self.rule_id = rule_id
        self.condition = condition  # e.g., "signal_updated", "config_changed"
        self.action = action  # e.g., "invalidate_learner", "invalidate_job_family"
        self.priority = priority
        self.created_at = datetime.utcnow()
    
    def should_invalidate(self, event_type: str, context: Dict[str, Any]) -> bool:
        """Check if this rule should invalidate cache based on event."""
        # Simple condition matching - can be extended with more complex logic
        return self.condition == event_type
    
    def get_invalidation_keys(self, context: Dict[str, Any]) -> List[str]:
        """Get cache keys to invalidate based on context."""
        if self.action == "invalidate_learner":
            learner_id = context.get("learner_id")
            if learner_id:
                return [f"learner:{learner_id}:*"]
        
        elif self.action == "invalidate_job_family":
            job_family = context.get("job_family")
            if job_family:
                return [f"job_family:{job_family}:*"]
        
        elif self.action == "invalidate_signal":
            signal_id = context.get("signal_id")
            if signal_id:
                # Invalidate all entries that might use this signal
                return [f"*:*:{signal_id}"]
        
        return []


class CompatibilityCacheService:
    """High-performance cache service for compatibility scores."""
    
    def __init__(self, cache_dir: Optional[Path] = None, 
                 max_entries: int = 10000,
                 default_ttl_minutes: int = 60):
        self.cache_dir = cache_dir or Path(__file__).parent.parent / "data" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache configuration
        self.max_entries = max_entries
        self.default_ttl_minutes = default_ttl_minutes
        
        # In-memory cache for fast access
        self.cache: Dict[str, CacheEntry] = {}
        
        # Persistent storage
        self.cache_file = self.cache_dir / "compatibility_cache.json"
        self.index_file = self.cache_dir / "cache_index.json"
        
        # Statistics
        self.stats = CacheStats()
        
        # Invalidation rules
        self.invalidation_rules = [
            CacheInvalidationRule("learner_update", "signal_updated", "invalidate_learner", priority=1),
            CacheInvalidationRule("config_change", "config_changed", "invalidate_job_family", priority=2),
            CacheInvalidationRule("signal_change", "signal_updated", "invalidate_signal", priority=0),
        ]
        
        # Load existing cache
        self._load_cache()
        self._cleanup_expired()
    
    def _generate_cache_key(self, request: CompatibilityScoreRequest) -> str:
        """Generate cache key for a request."""
        # Create a hash of the request parameters
        key_data = {
            "learner_id": request.learner_id,
            "job_family": request.job_family.value,
            "target_job_id": request.target_job_id,
            "weight_configuration_id": request.weight_configuration_id,
            "min_signal_quality": request.min_signal_quality.value,
            "max_signal_age_days": request.max_signal_age_days,
            "confidence_level": request.confidence_level
        }
        
        # Include signal hashes for more precise caching
        signal_hashes = []
        for signal in sorted(request.kash_signals, key=lambda x: x.signal_id):
            signal_data = f"{signal.signal_id}:{signal.normalized_score}:{signal.confidence}"
            signal_hash = hashlib.md5(signal_data.encode()).hexdigest()[:8]
            signal_hashes.append(signal_hash)
        
        key_data["signal_hashes"] = signal_hashes
        
        # Generate final key
        key_string = json.dumps(key_data, sort_keys=True)
        hash_key = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"compatibility:{request.learner_id}:{request.job_family.value}:{hash_key}"
    
    def _calculate_signal_hashes(self, signals: List) -> List[str]:
        """Calculate hashes for signals."""
        hashes = []
        for signal in sorted(signals, key=lambda x: x.signal_id):
            signal_data = f"{signal.signal_id}:{signal.normalized_score}:{signal.confidence}"
            signal_hash = hashlib.md5(signal_data.encode()).hexdigest()[:8]
            hashes.append(signal_hash)
        return hashes
    
    def _calculate_weight_config_hash(self, weight_config_id: str) -> str:
        """Calculate hash for weight configuration."""
        return hashlib.md5(weight_config_id.encode()).hexdigest()[:8]
    
    def get(self, request: CompatibilityScoreRequest) -> Tuple[Optional[CompatibilityScoreResponse], CacheHitStatus]:
        """Get cached compatibility score."""
        start_time = time.time()
        cache_key = self._generate_cache_key(request)
        
        entry = self.cache.get(cache_key)
        
        if not entry:
            self.stats.record_miss((time.time() - start_time) * 1000)
            return None, CacheHitStatus.MISS
        
        # Check if entry is expired
        if entry.is_expired:
            self.stats.record_expired()
            self.stats.record_miss((time.time() - start_time) * 1000)
            # Remove expired entry
            del self.cache[cache_key]
            return None, CacheHitStatus.EXPIRED
        
        # Check if entry is stale
        if entry.is_stale:
            self.stats.record_stale()
            status = CacheHitStatus.STALE
        else:
            status = CacheHitStatus.HIT
        
        # Mark as accessed
        entry.mark_accessed()
        
        access_time_ms = (time.time() - start_time) * 1000
        self.stats.record_hit(access_time_ms)
        
        return entry.value, status
    
    def put(self, request: CompatibilityScoreRequest, response: CompatibilityScoreResponse,
            ttl_minutes: Optional[int] = None) -> str:
        """Store compatibility score in cache."""
        cache_key = self._generate_cache_key(request)
        ttl_minutes = ttl_minutes or self.default_ttl_minutes
        
        # Create cache entry
        entry = CacheEntry(
            key=cache_key,
            value=response,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=ttl_minutes),
            source_version="1.0",
            signal_hashes=self._calculate_signal_hashes(request.kash_signals),
            weight_config_hash=self._calculate_weight_config_hash(
                response.compatibility_score.weight_configuration
            )
        )
        
        # Add to cache
        self.cache[cache_key] = entry
        
        # Evict old entries if cache is full
        if len(self.cache) > self.max_entries:
            self._evict_lru()
        
        # Update statistics
        self._update_stats()
        
        # Save to disk
        self._save_cache()
        
        return cache_key
    
    def invalidate(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern."""
        keys_to_remove = []
        
        if "*" in pattern:
            # Pattern matching
            import fnmatch
            for key in self.cache.keys():
                if fnmatch.fnmatch(key, pattern):
                    keys_to_remove.append(key)
        else:
            # Exact match
            if pattern in self.cache:
                keys_to_remove.append(pattern)
        
        # Remove entries
        for key in keys_to_remove:
            del self.cache[key]
        
        # Update statistics and save
        self._update_stats()
        self._save_cache()
        
        return len(keys_to_remove)
    
    def invalidate_by_learner(self, learner_id: str) -> int:
        """Invalidate all cache entries for a learner."""
        pattern = f"compatibility:{learner_id}:*"
        return self.invalidate(pattern)
    
    def invalidate_by_job_family(self, job_family: str) -> int:
        """Invalidate all cache entries for a job family."""
        pattern = f"compatibility:*:{job_family}:*"
        return self.invalidate(pattern)
    
    def invalidate_by_signal(self, signal_id: str) -> int:
        """Invalidate cache entries that might use a specific signal."""
        # This is a simplified implementation
        # In practice, you'd need to track which cache entries use which signals
        invalidated = 0
        
        for key, entry in list(self.cache.items()):
            # Check if signal hash is in entry's signal hashes
            signal_hash = hashlib.md5(signal_id.encode()).hexdigest()[:8]
            if signal_hash in entry.signal_hashes:
                del self.cache[key]
                invalidated += 1
        
        self._update_stats()
        self._save_cache()
        
        return invalidated
    
    def process_invalidation_event(self, event_type: str, context: Dict[str, Any]) -> int:
        """Process invalidation event and apply relevant rules."""
        total_invalidated = 0
        
        # Sort rules by priority (higher priority first)
        sorted_rules = sorted(self.invalidation_rules, key=lambda x: x.priority, reverse=True)
        
        for rule in sorted_rules:
            if rule.should_invalidate(event_type, context):
                patterns = rule.get_invalidation_keys(context)
                for pattern in patterns:
                    invalidated = self.invalidate(pattern)
                    total_invalidated += invalidated
        
        return total_invalidated
    
    def _evict_lru(self):
        """Evict least recently used entries."""
        # Sort by last accessed time (oldest first)
        sorted_entries = sorted(
            self.cache.items(),
            key=lambda x: x[1].last_accessed or x[1].created_at
        )
        
        # Remove oldest 10% of entries
        entries_to_remove = max(1, len(self.cache) // 10)
        
        for i in range(entries_to_remove):
            if i < len(sorted_entries):
                key = sorted_entries[i][0]
                del self.cache[key]
    
    def _cleanup_expired(self):
        """Remove expired entries."""
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.is_expired
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            self._save_cache()
    
    def _update_stats(self):
        """Update cache statistics."""
        self.stats.total_entries = len(self.cache)
        
        # Calculate size metrics
        total_size = 0
        for entry in self.cache.values():
            # Estimate size of entry
            entry_size = len(json.dumps(entry.value.model_dump(), default=str))
            total_size += entry_size
        
        self.stats.total_size_bytes = total_size
        self.stats.avg_entry_size_bytes = total_size / len(self.cache) if self.cache else 0
    
    def _load_cache(self):
        """Load cache from disk."""
        if not self.cache_file.exists():
            return
        
        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
            
            for key, entry_data in data.items():
                # Convert datetime strings back to datetime objects
                entry_data["created_at"] = datetime.fromisoformat(entry_data["created_at"])
                entry_data["expires_at"] = datetime.fromisoformat(entry_data["expires_at"])
                
                if entry_data.get("last_accessed"):
                    entry_data["last_accessed"] = datetime.fromisoformat(entry_data["last_accessed"])
                
                # Recreate CompatibilityScoreResponse
                response_data = entry_data.pop("value")
                entry_data["value"] = CompatibilityScoreResponse(**response_data)
                
                self.cache[key] = CacheEntry(**entry_data)
            
        except Exception as e:
            print(f"Error loading cache: {e}")
            self.cache = {}
    
    def _save_cache(self):
        """Save cache to disk."""
        try:
            data = {}
            for key, entry in self.cache.items():
                entry_dict = asdict(entry)
                # Convert datetime objects to strings
                entry_dict["created_at"] = entry.created_at.isoformat()
                entry_dict["expires_at"] = entry.expires_at.isoformat()
                
                if entry.last_accessed:
                    entry_dict["last_accessed"] = entry.last_accessed.isoformat()
                
                # Convert CompatibilityScoreResponse to dict
                entry_dict["value"] = entry.value.model_dump()
                
                data[key] = entry_dict
            
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
                
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        self._update_stats()
        
        return {
            "total_entries": self.stats.total_entries,
            "hit_rate": self.stats.hit_rate,
            "miss_rate": self.stats.miss_rate,
            "hit_count": self.stats.hit_count,
            "miss_count": self.stats.miss_count,
            "stale_count": self.stats.stale_count,
            "expired_count": self.stats.expired_count,
            "avg_access_time_ms": self.stats.avg_access_time_ms,
            "total_size_bytes": self.stats.total_size_bytes,
            "avg_entry_size_bytes": self.stats.avg_entry_size_bytes,
            "max_entries": self.max_entries,
            "default_ttl_minutes": self.default_ttl_minutes,
            "cache_utilization": self.stats.total_entries / self.max_entries
        }
    
    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        self.stats = CacheStats()
        self._save_cache()
    
    def get_top_accessed_entries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most frequently accessed cache entries."""
        sorted_entries = sorted(
            self.cache.items(),
            key=lambda x: x[1].access_count,
            reverse=True
        )
        
        top_entries = []
        for key, entry in sorted_entries[:limit]:
            top_entries.append({
                "key": key,
                "access_count": entry.access_count,
                "age_seconds": entry.age_seconds,
                "last_accessed": entry.last_accessed.isoformat() if entry.last_accessed else None,
                "score": entry.value.compatibility_score.overall_score
            })
        
        return top_entries
    
    def get_stale_entries(self, max_age_minutes: int = 30) -> List[Dict[str, Any]]:
        """Get stale cache entries."""
        stale_entries = []
        
        for key, entry in self.cache.items():
            if entry.is_stale:
                stale_entries.append({
                    "key": key,
                    "age_seconds": entry.age_seconds,
                    "expires_at": entry.expires_at.isoformat(),
                    "score": entry.value.compatibility_score.overall_score
                })
        
        return stale_entries
