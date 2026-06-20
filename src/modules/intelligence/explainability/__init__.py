"""Explainability module for KASH career intelligence."""

from .models import *
from .services import *

__version__ = "1.0.0"
__description__ = "KASH Explainability Module"

__all__ = [
    # Enums
    "ExplanationType",
    "ExplanationScope", 
    "ContributionDirection",
    "ConfidenceLevel",
    
    # Core models
    "FeatureContribution",
    "ExplanationMetadata",
    "ExplanationSnapshot",
    "StandardizedExplanation",
    "ExplanationComparison",
    
    # Query models
    "QAQuery",
    "QAQueryResult",
    
    # Configuration
    "ExplainabilityConfig",
    
    # Services
    "ExplainabilityService"
]
