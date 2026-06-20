"""Signal input models for compatibility scoring."""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

from .compatibility_score import SignalSourceEnum, SignalQualityEnum


class SignalDataType(str, Enum):
    """Type of signal data."""
    NUMERIC_SCORE = "numeric_score"
    CATEGORICAL = "categorical"
    BOOLEAN = "boolean"
    TEXTUAL = "textual"
    COMPOSITE = "composite"


class SignalStatus(str, Enum):
    """Status of a signal."""
    ACTIVE = "active"
    PENDING = "pending"
    ARCHIVED = "archived"
    ERROR = "error"
    DEPRECATED = "deprecated"


class NormalizationMethod(str, Enum):
    """Methods for normalizing raw signals."""
    MIN_MAX = "min_max"
    Z_SCORE = "z_score"
    ROBUST_SCALING = "robust_scaling"
    QUANTILE = "quantile"
    CUSTOM = "custom"


class SignalInput(BaseModel):
    """Raw signal input before normalization."""
    signal_id: str = Field(..., description="Unique signal identifier")
    domain: str = Field(..., description="KASH domain (knowledge, skills, abilities, habits)")
    source: SignalSourceEnum = Field(..., description="Source of the signal")
    
    # Raw data
    raw_value: Any = Field(..., description="Raw signal value")
    data_type: SignalDataType = Field(..., description="Type of raw data")
    
    # Metadata
    learner_id: str = Field(..., description="Learner identifier")
    assessment_id: Optional[str] = Field(None, description="Assessment identifier")
    timestamp: datetime = Field(..., description="When signal was generated")
    expires_at: Optional[datetime] = Field(None, description="When signal expires")
    
    # Quality indicators
    status: SignalStatus = Field(SignalStatus.ACTIVE, description="Signal status")
    quality: SignalQualityEnum = Field(SignalQualityEnum.UNKNOWN, description="Quality assessment")
    confidence: float = Field(0.5, ge=0, le=1, description="Confidence in this signal")
    
    # Processing info
    normalization_method: Optional[NormalizationMethod] = Field(None, description="Method used for normalization")
    normalized_value: Optional[float] = Field(None, description="Normalized value (0-1)")
    
    # Additional metadata
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @property
    def is_expired(self) -> bool:
        """Check if signal is expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if signal is valid for processing."""
        return (self.status == SignalStatus.ACTIVE and 
                not self.is_expired and 
                self.normalized_value is not None)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "signal_id": "signal_123",
                "domain": "skills",
                "source": "skills_module",
                "raw_value": 85,
                "data_type": "numeric_score",
                "learner_id": "learner_456",
                "timestamp": "2024-01-01T12:00:00Z",
                "quality": "high",
                "confidence": 0.9,
                "normalized_value": 0.85
            }
        }
    }


class SignalBatch(BaseModel):
    """Batch of signals for processing."""
    batch_id: str = Field(..., description="Unique batch identifier")
    learner_id: str = Field(..., description="Learner identifier")
    signals: List[SignalInput] = Field(..., description="Signals in this batch")
    
    # Batch metadata
    batch_type: str = Field(..., description="Type of batch (e.g., 'assessment', 'sync')")
    source_system: str = Field(..., description="System that provided this batch")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When batch was created")
    processed_at: Optional[datetime] = Field(None, description="When batch was processed")
    
    # Processing results
    processing_status: str = Field("pending", description="Processing status")
    signals_processed: int = Field(0, description="Number of signals successfully processed")
    signals_failed: int = Field(0, description="Number of signals that failed processing")
    error_messages: List[str] = Field(default_factory=list, description="Processing errors")
    
    @property
    def total_signals(self) -> int:
        """Total number of signals in batch."""
        return len(self.signals)
    
    @property
    def success_rate(self) -> float:
        """Processing success rate."""
        if self.total_signals == 0:
            return 0.0
        return self.signals_processed / self.total_signals
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "batch_id": "batch_789",
                "learner_id": "learner_456",
                "batch_type": "assessment",
                "source_system": "skills_module",
                "signals": [],
                "processing_status": "completed"
            }
        }
    }


