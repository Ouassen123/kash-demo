"""Database optimization service for KASH platform performance."""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

# Optional database imports
try:
    import asyncpg
    import sqlalchemy
    from sqlalchemy import text, Index, Column
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy.orm import declarative_base
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

from ...shared.cache.redis_cache import get_redis_cache, CacheConfig


@dataclass
class DatabaseConfig:
    """Configuration for database optimization."""
    # PostgreSQL connection
    host: str = "localhost"
    port: int = 5432
    database: str = "kash_platform"
    username: str = "kash_user"
    password: str = "kash_password"
    
    # Connection pool settings
    min_connections: int = 5
    max_connections: int = 20
    connection_timeout: int = 30
    command_timeout: int = 30
    
    # Query optimization
    query_timeout: int = 10
    statement_timeout: int = 30
    idle_in_transaction_session_timeout: int = 60
    
    # Performance settings
    shared_buffers: str = "256MB"
    effective_cache_size: str = "1GB"
    work_mem: str = "4MB"
    maintenance_work_mem: str = "64MB"
    checkpoint_completion_target: float = 0.9
    wal_buffers: str = "16MB"
    default_statistics_target: int = 100
    
    # Monitoring
    enable_query_logging: bool = True
    log_slow_queries: bool = True
    slow_query_threshold_ms: int = 1000


