"""Models package for compatibility scoring system."""

from .compatibility_score import (
    CompatibilityScore,
    CompatibilityScoreRequest,
    CompatibilityScoreResponse,
    KASHSignal,
    SignalBreakdown,
    ConfidenceInterval,
    WeightConfiguration,
    JobFamilyEnum,
    SignalSourceEnum,
    SignalQualityEnum
)

from .signal_inputs import (
    SignalInput,
    SignalBatch,
    SignalValidationResult,
    SignalTransformation,
    SignalAggregationRule,
    SignalFilter,
    SignalDataType,
    SignalStatus,
    NormalizationMethod
)

from .provenance import (
    ProvenanceEvent,
    SignalProvenance,
    ScoreProvenance,
    ConfigurationProvenance,
    DataLineage,
    ProvenanceQuery,
    ProvenanceEventType,
    DataFreshness
)

__all__ = [
    # Compatibility score models
    "CompatibilityScore",
    "CompatibilityScoreRequest", 
    "CompatibilityScoreResponse",
    "KASHSignal",
    "SignalBreakdown",
    "ConfidenceInterval",
    "WeightConfiguration",
    
    # Enums
    "JobFamilyEnum",
    "SignalSourceEnum", 
    "SignalQualityEnum",
    
    # Signal input models
    "SignalInput",
    "SignalBatch",
    "SignalValidationResult",
    "SignalTransformation",
    "SignalAggregationRule",
    "SignalFilter",
    
    # Signal enums
    "SignalDataType",
    "SignalStatus",
    "NormalizationMethod",
    
    # Provenance models
    "ProvenanceEvent",
    "SignalProvenance",
    "ScoreProvenance", 
    "ConfigurationProvenance",
    "DataLineage",
    "ProvenanceQuery",
    
    # Provenance enums
    "ProvenanceEventType",
    "DataFreshness"
]
