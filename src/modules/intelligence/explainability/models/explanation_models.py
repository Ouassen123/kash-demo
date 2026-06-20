"""Explainability models for SHAP integration and standardized explanations."""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum
import uuid


class ExplanationType(str, Enum):
    """Types of explanations supported."""
    SHAP = "shap"
    LIME = "lime"
    FEATURE_IMPORTANCE = "feature_importance"
    PARTIAL_DEPENDENCE = "partial_dependence"
    COUNTERFACTUAL = "counterfactual"


class ExplanationScope(str, Enum):
    """Scope of the explanation."""
    GLOBAL = "global"  # Model-level explanation
    LOCAL = "local"    # Single prediction explanation
    GROUP = "group"    # Group of predictions explanation


class ContributionDirection(str, Enum):
    """Direction of feature contribution."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class ConfidenceLevel(str, Enum):
    """Confidence levels for explanations."""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class FeatureContribution(BaseModel):
    """Individual feature contribution to explanation."""
    feature_name: str = Field(..., description="Name of the feature")
    feature_value: Optional[Union[str, int, float]] = Field(None, description="Value of the feature")
    contribution_score: float = Field(..., description="SHAP value or contribution score")
    contribution_direction: ContributionDirection = Field(..., description="Direction of contribution")
    contribution_percentage: float = Field(..., description="Percentage of total contribution")
    feature_type: str = Field(..., description="Type of feature (compatibility, historical, etc.)")
    importance_rank: int = Field(..., description="Rank in feature importance")
    baseline_value: Optional[float] = Field(None, description="Baseline value for comparison")
    
    class Config:
        use_enum_values = True


class ExplanationMetadata(BaseModel):
    """Metadata about how the explanation was generated."""
    explanation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    explanation_type: ExplanationType = Field(..., description="Type of explanation")
    explanation_scope: ExplanationScope = Field(..., description="Scope of explanation")
    model_id: str = Field(..., description="ID of the model being explained")
    model_version: str = Field(..., description="Version of the model")
    model_type: str = Field(..., description="Type of model (compatibility, predictive, etc.)")
    
    # Generation metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by: str = Field(..., description="Service or user that generated explanation")
    computation_time_ms: Optional[float] = Field(None, description="Time to compute explanation in ms")
    
    # Data metadata
    feature_count: int = Field(..., description="Number of features used")
    feature_list: List[str] = Field(..., description="List of feature names")
    sample_size: Optional[int] = Field(None, description="Sample size for global explanations")
    
    # Model metadata
    algorithm: Optional[str] = Field(None, description="Algorithm used by the model")
    model_weights: Optional[Dict[str, float]] = Field(None, description="Model weights if available")
    training_data_hash: Optional[str] = Field(None, description="Hash of training data")
    
    # Quality metrics
    explanation_quality_score: Optional[float] = Field(None, ge=0, le=1, description="Quality of explanation")
    confidence_level: ConfidenceLevel = Field(..., description="Confidence in explanation")
    uncertainty_estimate: Optional[float] = Field(None, ge=0, le=1, description="Uncertainty in explanation")
    
    # Technical details
    shap_version: Optional[str] = Field(None, description="SHAP library version used")
    background_dataset_size: Optional[int] = Field(None, description="Size of background dataset")
    explanation_parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters used")
    
    class Config:
        use_enum_values = True


class ExplanationSnapshot(BaseModel):
    """Cached explanation snapshot for reference and comparison."""
    snapshot_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    explanation_metadata: ExplanationMetadata = Field(..., description="Explanation metadata")
    
    # Reference information
    learner_id: Optional[str] = Field(None, description="Learner ID for local explanations")
    target_role: Optional[str] = Field(None, description="Target role if applicable")
    prediction_id: Optional[str] = Field(None, description="Associated prediction ID")
    
    # Data snapshot
    input_features: Dict[str, Union[str, int, float]] = Field(..., description="Input features used")
    prediction_value: Optional[float] = Field(None, description="Original prediction value")
    prediction_confidence: Optional[float] = Field(None, description="Prediction confidence")
    
    # Explanation data
    feature_contributions: List[FeatureContribution] = Field(..., description="Feature contributions")
    base_value: Optional[float] = Field(None, description="Base value for SHAP")
    total_contribution: float = Field(..., description="Sum of all contributions")
    
    # Quality and validation
    explanation_quality_metrics: Dict[str, float] = Field(default_factory=dict, description="Quality metrics")
    validation_status: str = Field("pending", description="Validation status")
    validated_by: Optional[str] = Field(None, description="Who validated the explanation")
    validation_notes: Optional[str] = Field(None, description="Validation notes")
    
    # Temporal information
    signal_freshness_days: Dict[str, int] = Field(default_factory=dict, description="Freshness of input signals")
    data_quality_score: Optional[float] = Field(None, ge=0, le=1, description="Quality of input data")
    
    # Versioning
    version: int = Field(1, description="Version of this explanation")
    parent_snapshot_id: Optional[str] = Field(None, description="Parent explanation if this is a revision")
    change_summary: Optional[str] = Field(None, description="Summary of changes from parent")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True


class StandardizedExplanation(BaseModel):
    """Standardized explanation output for dashboard consumption."""
    explanation_id: str = Field(..., description="Unique explanation identifier")
    explanation_type: ExplanationType = Field(..., description="Type of explanation")
    explanation_scope: ExplanationScope = Field(..., description="Scope of explanation")
    
    # Core explanation data
    prediction_value: float = Field(..., description="Original prediction value")
    base_value: Optional[float] = Field(None, description="Base value for comparison")
    feature_contributions: List[FeatureContribution] = Field(..., description="Feature contributions")
    
    # Summary information
    top_positive_factors: List[FeatureContribution] = Field(..., description="Top positive contributing factors")
    top_negative_factors: List[FeatureContribution] = Field(..., description="Top negative contributing factors")
    key_insights: List[str] = Field(..., description="Key insights from explanation")
    
    # Quality and confidence
    confidence_level: ConfidenceLevel = Field(..., description="Confidence in explanation")
    explanation_quality_score: Optional[float] = Field(None, ge=0, le=1, description="Quality score")
    data_quality_indicators: Dict[str, Any] = Field(default_factory=dict, description="Data quality info")
    
    # Context information
    learner_id: Optional[str] = Field(None, description="Learner ID if applicable")
    model_info: Dict[str, str] = Field(..., description="Model information")
    generation_info: Dict[str, Any] = Field(..., description="Generation metadata")
    
    # Recommendations
    actionable_recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations")
    improvement_areas: List[str] = Field(default_factory=list, description="Areas for improvement")
    strength_areas: List[str] = Field(default_factory=list, description="Strength areas to maintain")
    
    # Technical details for advanced users
    technical_metadata: Dict[str, Any] = Field(default_factory=dict, description="Technical details")
    
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True


class ExplanationComparison(BaseModel):
    """Comparison between two explanations."""
    comparison_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    explanation_1_id: str = Field(..., description="First explanation ID")
    explanation_2_id: str = Field(..., description="Second explanation ID")
    
    # Comparison metadata
    comparison_date: datetime = Field(default_factory=datetime.utcnow)
    comparison_reason: str = Field(..., description="Reason for comparison")
    compared_by: str = Field(..., description="Who performed comparison")
    
    # Feature changes
    feature_changes: List[Dict[str, Any]] = Field(..., description="Changes in feature contributions")
    new_top_features: List[str] = Field(..., description="Features that became top contributors")
    lost_top_features: List[str] = Field(..., description="Features that lost top contributor status")
    
    # Overall changes
    prediction_change: Optional[float] = Field(None, description="Change in prediction value")
    confidence_change: Optional[str] = Field(None, description="Change in confidence level")
    quality_change: Optional[float] = Field(None, description="Change in explanation quality")
    
    # Analysis
    change_summary: str = Field(..., description="Summary of changes")
    significance_level: str = Field(..., description="Statistical significance of changes")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations based on comparison")
    
    class Config:
        use_enum_values = True


class QAQuery(BaseModel):
    """Query for QA tooling."""
    query_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query_type: str = Field(..., description="Type of query (history, comparison, anomaly)")
    parameters: Dict[str, Any] = Field(..., description="Query parameters")
    
    # Filters
    learner_id: Optional[str] = Field(None, description="Filter by learner ID")
    model_id: Optional[str] = Field(None, description="Filter by model ID")
    date_range: Optional[Dict[str, datetime]] = Field(None, description="Date range filter")
    explanation_types: Optional[List[ExplanationType]] = Field(None, description="Filter by explanation types")
    
    # Sorting and pagination
    sort_by: str = Field("generated_at", description="Sort field")
    sort_order: str = Field("desc", description="Sort order")
    limit: int = Field(100, ge=1, le=1000, description="Result limit")
    offset: int = Field(0, ge=0, description="Result offset")
    
    requested_by: str = Field(..., description="Who requested the query")
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True


class QAQueryResult(BaseModel):
    """Result of QA query."""
    query_id: str = Field(..., description="Query ID")
    result_type: str = Field(..., description="Type of result")
    
    # Results
    explanations: List[ExplanationSnapshot] = Field(default_factory=list, description="Explanation snapshots")
    comparisons: List[ExplanationComparison] = Field(default_factory=list, description="Comparisons")
    anomalies: List[Dict[str, Any]] = Field(default_factory=list, description="Detected anomalies")
    
    # Summary statistics
    total_explanations: int = Field(0, description="Total explanations found")
    total_comparisons: int = Field(0, description="Total comparisons found")
    total_anomalies: int = Field(0, description="Total anomalies found")
    
    # Quality metrics
    average_quality_score: Optional[float] = Field(None, description="Average explanation quality")
    quality_distribution: Dict[str, int] = Field(default_factory=dict, description="Distribution of quality scores")
    
    # Performance metrics
    query_time_ms: float = Field(..., description="Time to execute query in ms")
    cache_hit: bool = Field(False, description="Whether result came from cache")
    
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True


class ExplainabilityConfig(BaseModel):
    """Configuration for explainability service."""
    service_name: str = Field("kash_explainability", description="Service name")
    version: str = Field("1.0", description="Service version")
    
    # SHAP configuration
    shap_background_size: int = Field(100, description="Background dataset size for SHAP")
    shap_max_display: int = Field(20, description="Maximum features to display")
    shap_algorithm: str = Field("auto", description="SHAP algorithm to use")
    
    # Caching configuration
    cache_enabled: bool = Field(True, description="Enable explanation caching")
    cache_ttl_hours: int = Field(24, description="Cache TTL in hours")
    max_cache_size: int = Field(10000, description="Maximum cache size")
    
    # Quality thresholds
    min_quality_threshold: float = Field(0.7, description="Minimum explanation quality")
    confidence_threshold: float = Field(0.8, description="Confidence threshold for alerts")
    
    # Performance configuration
    max_computation_time_ms: float = Field(5000, description="Max computation time")
    parallel_processing: bool = Field(True, description="Enable parallel processing")
    max_workers: int = Field(4, description="Maximum worker threads")
    
    # Feature configuration
    feature_groups: Dict[str, List[str]] = Field(default_factory=dict, description="Feature groupings")
    feature_display_names: Dict[str, str] = Field(default_factory=dict, description="Display names for features")
    feature_descriptions: Dict[str, str] = Field(default_factory=dict, description="Feature descriptions")
    
    # Output configuration
    include_technical_details: bool = Field(True, description="Include technical details")
    include_recommendations: bool = Field(True, description="Include recommendations")
    max_recommendations: int = Field(5, description="Maximum recommendations to include")
    
    # Monitoring configuration
    enable_monitoring: bool = Field(True, description="Enable performance monitoring")
    log_level: str = Field("INFO", description="Logging level")
    metrics_endpoint: Optional[str] = Field(None, description="Metrics endpoint")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True
