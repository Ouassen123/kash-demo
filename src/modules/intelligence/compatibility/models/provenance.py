"""Provenance and metadata tracking models for compatibility scoring."""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from enum import Enum

from .signal_inputs import SignalSourceEnum, SignalQualityEnum


class ProvenanceEventType(str, Enum):
    """Types of provenance events."""
    SIGNAL_CREATED = "signal_created"
    SIGNAL_UPDATED = "signal_updated"
    SIGNAL_NORMALIZED = "signal_normalized"
    SIGNAL_AGGREGATED = "signal_aggregated"
    SCORE_CALCULATED = "score_calculated"
    CONFIGURATION_CHANGED = "configuration_changed"
    VALIDATION_PERFORMED = "validation_performed"
    CACHE_CLEARED = "cache_cleared"
    ERROR_OCCURRED = "error_occurred"


class DataFreshness(str, Enum):
    """Data freshness levels."""
    FRESH = "fresh"          # Less than 7 days old
    RECENT = "recent"        # 7-30 days old
    STALE = "stale"          # 30-90 days old
    EXPIRED = "expired"      # More than 90 days old
    UNKNOWN = "unknown"      # Age cannot be determined


class ProvenanceEvent(BaseModel):
    """Individual provenance event."""
    event_id: str = Field(..., description="Unique event identifier")
    event_type: ProvenanceEventType = Field(..., description="Type of event")
    timestamp: datetime = Field(..., description="When event occurred")
    
    # Event context
    learner_id: Optional[str] = Field(None, description="Related learner ID")
    score_id: Optional[str] = Field(None, description="Related score ID")
    signal_id: Optional[str] = Field(None, description="Related signal ID")
    batch_id: Optional[str] = Field(None, description="Related batch ID")
    
    # Event details
    description: str = Field(..., description="Event description")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional event details")
    
    # System information
    source_system: str = Field(..., description="System that generated the event")
    user_id: Optional[str] = Field(None, description="User who triggered the event (if applicable)")
    session_id: Optional[str] = Field(None, description="Session identifier")
    
    # Technical details
    algorithm_version: Optional[str] = Field(None, description="Algorithm version used")
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "event_id": "event_123",
                "event_type": "score_calculated",
                "timestamp": "2024-01-01T12:00:00Z",
                "learner_id": "learner_456",
                "score_id": "score_789",
                "description": "Compatibility score calculated for technology job family",
                "source_system": "compatibility_service",
                "algorithm_version": "1.0",
                "processing_time_ms": 45
            }
        }
    }


class SignalProvenance(BaseModel):
    """Provenance information for a signal."""
    signal_id: str = Field(..., description="Signal identifier")
    
    # Origin information
    original_source: SignalSourceEnum = Field(..., description="Original source of the signal")
    source_system: str = Field(..., description="System that provided the signal")
    source_version: str = Field(default="1.0", description="Version of the source system")
    
    # Creation and modification
    created_at: datetime = Field(..., description="When signal was originally created")
    last_modified: datetime = Field(..., description="When signal was last modified")
    modified_by: Optional[str] = Field(None, description="Who last modified the signal")
    
    # Processing history
    processing_steps: List[str] = Field(default_factory=list, description="Processing steps applied")
    transformations_applied: List[str] = Field(default_factory=list, description="Transformations applied")
    
    # Quality evolution
    quality_history: List[Dict[str, Any]] = Field(default_factory=list, description="History of quality assessments")
    confidence_history: List[Dict[str, Any]] = Field(default_factory=list, description="History of confidence scores")
    
    # Validation history
    validation_results: List[Dict[str, Any]] = Field(default_factory=list, description="History of validations")
    
    # Data lineage
    parent_signals: List[str] = Field(default_factory=list, description="Signals this was derived from")
    child_signals: List[str] = Field(default_factory=list, description="Signals derived from this")
    
    # Freshness information
    freshness: DataFreshness = Field(DataFreshness.UNKNOWN, description="Current freshness level")
    freshness_calculated_at: Optional[datetime] = Field(None, description="When freshness was calculated")
    
    @property
    def age_days(self) -> int:
        """Calculate age in days."""
        return (datetime.utcnow() - self.created_at).days
    
    @property
    def is_recent(self) -> bool:
        """Check if signal is recent (less than 30 days)."""
        return self.age_days < 30
    
    @property
    def has_quality_improved(self) -> bool:
        """Check if quality has improved over time."""
        if len(self.quality_history) < 2:
            return False
        
        latest = self.quality_history[-1]
        earliest = self.quality_history[0]
        
        quality_hierarchy = {
            SignalQualityEnum.UNKNOWN: 0,
            SignalQualityEnum.LOW: 1,
            SignalQualityEnum.MEDIUM: 2,
            SignalQualityEnum.HIGH: 3
        }
        
        latest_level = quality_hierarchy.get(latest.get("quality"), 0)
        earliest_level = quality_hierarchy.get(earliest.get("quality"), 0)
        
        return latest_level > earliest_level
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "signal_id": "signal_123",
                "original_source": "skills_module",
                "source_system": "skills_assessment_platform",
                "created_at": "2024-01-01T12:00:00Z",
                "last_modified": "2024-01-02T15:30:00Z",
                "processing_steps": ["validation", "normalization", "quality_assessment"],
                "freshness": "fresh"
            }
        }
    }


