"""API endpoints for explainability service."""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from ..models.explanation_models import (
    StandardizedExplanation, ExplanationComparison, QAQuery, QAQueryResult,
    ExplanationType, ExplanationScope, ConfidenceLevel
)
from ..services.explainability_service import ExplainabilityService


router = APIRouter(prefix="/explainability", tags=["explainability"])
explainability_service = ExplainabilityService()
logger = logging.getLogger(__name__)


@router.get("/health", summary="Health check for explainability service")
async def health_check():
    """Health check endpoint."""
    stats = explainability_service.get_service_stats()
    return {
        "status": "healthy",
        "service": "explainability",
        "version": "1.0.0",
        "shap_available": stats["shap_available"],
        "cache_size": stats["cache_size"]
    }


@router.post("/compatibility/{learner_id}/{job_family}", 
            response_model=StandardizedExplanation,
            summary="Explain compatibility score")
async def explain_compatibility_score(
    learner_id: str,
    job_family: str,
    include_recommendations: bool = Query(True, description="Include actionable recommendations")
):
    """
    Generate SHAP explanation for compatibility score.
    
    - **learner_id**: ID of the learner
    - **job_family**: Target job family
    - **include_recommendations**: Whether to include actionable recommendations
    """
    try:
        explanation = explainability_service.explain_compatibility_score(
            learner_id=learner_id,
            job_family=job_family,
            include_recommendations=include_recommendations
        )
        return explanation
    except Exception as e:
        logger.error(f"Error explaining compatibility score: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prediction/{model_id}",
            response_model=StandardizedExplanation,
            summary="Explain prediction")
async def explain_prediction(
    model_id: str,
    feature_vector: List[float],
    feature_names: List[str],
    learner_id: Optional[str] = Query(None, description="Learner ID for context"),
    include_recommendations: bool = Query(True, description="Include actionable recommendations")
):
    """
    Generate SHAP explanation for predictive model prediction.
    
    - **model_id**: ID of the predictive model
    - **feature_vector**: Feature values for prediction
    - **feature_names**: Names corresponding to feature values
    - **learner_id**: Optional learner ID for context
    - **include_recommendations**: Whether to include actionable recommendations
    """
    try:
        if len(feature_vector) != len(feature_names):
            raise HTTPException(
                status_code=400, 
                detail="feature_vector and feature_names must have same length"
            )
        
        explanation = explainability_service.explain_prediction(
            model_id=model_id,
            feature_vector=feature_vector,
            feature_names=feature_names,
            learner_id=learner_id,
            include_recommendations=include_recommendations
        )
        return explanation
    except Exception as e:
        logger.error(f"Error explaining prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/explanation/{explanation_id}",
           response_model=Dict[str, Any],
           summary="Get cached explanation")
async def get_explanation(explanation_id: str):
    """Retrieve cached explanation by ID."""
    try:
        explanation = explainability_service.get_cached_explanation(explanation_id)
        if not explanation:
            raise HTTPException(status_code=404, detail="Explanation not found")
        
        return explanation.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving explanation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query",
            response_model=QAQueryResult,
            summary="Query explanations with filters")
async def query_explanations(query: QAQuery):
    """
    Query explanations with filters and pagination.
    
    Supports filtering by:
    - learner_id
    - model_id  
    - date_range
    - explanation_types
    """
    try:
        result = explainability_service.query_explanations(query)
        return result
    except Exception as e:
        logger.error(f"Error querying explanations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare/{explanation_1_id}/{explanation_2_id}",
            response_model=ExplanationComparison,
            summary="Compare two explanations")
async def compare_explanations(
    explanation_1_id: str,
    explanation_2_id: str,
    comparison_reason: str = Query(..., description="Reason for comparison"),
    compared_by: str = Query(..., description="Who is performing comparison")
):
    """
    Compare two explanations to identify changes and insights.
    
    - **explanation_1_id**: First explanation ID
    - **explanation_2_id**: Second explanation ID  
    - **comparison_reason**: Reason for performing comparison
    - **compared_by**: Who is performing the comparison
    """
    try:
        comparison = explainability_service.compare_explanations(
            explanation_1_id=explanation_1_id,
            explanation_2_id=explanation_2_id,
            comparison_reason=comparison_reason,
            compared_by=compared_by
        )
        return comparison
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error comparing explanations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learner/{learner_id}/explanations",
           response_model=List[Dict[str, Any]],
           summary="Get all explanations for a learner")
