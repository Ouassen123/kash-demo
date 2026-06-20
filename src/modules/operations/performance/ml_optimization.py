"""ML model performance optimization service for KASH platform."""

import asyncio
import joblib
import numpy as np
import pandas as pd
import json
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging
import hashlib
import pickle
import time
from concurrent.futures import ThreadPoolExecutor
import multiprocessing

# ML libraries
try:
    import lightgbm as lgb
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    from sklearn.feature_extraction import DictVectorizer
    import scipy.sparse
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

from ...shared.cache.redis_cache import get_prediction_cache, get_redis_cache


@dataclass
class MLPerformanceConfig:
    """Configuration for ML model performance optimization."""
    # Model inference optimization
    enable_model_caching: bool = True
    enable_prediction_caching: bool = True
    cache_ttl_seconds: int = 3600  # 1 hour
    
    # Batch processing
    enable_batch_optimization: bool = True
    max_batch_size: int = 1000
    batch_timeout_seconds: int = 5
    
    # Model optimization
    enable_model_optimization: bool = True
    lightgbm_num_threads: int = -1  # Use all available threads
    lightgbm_predict_disable: bool = False
    lightgbn_predict_raw_score: bool = False
    
    # Feature optimization
    enable_feature_caching: bool = True
    enable_feature_vectorization_cache: bool = True
    max_feature_cache_size: int = 10000
    
    # Memory optimization
    enable_memory_optimization: bool = True
    model_unload_timeout_seconds: int = 1800  # 30 minutes
    
    # Performance monitoring
    enable_performance_tracking: bool = True
    log_slow_predictions: bool = True
    slow_prediction_threshold_ms: float = 100.0


class ModelCache:
    """In-memory cache for ML models with LRU eviction."""
    
    def __init__(self, max_size: int = 10, unload_timeout: int = 1800):
        self.max_size = max_size
        self.unload_timeout = unload_timeout
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, datetime] = {}
        self.logger = logging.getLogger(__name__)
    
    def get(self, model_id: str) -> Optional[Any]:
        """Get model from cache."""
        if model_id not in self.cache:
            return None
        
        # Check if model has expired
        last_access = self.access_times.get(model_id)
        if last_access and (datetime.utcnow() - last_access).seconds > self.unload_timeout:
            self._remove_model(model_id)
            return None
        
        # Update access time
        self.access_times[model_id] = datetime.utcnow()
        
        return self.cache[model_id]["model"]
    
    def put(self, model_id: str, model: Any, metadata: Optional[Dict[str, Any]] = None):
        """Put model in cache."""
        # Remove oldest if at capacity
        if len(self.cache) >= self.max_size:
            self._evict_oldest()
        
        # Store model
        self.cache[model_id] = {
            "model": model,
            "metadata": metadata or {},
            "loaded_at": datetime.utcnow()
        }
        self.access_times[model_id] = datetime.utcnow()
        
        self.logger.info(f"Model {model_id} loaded into cache")
    
    def _remove_model(self, model_id: str):
        """Remove model from cache."""
        if model_id in self.cache:
            del self.cache[model_id]
        if model_id in self.access_times:
            del self.access_times[model_id]
    
    def _evict_oldest(self):
        """Evict oldest model from cache."""
        if not self.access_times:
            return
        
        oldest_model = min(self.access_times.items(), key=lambda x: x[1])
        self._remove_model(oldest_model[0])
        
        self.logger.info(f"Evicted model {oldest_model[0]} from cache")
    
    def clear(self):
        """Clear all models from cache."""
        self.cache.clear()
        self.access_times.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cached_models": len(self.cache),
            "max_size": self.max_size,
            "utilization": len(self.cache) / self.max_size,
            "models": list(self.cache.keys())
        }