class ScoreProvenance(BaseModel):
    """Provenance information for a compatibility score."""
    score_id: str = Field(..., description="Score identifier")
    
    # Calculation information
    calculated_at: datetime = Field(..., description="When score was calculated")
    calculation_version: str = Field(..., description="Algorithm version used")
    calculation_duration_ms: int = Field(..., description="Time taken to calculate score")
    
    # Input signals used
    input_signals: List[str] = Field(..., description="IDs of signals used in calculation")
    excluded_signals: List[str] = Field(default_factory=list, description="Signals that were excluded")
    
    # Configuration used
    weight_configuration_id: str = Field(..., description="Weight configuration used")
    aggregation_rules: List[str] = Field(default_factory=list, description="Aggregation rules applied")
    
    # Processing steps
    processing_steps: List[Dict[str, Any]] = Field(default_factory=list, description="Detailed processing steps")
    intermediate_results: Dict[str, Any] = Field(default_factory=dict, description="Intermediate calculation results")
    
    # Quality metrics
    input_data_quality: Dict[str, float] = Field(default_factory=dict, description="Quality metrics for input data")
    calculation_confidence: float = Field(..., ge=0, le=1, description="Confidence in calculation")
    
    # Environment information
    environment: str = Field(..., description="Environment where calculation occurred (dev, staging, prod)")
    server_instance: Optional[str] = Field(None, description="Server instance that performed calculation")
    
    # User context
    requested_by: Optional[str] = Field(None, description="User who requested the calculation")
    request_context: Dict[str, Any] = Field(default_factory=dict, description="Context of the request")
    
    # Cache information
    cache_hit: bool = Field(False, description="Whether result was retrieved from cache")
    cache_key: Optional[str] = Field(None, description="Cache key used")
    cache_expires_at: Optional[datetime] = Field(None, description="When cache entry expires")
    
    @property
    def signal_count(self) -> int:
        """Number of signals used."""
        return len(self.input_signals)
    
    @property
    def excluded_count(self) -> int:
        """Number of signals excluded."""
        return len(self.excluded_signals)
    
    @property
    def total_signals_considered(self) -> int:
        """Total signals considered (used + excluded)."""
        return self.signal_count + self.excluded_count
    
    @property
    def is_cached_result(self) -> bool:
        """Check if this is a cached result."""
        return self.cache_hit
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "score_id": "score_456",
                "calculated_at": "2024-01-01T12:00:00Z",
                "calculation_version": "1.0",
                "calculation_duration_ms": 45,
                "input_signals": ["signal_123", "signal_124", "signal_125"],
                "weight_configuration_id": "config_tech_001",
                "calculation_confidence": 0.85,
                "environment": "production"
            }
        }
    }