async def get_learner_explanations(
    learner_id: str,
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    """Get all explanations for a specific learner."""
    try:
        query = QAQuery(
            query_type="learner_history",
            parameters={"learner_id": learner_id},
            learner_id=learner_id,
            limit=limit,
            offset=offset,
            requested_by="api"
        )
        
        result = explainability_service.query_explanations(query)
        return [exp.model_dump() for exp in result.explanations]
    except Exception as e:
        logger.error(f"Error getting learner explanations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model/{model_id}/explanations",
           response_model=List[Dict[str, Any]],
           summary="Get all explanations for a model")
async def get_model_explanations(
    model_id: str,
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    """Get all explanations for a specific model."""
    try:
        query = QAQuery(
            query_type="model_history",
            parameters={"model_id": model_id},
            model_id=model_id,
            limit=limit,
            offset=offset,
            requested_by="api"
        )
        
        result = explainability_service.query_explanations(query)
        return [exp.model_dump() for exp in result.explanations]
    except Exception as e:
        logger.error(f"Error getting model explanations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", summary="Get explainability service statistics")
async def get_service_stats():
    """Get service statistics and health metrics."""
    try:
        stats = explainability_service.get_service_stats()
        return {
            "service_stats": stats,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy"
        }
    except Exception as e:
        logger.error(f"Error getting service stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/cleanup", summary="Clean up explanation cache")
async def cleanup_cache(background_tasks: BackgroundTasks):
    """Clean up old explanations from cache."""
    try:
        background_tasks.add_task(explainability_service.cleanup_cache)
        return {
            "message": "Cache cleanup started",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error starting cache cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/explanation-types", summary="Get available explanation types")
async def get_explanation_types():
    """Get list of supported explanation types."""
    return {
        "types": [t.value for t in ExplanationType],
        "descriptions": {
            "shap": "SHAP (SHapley Additive exPlanations) - Game theory based explanations",
            "lime": "LIME (Local Interpretable Model-agnostic Explanations) - Local approximations",
            "feature_importance": "Global feature importance from model coefficients",
            "partial_dependence": "Partial dependence plots for feature effects",
            "counterfactual": "Counterfactual explanations showing minimal changes"
        }
    }


@router.get("/confidence-levels", summary="Get confidence level descriptions")
async def get_confidence_levels():
    """Get descriptions of confidence levels."""
    return {
        "levels": [l.value for l in ConfidenceLevel],
        "descriptions": {
            "very_low": "Explanation has very low confidence, results may be unreliable",
            "low": "Explanation has low confidence, interpret with caution",
            "medium": "Explanation has moderate confidence, generally reliable",
            "high": "Explanation has high confidence, results are reliable",
            "very_high": "Explanation has very high confidence, results are highly reliable"
        }
    }


@router.post("/batch/explain-compatibility",
            response_model=List[StandardizedExplanation],
            summary="Batch explain compatibility scores")
async def batch_explain_compatibility(
    requests: List[Dict[str, str]],
    include_recommendations: bool = Query(True, description="Include actionable recommendations")
):
    """
    Generate explanations for multiple compatibility score requests.
    
    Each request should contain:
    - learner_id: ID of the learner
    - job_family: Target job family
    """
    try:
        explanations = []
        
        for request in requests:
            learner_id = request.get("learner_id")
            job_family = request.get("job_family")
            
            if not learner_id or not job_family:
                continue
            
            explanation = explainability_service.explain_compatibility_score(
                learner_id=learner_id,
                job_family=job_family,
                include_recommendations=include_recommendations
            )
            explanations.append(explanation)
        
        return explanations
    except Exception as e:
        logger.error(f"Error in batch compatibility explanation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch/explain-prediction",
            response_model=List[StandardizedExplanation],
            summary="Batch explain predictions")
async def batch_explain_predictions(
    requests: List[Dict[str, Any]],
    include_recommendations: bool = Query(True, description="Include actionable recommendations")
):
    """
    Generate explanations for multiple prediction requests.
    
    Each request should contain:
    - model_id: ID of the predictive model
    - feature_vector: Feature values for prediction
    - feature_names: Names corresponding to feature values
    - learner_id: Optional learner ID for context
    """
    try:
        explanations = []
        
        for request in requests:
            model_id = request.get("model_id")
            feature_vector = request.get("feature_vector", [])
            feature_names = request.get("feature_names", [])
            learner_id = request.get("learner_id")
            
            if not model_id or not feature_vector or not feature_names:
                continue
            
            if len(feature_vector) != len(feature_names):
                continue
            
            explanation = explainability_service.explain_prediction(
                model_id=model_id,
                feature_vector=feature_vector,
                feature_names=feature_names,
                learner_id=learner_id,
                include_recommendations=include_recommendations
            )
            explanations.append(explanation)
        
        return explanations
    except Exception as e:
        logger.error(f"Error in batch prediction explanation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/summary/{learner_id}",
           summary="Get dashboard summary for learner")
async def get_dashboard_summary(learner_id: str):
    """Get summary data for explainability dashboard."""
    try:
        # Get recent explanations for learner
        query = QAQuery(
            query_type="dashboard_summary",
            parameters={"learner_id": learner_id},
            learner_id=learner_id,
            limit=10,
            sort_by="generated_at",
            sort_order="desc",
            requested_by="dashboard"
        )
        
        result = explainability_service.query_explanations(query)
        
        # Calculate summary statistics
        explanations = result.explanations
        total_explanations = len(explanations)
        
        if total_explanations == 0:
            return {
                "learner_id": learner_id,
                "total_explanations": 0,
                "recent_explanations": [],
                "confidence_distribution": {},
                "average_quality": None,
                "top_insights": ["No explanations available"]
            }
        
        # Confidence distribution
        confidence_dist = {}
        for exp in explanations:
            level = exp.explanation_metadata.confidence_level.value
            confidence_dist[level] = confidence_dist.get(level, 0) + 1
        
        # Average quality
        quality_scores = [
            exp.explanation_metadata.explanation_quality_score 
            for exp in explanations 
            if exp.explanation_metadata.explanation_quality_score is not None
        ]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else None
        
        # Top insights from recent explanations
        top_insights = []
        for exp in explanations[:5]:
            if exp.prediction_value is not None:
                if exp.prediction_value > 0.8:
                    top_insights.append(f"High prediction score ({exp.prediction_value:.2f})")
                elif exp.prediction_value < 0.3:
                    top_insights.append(f"Low prediction score ({exp.prediction_value:.2f}) - needs attention")
        
        return {
            "learner_id": learner_id,
            "total_explanations": total_explanations,
            "recent_explanations": [exp.model_dump() for exp in explanations[:5]],
            "confidence_distribution": confidence_dist,
            "average_quality": avg_quality,
            "top_insights": top_insights[:3],
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating dashboard summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
