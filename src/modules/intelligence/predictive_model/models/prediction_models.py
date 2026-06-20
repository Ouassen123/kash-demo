"""Core data models for predictive success modeling."""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum
import uuid


class PredictionTarget(str, Enum):
    """Types of predictions the model can make."""
    SUCCESS_LIKELIHOOD = "success_likelihood"
    RETENTION_PROBABILITY = "retention_probability"
    READINESS_SCORE = "readiness_score"
    CAREER_PROGRESS = "career_progress"
    SKILL_GAP_RISK = "skill_gap_risk"


class ModelType(str, Enum):
    """Types of predictive models."""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    SURVIVAL_ANALYSIS = "survival_analysis"
    TIME_SERIES = "time_series"


class FeatureType(str, Enum):
    """Types of features used in predictions."""
    COMPATIBILITY_SCORE = "compatibility_score"
    DOMAIN_BREAKDOWN = "domain_breakdown"
    SIGNAL_TREND = "signal_trend"
    HISTORICAL_PERFORMANCE = "historical_performance"
    DEMOGRAPHIC = "demographic"
    BEHAVIORAL = "behavioral"
    ENVIRONMENTAL = "environmental"


class ConfidenceLevel(str, Enum):
    """Confidence levels for predictions."""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class DataQuality(str, Enum):
    """Data quality indicators."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    INSUFFICIENT = "insufficient"


class FeatureImportance(BaseModel):
    """Feature importance for model explainability."""
    feature_name: str = Field(..., description="Name of the feature")
    importance_score: float = Field(..., ge=0, le=1, description="Importance score (0-1)")
    feature_type: FeatureType = Field(..., description="Type of feature")
    contribution_direction: str = Field(..., description="Positive or negative contribution")
    raw_value: Optional[float] = Field(None, description="Raw feature value")
    normalized_value: Optional[float] = Field(None, description="Normalized feature value")


class PredictionExplanation(BaseModel):
    """Explanation for a prediction."""
    primary_factors: List[FeatureImportance] = Field(..., description="Main factors driving the prediction")
    secondary_factors: List[FeatureImportance] = Field(..., description="Secondary factors")
    competency_gaps: List[str] = Field(default_factory=list, description="Identified competency gaps")
    strength_areas: List[str] = Field(default_factory=list, description="Areas of strength")
    data_limitations: List[str] = Field(default_factory=list, description="Data quality limitations")
    confidence_factors: Dict[str, float] = Field(default_factory=dict, description="Factors affecting confidence")


class PredictionResult(BaseModel):
    """Result of a prediction."""
    prediction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    learner_id: str = Field(..., description="Learner identifier")
    target_role: Optional[str] = Field(None, description="Target role if applicable")
    prediction_type: PredictionTarget = Field(..., description="Type of prediction")
    predicted_value: float = Field(..., description="Predicted value (probability, score, etc.)")
    confidence_level: ConfidenceLevel = Field(..., description="Confidence in prediction")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence score (0-1)")
    prediction_date: datetime = Field(default_factory=datetime.utcnow)
    
    # Explainability
    explanation: PredictionExplanation = Field(..., description="Explanation of prediction")
    
    # Metadata
    model_version: str = Field(..., description="Model version used")
    data_quality: DataQuality = Field(..., description="Quality of input data")
    data_freshness: Optional[int] = Field(None, description="Data freshness in days")
    feature_count: int = Field(..., description="Number of features used")
    
    # Tracking
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TrainingFeature(BaseModel):
    """Feature definition for training."""
    feature_name: str = Field(..., description="Name of the feature")
    feature_type: FeatureType = Field(..., description="Type of feature")
    data_type: str = Field(..., description="Data type (numeric, categorical, etc.)")
    source: str = Field(..., description="Source of the feature")
    transformation: Optional[str] = Field(None, description="Transformation applied")
    is_active: bool = Field(True, description="Whether feature is active")
    importance_rank: Optional[int] = Field(None, description="Rank in feature importance")
    missing_value_strategy: str = Field("mean", description="Strategy for missing values")


class TrainingDataset(BaseModel):
    """Training dataset metadata."""
    dataset_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    dataset_name: str = Field(..., description="Name of the dataset")
    version: str = Field(..., description="Dataset version")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Dataset characteristics
    total_samples: int = Field(..., description="Total number of samples")
    training_samples: int = Field(..., description="Number of training samples")
    validation_samples: int = Field(..., description="Number of validation samples")
    test_samples: int = Field(..., description="Number of test samples")
    
    # Feature information
    feature_count: int = Field(..., description="Number of features")
    features: List[TrainingFeature] = Field(..., description="List of features")
    
    # Target information
    target_variable: str = Field(..., description="Target variable name")
    target_distribution: Dict[str, float] = Field(..., description="Target variable distribution")
    
    # Data quality
    missing_data_percentage: float = Field(..., ge=0, le=100, description="Percentage of missing data")
    outlier_percentage: float = Field(..., ge=0, le=100, description="Percentage of outliers")
    
    # Temporal information
    data_start_date: Optional[datetime] = Field(None, description="Start date of data")
    data_end_date: Optional[datetime] = Field(None, description="End date of data")
    
    # Source information
    data_sources: List[str] = Field(..., description="Data sources used")
    preprocessing_steps: List[str] = Field(default_factory=list, description="Preprocessing steps applied")


class ModelPerformance(BaseModel):
    """Model performance metrics."""
    model_version: str = Field(..., description="Model version")
    evaluation_date: datetime = Field(default_factory=datetime.utcnow)
    
    # Classification metrics
    accuracy: Optional[float] = Field(None, ge=0, le=1, description="Accuracy score")
    precision: Optional[float] = Field(None, ge=0, le=1, description="Precision score")
    recall: Optional[float] = Field(None, ge=0, le=1, description="Recall score")
    f1_score: Optional[float] = Field(None, ge=0, le=1, description="F1 score")
    auc_roc: Optional[float] = Field(None, ge=0, le=1, description="AUC-ROC score")
    
    # Regression metrics
    mse: Optional[float] = Field(None, ge=0, description="Mean squared error")
    rmse: Optional[float] = Field(None, ge=0, description="Root mean squared error")
    mae: Optional[float] = Field(None, ge=0, description="Mean absolute error")
    r2_score: Optional[float] = Field(None, description="R-squared score")
    
    # Business metrics
    calibration_score: Optional[float] = Field(None, ge=0, le=1, description="Calibration score")
    business_impact_score: Optional[float] = Field(None, ge=0, le=1, description="Business impact score")
    
    # Fairness metrics
    fairness_metrics: Dict[str, float] = Field(default_factory=dict, description="Fairness metrics")
    
    # Performance by segment
    performance_by_segment: Dict[str, Dict[str, float]] = Field(
        default_factory=dict, description="Performance by segment"
    )


class ModelMetadata(BaseModel):
    """Metadata for a trained model."""
    model_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    model_name: str = Field(..., description="Name of the model")
    model_version: str = Field(..., description="Version of the model")
    model_type: ModelType = Field(..., description="Type of model")
    prediction_target: PredictionTarget = Field(..., description="Prediction target")
    
    # Training information
    training_dataset: TrainingDataset = Field(..., description="Training dataset used")
    training_date: datetime = Field(default_factory=datetime.utcnow)
    training_duration_hours: float = Field(..., description="Training duration in hours")
    
    # Model parameters
    hyperparameters: Dict[str, Any] = Field(..., description="Model hyperparameters")
    feature_importance: List[FeatureImportance] = Field(..., description="Feature importance")
    
    # Performance
    performance: ModelPerformance = Field(..., description="Model performance metrics")
    
    # Validation
    cross_validation_score: float = Field(..., description="Cross-validation score")
    validation_method: str = Field(..., description="Validation method used")
    
    # Deployment
    is_deployed: bool = Field(False, description="Whether model is deployed")
    deployment_date: Optional[datetime] = Field(None, description="Deployment date")
    deployment_environment: Optional[str] = Field(None, description="Deployment environment")
    
    # Monitoring
    monitoring_enabled: bool = Field(True, description="Whether monitoring is enabled")
    drift_detection_enabled: bool = Field(True, description="Whether drift detection is enabled")
    
    # Governance
    created_by: str = Field(..., description="Who created the model")
    approved_by: Optional[str] = Field(None, description="Who approved the model")
    approval_date: Optional[datetime] = Field(None, description="Approval date")
    
    # Retraining
    retraining_schedule: Optional[str] = Field(None, description="Retraining schedule")
    last_retraining_date: Optional[datetime] = Field(None, description="Last retraining date")
    
    # Documentation
    description: str = Field(..., description="Model description")
    business_objective: str = Field(..., description="Business objective")
    limitations: List[str] = Field(default_factory=list, description="Model limitations")
    intended_use: str = Field(..., description="Intended use of the model")
    
    # Technical details
    framework: str = Field(..., description="ML framework used")
    algorithm: str = Field(..., description="Algorithm used")
    model_size_mb: Optional[float] = Field(None, description="Model size in MB")
    inference_latency_ms: Optional[float] = Field(None, description="Inference latency in ms")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DriftDetection(BaseModel):
    """Data drift detection results."""
    drift_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    model_version: str = Field(..., description="Model version being monitored")
    detection_date: datetime = Field(default_factory=datetime.utcnow)
    
    # Drift metrics
    population_stability_index: float = Field(..., description="Population stability index")
    kolmogorov_smirnov_statistic: float = Field(..., description="KS statistic")
    feature_drift_scores: Dict[str, float] = Field(..., description="Drift scores by feature")
    
    # Assessment
    drift_detected: bool = Field(..., description="Whether drift was detected")
    drift_severity: str = Field(..., description="Severity of drift")
    affected_features: List[str] = Field(..., description="Features affected by drift")
    
    # Recommendations
    recommended_actions: List[str] = Field(default_factory=list, description="Recommended actions")
    retraining_recommended: bool = Field(False, description="Whether retraining is recommended")
    
    # Context
    baseline_period: str = Field(..., description="Baseline period used")
    comparison_period: str = Field(..., description="Comparison period used")
    sample_size_baseline: int = Field(..., description="Sample size in baseline")
    sample_size_current: int = Field(..., description="Sample size in current period")


class PredictionAlert(BaseModel):
    """Alert for significant prediction changes."""
    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    learner_id: str = Field(..., description="Learner identifier")
    alert_type: str = Field(..., description="Type of alert")
    severity: str = Field(..., description="Alert severity")
    
    # Change information
    previous_prediction: Optional[float] = Field(None, description="Previous prediction value")
    current_prediction: float = Field(..., description="Current prediction value")
    change_magnitude: float = Field(..., description="Magnitude of change")
    change_percentage: float = Field(..., description="Percentage change")
    
    # Context
    prediction_type: PredictionTarget = Field(..., description="Type of prediction")
    model_version: str = Field(..., description="Model version")
    alert_date: datetime = Field(default_factory=datetime.utcnow)
    
    # Explanation
    reason_for_change: str = Field(..., description="Reason for the change")
    contributing_factors: List[str] = Field(default_factory=list, description="Factors contributing to change")
    
    # Actions
    recommended_actions: List[str] = Field(default_factory=list, description="Recommended actions")
    auto_escalation: bool = Field(False, description="Whether to auto-escalate")
    
    # Status
    acknowledged: bool = Field(False, description="Whether alert is acknowledged")
    acknowledged_by: Optional[str] = Field(None, description="Who acknowledged the alert")
    acknowledged_at: Optional[datetime] = Field(None, description="When alert was acknowledged")
    resolved: bool = Field(False, description="Whether alert is resolved")
    resolved_at: Optional[datetime] = Field(None, description="When alert was resolved")


class BatchPredictionRequest(BaseModel):
    """Request for batch predictions."""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    learner_ids: List[str] = Field(..., description="List of learner IDs")
    prediction_types: List[PredictionTarget] = Field(..., description="Types of predictions to make")
    target_roles: Optional[List[str]] = Field(None, description="Target roles for predictions")
    model_version: Optional[str] = Field(None, description="Specific model version to use")
    include_explanations: bool = Field(True, description="Whether to include explanations")
    batch_size: int = Field(100, ge=1, le=1000, description="Batch size for processing")
    priority: str = Field("normal", description="Processing priority")


class BatchPredictionResponse(BaseModel):
    """Response for batch predictions."""
    request_id: str = Field(..., description="Request ID")
    status: str = Field(..., description="Request status")
    total_predictions: int = Field(..., description="Total number of predictions")
    successful_predictions: int = Field(..., description="Number of successful predictions")
    failed_predictions: int = Field(..., description="Number of failed predictions")
    
    # Results
    predictions: List[PredictionResult] = Field(..., description="Prediction results")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Errors encountered")
    
    # Processing information
    processing_time_seconds: float = Field(..., description="Processing time in seconds")
    model_version: str = Field(..., description="Model version used")
    
    # Pagination
    has_more: bool = Field(False, description="Whether there are more results")
    next_page_token: Optional[str] = Field(None, description="Token for next page")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