class ConfigurationProvenance(BaseModel):
    """Provenance information for configuration changes."""
    configuration_id: str = Field(..., description="Configuration identifier")
    configuration_type: str = Field(..., description="Type of configuration (weights, rules, filters)")
    
    # Change information
    changed_at: datetime = Field(..., description="When change was made")
    changed_by: str = Field(..., description="Who made the change")
    change_reason: str = Field(..., description="Reason for the change")
    
    # Version information
    previous_version: str = Field(..., description="Previous version")
    new_version: str = Field(..., description="New version")
    
    # Change details
    changed_fields: List[str] = Field(..., description="Fields that were changed")
    old_values: Dict[str, Any] = Field(..., description="Previous values")
    new_values: Dict[str, Any] = Field(..., description="New values")
    
    # Impact assessment
    impact_assessment: str = Field(..., description="Assessment of change impact")
    affected_scores: List[str] = Field(default_factory=list, description="Scores affected by this change")
    
    # Approval information
    approved_by: Optional[str] = Field(None, description="Who approved the change")
    approved_at: Optional[datetime] = Field(None, description="When change was approved")
    
    # Rollback information
    can_rollback: bool = Field(True, description="Whether this change can be rolled back")
    rollback_deadline: Optional[datetime] = Field(None, description="Deadline for rollback")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "configuration_id": "config_tech_001",
                "configuration_type": "weights",
                "changed_at": "2024-01-01T12:00:00Z",
                "changed_by": "admin_user",
                "change_reason": "Updated weights to reflect new industry standards",
                "previous_version": "1.0",
                "new_version": "1.1",
                "changed_fields": ["domain_weights.skills", "domain_weights.knowledge"],
                "impact_assessment": "Medium impact on technology job family scores"
            }
        }
    }


class DataLineage(BaseModel):
    """Complete data lineage for signals and scores."""
    lineage_id: str = Field(..., description="Unique lineage identifier")
    root_signals: List[str] = Field(..., description="Original source signals")
    
    # Lineage graph
    lineage_graph: Dict[str, List[str]] = Field(..., description="Directed graph of data flow")
    transformation_steps: List[Dict[str, Any]] = Field(default_factory=list, description="All transformation steps")
    
    # Quality tracking
    quality_evolution: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict, description="Quality changes over time")
    confidence_evolution: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict, description="Confidence changes over time")
    
    # Dependency analysis
    dependencies: Dict[str, Set[str]] = Field(default_factory=dict, description="Dependencies between data items")
    impact_analysis: Dict[str, List[str]] = Field(default_factory=dict, description="Impact of changes on downstream items")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When lineage was created")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="When lineage was last updated")
    
    def get_upstream_dependencies(self, item_id: str) -> List[str]:
        """Get all upstream dependencies for an item."""
        visited = set()
        queue = [item_id]
        dependencies = []
        
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            
            visited.add(current)
            upstream = self.dependencies.get(current, set())
            
            for dep in upstream:
                if dep not in visited:
                    queue.append(dep)
                    dependencies.append(dep)
        
        return dependencies
    
    def get_downstream_impact(self, item_id: str) -> List[str]:
        """Get all downstream items affected by this item."""
        return self.impact_analysis.get(item_id, [])
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "lineage_id": "lineage_789",
                "root_signals": ["signal_raw_001", "signal_raw_002"],
                "lineage_graph": {
                    "signal_raw_001": ["signal_norm_001"],
                    "signal_norm_001": ["signal_agg_001"],
                    "signal_agg_001": ["score_001"]
                }
            }
        }
    }


class ProvenanceQuery(BaseModel):
    """Query for provenance information."""
    query_id: str = Field(..., description="Unique query identifier")
    
    # Query filters
    learner_id: Optional[str] = Field(None, description="Filter by learner ID")
    score_id: Optional[str] = Field(None, description="Filter by score ID")
    signal_id: Optional[str] = Field(None, description="Filter by signal ID")
    event_types: List[ProvenanceEventType] = Field(default_factory=list, description="Filter by event types")
    
    # Time range
    start_time: Optional[datetime] = Field(None, description="Start of time range")
    end_time: Optional[datetime] = Field(None, description="End of time range")
    
    # Source filters
    source_systems: List[str] = Field(default_factory=list, description="Filter by source systems")
    users: List[str] = Field(default_factory=list, description="Filter by users")
    
    # Query options
    include_details: bool = Field(True, description="Include detailed event information")
    max_results: int = Field(100, ge=1, le=1000, description="Maximum number of results")
    sort_by: str = Field("timestamp", description="Field to sort by")
    sort_order: str = Field("desc", description="Sort order (asc/desc)")
    
    # Pagination
    offset: int = Field(0, ge=0, description="Number of results to skip")
    
    executed_at: Optional[datetime] = Field(None, description="When query was executed")
    result_count: int = Field(0, description="Number of results returned")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "query_id": "query_123",
                "learner_id": "learner_456",
                "event_types": ["score_calculated", "signal_created"],
                "start_time": "2024-01-01T00:00:00Z",
                "end_time": "2024-01-31T23:59:59Z",
                "max_results": 50
            }
        }
    }