class DatabaseOptimizationService:
    """Database optimization service for performance tuning."""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self.logger = logging.getLogger(__name__)
        
        # Database connection
        self.engine: Optional[sqlalchemy.ext.asyncio.AsyncEngine] = None
        self.session_factory: Optional[async_sessionmaker] = None
        
        # Performance tracking
        self.query_stats: Dict[str, Any] = {
            "total_queries": 0,
            "slow_queries": 0,
            "avg_execution_time_ms": 0.0,
            "cache_hit_rate": 0.0,
            "connection_pool_stats": {}
        }
        
        # Initialize database connection
        self._initialize_database()
        
        self.logger.info("Database optimization service initialized")
    
    def _initialize_database(self):
        """Initialize database connection pool."""
        if not DATABASE_AVAILABLE:
            self.logger.warning("Database libraries not available, optimization disabled")
            return
        
        try:
            # Create database URL
            database_url = (
                f"postgresql+asyncpg://{self.config.username}:{self.config.password}"
                f"@{self.config.host}:{self.config.port}/{self.config.database}"
            )
            
            # Create async engine with optimized settings
            self.engine = create_async_engine(
                database_url,
                pool_size=self.config.min_connections,
                max_overflow=self.config.max_connections - self.config.min_connections,
                pool_timeout=self.config.connection_timeout,
                pool_recycle=3600,  # Recycle connections every hour
                pool_pre_ping=True,  # Validate connections
                echo=self.config.enable_query_logging,
                connect_args={
                    "command_timeout": self.config.command_timeout,
                    "server_settings": {
                        "application_name": "kash_platform",
                        "statement_timeout": str(self.config.statement_timeout * 1000),
                        "idle_in_transaction_session_timeout": str(self.config.idle_in_transaction_session_timeout),
                    }
                }
            )
            
            # Create session factory
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            self.logger.info("Database connection pool initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            self.engine = None
    
    async def create_indexes(self) -> Dict[str, bool]:
        """Create performance indexes for common queries."""
        if not self.engine:
            return {"status": "error", "message": "Database not available"}
        
        results = {}
        
        # Index definitions for performance optimization
        indexes = [
            # User-related indexes
            {
                "name": "idx_users_email_active",
                "table": "users",
                "columns": ["email", "is_active"],
                "description": "User login and authentication queries"
            },
            {
                "name": "idx_users_created_at",
                "table": "users", 
                "columns": ["created_at"],
                "description": "User registration analytics"
            },
            
            # ESCO/O*NET data indexes
            {
                "name": "idx_esco_occupations_title",
                "table": "esco_occupations",
                "columns": ["title"],
                "description": "Occupation search by title"
            },
            {
                "name": "idx_esco_occupations_isco_group",
                "table": "esco_occupations",
                "columns": ["isco_group"],
                "description": "Occupation filtering by ISCO group"
            },
            {
                "name": "idx_esco_skills_pref_label",
                "table": "esco_skills",
                "columns": ["pref_label"],
                "description": "Skill search by label"
            },
            {
                "name": "idx_esco_skill_relations_skill_uri",
                "table": "esco_skill_relations",
                "columns": ["skill_uri"],
                "description": "Skill relation lookups"
            },
            
            # Compatibility scoring indexes
            {
                "name": "idx_compatibility_scores_learner_job",
                "table": "compatibility_scores",
                "columns": ["learner_id", "job_family"],
                "description": "Learner compatibility lookups"
            },
            {
                "name": "idx_compatibility_scores_created_at",
                "table": "compatibility_scores",
                "columns": ["created_at"],
                "description": "Recent compatibility scores"
            },
            {
                "name": "idx_compatibility_scores_score",
                "table": "compatibility_scores",
                "columns": ["overall_score"],
                "description": "Score-based filtering"
            },
            
            # Prediction and ML indexes
            {
                "name": "idx_predictions_learner_model",
                "table": "predictions",
                "columns": ["learner_id", "model_id"],
                "description": "Prediction history lookups"
            },
            {
                "name": "idx_predictions_created_at",
                "table": "predictions",
                "columns": ["created_at"],
                "description": "Recent predictions"
            },
            {
                "name": "idx_predictions_confidence",
                "table": "predictions",
                "columns": ["confidence_level"],
                "description": "Confidence-based filtering"
            },
            
            # Feature engineering indexes
            {
                "name": "idx_features_learner_type",
                "table": "learner_features",
                "columns": ["learner_id", "feature_type"],
                "description": "Feature lookups by learner and type"
            },
            {
                "name": "idx_features_created_at",
                "table": "learner_features",
                "columns": ["created_at"],
                "description": "Recent features"
            },
            
            # Explanation indexes
            {
                "name": "idx_explanations_learner_model",
                "table": "explanations",
                "columns": ["learner_id", "model_id"],
                "description": "Explanation history lookups"
            },
            {
                "name": "idx_explanations_created_at",
                "table": "explanations",
                "columns": ["created_at"],
                "description": "Recent explanations"
            }
        ]
        
        async with self.session_factory() as session:
            for index_def in indexes:
                try:
                    # Check if index exists
                    check_sql = f"""
                        SELECT indexname 
                        FROM pg_indexes 
                        WHERE tablename = '{index_def['table']}' 
                        AND indexname = '{index_def['name']}'
                    """
                    
                    result = await session.execute(text(check_sql))
                    existing = result.fetchone()
                    
                    if not existing:
                        # Create index
                        columns_str = ", ".join(index_def["columns"])
                        create_sql = f"""
                            CREATE INDEX CONCURRENTLY {index_def['name']}
                            ON {index_def['table']} ({columns_str})
                        """
                        
                        await session.execute(text(create_sql))
                        await session.commit()
                        
                        results[index_def["name"]] = True
                        self.logger.info(f"Created index: {index_def['name']}")
                    else:
                        results[index_def["name"]] = True
                        self.logger.info(f"Index already exists: {index_def['name']}")
                        
                except Exception as e:
                    results[index_def["name"]] = False
                    self.logger.error(f"Failed to create index {index_def['name']}: {e}")
        
        return results
    
    async def optimize_table_statistics(self) -> Dict[str, Any]:
        """Update table statistics for better query planning."""
        if not self.engine:
            return {"status": "error", "message": "Database not available"}
        
        # Tables that need frequent statistics updates
        tables = [
            "users",
            "esco_occupations", 
            "esco_skills",
            "compatibility_scores",
            "predictions",
            "learner_features",
            "explanations"
        ]
        
        results = {}
        
        async with self.session_factory() as session:
            for table in tables:
                try:
                    # Update table statistics
                    analyze_sql = f"ANALYZE {table}"
                    await session.execute(text(analyze_sql))
                    await session.commit()
                    
                    results[table] = True
                    self.logger.info(f"Updated statistics for table: {table}")
                    
                except Exception as e:
                    results[table] = False
                    self.logger.error(f"Failed to analyze table {table}: {e}")
        
        return results
    
    async def get_query_performance_stats(self) -> Dict[str, Any]:
        """Get database query performance statistics."""
        if not self.engine:
            return {"status": "error", "message": "Database not available"}
        
        stats = {}
        
        async with self.session_factory() as session:
            try:
                # Get general database stats
                db_stats_sql = """
                    SELECT 
                        datname,
                        numbackends,
                        xact_commit,
                        xact_rollback,
                        blks_read,
                        blks_hit,
                        tup_returned,
                        tup_fetched,
                        tup_inserted,
                        tup_updated,
                        tup_deleted
                    FROM pg_stat_database 
                    WHERE datname = current_database()
                """
                
                result = await session.execute(text(db_stats_sql))
                db_stats = result.fetchone()
                
                if db_stats:
                    stats["database"] = {
                        "active_connections": db_stats.numbackends,
                        "transactions_committed": db_stats.xact_commit,
                        "transactions_rolled_back": db_stats.xact_rollback,
                        "blocks_read": db_stats.blks_read,
                        "blocks_hit": db_stats.blks_hit,
                        "cache_hit_rate": (
                            db_stats.blks_hit / (db_stats.blks_read + db_stats.blks_hit) 
                            if (db_stats.blks_read + db_stats.blks_hit) > 0 else 0
                        ),
                        "tuples_returned": db_stats.tup_returned,
                        "tuples_fetched": db_stats.tup_fetched,
                        "tuples_inserted": db_stats.tup_inserted,
                        "tuples_updated": db_stats.tup_updated,
                        "tuples_deleted": db_stats.tup_deleted
                    }
                
                # Get table stats
                table_stats_sql = """
                    SELECT 
                        schemaname,
                        tablename,
                        seq_scan,
                        seq_tup_read,
                        idx_scan,
                        idx_tup_fetch,
                        n_tup_ins,
                        n_tup_upd,
                        n_tup_del,
                        n_live_tup,
                        n_dead_tup
                    FROM pg_stat_user_tables
                    ORDER BY n_live_tup DESC
                """
                
                result = await session.execute(text(table_stats_sql))
                table_rows = result.fetchall()
                
                stats["tables"] = []
                for row in table_rows:
                    stats["tables"].append({
                        "schema": row.schemaname,
                        "table": row.tablename,
                        "sequential_scans": row.seq_scan,
                        "sequential_tuples_read": row.seq_tup_read,
                        "index_scans": row.idx_scan,
                        "index_tuples_fetched": row.idx_tup_fetch,
                        "tuples_inserted": row.n_tup_ins,
                        "tuples_updated": row.n_tup_upd,
                        "tuples_deleted": row.n_tup_del,
                        "live_tuples": row.n_live_tup,
                        "dead_tuples": row.n_dead_tup
                    })
                
                # Get index usage stats
                index_stats_sql = """
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        idx_scan,
                        idx_tup_read,
                        idx_tup_fetch
                    FROM pg_stat_user_indexes
                    ORDER BY idx_scan DESC
                """
                
                result = await session.execute(text(index_stats_sql))
                index_rows = result.fetchall()
                
                stats["indexes"] = []
                for row in index_rows:
                    stats["indexes"].append({
                        "schema": row.schemaname,
                        "table": row.tablename,
                        "index": row.indexname,
                        "scans": row.idx_scan,
                        "tuples_read": row.idx_tup_read,
                        "tuples_fetched": row.idx_tup_fetch
                    })
                
                # Get slow queries (if pg_stat_statements is enabled)
                try:
                    slow_queries_sql = """
                        SELECT 
                            query,
                            calls,
                            total_time,
                            mean_time,
                            rows
                        FROM pg_stat_statements 
                        WHERE mean_time > %s
                        ORDER BY mean_time DESC
                        LIMIT 10
                    """
                    
                    result = await session.execute(text(slow_queries_sql), [self.config.slow_query_threshold_ms])
                    slow_query_rows = result.fetchall()
                    
                    stats["slow_queries"] = []
                    for row in slow_query_rows:
                        stats["slow_queries"].append({
                            "query": row.query[:200] + "..." if len(row.query) > 200 else row.query,
                            "calls": row.calls,
                            "total_time_ms": row.total_time,
                            "mean_time_ms": row.mean_time,
                            "rows": row.rows
                        })
                        
                except Exception:
                    stats["slow_queries"] = []  # pg_stat_statements not available
                
            except Exception as e:
                self.logger.error(f"Error getting database stats: {e}")
                stats["error"] = str(e)
        
        return stats
    
    async def get_connection_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        if not self.engine:
            return {"status": "error", "message": "Database not available"}
        
        pool = self.engine.pool
        
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
            "total_connections": pool.size() + pool.overflow(),
            "available_connections": pool.checkedin(),
            "active_connections": pool.checkedout()
        }
    
    async def cleanup_dead_tuples(self) -> Dict[str, Any]:
        """Clean up dead tuples to reclaim space."""
        if not self.engine:
            return {"status": "error", "message": "Database not available"}
        
        results = {}
        
        # Tables that benefit from VACUUM
        tables = [
            "compatibility_scores",
            "predictions", 
            "learner_features",
            "explanations"
        ]
        
        async with self.session_factory() as session:
            for table in tables:
                try:
                    # Run VACUUM ANALYZE
                    vacuum_sql = f"VACUUM ANALYZE {table}"
                    await session.execute(text(vacuum_sql))
                    
                    results[table] = True
                    self.logger.info(f"VACUUM completed for table: {table}")
                    
                except Exception as e:
                    results[table] = False
                    self.logger.error(f"Failed to VACUUM table {table}: {e}")
        
        return results
    
    async def configure_performance_settings(self) -> Dict[str, bool]:
        """Configure database performance settings."""
        if not self.engine:
            return {"status": "error", "message": "Database not available"}
        
        settings = {
            "shared_buffers": self.config.shared_buffers,
            "effective_cache_size": self.config.effective_cache_size,
            "work_mem": self.config.work_mem,
            "maintenance_work_mem": self.config.maintenance_work_mem,
            "checkpoint_completion_target": self.config.checkpoint_completion_target,
            "wal_buffers": self.config.wal_buffers,
            "default_statistics_target": self.config.default_statistics_target,
            "random_page_cost": "1.1",  # Optimized for SSD
            "effective_io_concurrency": "200",  # Optimized for SSD
        }
        
        results = {}
        
        async with self.session_factory() as session:
            for setting, value in settings.items():
                try:
                    # Set configuration parameter
                    set_sql = f"ALTER SYSTEM SET {setting} = '{value}'"
                    await session.execute(text(set_sql))
                    await session.commit()
                    
                    results[setting] = True
                    self.logger.info(f"Set {setting} = {value}")
                    
                except Exception as e:
                    results[setting] = False
                    self.logger.error(f"Failed to set {setting}: {e}")
        
        # Reload configuration
        try:
            await session.execute(text("SELECT pg_reload_conf()"))
            await session.commit()
            self.logger.info("Database configuration reloaded")
        except Exception as e:
            self.logger.error(f"Failed to reload configuration: {e}")
        
        return results
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for database service."""
        health = {
            "status": "unhealthy",
            "database_available": DATABASE_AVAILABLE,
            "connection_status": "disconnected",
            "connection_pool": {},
            "performance_stats": {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if self.engine:
            try:
                # Test database connection
                async with self.session_factory() as session:
                    await session.execute(text("SELECT 1"))
                
                health["status"] = "healthy"
                health["connection_status"] = "connected"
                
                # Get connection pool stats
                health["connection_pool"] = await self.get_connection_pool_stats()
                
                # Get basic performance stats
                perf_stats = await self.get_query_performance_stats()
                health["performance_stats"] = perf_stats.get("database", {})
                
            except Exception as e:
                health["connection_status"] = f"error: {str(e)}"
        
        return health
    
    async def close(self):
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()
            self.logger.info("Database connections closed")


# Database query optimization decorator
def optimize_query(ttl_seconds: int = 300, cache_key_prefix: str = ""):
    """Decorator for caching and optimizing database queries."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{cache_key_prefix}:{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache
            redis_cache = get_redis_cache()
            cached_result = await redis_cache.get(cache_key)
            
            if cached_result is not None:
                return cached_result
            
            # Execute query
            result = await func(*args, **kwargs)
            
            # Cache result
            await redis_cache.set(cache_key, result, ttl=ttl_seconds, tags=["database_query", func.__name__])
            
            return result
        
        return wrapper
    return decorator


# Global database service instance
_database_service: Optional[DatabaseOptimizationService] = None


def get_database_service() -> DatabaseOptimizationService:
    """Get global database optimization service."""
    global _database_service
    if _database_service is None:
        _database_service = DatabaseOptimizationService()
    return _database_service


async def initialize_database(config: Optional[DatabaseConfig] = None) -> bool:
    """Initialize database optimization service."""
    try:
        global _database_service
        _database_service = DatabaseOptimizationService(config)
        
        # Test connection
        health = await _database_service.health_check()
        
        if health["status"] == "healthy":
            # Create performance indexes
            await _database_service.create_indexes()
            
            # Update statistics
            await _database_service.optimize_table_statistics()
        
        return health["status"] == "healthy"
        
    except Exception as e:
        logging.error(f"Failed to initialize database: {e}")
        return False


async def cleanup_database():
    """Cleanup database connections."""
    global _database_service
    if _database_service:
        await _database_service.close()
    _database_service = None
