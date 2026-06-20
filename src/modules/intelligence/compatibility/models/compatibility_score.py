"""Compatibility score models for KASH signal aggregation."""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
from decimal import Decimal


class JobFamilyEnum(str, Enum):
    """Job family enumeration for weight configuration."""
    TECHNOLOGY = "technology"
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    EDUCATION = "education"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    GOVERNMENT = "government"
    CONSULTING = "consulting"
    MEDIA = "media"
    NON_PROFIT = "non_profit"
    ENGINEERING = "engineering"
    SALES = "sales"
    MARKETING = "marketing"
    HUMAN_RESOURCES = "human_resources"
    OPERATIONS = "operations"
    LEGAL = "legal"
    OTHER = "other"


class SignalSourceEnum(str, Enum):
    """Source of KASH signals."""
    KNOWLEDGE_MODULE = "knowledge_module"
    SKILLS_MODULE = "skills_module"
    ABILITIES_MODULE = "abilities_module"
    HABITS_MODULE = "habits_module"
    MANUAL_ASSESSMENT = "manual_assessment"
    EXTERNAL_IMPORT = "external_import"
    LEGACY_SYSTEM = "legacy_system"


class SignalQualityEnum(str, Enum):
    """Quality level of input signals."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class KASHSignal(BaseModel):
    """Individual KASH domain signal."""
    domain: str = Field(..., description="KASH domain (knowledge, skills, abilities, habits)")
    source: SignalSourceEnum = Field(..., description="Source of the signal")
    raw_score: float = Field(..., ge=0, le=1, description="Raw signal score (0-1)")
    normalized_score: float = Field(..., ge=0, le=1, description="Normalized signal score")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in this signal")
    quality: SignalQualityEnum = Field(..., description="Quality assessment of the signal")
    
    # Metadata
    signal_id: str = Field(..., description="Unique signal identifier")
    timestamp: datetime = Field(..., description="When signal was generated")
    version: str = Field(default="1.0", description="Signal version")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional signal metadata")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "domain": "skills",
                "source": "skills_module",
                "raw_score": 0.85,
                "normalized_score": 0.82,
                "confidence": 0.9,
                "quality": "high",
                "signal_id": "signal_123",
                "timestamp": "2024-01-01T12:00:00Z",
                "version": "1.0"
            }
        }
    }


class SignalBreakdown(BaseModel):
    """Breakdown of signals by domain and quality."""
    domain: str = Field(..., description="KASH domain")
    signals: List[KASHSignal] = Field(..., description="Individual signals in this domain")
    aggregated_score: float = Field(..., ge=0, le=1, description="Aggregated score for this domain")
    weight: float = Field(..., ge=0, le=1, description="Weight of this domain in overall score")
    weighted_score: float = Field(..., description="Weighted contribution to overall score")
    
    # Quality metrics
    signal_count: int = Field(..., description="Number of signals in this domain")
    average_confidence: float = Field(..., ge=0, le=1, description="Average confidence of signals")
    quality_distribution: Dict[SignalQualityEnum, int] = Field(..., description="Distribution of signal qualities")
    
    # Missing data indicators
    missing_signals: List[str] = Field(default_factory=list, description="Expected but missing signals")
    stale_signals: List[str] = Field(default_factory=list, description="Signals that are too old")
    
    @property
    def data_completeness(self) -> float:
        """Calculate data completeness for this domain."""
        if not self.signals:
            return 0.0
        # High-quality signals count more toward completeness
        quality_weights = {
            SignalQualityEnum.HIGH: 1.0,
            SignalQualityEnum.MEDIUM: 0.7,
            SignalQualityEnum.LOW: 0.4,
            SignalQualityEnum.UNKNOWN: 0.1
        }
        
        total_weight = sum(quality_weights.get(s.quality, 0.1) for s in self.signals)
        max_possible_weight = len(self.signals) * 1.0
        
        return min(1.0, total_weight / max_possible_weight) if max_possible_weight > 0 else 0.0
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "domain": "skills",
                "aggregated_score": 0.78,
                "weight": 0.4,
                "weighted_score": 0.312,
                "signal_count": 5,
                "average_confidence": 0.85,
                "quality_distribution": {"high": 3, "medium": 2, "low": 0, "unknown": 0}
            }
        }
    }


class ConfidenceInterval(BaseModel):
    """Confidence interval for compatibility score."""
    lower_bound: float = Field(..., ge=0, le=1, description="Lower bound of confidence interval")
    upper_bound: float = Field(..., ge=0, le=1, description="Upper bound of confidence interval")
    confidence_level: float = Field(..., ge=0, le=1, description="Confidence level (e.g., 0.95 for 95% confidence)")
    margin_of_error: float = Field(..., ge=0, description="Margin of error")
    
    @property
    def range_width(self) -> float:
        """Calculate the width of the confidence interval."""
        return self.upper_bound - self.lower_bound
    
    @property
    def is_precise(self) -> bool:
        """Check if the interval is precise (narrow range)."""
        return self.range_width <= 0.1  # Consider precise if range ≤ 0.1
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "lower_bound": 0.72,
                "upper_bound": 0.84,
                "confidence_level": 0.95,
                "margin_of_error": 0.06
            }
        }
    }


class CompatibilityScore(BaseModel):
    """Complete compatibility score with all supporting data."""
    score_id: str = Field(..., description="Unique score identifier")
    learner_id: str = Field(..., description="Learner identifier")
    job_family: JobFamilyEnum = Field(..., description="Target job family")
    target_job_id: Optional[str] = Field(None, description="Specific target job ID")
    
    # Core scores
    overall_score: float = Field(..., ge=0, le=1, description="Overall compatibility score (0-1)")
    normalized_score: float = Field(..., ge=0, le=100, description="Normalized score (0-100)")
    
    # Domain breakdowns
    domain_breakdowns: Dict[str, SignalBreakdown] = Field(..., description="Breakdown by KASH domains")
    
    # Confidence and uncertainty
    confidence_interval: ConfidenceInterval = Field(..., description="Confidence interval for the score")
    overall_confidence: float = Field(..., ge=0, le=1, description="Overall confidence in the score")
    
    # Quality indicators
    data_quality_score: float = Field(..., ge=0, le=1, description="Overall data quality score")
    signal_freshness_score: float = Field(..., ge=0, le=1, description="Freshness of input signals")
    completeness_score: float = Field(..., ge=0, le=1, description="Completeness of required signals")
    
    # Classification
    compatibility_level: str = Field(..., description="Compatibility level (excellent, good, moderate, poor)")
    recommendation_strength: str = Field(..., description="Strength of recommendation (strong, moderate, weak)")
    
    # Metadata
    calculated_at: datetime = Field(default_factory=datetime.utcnow, description="When score was calculated")
    calculation_version: str = Field(default="1.0", description="Scoring algorithm version")
    weight_configuration: str = Field(..., description="Weight configuration used")
    
    @property
    def is_high_compatibility(self) -> bool:
        """Check if this is a high compatibility score."""
        return self.overall_score >= 0.8
    
    @property
    def is_moderate_compatibility(self) -> bool:
        """Check if this is a moderate compatibility score."""
        return 0.6 <= self.overall_score < 0.8
    
    @property
    def needs_improvement(self) -> bool:
        """Check if this score needs improvement."""
        return self.overall_score < 0.6
    
    @property
    def is_reliable(self) -> bool:
        """Check if the score is reliable (high confidence and quality)."""
        return (self.overall_confidence >= 0.8 and 
                self.data_quality_score >= 0.7 and 
                self.completeness_score >= 0.7)
    
    def get_domain_score(self, domain: str) -> Optional[float]:
        """Get score for a specific domain."""
        breakdown = self.domain_breakdowns.get(domain)
        return breakdown.aggregated_score if breakdown else None
    
    def get_top_domains(self, limit: int = 3) -> List[Tuple[str, float]]:
        """Get top-performing domains."""
        domain_scores = [
            (domain, breakdown.aggregated_score) 
            for domain, breakdown in self.domain_breakdowns.items()
        ]
        domain_scores.sort(key=lambda x: x[1], reverse=True)
        return domain_scores[:limit]
    
    def get_weakest_domains(self, limit: int = 3) -> List[Tuple[str, float]]:
        """Get weakest domains needing improvement."""
        domain_scores = [
            (domain, breakdown.aggregated_score) 
            for domain, breakdown in self.domain_breakdowns.items()
        ]
        domain_scores.sort(key=lambda x: x[1])
        return domain_scores[:limit]
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "score_id": "score_456",
                "learner_id": "learner_123",
                "job_family": "technology",
                "overall_score": 0.78,
                "normalized_score": 78.0,
                "confidence_interval": {
                    "lower_bound": 0.72,
                    "upper_bound": 0.84,
                    "confidence_level": 0.95,
                    "margin_of_error": 0.06
                },
                "overall_confidence": 0.85,
                "data_quality_score": 0.82,
                "compatibility_level": "good",
                "recommendation_strength": "moderate"
            }
        }
    }


class WeightConfiguration(BaseModel):
    """Weight configuration for job family scoring."""
    config_id: str = Field(..., description="Unique configuration identifier")
    job_family: JobFamilyEnum = Field(..., description="Job family this configuration applies to")
    business_context: str = Field(..., description="Business context for this configuration")
    
    # Domain weights
    domain_weights: Dict[str, float] = Field(..., description="Weights for each KASH domain")
    
    # Quality adjustments
    quality_multipliers: Dict[SignalQualityEnum, float] = Field(..., description="Multipliers based on signal quality")
    
    # Minimum requirements
    minimum_domain_scores: Dict[str, float] = Field(default_factory=dict, description="Minimum scores required per domain")
    
    # Metadata
    created_by: str = Field(..., description="Who created this configuration")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When configuration was created")
    is_active: bool = Field(True, description="Whether this configuration is active")
    version: str = Field(default="1.0", description="Configuration version")
    
    def validate_weights(self) -> bool:
        """Validate that weights sum to 1.0."""
        total_weight = sum(self.domain_weights.values())
        return abs(total_weight - 1.0) < 0.01  # Allow small floating point errors
    
    def get_domain_weight(self, domain: str) -> float:
        """Get weight for a specific domain."""
        return self.domain_weights.get(domain, 0.0)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "config_id": "config_tech_001",
                "job_family": "technology",
                "business_context": "Software development roles requiring strong technical skills",
                "domain_weights": {
                    "knowledge": 0.2,
                    "skills": 0.4,
                    "abilities": 0.3,
                    "habits": 0.1
                },
                "quality_multipliers": {
                    "high": 1.0,
                    "medium": 0.8,
                    "low": 0.6,
                    "unknown": 0.4
                },
                "minimum_domain_scores": {
                    "skills": 0.6,
                    "abilities": 0.5
                }
            }
        }
    }


class CompatibilityScoreRequest(BaseModel):
    """Request for compatibility score calculation."""
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
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "learner_id": "learner_123",
                "job_family": "technology",
                "kash_signals": [
                    {
                        "domain": "skills",
                        "source": "skills_module",
                        "raw_score": 0.85,
                        "normalized_score": 0.82,
                        "confidence": 0.9,
                        "quality": "high"
                    }
                ],
                "include_confidence_interval": True,
                "confidence_level": 0.95
            }
        }
    }


class CompatibilityScoreResponse(BaseModel):
    """Response containing compatibility score and supporting data."""
    request_id: str = Field(..., description="Unique request identifier")
    compatibility_score: CompatibilityScore = Field(..., description="Calculated compatibility score")
    
    # Processing metadata
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    signals_processed: int = Field(..., description="Number of signals processed")
    signals_filtered: int = Field(..., description="Number of signals filtered out")
    
    # Quality metrics
    input_data_quality: Dict[str, Any] = Field(..., description="Quality metrics for input data")
    calculation_diagnostics: List[str] = Field(default_factory=list, description="Diagnostic messages")
    
    # Recommendations
    improvement_suggestions: List[str] = Field(default_factory=list, description="Suggestions for score improvement")
    next_steps: List[str] = Field(default_factory=list, description="Recommended next steps")
    
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="When response was generated")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "request_id": "req_789",
                "processing_time_ms": 45,
                "signals_processed": 12,
                "signals_filtered": 2,
                "improvement_suggestions": [
                    "Improve technical skills through practice projects",
                    "Gain more experience with collaboration tools"
                ]
            }
        }
    }
