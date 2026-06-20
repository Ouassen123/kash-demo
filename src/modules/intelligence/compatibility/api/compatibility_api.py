"""FastAPI service for compatibility score endpoints."""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..models import (
    CompatibilityScoreRequest,
    CompatibilityScoreResponse,
    KASHSignal,
    JobFamilyEnum,
    SignalSourceEnum,
    SignalQualityEnum
)
from ..services.scoring_pipeline import ScoringPipeline
from ..services.weight_manager import WeightManager
from ..services.provenance_tracker import ProvenanceTracker
from ..services.cache_service import CompatibilityCacheService, CacheHitStatus


# Initialize FastAPI app
app = FastAPI(
    title="KASH Compatibility Score API",
    description="API for calculating learner-job compatibility scores using KASH signals",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
scoring_pipeline = ScoringPipeline()
weight_manager = WeightManager()
provenance_tracker = ProvenanceTracker()
cache_service = CompatibilityCacheService()


# Pydantic models for API requests/responses
class ScoreRequest(BaseModel):
    """API request for compatibility score calculation."""
    learner_id: str = Field(..., description="Learner identifier")
    job_family: JobFamilyEnum = Field(..., description="Target job family")
    target_job_id: Optional[str] = Field(None, description="Specific target job ID")
    
    # Input signals
    kash_signals: List[KASHSignal] = Field(..., description="KASH signals for the learner")
    
    # Configuration options
    weight_configuration_id: Optional[str] = Field(None, description="Specific weight configuration to use")
    business_context: Optional[str] = Field(None, description="Business context for scoring")
    include_confidence_interval: bool = Field(True, description="Whether to calculate confidence interval")
    confidence_level: float = Field(0.95, ge=0.8, le=0.99, description="Confidence level for intervals")
    
    # Quality thresholds
    min_signal_quality: SignalQualityEnum = Field(SignalQualityEnum.LOW, description="Minimum signal quality to include")
    max_signal_age_days: int = Field(365, description="Maximum age of signals to consider")
    
    # Cache options
    use_cache: bool = Field(True, description="Whether to use cache")
    cache_ttl_minutes: Optional[int] = Field(None, description="Cache TTL in minutes")


class BatchScoreRequest(BaseModel):
    """API request for batch compatibility score calculation."""
    requests: List[ScoreRequest] = Field(..., description="List of score requests")
    max_concurrent: int = Field(10, ge=1, le=50, description="Maximum concurrent calculations")


class CacheInvalidationRequest(BaseModel):
    """API request for cache invalidation."""
    pattern: Optional[str] = Field(None, description="Cache key pattern to invalidate")
    learner_id: Optional[str] = Field(None, description="Invalidate all entries for learner")
    job_family: Optional[str] = Field(None, description="Invalidate all entries for job family")
    signal_id: Optional[str] = Field(None, description="Invalidate entries using specific signal")


class APIResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[Any] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if unsuccessful")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    version: str = Field(..., description="API version")
    dependencies: Dict[str, str] = Field(..., description="Dependency status")


# Dependency injection
def get_scoring_pipeline():
    """Get scoring pipeline instance."""
    return scoring_pipeline


def get_cache_service():
    """Get cache service instance."""
    return cache_service


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API health and dependencies."""
    try:
        # Check dependencies
        deps_status = {}
        
        # Check weight manager
        try:
            configs = weight_manager.get_all_configurations()
            deps_status["weight_manager"] = "healthy"
        except Exception as e:
            deps_status["weight_manager"] = f"error: {str(e)}"
        
        # Check provenance tracker
        try:
            events = list(provenance_tracker.events.keys())[:5]  # Just check access
            deps_status["provenance_tracker"] = "healthy"
        except Exception as e:
            deps_status["provenance_tracker"] = f"error: {str(e)}"
        
        # Check cache service
        try:
            cache_stats = cache_service.get_stats()
            deps_status["cache_service"] = "healthy"
        except Exception as e:
            deps_status["cache_service"] = f"error: {str(e)}"
        
        overall_status = "healthy" if all("healthy" in status for status in deps_status.values()) else "degraded"
        
        return HealthResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            version="1.0.0",
            dependencies=deps_status
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


# Main scoring endpoint
@app.post("/v1/scores/calculate", response_model=APIResponse)
async def calculate_compatibility_score(
    request: ScoreRequest,
    background_tasks: BackgroundTasks,
    scoring_pipeline: ScoringPipeline = Depends(get_scoring_pipeline),
    cache_service: CompatibilityCacheService = Depends(get_cache_service)
):
    """Calculate compatibility score for a learner-job combination."""
    try:
        start_time = datetime.utcnow()
        
        # Convert API request to internal model
        internal_request = CompatibilityScoreRequest(
            learner_id=request.learner_id,
            job_family=request.job_family,
            target_job_id=request.target_job_id,
            kash_signals=request.kash_signals,
            weight_configuration_id=request.weight_configuration_id,
            business_context=request.business_context,
            include_confidence_interval=request.include_confidence_interval,
            confidence_level=request.confidence_level,
            min_signal_quality=request.min_signal_quality,
            max_signal_age_days=request.max_signal_age_days
        )
        
        # Try to get from cache first
        cache_status = CacheHitStatus.MISS
        cached_response = None
        
        if request.use_cache:
            cached_response, cache_status = cache_service.get(internal_request)
        
        if cached_response is not None:
            # Return cached result
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return APIResponse(
                success=True,
                data=cached_response,
                metadata={
                    "cache_hit": True,
                    "cache_status": cache_status.value,
                    "processing_time_ms": processing_time,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        # Calculate new score
        response = scoring_pipeline.calculate_compatibility_score(internal_request)
        
        # Store in cache if enabled
        if request.use_cache:
            background_tasks.add_task(
                cache_service.put,
                internal_request,
                response,
                request.cache_ttl_minutes
            )
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return APIResponse(
            success=True,
            data=response,
            metadata={
                "cache_hit": False,
                "cache_status": cache_status.value,
                "processing_time_ms": processing_time,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        return APIResponse(
            success=False,
            error=str(e),
            metadata={
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# Batch scoring endpoint
@app.post("/v1/scores/batch", response_model=APIResponse)
async def calculate_batch_scores(
    request: BatchScoreRequest,
    background_tasks: BackgroundTasks,
    scoring_pipeline: ScoringPipeline = Depends(get_scoring_pipeline),
    cache_service: CompatibilityCacheService = Depends(get_cache_service)
):
    """Calculate compatibility scores for multiple learner-job combinations."""
    try:
        start_time = datetime.utcnow()
        results = []
        errors = []
        
        # Process requests in batches
        for i, api_request in enumerate(request.requests):
            try:
                # Convert to internal request
                internal_request = CompatibilityScoreRequest(
                    learner_id=api_request.learner_id,
                    job_family=api_request.job_family,
                    target_job_id=api_request.target_job_id,
                    kash_signals=api_request.kash_signals,
                    weight_configuration_id=api_request.weight_configuration_id,
                    business_context=api_request.business_context,
                    include_confidence_interval=api_request.include_confidence_interval,
                    confidence_level=api_request.confidence_level,
                    min_signal_quality=api_request.min_signal_quality,
                    max_signal_age_days=api_request.max_signal_age_days
                )
                
                # Try cache first
                cached_response = None
                cache_status = CacheHitStatus.MISS
                
                if api_request.use_cache:
                    cached_response, cache_status = cache_service.get(internal_request)
                
                if cached_response is not None:
                    results.append({
                        "request_index": i,
                        "success": True,
                        "data": cached_response,
                        "cache_hit": True,
                        "cache_status": cache_status.value
                    })
                else:
                    # Calculate new score
                    response = scoring_pipeline.calculate_compatibility_score(internal_request)
                    
                    # Store in cache
                    if api_request.use_cache:
                        background_tasks.add_task(
                            cache_service.put,
                            internal_request,
                            response,
                            api_request.cache_ttl_minutes
                        )
                    
                    results.append({
                        "request_index": i,
                        "success": True,
                        "data": response,
                        "cache_hit": False,
                        "cache_status": cache_status.value
                    })
                
            except Exception as e:
                errors.append({
                    "request_index": i,
                    "error": str(e)
                })
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return APIResponse(
            success=len(errors) == 0,
            data={
                "results": results,
                "errors": errors,
                "summary": {
                    "total_requests": len(request.requests),
                    "successful": len(results),
                    "failed": len(errors),
                    "cache_hits": sum(1 for r in results if r.get("cache_hit", False))
                }
            },
            metadata={
                "processing_time_ms": processing_time,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        return APIResponse(
            success=False,
            error=str(e),
            metadata={
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# Get score by ID (if cached)
@app.get("/v1/scores/{score_id}", response_model=APIResponse)
async def get_score_by_id(
    score_id: str,
    cache_service: CompatibilityCacheService = Depends(get_cache_service)
):
    """Get a specific compatibility score by ID."""
    try:
        # This would require implementing score lookup by ID in cache service
        # For now, return a placeholder response
        
        return APIResponse(
            success=False,
            error="Score lookup by ID not implemented",
            metadata={
                "score_id": score_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        return APIResponse(
            success=False,
            error=str(e),
            metadata={
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# Cache management endpoints
@app.post("/v1/cache/invalidate", response_model=APIResponse)
async def invalidate_cache(
    request: CacheInvalidationRequest,
    cache_service: CompatibilityCacheService = Depends(get_cache_service)
):
    """Invalidate cache entries."""
    try:
        invalidated_count = 0
        
        if request.pattern:
            invalidated_count += cache_service.invalidate(request.pattern)
        
        if request.learner_id:
            invalidated_count += cache_service.invalidate_by_learner(request.learner_id)
        
        if request.job_family:
            invalidated_count += cache_service.invalidate_by_job_family(request.job_family)
        
        if request.signal_id:
            invalidated_count += cache_service.invalidate_by_signal(request.signal_id)
        
        return APIResponse(
            success=True,
            data={
                "invalidated_entries": invalidated_count
            },
            metadata={
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        return APIResponse(
            success=False,
            error=str(e),
            metadata={
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@app.get("/v1/cache/stats", response_model=APIResponse)
async def get_cache_stats(
    cache_service: CompatibilityCacheService = Depends(get_cache_service)
):
    """Get cache statistics."""
    try:
        stats = cache_service.get_stats()
        
        return APIResponse(
            success=True,
            data=stats,
            metadata={
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        return APIResponse(
            success=False,
            error=str(e),
            metadata={
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@app.delete("/v1/cache", response_model=APIResponse)
async def clear_cache(
    cache_service: CompatibilityCacheService = Depends(get_cache_service)
):
    """Clear all cache entries."""
    try:
        cache_service.clear()
        
        return APIResponse(
            success=True,
            data={"message": "Cache cleared successfully"},
            metadata={
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        return APIResponse(
            success=False,
            error=str(e),
            metadata={
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# Weight configuration endpoints
@app.get("/v1/weights/configurations", response_model=APIResponse)
async def get_weight_configurations(
    job_family: Optional[JobFamilyEnum] = Query(None, description="Filter by job family"),
    active_only: bool = Query(True, description="Only active configurations")
):
    """Get weight configurations."""
    try:
        configurations = weight_manager.get_all_configurations(job_family, active_only)
        
        return APIResponse(
            success=True,
            data={
                "configurations": [config.model_dump() for config in configurations],
                "total": len(configurations)
            },
            metadata={
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        return APIResponse(
            success=False,
            error=str(e),
            metadata={
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@app.get("/v1/weights/stats", response_model=APIResponse)
async def get_weight_stats():
    """Get weight configuration statistics."""
    try:
        stats = weight_manager.get_configuration_stats()
        
        return APIResponse(
            success=True,
            data=stats,
            metadata={
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        return APIResponse(
            success=False,
            error=str(e),
            metadata={
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# Provenance endpoints
@app.get("/v1/provenance/events", response_model=APIResponse)
async def get_provenance_events(
    learner_id: Optional[str] = Query(None, description="Filter by learner ID"),
    score_id: Optional[str] = Query(None, description="Filter by score ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of events")
):
    """Get provenance events."""
    try:
        from ..models import ProvenanceQuery
        
        query = ProvenanceQuery(
            query_id=str(uuid.uuid4()),
            learner_id=learner_id,
            score_id=score_id,
            max_results=limit
        )
        
        events = provenance_tracker.query_events(query)
        
        return APIResponse(
            success=True,
            data={
                "events": [event.model_dump() for event in events],
                "total": len(events),
                "query": query.model_dump()
            },
            metadata={
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        return APIResponse(
            success=False,
            error=str(e),
            metadata={
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@app.get("/v1/provenance/learners/{learner_id}/quality", response_model=APIResponse)
async def get_learner_data_quality(learner_id: str):
    """Get data quality summary for a learner."""
    try:
        quality_summary = provenance_tracker.get_data_quality_summary(learner_id)
        
        return APIResponse(
            success=True,
            data=quality_summary,
            metadata={
                "learner_id": learner_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        return APIResponse(
            success=False,
            error=str(e),
            metadata={
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize API on startup."""
    print("🚀 KASH Compatibility Score API starting up...")
    print(f"   Cache max entries: {cache_service.max_entries}")
    print(f"   Cache TTL: {cache_service.default_ttl_minutes} minutes")
    print("   Ready to serve requests!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("🛑 KASH Compatibility Score API shutting down...")
    cache_service._save_cache()
    print("   Cache saved. Goodbye!")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