class SignalValidationResult(BaseModel):
    """Result of signal validation."""
    signal_id: str = Field(..., description="Signal identifier")
    is_valid: bool = Field(..., description="Whether signal is valid")
    validation_errors: List[str] = Field(default_factory=list, description="Validation errors")
    validation_warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    
    # Quality assessment
    data_quality_score: float = Field(..., ge=0, le=1, description="Data quality score")
    freshness_score: float = Field(..., ge=0, le=1, description="Freshness score (newer is better)")
    completeness_score: float = Field(..., ge=0, le=1, description="Completeness score")
    
    # Recommendations
    recommended_actions: List[str] = Field(default_factory=list, description="Recommended actions")
    
    validated_at: datetime = Field(default_factory=datetime.utcnow, description="When validation occurred")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "signal_id": "signal_123",
                "is_valid": True,
                "validation_errors": [],
                "validation_warnings": ["Signal is approaching expiration"],
                "data_quality_score": 0.85,
                "freshness_score": 0.9,
                "completeness_score": 0.95
            }
        }
    }


class SignalTransformation(BaseModel):
    """Transformation applied to a signal."""
    transformation_id: str = Field(..., description="Unique transformation identifier")
    signal_id: str = Field(..., description="Signal identifier")
    
    # Transformation details
    transformation_type: str = Field(..., description="Type of transformation")
    input_value: Any = Field(..., description="Value before transformation")
    output_value: Any = Field(..., description="Value after transformation")
    
    # Configuration
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Transformation parameters")
    algorithm_version: str = Field(..., description="Algorithm version used")
    
    # Quality impact
    quality_before: SignalQualityEnum = Field(..., description="Quality before transformation")
    quality_after: SignalQualityEnum = Field(..., description="Quality after transformation")
    confidence_before: float = Field(..., ge=0, le=1, description="Confidence before transformation")
    confidence_after: float = Field(..., ge=0, le=1, description="Confidence after transformation")
    
    # Metadata
    applied_at: datetime = Field(default_factory=datetime.utcnow, description="When transformation was applied")
    applied_by: str = Field(..., description="Who/what applied the transformation")
    
    @property
    def improved_quality(self) -> bool:
        """Check if transformation improved quality."""
        quality_hierarchy = {
            SignalQualityEnum.UNKNOWN: 0,
            SignalQualityEnum.LOW: 1,
            SignalQualityEnum.MEDIUM: 2,
            SignalQualityEnum.HIGH: 3
        }
        
        before_level = quality_hierarchy.get(self.quality_before, 0)
        after_level = quality_hierarchy.get(self.quality_after, 0)
        
        return after_level > before_level
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "transformation_id": "transform_456",
                "signal_id": "signal_123",
                "transformation_type": "normalization",
                "input_value": 85,
                "output_value": 0.85,
                "parameters": {"method": "min_max", "range": [0, 100]},
                "quality_before": "medium",
                "quality_after": "high"
            }
        }
    }


class SignalAggregationRule(BaseModel):
    """Rule for aggregating multiple signals in a domain."""
    rule_id: str = Field(..., description="Unique rule identifier")
    domain: str = Field(..., description="KASH domain this rule applies to")
    rule_name: str = Field(..., description="Human-readable rule name")
    
    # Aggregation method
    aggregation_method: str = Field(..., description="Method for aggregation (weighted_average, median, max, custom)")
    weight_distribution: Dict[str, float] = Field(default_factory=dict, description="Weight distribution for signals")
    
    # Quality requirements
    min_signal_quality: SignalQualityEnum = Field(SignalQualityEnum.LOW, description="Minimum signal quality")
    min_signal_count: int = Field(1, description="Minimum number of signals required")
    max_age_days: int = Field(365, description="Maximum age of signals to consider")
    
    # Outlier handling
    outlier_detection: bool = Field(False, description="Whether to detect and handle outliers")
    outlier_method: str = Field("iqr", description="Method for outlier detection")
    outlier_threshold: float = Field(1.5, description="Threshold for outlier detection")
    
    # Fallback behavior
    fallback_method: str = Field("zero", description="Method to use when requirements aren't met")
    fallback_value: Optional[float] = Field(None, description="Fallback value if applicable")
    
    # Metadata
    created_by: str = Field(..., description="Who created this rule")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When rule was created")
    is_active: bool = Field(True, description="Whether this rule is active")
    version: str = Field(default="1.0", description="Rule version")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "rule_id": "rule_skills_001",
                "domain": "skills",
                "rule_name": "Weighted average for technical skills",
                "aggregation_method": "weighted_average",
                "weight_distribution": {
                    "programming": 0.4,
                    "databases": 0.3,
                    "frameworks": 0.3
                },
                "min_signal_quality": "medium",
                "min_signal_count": 2,
                "outlier_detection": True
            }
        }
    }


