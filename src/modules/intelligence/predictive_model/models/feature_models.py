"""Feature engineering and training data models."""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from enum import Enum
import uuid

from .prediction_models import FeatureType, ModelType, PredictionTarget


class FeatureEngineeringStep(BaseModel):
    """Individual feature engineering step."""
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    step_name: str = Field(..., description="Name of the engineering step")
    step_type: str = Field(..., description="Type of step (transformation, aggregation, etc.)")
    input_features: List[str] = Field(..., description="Input features for this step")
    output_features: List[str] = Field(..., description="Output features from this step")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Step parameters")
    is_active: bool = Field(True, description="Whether step is active")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FeatureDefinition(BaseModel):
    """Complete definition of a feature."""
    feature_name: str = Field(..., description="Name of the feature")
    feature_type: FeatureType = Field(..., description="Type of feature")
    data_type: str = Field(..., description="Data type (numeric, categorical, text, etc.)")
    
    # Source information
    source_table: str = Field(..., description="Source table/view")
    source_column: Optional[str] = Field(None, description="Source column name")
    source_calculation: Optional[str] = Field(None, description="Calculation if derived")
    
    # Engineering
    engineering_steps: List[FeatureEngineeringStep] = Field(
        default_factory=list, description="Engineering steps applied"
    )
    
    # Validation
    validation_rules: Dict[str, Any] = Field(default_factory=dict, description="Validation rules")
    allowed_values: Optional[List[Union[str, int, float]]] = Field(None, description="Allowed values")
    
    # Statistics
    min_value: Optional[float] = Field(None, description="Minimum value")
    max_value: Optional[float] = Field(None, description="Maximum value")
    mean_value: Optional[float] = Field(None, description="Mean value")
    std_deviation: Optional[float] = Field(None, description="Standard deviation")
    missing_percentage: Optional[float] = Field(None, description="Percentage of missing values")
    
    # Usage
    is_active: bool = Field(True, description="Whether feature is active")
    is_target: bool = Field(False, description="Whether this is a target variable")
    importance_score: Optional[float] = Field(None, ge=0, le=1, description="Importance score")
    
    # Metadata
    description: str = Field(..., description="Feature description")
    business_meaning: str = Field(..., description="Business meaning of the feature")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CompatibilityFeatures(BaseModel):
    """Features derived from compatibility scores."""
    learner_id: str = Field(..., description="Learner identifier")
    job_family: str = Field(..., description="Job family")
    
    # Overall compatibility
    overall_compatibility_score: float = Field(..., ge=0, le=1, description="Overall compatibility score")
    compatibility_confidence: float = Field(..., ge=0, le=1, description="Confidence in compatibility score")
    
    # Domain breakdowns
    knowledge_score: float = Field(..., ge=0, le=1, description="Knowledge domain score")
    skills_score: float = Field(..., ge=0, le=1, description="Skills domain score")
    abilities_score: float = Field(..., ge=0, le=1, description="Abilities domain score")
    habits_score: float = Field(..., ge=0, le=1, description="Habits domain score")
    
    # Quality metrics
    data_quality_score: float = Field(..., ge=0, le=1, description="Data quality score")
    signal_freshness_score: float = Field(..., ge=0, le=1, description="Signal freshness score")
    completeness_score: float = Field(..., ge=0, le=1, description="Data completeness score")
    
    # Signal counts
    total_signals: int = Field(..., description="Total number of signals")
    knowledge_signals: int = Field(..., description="Number of knowledge signals")
    skills_signals: int = Field(..., description="Number of skills signals")
    abilities_signals: int = Field(..., description="Number of abilities signals")
    habits_signals: int = Field(..., description="Number of habits signals")
    
    # Missing and stale signals
    missing_signals_count: int = Field(..., description="Count of missing signals")
    stale_signals_count: int = Field(..., description="Count of stale signals")
    
    # Temporal information
    last_updated: datetime = Field(..., description="When compatibility was last updated")
    signal_age_days: int = Field(..., description="Age of signals in days")


