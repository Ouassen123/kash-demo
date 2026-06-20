"""Compatibility scoring module for KASH career intelligence."""

from .models import *
from .services import *
from .api import *

__version__ = "1.0.0"
__description__ = "KASH Compatibility Score Calculation Module"

__all__ = [
    # Models
    "CompatibilityScore",
    "CompatibilityScoreRequest",
    "CompatibilityScoreResponse",
    "KASHSignal",
    "SignalBreakdown",
    "ConfidenceInterval",
    "WeightConfiguration",
    "SignalInput",
    "SignalBatch",
    "SignalValidationResult",
    "SignalTransformation",
    "SignalAggregationRule",
    "SignalFilter",
    "ProvenanceEvent",
    "SignalProvenance",
    "ScoreProvenance",
    "ConfigurationProvenance",
    "DataLineage",
    "ProvenanceQuery",
    
    # Enums
    "JobFamilyEnum",
    "SignalSourceEnum",
    "SignalQualityEnum",
    "SignalDataType",
    "SignalStatus",
    "NormalizationMethod",
    "ProvenanceEventType",
    "DataFreshness",
    
    # Services
    "ScoringPipeline",
    "ScoringContext",
    "WeightManager",
    "ProvenanceTracker",
    "CompatibilityCacheService",
    "CacheEntry",
    "CacheStats",
    "CacheHitStatus",
    "CacheInvalidationRule",
    
    # API
    "app"
]