class SignalFilter(BaseModel):
    """Filter for selecting signals."""
    filter_id: str = Field(..., description="Unique filter identifier")
    filter_name: str = Field(..., description="Human-readable filter name")
    
    # Filter criteria
    domains: List[str] = Field(default_factory=list, description="Domains to include (empty = all)")
    sources: List[SignalSourceEnum] = Field(default_factory=list, description="Sources to include (empty = all)")
    min_quality: SignalQualityEnum = Field(SignalQualityEnum.LOW, description="Minimum quality level")
    min_confidence: float = Field(0.0, ge=0, le=1, description="Minimum confidence level")
    
    # Time filters
    min_timestamp: Optional[datetime] = Field(None, description="Earliest timestamp to include")
    max_timestamp: Optional[datetime] = Field(None, description="Latest timestamp to include")
    max_age_days: Optional[int] = Field(None, description="Maximum age of signals in days")
    
    # Value filters
    min_normalized_value: Optional[float] = Field(None, ge=0, le=1, description="Minimum normalized value")
    max_normalized_value: Optional[float] = Field(None, ge=0, le=1, description="Maximum normalized value")
    
    # Tag filters
    required_tags: List[str] = Field(default_factory=list, description="Tags that must be present")
    excluded_tags: List[str] = Field(default_factory=list, description="Tags that must not be present")
    
    # Metadata
    created_by: str = Field(..., description="Who created this filter")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When filter was created")
    
    def matches_signal(self, signal: 'SignalInput') -> bool:
        """Check if a signal matches this filter."""
        # Domain filter
        if self.domains and signal.domain not in self.domains:
            return False
        
        # Source filter
        if self.sources and signal.source not in self.sources:
            return False
        
        # Quality filter
        quality_hierarchy = {
            SignalQualityEnum.UNKNOWN: 0,
            SignalQualityEnum.LOW: 1,
            SignalQualityEnum.MEDIUM: 2,
            SignalQualityEnum.HIGH: 3
        }
        
        if quality_hierarchy.get(signal.quality, 0) < quality_hierarchy.get(self.min_quality, 0):
            return False
        
        # Confidence filter
        if signal.confidence < self.min_confidence:
            return False
        
        # Time filters
        if self.min_timestamp and signal.timestamp < self.min_timestamp:
            return False
        
        if self.max_timestamp and signal.timestamp > self.max_timestamp:
            return False
        
        if self.max_age_days:
            age_days = (datetime.utcnow() - signal.timestamp).days
            if age_days > self.max_age_days:
                return False
        
        # Value filters
        if signal.normalized_value is not None:
            if self.min_normalized_value is not None and signal.normalized_value < self.min_normalized_value:
                return False
            
            if self.max_normalized_value is not None and signal.normalized_value > self.max_normalized_value:
                return False
        
        # Tag filters
        if self.required_tags:
            if not all(tag in signal.tags for tag in self.required_tags):
                return False
        
        if self.excluded_tags:
            if any(tag in signal.tags for tag in self.excluded_tags):
                return False
        
        return True
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "filter_id": "filter_high_quality",
                "filter_name": "High quality recent signals",
                "min_quality": "high",
                "min_confidence": 0.8,
                "max_age_days": 90,
                "required_tags": ["verified"]
            }
        }
    }