class FeatureVectorCache:
    """Cache for feature vectors and preprocessing objects."""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.cache: Dict[str, Any] = {}
        self.access_order: List[str] = []
        self.logger = logging.getLogger(__name__)
    
    def get(self, key: str) -> Optional[Any]:
        """Get feature vector from cache."""
        if key in self.cache:
            # Move to end (LRU)
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        return None
    
    def put(self, key: str, value: Any):
        """Put feature vector in cache."""
        # Remove oldest if at capacity
        if len(self.cache) >= self.max_size and key not in self.cache:
            oldest_key = self.access_order.pop(0)
            del self.cache[oldest_key]
        
        if key not in self.cache:
            self.access_order.append(key)
        
        self.cache[key] = value
    
    def clear(self):
        """Clear cache."""
        self.cache.clear()
        self.access_order.clear()


class MLPerformanceService:
    """ML model performance optimization service."""
    
    def __init__(self, config: Optional[MLPerformanceConfig] = None):
        self.config = config or MLPerformanceConfig()
        self.logger = logging.getLogger(__name__)
        
        # Caches
        self.model_cache = ModelCache(
            max_size=10,
            unload_timeout=self.config.model_unload_timeout_seconds
        )
        self.feature_cache = FeatureVectorCache(max_size=self.config.max_feature_cache_size)
        
        # External cache services
        self.prediction_cache = get_prediction_cache()
        self.redis_cache = get_redis_cache()
        
        # Performance tracking
        self.performance_stats = {
            "total_predictions": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_prediction_time_ms": 0.0,
            "batch_predictions": 0,
            "model_loads": 0,
            "slow_predictions": 0,
            "memory_optimizations": 0
        }
        
        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=multiprocessing.cpu_count())
        
        self.logger.info("ML performance service initialized")
    
    def _generate_feature_hash(self, features: Union[Dict, List, np.ndarray]) -> str:
        """Generate hash for feature vector."""
        if isinstance(features, dict):
            # Sort dict for consistent hashing
            features_str = json.dumps(features, sort_keys=True)
        elif isinstance(features, list):
            features_str = str(features)
        elif isinstance(features, np.ndarray):
            features_str = features.tobytes().hex()
        else:
            features_str = str(features)
        
        return hashlib.md5(features_str.encode()).hexdigest()
    
    async def predict_optimized(self, model_id: str, features: Union[Dict, List, np.ndarray],
                               include_explanation: bool = False) -> Dict[str, Any]:
        """Optimized prediction with caching and performance tracking."""
        start_time = time.time()
        
        try:
            # Generate feature hash for caching
            feature_hash = self._generate_feature_hash(features)
            
            # Check prediction cache
            if self.config.enable_prediction_caching:
                cached_prediction = await self.prediction_cache.get_prediction(model_id, feature_hash)
                if cached_prediction:
                    self.performance_stats["cache_hits"] += 1
                    prediction_time = (time.time() - start_time) * 1000
                    self._update_performance_stats(prediction_time)
                    return cached_prediction
            
            self.performance_stats["cache_misses"] += 1
            
            # Get model from cache or load from disk
            model = await self._get_model_cached(model_id)
            if model is None:
                raise ValueError(f"Model {model_id} not found")
            
            # Preprocess features
            processed_features = await self._preprocess_features_cached(model_id, features)
            
            # Make prediction
            prediction = await self._predict_with_model(model, processed_features)
            
            # Add explanation if requested
            if include_explanation and hasattr(model, 'feature_importances_'):
                prediction["feature_importance"] = dict(zip(
                    getattr(model, 'feature_names_', [f"feature_{i}" for i in range(len(model.feature_importances_))]),
                    model.feature_importances_
                ))
            
            # Cache prediction
            if self.config.enable_prediction_caching:
                await self.prediction_cache.set_prediction(model_id, feature_hash, prediction)
            
            # Update performance stats
            prediction_time = (time.time() - start_time) * 1000
            self._update_performance_stats(prediction_time)
            
            return prediction
            
        except Exception as e:
            self.logger.error(f"Error in optimized prediction: {e}")
            raise
    
    async def predict_batch_optimized(self, model_id: str, features_list: List[Union[Dict, List, np.ndarray]],
                                     include_explanations: bool = False) -> List[Dict[str, Any]]:
        """Optimized batch prediction with parallel processing."""
        if not self.config.enable_batch_optimization:
            # Fall back to individual predictions
            results = []
            for features in features_list:
                result = await self.predict_optimized(model_id, features, include_explanations)
                results.append(result)
            return results
        
        start_time = time.time()
        
        try:
            # Check batch cache
            batch_hash = self._generate_feature_hash(features_list)
            if self.config.enable_prediction_caching:
                cached_batch = await self.prediction_cache.get_batch_predictions(model_id, batch_hash)
                if cached_batch:
                    self.performance_stats["cache_hits"] += 1
                    batch_time = (time.time() - start_time) * 1000
                    self._update_performance_stats(batch_time)
                    return cached_batch
            
            self.performance_stats["cache_misses"] += 1
            
            # Get model
            model = await self._get_model_cached(model_id)
            if model is None:
                raise ValueError(f"Model {model_id} not found")
            
            # Process features in parallel
            processed_features_list = await self._preprocess_features_batch_cached(model_id, features_list)
            
            # Make batch prediction
            predictions = await self._predict_batch_with_model(model, processed_features_list)
            
            # Add explanations if requested
            if include_explanations and hasattr(model, 'feature_importances_'):
                feature_names = getattr(model, 'feature_names_', 
                                      [f"feature_{i}" for i in range(len(model.feature_importances_))])
                importance_dict = dict(zip(feature_names, model.feature_importances_))
                
                for prediction in predictions:
                    prediction["feature_importance"] = importance_dict
            
            # Cache batch results
            if self.config.enable_prediction_caching:
                await self.prediction_cache.set_batch_predictions(model_id, batch_hash, predictions)
            
            # Update performance stats
            batch_time = (time.time() - start_time) * 1000
            self.performance_stats["batch_predictions"] += 1
            self._update_performance_stats(batch_time)
            
            return predictions
            
        except Exception as e:
            self.logger.error(f"Error in optimized batch prediction: {e}")
            raise
    
    async def _get_model_cached(self, model_id: str) -> Optional[Any]:
        """Get model from cache or load from disk."""
        # Check in-memory cache
        model = self.model_cache.get(model_id)
        if model is not None:
            return model
        
        # Load from disk
        try:
            model_path = f"models/{model_id}.pkl"
            model = joblib.load(model_path)
            
            # Optimize model if LightGBM
            if self.config.enable_model_optimization and hasattr(model, 'predict'):
                model = self._optimize_lightgbm_model(model)
            
            # Cache model
            if self.config.enable_model_caching:
                self.model_cache.put(model_id, model, {
                    "loaded_at": datetime.utcnow(),
                    "model_type": type(model).__name__
                })
            
            self.performance_stats["model_loads"] += 1
            self.logger.info(f"Loaded model {model_id} from disk")
            
            return model
            
        except Exception as e:
            self.logger.error(f"Failed to load model {model_id}: {e}")
            return None
    
    def _optimize_lightgbm_model(self, model: Any) -> Any:
        """Optimize LightGBM model for inference."""
        if not hasattr(model, 'predict'):
            return model
        
        try:
            # Set LightGBM parameters for faster inference
            if hasattr(model, 'predict'):
                # Optimize for inference speed
                if hasattr(model, 'set_params'):
                    model.set_params(
                        num_threads=self.config.lightgbm_num_threads,
                        predict_disable=self.config.lightgbm_predict_disable,
                        predict_raw_score=self.config.lightgbn_predict_raw_score
                    )
            
            self.logger.info("Optimized LightGBM model for inference")
            
        except Exception as e:
            self.logger.warning(f"Failed to optimize LightGBM model: {e}")
        
        return model
    
    async def _preprocess_features_cached(self, model_id: str, features: Union[Dict, List, np.ndarray]) -> Any:
        """Preprocess features with caching."""
        if not self.config.enable_feature_caching:
            return self._preprocess_features(model_id, features)
        
        cache_key = f"preprocess:{model_id}:{self._generate_feature_hash(features)}"
        
        # Check cache
        cached_features = self.feature_cache.get(cache_key)
        if cached_features is not None:
            return cached_features
        
        # Preprocess features
        processed_features = self._preprocess_features(model_id, features)
        
        # Cache result
        self.feature_cache.put(cache_key, processed_features)
        
        return processed_features
    
    async def _preprocess_features_batch_cached(self, model_id: str, features_list: List[Union[Dict, List, np.ndarray]]) -> List[Any]:
        """Preprocess batch features with caching."""
        if not self.config.enable_feature_caching:
            return [self._preprocess_features(model_id, features) for features in features_list]
        
        processed_list = []
        
        for features in features_list:
            cache_key = f"preprocess:{model_id}:{self._generate_feature_hash(features)}"
            
            # Check cache
            cached_features = self.feature_cache.get(cache_key)
            if cached_features is not None:
                processed_list.append(cached_features)
            else:
                # Preprocess features
                processed_features = self._preprocess_features(model_id, features)
                processed_list.append(processed_features)
                
                # Cache result
                self.feature_cache.put(cache_key, processed_features)
        
        return processed_list
    
    def _preprocess_features(self, model_id: str, features: Union[Dict, List, np.ndarray]) -> Any:
        """Preprocess features for model input."""
        # This is a simplified version - in practice, you'd load the actual preprocessing pipeline
        if isinstance(features, dict):
            # Convert dict to array (simplified)
            return np.array(list(features.values())).reshape(1, -1)
        elif isinstance(features, list):
            return np.array(features).reshape(1, -1)
        elif isinstance(features, np.ndarray):
            if features.ndim == 1:
                return features.reshape(1, -1)
            return features
        else:
            raise ValueError(f"Unsupported feature type: {type(features)}")
    
    async def _predict_with_model(self, model: Any, features: Any) -> Dict[str, Any]:
        """Make prediction with model."""
        try:
            # Use thread pool for CPU-intensive prediction
            loop = asyncio.get_event_loop()
            
            if hasattr(model, 'predict_proba'):
                # Classification model
                prediction_proba = await loop.run_in_executor(
                    self.executor, model.predict_proba, features
                )
                prediction = await loop.run_in_executor(
                    self.executor, model.predict, features
                )
                
                return {
                    "prediction": int(prediction[0]),
                    "prediction_proba": prediction_proba[0].tolist(),
                    "confidence": float(np.max(prediction_proba[0])),
                    "predicted_at": datetime.utcnow().isoformat()
                }
            
            else:
                # Regression model
                prediction = await loop.run_in_executor(
                    self.executor, model.predict, features
                )
                
                return {
                    "prediction": float(prediction[0]),
                    "predicted_at": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error making prediction: {e}")
            raise
    
    async def _predict_batch_with_model(self, model: Any, features_list: List[Any]) -> List[Dict[str, Any]]:
        """Make batch prediction with model."""
        try:
            # Stack features for batch prediction
            stacked_features = np.vstack(features_list)
            
            loop = asyncio.get_event_loop()
            
            if hasattr(model, 'predict_proba'):
                # Classification model
                prediction_proba = await loop.run_in_executor(
                    self.executor, model.predict_proba, stacked_features
                )
                predictions = await loop.run_in_executor(
                    self.executor, model.predict, stacked_features
                )
                
                results = []
                for i, pred in enumerate(predictions):
                    results.append({
                        "prediction": int(pred),
                        "prediction_proba": prediction_proba[i].tolist(),
                        "confidence": float(np.max(prediction_proba[i])),
                        "predicted_at": datetime.utcnow().isoformat()
                    })
                
                return results
            
            else:
                # Regression model
                predictions = await loop.run_in_executor(
                    self.executor, model.predict, stacked_features
                )
                
                results = []
                for pred in predictions:
                    results.append({
                        "prediction": float(pred),
                        "predicted_at": datetime.utcnow().isoformat()
                    })
                
                return results
                
        except Exception as e:
            self.logger.error(f"Error making batch prediction: {e}")
            raise
    
    def _update_performance_stats(self, prediction_time_ms: float):
        """Update performance statistics."""
        self.performance_stats["total_predictions"] += 1
        
        # Update average prediction time
        if self.performance_stats["avg_prediction_time_ms"] == 0:
            self.performance_stats["avg_prediction_time_ms"] = prediction_time_ms
        else:
            alpha = 0.1
            self.performance_stats["avg_prediction_time_ms"] = (
                alpha * prediction_time_ms + 
                (1 - alpha) * self.performance_stats["avg_prediction_time_ms"]
            )
        
        # Track slow predictions
        if prediction_time_ms > self.config.slow_prediction_threshold_ms:
            self.performance_stats["slow_predictions"] += 1
            if self.config.log_slow_predictions:
                self.logger.warning(f"Slow prediction detected: {prediction_time_ms:.2f}ms")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        total_predictions = self.performance_stats["total_predictions"]
        
        # Calculate rates
        cache_total = self.performance_stats["cache_hits"] + self.performance_stats["cache_misses"]
        cache_hit_rate = (
            self.performance_stats["cache_hits"] / cache_total 
            if cache_total > 0 else 0
        )
        
        slow_prediction_rate = (
            self.performance_stats["slow_predictions"] / total_predictions 
            if total_predictions > 0 else 0
        )
        
        return {
            **self.performance_stats,
            "cache_hit_rate": cache_hit_rate,
            "slow_prediction_rate": slow_prediction_rate,
            "model_cache_stats": self.model_cache.get_stats(),
            "feature_cache_size": len(self.feature_cache.cache)
        }
    
    async def clear_caches(self):
        """Clear all caches."""
        self.model_cache.clear()
        self.feature_cache.clear()
        
        # Clear Redis caches
        await self.prediction_cache.cache.clear_prefix("prediction:")
        await self.prediction_cache.cache.clear_prefix("batch:")
        
        self.logger.info("All ML caches cleared")
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for ML performance service."""
        stats = self.get_performance_stats()
        
        return {
            "status": "healthy",
            "ml_available": ML_AVAILABLE,
            "performance_stats": stats,
            "config": {
                "model_caching": self.config.enable_model_caching,
                "prediction_caching": self.config.enable_prediction_caching,
                "batch_optimization": self.config.enable_batch_optimization,
                "feature_caching": self.config.enable_feature_caching
            },
            "timestamp": datetime.utcnow().isoformat()
        }


# Global ML performance service
_ml_performance_service: Optional[MLPerformanceService] = None


def get_ml_performance_service() -> MLPerformanceService:
    """Get global ML performance service."""
    global _ml_performance_service
    if _ml_performance_service is None:
        _ml_performance_service = MLPerformanceService()
    return _ml_performance_service


async def initialize_ml_performance(config: Optional[MLPerformanceConfig] = None) -> bool:
    """Initialize ML performance service."""
    try:
        global _ml_performance_service
        _ml_performance_service = MLPerformanceService(config)
        
        # Test health
        health = await _ml_performance_service.health_check()
        
        return health["status"] == "healthy"
        
    except Exception as e:
        logging.error(f"Failed to initialize ML performance service: {e}")
        return False


async def cleanup_ml_performance():
    """Cleanup ML performance service."""
    global _ml_performance_service
    if _ml_performance_service:
        await _ml_performance_service.clear_caches()
    _ml_performance_service = None
