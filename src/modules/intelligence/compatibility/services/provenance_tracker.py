"""Provenance tracking service for compatibility scoring."""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..models import (
    ProvenanceEvent,
    SignalProvenance,
    ScoreProvenance,
    ConfigurationProvenance,
    DataLineage,
    ProvenanceQuery,
    ProvenanceEventType,
    DataFreshness,
    SignalSourceEnum,
    SignalQualityEnum
)


class ProvenanceTracker:
    """Tracks provenance for signals, scores, and configurations."""
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path(__file__).parent.parent / "data" / "provenance"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Storage files
        self.events_file = self.storage_path / "provenance_events.json"
        self.signals_file = self.storage_path / "signal_provenance.json"
        self.scores_file = self.storage_path / "score_provenance.json"
        self.configurations_file = self.storage_path / "configuration_provenance.json"
        self.lineage_file = self.storage_path / "data_lineage.json"
        
        # Load existing data
        self.events = self._load_events()
        self.signal_provenance = self._load_signal_provenance()
        self.score_provenance = self._load_score_provenance()
        self.configuration_provenance = self._load_configuration_provenance()
        self.lineage = self._load_lineage()
    
    def _load_events(self) -> Dict[str, ProvenanceEvent]:
        """Load provenance events from storage."""
        if not self.events_file.exists():
            return {}
        
        try:
            with open(self.events_file, 'r') as f:
                data = json.load(f)
            
            events = {}
            for event_id, event_data in data.items():
                # Convert datetime strings back to datetime objects
                if event_data.get("timestamp"):
                    event_data["timestamp"] = datetime.fromisoformat(event_data["timestamp"])
                
                events[event_id] = ProvenanceEvent(**event_data)
            
            return events
        except Exception as e:
            print(f"Error loading events: {e}")
            return {}
    
    def _load_signal_provenance(self) -> Dict[str, SignalProvenance]:
        """Load signal provenance from storage."""
        if not self.signals_file.exists():
            return {}
        
        try:
            with open(self.signals_file, 'r') as f:
                data = json.load(f)
            
            provenance = {}
            for signal_id, prov_data in data.items():
                # Convert datetime strings
                for field in ["created_at", "last_modified", "freshness_calculated_at"]:
                    if prov_data.get(field):
                        prov_data[field] = datetime.fromisoformat(prov_data[field])
                
                # Convert quality enums
                for item in prov_data.get("quality_history", []):
                    if item.get("quality"):
                        item["quality"] = SignalQualityEnum(item["quality"])
                
                provenance[signal_id] = SignalProvenance(**prov_data)
            
            return provenance
        except Exception as e:
            print(f"Error loading signal provenance: {e}")
            return {}
    
    def _load_score_provenance(self) -> Dict[str, ScoreProvenance]:
        """Load score provenance from storage."""
        if not self.scores_file.exists():
            return {}
        
        try:
            with open(self.scores_file, 'r') as f:
                data = json.load(f)
            
            provenance = {}
            for score_id, prov_data in data.items():
                # Convert datetime strings
                for field in ["calculated_at", "cache_expires_at"]:
                    if prov_data.get(field):
                        prov_data[field] = datetime.fromisoformat(prov_data[field])
                
                provenance[score_id] = ScoreProvenance(**prov_data)
            
            return provenance
        except Exception as e:
            print(f"Error loading score provenance: {e}")
            return {}
    
    def _load_configuration_provenance(self) -> Dict[str, ConfigurationProvenance]:
        """Load configuration provenance from storage."""
        if not self.configurations_file.exists():
            return {}
        
        try:
            with open(self.configurations_file, 'r') as f:
                data = json.load(f)
            
            provenance = {}
            for config_id, prov_data in data.items():
                # Convert datetime strings
                for field in ["changed_at", "approved_at", "rollback_deadline"]:
                    if prov_data.get(field):
                        prov_data[field] = datetime.fromisoformat(prov_data[field])
                
                provenance[config_id] = ConfigurationProvenance(**prov_data)
            
            return provenance
        except Exception as e:
            print(f"Error loading configuration provenance: {e}")
            return {}
    
    def _load_lineage(self) -> Dict[str, DataLineage]:
        """Load data lineage from storage."""
        if not self.lineage_file.exists():
            return {}
        
        try:
            with open(self.lineage_file, 'r') as f:
                data = json.load(f)
            
            lineage = {}
            for lineage_id, lineage_data in data.items():
                # Convert datetime strings
                for field in ["created_at", "last_updated"]:
                    if lineage_data.get(field):
                        lineage_data[field] = datetime.fromisoformat(lineage_data[field])
                
                lineage[lineage_id] = DataLineage(**lineage_data)
            
            return lineage
        except Exception as e:
            print(f"Error loading lineage: {e}")
            return {}
    
    def _save_events(self):
        """Save events to storage."""
        data = {}
        for event_id, event in self.events.items():
            data[event_id] = event.model_dump()
        
        with open(self.events_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _save_signal_provenance(self):
        """Save signal provenance to storage."""
        data = {}
        for signal_id, provenance in self.signal_provenance.items():
            data[signal_id] = provenance.model_dump()
        
        with open(self.signals_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _save_score_provenance(self):
        """Save score provenance to storage."""
        data = {}
        for score_id, provenance in self.score_provenance.items():
            data[score_id] = provenance.model_dump()
        
        with open(self.scores_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _save_configuration_provenance(self):
        """Save configuration provenance to storage."""
        data = {}
        for config_id, provenance in self.configuration_provenance.items():
            data[config_id] = provenance.model_dump()
        
        with open(self.configurations_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _save_lineage(self):
        """Save lineage to storage."""
        data = {}
        for lineage_id, lineage in self.lineage.items():
            data[lineage_id] = lineage.model_dump()
        
        with open(self.lineage_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def record_event(self, event_type: str, description: str = "", **kwargs):
        """Record a provenance event."""
        
        event = ProvenanceEvent(
            event_id=str(uuid.uuid4()),
            event_type=ProvenanceEventType(event_type),
            timestamp=datetime.utcnow(),
            description=description,
            source_system="compatibility_service",
            **kwargs
        )
        
        self.events[event.event_id] = event
        self._save_events()
        
        return event.event_id
    
    def create_signal_provenance(self, signal_id: str, original_source: SignalSourceEnum,
                                source_system: str, created_at: datetime,
                                **kwargs) -> SignalProvenance:
        """Create provenance for a new signal."""
        
        provenance = SignalProvenance(
            signal_id=signal_id,
            original_source=original_source,
            source_system=source_system,
            created_at=created_at,
            last_modified=created_at,
            **kwargs
        )
        
        self.signal_provenance[signal_id] = provenance
        self._save_signal_provenance()
        
        # Record creation event
        self.record_event(
            event_type="signal_created",
            signal_id=signal_id,
            description=f"Signal {signal_id} created from {original_source.value}"
        )
        
        return provenance
    
    def update_signal_provenance(self, signal_id: str, **updates):
        """Update signal provenance."""
        
        provenance = self.signal_provenance.get(signal_id)
        if not provenance:
            return
        
        # Update fields
        for field, value in updates.items():
            if hasattr(provenance, field):
                setattr(provenance, field, value)
        
        provenance.last_modified = datetime.utcnow()
        
        self._save_signal_provenance()
        
        # Record update event
        self.record_event(
            event_type="signal_updated",
            signal_id=signal_id,
            description=f"Signal {signal_id} updated"
        )
    
    def create_score_provenance(self, score_id: str, learner_id: str,
                              input_signals: List[str], weight_configuration_id: str,
                              calculation_duration_ms: int, **kwargs) -> ScoreProvenance:
        """Create provenance for a calculated score."""
        
        provenance = ScoreProvenance(
            score_id=score_id,
            calculated_at=datetime.utcnow(),
            calculation_version="1.0",
            calculation_duration_ms=calculation_duration_ms,
            input_signals=input_signals,
            weight_configuration_id=weight_configuration_id,
            learner_id=learner_id,
            environment="production",
            **kwargs
        )
        
        self.score_provenance[score_id] = provenance
        self._save_score_provenance()
        
        # Record calculation event
        self.record_event(
            event_type="score_calculated",
            score_id=score_id,
            learner_id=learner_id,
            description=f"Score {score_id} calculated for learner {learner_id}"
        )
        
        return provenance
    
    def create_configuration_provenance(self, configuration_id: str, configuration_type: str,
                                       changed_by: str, change_reason: str,
                                       previous_version: str, new_version: str,
                                       changed_fields: List[str], old_values: Dict[str, Any],
                                       new_values: Dict[str, Any], **kwargs) -> ConfigurationProvenance:
        """Create provenance for a configuration change."""
        
        provenance = ConfigurationProvenance(
            configuration_id=configuration_id,
            configuration_type=configuration_type,
            changed_at=datetime.utcnow(),
            changed_by=changed_by,
            change_reason=change_reason,
            previous_version=previous_version,
            new_version=new_version,
            changed_fields=changed_fields,
            old_values=old_values,
            new_values=new_values,
            **kwargs
        )
        
        self.configuration_provenance[configuration_id] = provenance
        self._save_configuration_provenance()
        
        # Record configuration change event
        self.record_event(
            event_type="configuration_changed",
            description=f"Configuration {configuration_id} changed by {changed_by}",
            details={
                "configuration_type": configuration_type,
                "change_reason": change_reason,
                "changed_fields": changed_fields
            }
        )
        
        return provenance
    
    def get_signal_provenance(self, signal_id: str) -> Optional[SignalProvenance]:
        """Get provenance for a specific signal."""
        return self.signal_provenance.get(signal_id)
    
    def get_score_provenance(self, score_id: str) -> Optional[ScoreProvenance]:
        """Get provenance for a specific score."""
        return self.score_provenance.get(score_id)
    
    def get_learner_signals(self, learner_id: str) -> List[SignalProvenance]:
        """Get all signals for a learner."""
        return [prov for prov in self.signal_provenance.values() 
                if hasattr(prov, 'learner_id') and prov.learner_id == learner_id]
    
    def get_learner_scores(self, learner_id: str) -> List[ScoreProvenance]:
        """Get all scores for a learner."""
        return [prov for prov in self.score_provenance.values() 
                if prov.learner_id == learner_id]
    
    def query_events(self, query: ProvenanceQuery) -> List[ProvenanceEvent]:
        """Query provenance events based on criteria."""
        
        filtered_events = []
        
        for event in self.events.values():
            # Apply filters
            if query.learner_id and event.learner_id != query.learner_id:
                continue
            
            if query.score_id and event.score_id != query.score_id:
                continue
            
            if query.signal_id and event.signal_id != query.signal_id:
                continue
            
            if query.event_types and event.event_type not in query.event_types:
                continue
            
            if query.start_time and event.timestamp < query.start_time:
                continue
            
            if query.end_time and event.timestamp > query.end_time:
                continue
            
            if query.source_systems and event.source_system not in query.source_systems:
                continue
            
            if query.users and event.user_id not in query.users:
                continue
            
            filtered_events.append(event)
        
        # Sort results
        if query.sort_by == "timestamp":
            filtered_events.sort(key=lambda x: x.timestamp, 
                               reverse=(query.sort_order == "desc"))
        
        # Apply pagination
        start_idx = query.offset
        end_idx = start_idx + query.max_results
        
        return filtered_events[start_idx:end_idx]
    
    def get_freshness_metrics(self, signal_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get freshness metrics for a list of signals."""
        
        metrics = {}
        
        for signal_id in signal_ids:
            provenance = self.signal_provenance.get(signal_id)
            if not provenance:
                continue
            
            # Calculate freshness
            age_days = (datetime.utcnow() - provenance.created_at).days
            
            if age_days <= 7:
                freshness = DataFreshness.FRESH
                freshness_score = 1.0
            elif age_days <= 30:
                freshness = DataFreshness.RECENT
                freshness_score = 0.8
            elif age_days <= 90:
                freshness = DataFreshness.STALE
                freshness_score = 0.6
            else:
                freshness = DataFreshness.EXPIRED
                freshness_score = 0.4
            
            # Update provenance with calculated freshness
            provenance.freshness = freshness
            provenance.freshness_calculated_at = datetime.utcnow()
            
            metrics[signal_id] = {
                "age_days": age_days,
                "freshness": freshness,
                "freshness_score": freshness_score,
                "is_recent": age_days < 30,
                "is_stale": age_days > 90
            }
        
        # Save updated provenance
        self._save_signal_provenance()
        
        return metrics
    
    def get_data_quality_summary(self, learner_id: str) -> Dict[str, Any]:
        """Get data quality summary for a learner."""
        
        signals = self.get_learner_signals(learner_id)
        
        if not signals:
            return {
                "total_signals": 0,
                "quality_distribution": {},
                "freshness_distribution": {},
                "average_age_days": 0,
                "data_quality_score": 0.0
            }
        
        # Quality distribution
        quality_counts = {}
        for signal in signals:
            quality_counts[signal.quality] = quality_counts.get(signal.quality, 0) + 1
        
        # Freshness distribution
        freshness_counts = {}
        total_age = 0
        
        for signal in signals:
            freshness = signal.freshness
            freshness_counts[freshness] = freshness_counts.get(freshness, 0) + 1
            total_age += signal.age_days
        
        # Calculate data quality score
        quality_weights = {
            SignalQualityEnum.HIGH: 1.0,
            SignalQualityEnum.MEDIUM: 0.8,
            SignalQualityEnum.LOW: 0.6,
            SignalQualityEnum.UNKNOWN: 0.4
        }
        
        quality_score = sum(quality_weights.get(s.quality, 0.4) for s in signals) / len(signals)
        
        return {
            "total_signals": len(signals),
            "quality_distribution": {k.value: v for k, v in quality_counts.items()},
            "freshness_distribution": {k.value: v for k, v in freshness_counts.items()},
            "average_age_days": total_age / len(signals),
            "data_quality_score": quality_score
        }
    
    def cleanup_old_events(self, days_to_keep: int = 90):
        """Clean up old provenance events."""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Remove old events
        old_events = [
            event_id for event_id, event in self.events.items()
            if event.timestamp < cutoff_date
        ]
        
        for event_id in old_events:
            del self.events[event_id]
        
        if old_events:
            self._save_events()
            print(f"Cleaned up {len(old_events)} old provenance events")
    
    def export_provenance_data(self, learner_id: Optional[str] = None,
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Export provenance data for analysis."""
        
        # Filter signals
        signals = []
        for provenance in self.signal_provenance.values():
            if learner_id and hasattr(provenance, 'learner_id') and provenance.learner_id != learner_id:
                continue
            
            if start_date and provenance.created_at < start_date:
                continue
            
            if end_date and provenance.created_at > end_date:
                continue
            
            signals.append(provenance.model_dump())
        
        # Filter scores
        scores = []
        for provenance in self.score_provenance.values():
            if learner_id and provenance.learner_id != learner_id:
                continue
            
            if start_date and provenance.calculated_at < start_date:
                continue
            
            if end_date and provenance.calculated_at > end_date:
                continue
            
            scores.append(provenance.model_dump())
        
        # Filter events
        query = ProvenanceQuery(
            query_id=str(uuid.uuid4()),
            learner_id=learner_id,
            start_time=start_date,
            end_time=end_date,
            max_results=10000
        )
        
        events = [event.model_dump() for event in self.query_events(query)]
        
        return {
            "exported_at": datetime.utcnow().isoformat(),
            "learner_id": learner_id,
            "date_range": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None
            },
            "signals": signals,
            "scores": scores,
            "events": events,
            "summary": {
                "total_signals": len(signals),
                "total_scores": len(scores),
                "total_events": len(events)
            }
        }