class HistoricalPerformanceFeatures(BaseModel):
    """Features derived from historical performance."""
    learner_id: str = Field(..., description="Learner identifier")
    
    # Academic performance
    gpa_trend: List[float] = Field(..., description="GPA trend over time")
    course_completion_rate: float = Field(..., ge=0, le=1, description="Course completion rate")
    average_grade: Optional[float] = Field(None, description="Average grade")
    grade_improvement_trend: Optional[float] = Field(None, description="Grade improvement trend")
    
    # Skills assessment performance
    skills_assessment_scores: List[float] = Field(..., description="Skills assessment scores")
    skills_improvement_rate: float = Field(..., description="Skills improvement rate")
    mastery_level_achieved: int = Field(..., description="Number of mastery levels achieved")
    
    # Project performance
    project_success_rate: float = Field(..., ge=0, le=1, description="Project success rate")
    project_complexity_trend: List[float] = Field(..., description="Project complexity trend")
    collaboration_score: Optional[float] = Field(None, ge=0, le=1, description="Collaboration score")
    
    # Engagement metrics
    login_frequency: float = Field(..., description="Login frequency per week")
    time_spent_learning: float = Field(..., description="Hours spent learning per week")
    interaction_level: float = Field(..., ge=0, le=1, description="Interaction level")
    peer_engagement_score: Optional[float] = Field(None, ge=0, le=1, description="Peer engagement score")
    
    # Progress metrics
    skill_acquisition_rate: float = Field(..., description="Skills acquired per month")
    learning_velocity: float = Field(..., description="Learning velocity score")
    milestone_completion_rate: float = Field(..., ge=0, le=1, description="Milestone completion rate")
    
    # Temporal patterns
    learning_consistency: float = Field(..., ge=0, le=1, description="Learning consistency score")
    peak_performance_hours: List[int] = Field(..., description="Peak performance hours")
    seasonal_patterns: Dict[str, float] = Field(default_factory=dict, description="Seasonal patterns")
    
    # Risk indicators
    dropout_risk_score: float = Field(..., ge=0, le=1, description="Dropout risk score")
    disengagement_indicators: List[str] = Field(default_factory=list, description="Disengagement indicators")
    intervention_history: List[str] = Field(default_factory=list, description="Previous interventions")
    
    # Time in program
    days_in_program: int = Field(..., description="Days in the program")
    current_level: str = Field(..., description="Current level in program")
    progress_percentage: float = Field(..., ge=0, le=100, description="Progress percentage")
    
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class DemographicFeatures(BaseModel):
    """Demographic and background features."""
    learner_id: str = Field(..., description="Learner identifier")
    
    # Basic demographics
    age: Optional[int] = Field(None, description="Age")
    education_level: Optional[str] = Field(None, description="Education level")
    field_of_study: Optional[str] = Field(None, description="Field of study")
    
    # Work experience
    years_of_experience: Optional[float] = Field(None, description="Years of experience")
    industry_experience: List[str] = Field(default_factory=list, description="Industry experience")
    leadership_experience: bool = Field(False, description="Has leadership experience")
    
    # Geographic
    country: Optional[str] = Field(None, description="Country")
    region: Optional[str] = Field(None, description="Region")
    timezone: Optional[str] = Field(None, description="Timezone")
    
    # Socioeconomic (optional, with privacy considerations)
    socioeconomic_status: Optional[str] = Field(None, description="Socioeconomic status")
    first_generation: Optional[bool] = Field(None, description="First generation student")
    
    # Language
    native_language: Optional[str] = Field(None, description="Native language")
    languages_spoken: List[str] = Field(default_factory=list, description="Languages spoken")
    
    # Accessibility
    accessibility_needs: List[str] = Field(default_factory=list, description="Accessibility needs")
    learning_preferences: List[str] = Field(default_factory=list, description="Learning preferences")
    
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class BehavioralFeatures(BaseModel):
    """Behavioral and engagement features."""
    learner_id: str = Field(..., description="Learner identifier")
    
    # Learning patterns
    preferred_learning_time: str = Field(..., description="Preferred learning time")
    learning_session_duration: float = Field(..., description="Average session duration")
    break_frequency: float = Field(..., description="Break frequency during learning")
    
    # Content preferences
    preferred_content_types: List[str] = Field(..., description="Preferred content types")
    difficulty_preference: str = Field(..., description="Preferred difficulty level")
    learning_style_indicators: Dict[str, float] = Field(default_factory=dict, description="Learning style indicators")
    
    # Social learning
    forum_participation: float = Field(..., ge=0, le=1, description="Forum participation score")
    peer_interaction_frequency: float = Field(..., description="Peer interaction frequency")
    mentor_engagement: float = Field(..., ge=0, le=1, description="Mentor engagement score")
    
    # Self-regulation
    goal_setting_behavior: float = Field(..., ge=0, le=1, description="Goal setting behavior")
    self_assessment_frequency: float = Field(..., description="Self-assessment frequency")
    help_seeking_behavior: float = Field(..., ge=0, le=1, description="Help seeking behavior")
    
    # Motivation indicators
    intrinsic_motivation_score: float = Field(..., ge=0, le=1, description="Intrinsic motivation score")
    extrinsic_motivation_score: float = Field(..., ge=0, le=1, description="Extrinsic motivation score")
    persistence_score: float = Field(..., ge=0, le=1, description="Persistence score")
    
    # Risk behaviors
    procrastination_indicators: List[str] = Field(default_factory=list, description="Procrastination indicators")
    avoidance_patterns: List[str] = Field(default_factory=list, description="Avoidance patterns")
    burnout_risk_score: float = Field(..., ge=0, le=1, description="Burnout risk score")
    
    # Technology usage
    platform_usage_patterns: Dict[str, float] = Field(default_factory=dict, description="Platform usage patterns")
    device_preferences: List[str] = Field(default_factory=list, description="Device preferences")
    technical_proficiency: float = Field(..., ge=0, le=1, description="Technical proficiency")
    
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class TargetVariable(BaseModel):
    """Target variable for training."""
    learner_id: str = Field(..., description="Learner identifier")
    target_type: PredictionTarget = Field(..., description="Type of target")
    target_value: float = Field(..., description="Target value")
    
    # Context
    target_role: Optional[str] = Field(None, description="Target role if applicable")
    time_horizon_days: Optional[int] = Field(None, description="Time horizon for prediction")
    
    # Metadata
    observation_date: datetime = Field(..., description="Date of observation")
    outcome_date: Optional[datetime] = Field(None, description="Date when outcome was observed")
    
    # Quality indicators
    confidence_in_label: float = Field(..., ge=0, le=1, description="Confidence in target label")
    label_source: str = Field(..., description="Source of target label")
    verification_method: Optional[str] = Field(None, description="Method used to verify outcome")
    
    # Additional context
    contributing_factors: List[str] = Field(default_factory=list, description="Factors contributing to outcome")
    external_factors: List[str] = Field(default_factory=list, description="External factors affecting outcome")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TrainingExample(BaseModel):
    """Complete training example with all features and target."""
    example_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    learner_id: str = Field(..., description="Learner identifier")
    
    # Features
    compatibility_features: CompatibilityFeatures = Field(..., description="Compatibility features")
    historical_features: HistoricalPerformanceFeatures = Field(..., description="Historical performance features")
    demographic_features: Optional[DemographicFeatures] = Field(None, description="Demographic features")
    behavioral_features: Optional[BehavioralFeatures] = Field(None, description="Behavioral features")
    
    # Target
    target: TargetVariable = Field(..., description="Target variable")
    
    # Metadata
    feature_vector: List[float] = Field(..., description="Flattened feature vector")
    feature_names: List[str] = Field(..., description="Names of features in vector")
    
    # Quality indicators
    data_quality_score: float = Field(..., ge=0, le=1, description="Overall data quality score")
    missing_features: List[str] = Field(default_factory=list, description="List of missing features")
    outlier_indicators: List[str] = Field(default_factory=list, description="Outlier indicators")
    
    # Temporal information
    snapshot_date: datetime = Field(..., description="Date of snapshot")
    feature_freshness_days: Dict[str, int] = Field(default_factory=dict, description="Freshness of features")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FeatureStore(BaseModel):
    """Feature store metadata and configuration."""
    store_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    store_name: str = Field(..., description="Name of the feature store")
    version: str = Field(..., description="Version of the feature store")
    
    # Feature definitions
    feature_definitions: List[FeatureDefinition] = Field(..., description="All feature definitions")
    active_features: List[str] = Field(..., description="List of active feature names")
    
    # Data sources
    data_sources: Dict[str, str] = Field(..., description="Data sources and their descriptions")
    refresh_schedule: str = Field(..., description="Refresh schedule for features")
    
    # Quality monitoring
    quality_thresholds: Dict[str, Dict[str, float]] = Field(
        default_factory=dict, description="Quality thresholds by feature"
    )
    monitoring_enabled: bool = Field(True, description="Whether monitoring is enabled")
    
    # Access control
    access_permissions: Dict[str, List[str]] = Field(
        default_factory=dict, description="Access permissions"
    )
    
    # Metadata
    description: str = Field(..., description="Description of the feature store")
    created_by: str = Field(..., description="Who created the feature store")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TrainingPipeline(BaseModel):
    """Training pipeline configuration and execution."""
    pipeline_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pipeline_name: str = Field(..., description="Name of the training pipeline")
    model_type: ModelType = Field(..., description="Type of model being trained")
    prediction_target: PredictionTarget = Field(..., description="Prediction target")
    
    # Data configuration
    feature_store_id: str = Field(..., description="Feature store to use")
    training_data_query: str = Field(..., description="Query to get training data")
    validation_split: float = Field(..., ge=0, le=1, description="Validation split ratio")
    test_split: float = Field(..., ge=0, le=1, description="Test split ratio")
    
    # Feature selection
    feature_selection_method: str = Field(..., description="Feature selection method")
    max_features: Optional[int] = Field(None, description="Maximum number of features")
    feature_importance_threshold: Optional[float] = Field(None, description="Feature importance threshold")
    
    # Model configuration
    algorithm: str = Field(..., description="Algorithm to use")
    hyperparameters: Dict[str, Any] = Field(default_factory=dict, description="Hyperparameters")
    cross_validation_folds: int = Field(..., description="Number of CV folds")
    
    # Training configuration
    random_seed: int = Field(42, description="Random seed")
    parallel_jobs: int = Field(1, description="Number of parallel jobs")
    memory_limit_gb: Optional[float] = Field(None, description="Memory limit in GB")
    
    # Preprocessing
    preprocessing_steps: List[str] = Field(default_factory=list, description="Preprocessing steps")
    scaling_method: Optional[str] = Field(None, description="Scaling method")
    encoding_method: Optional[str] = Field(None, description="Encoding method")
    
    # Quality controls
    quality_checks: List[str] = Field(default_factory=list, description="Quality checks to perform")
    outlier_detection: bool = Field(True, description="Whether to detect outliers")
    missing_value_threshold: float = Field(0.5, description="Threshold for missing values")
    
    # Execution
    status: str = Field("pending", description="Pipeline status")
    start_time: Optional[datetime] = Field(None, description="Pipeline start time")
    end_time: Optional[datetime] = Field(None, description="Pipeline end time")
    duration_minutes: Optional[float] = Field(None, description="Duration in minutes")
    
    # Results
    model_id: Optional[str] = Field(None, description="ID of trained model")
    training_metrics: Dict[str, float] = Field(default_factory=dict, description="Training metrics")
    validation_metrics: Dict[str, float] = Field(default_factory=dict, description="Validation metrics")
    
    # Artifacts
    model_artifact_path: Optional[str] = Field(None, description="Path to model artifact")
    feature_importance_path: Optional[str] = Field(None, description="Path to feature importance")
    training_logs_path: Optional[str] = Field(None, description="Path to training logs")
    
    # Metadata
    created_by: str = Field(..., description="Who created the pipeline")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
