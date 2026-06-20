"""API layer for multimodal fusion algorithm."""

from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime

from .preprocessor import MultimodalPreprocessor
from .fusion_engine import MultimodalFusionEngine
from .monitoring.diagnostics import FusionDiagnostics
from src.core.logging import get_logger

logger = get_logger(__name__)


class MultimodalFusionAPI:
    """Facade for multimodal fusion preprocessing, fusion, and diagnostics."""

    def __init__(self, modality_weights: Optional[Dict[str, float]] = None):
        """
        Initialize fusion API.

        Args:
            modality_weights: Optional weights for text, audio, behavioral modalities
        """
        self.preprocessor = MultimodalPreprocessor()
        self.fusion_engine = MultimodalFusionEngine(modality_weights)
        self.diagnostics = FusionDiagnostics()
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

    def create_fusion_session(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Create a new fusion session.

        Args:
            user_id: Optional user identifier

        Returns:
            Session creation result.
        """
        session_id = str(uuid.uuid4())
        
        # Register session with preprocessor
        preprocessor_result = self.preprocessor.register_session(session_id)
        
        # Store session metadata
        session_metadata = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "status": "initialized",
            "preprocessor_result": preprocessor_result,
        }
        self.active_sessions[session_id] = session_metadata

        logger.info(f"Created fusion session {session_id}")
        return {
            "session_id": session_id,
            "user_id": user_id,
            "status": "initialized",
            "created_at": session_metadata["created_at"],
        }

    def add_text_data(
        self,
        session_id: str,
        text_responses: List[Dict[str, Any]],
        prompt_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Add text data to fusion session."""
        result = self.preprocessor.add_text_data(session_id, text_responses, prompt_metadata)
        
        if "error" not in result:
            self.active_sessions[session_id]["status"] = result["status"]
            self.active_sessions[session_id]["text_added_at"] = datetime.utcnow().isoformat()
        
        return result

    def add_audio_data(
        self,
        session_id: str,
        audio_segments: List[Dict[str, Any]],
        audio_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Add audio data to fusion session."""
        result = self.preprocessor.add_audio_data(session_id, audio_segments, audio_metadata)
        
        if "error" not in result:
            self.active_sessions[session_id]["status"] = result["status"]
            self.active_sessions[session_id]["audio_added_at"] = datetime.utcnow().isoformat()
        
        return result

    def add_behavioral_tags(
        self,
        session_id: str,
        behavioral_tags: List[Dict[str, Any]],
        tag_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Add behavioral tags to fusion session."""
        result = self.preprocessor.add_behavioral_tags(session_id, behavioral_tags, tag_metadata)
        
        if "error" not in result:
            self.active_sessions[session_id]["status"] = result["status"]
            self.active_sessions[session_id]["tags_added_at"] = datetime.utcnow().isoformat()
        
        return result

    def synchronize_session(self, session_id: str) -> Dict[str, Any]:
        """Synchronize modalities and detect misalignments."""
        sync_result = self.preprocessor.synchronize_modalities(session_id)
        
        if "error" in sync_result:
            return sync_result

        self.active_sessions[session_id]["status"] = sync_result.get("status", "synchronized")
        self.active_sessions[session_id]["synchronized_at"] = datetime.utcnow().isoformat()
        self.active_sessions[session_id]["synchronization"] = sync_result

        response = dict(sync_result)
        response["aligned_pair_details"] = sync_result.get("aligned_pair_details", [])
        response["aligned_pairs"] = sync_result.get("aligned_pairs", 0)
        return response

    def handle_partial_session(self, session_id: str) -> Dict[str, Any]:
        """Handle partial sessions with fallbacks."""
        result = self.preprocessor.handle_partial_session(session_id)
        
        if "error" not in result:
            self.active_sessions[session_id]["status"] = "partial_handled"
            self.active_sessions[session_id]["fallback"] = result
            self.active_sessions[session_id]["handled_at"] = datetime.utcnow().isoformat()
        
        return result

    def fuse_session_features(self, session_id: str) -> Dict[str, Any]:
        """Fuse session features into interpretable vectors."""
        session_metadata = self.active_sessions.get(session_id)
        if not session_metadata:
            return {"error": "Session not found"}

        # Get complete session data
        session_summary = self.preprocessor.get_session_summary(session_id)
        if not session_summary:
            return {"error": "Session data not available"}

        # Get synchronization and fallback data
        synchronization = session_summary.get("synchronization")
        fallback = session_summary.get("fallback")

        # Perform fusion
        fusion_result = self.fusion_engine.fuse_session_features(
            session_summary, synchronization, fallback
        )

        # Record diagnostics
        diagnostics_result = self.diagnostics.record_session_diagnostics(
            session_id, fusion_result, session_summary
        )

        # Update session status
        self.active_sessions[session_id]["status"] = "fused"
        self.active_sessions[session_id]["fused_at"] = datetime.utcnow().isoformat()
        self.active_sessions[session_id]["fusion_result"] = fusion_result
        self.active_sessions[session_id]["diagnostics"] = diagnostics_result

        logger.info(f"Fused features for session {session_id}")
        return {
            "session_id": session_id,
            "status": "fused",
            "feature_vector": fusion_result["feature_vector"],
            "cognitive_features": fusion_result["cognitive_features"],
            "behavioral_indicators": fusion_result["behavioral_indicators"],
            "confidence": fusion_result["confidence_metadata"],
            "fused_at": fusion_result["fused_at"],
        }

    def get_session_result(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get complete fusion result for a session."""
        session_metadata = self.active_sessions.get(session_id)
        if not session_metadata:
            return None

        return {
            "session_id": session_id,
            "session_metadata": session_metadata,
            "session_summary": self.preprocessor.get_session_summary(session_id),
            "fusion_result": session_metadata.get("fusion_result"),
            "diagnostics": session_metadata.get("diagnostics"),
        }

    def get_session_diagnostics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get diagnostic information for a session."""
        return self.diagnostics.get_session_diagnostics(session_id)

    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health metrics."""
        return self.diagnostics.get_system_health()

    def get_alert_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of recent alerts."""
        return self.diagnostics.get_alert_summary(hours)

    def get_modality_drift_report(self, days: int = 7) -> Dict[str, Any]:
        """Get modality availability drift report."""
        return self.diagnostics.get_modality_drift_report(days)

    def export_diagnostics_report(self, format_type: str = "json") -> Dict[str, Any]:
        """Export comprehensive diagnostics report."""
        return self.diagnostics.export_diagnostics_report(format_type)

    def list_sessions(self, status: Optional[str] = None, user_id: Optional[int] = None) -> List[str]:
        """List fusion sessions with optional filters."""
        sessions = []
        
        for session_id, metadata in self.active_sessions.items():
            # Apply status filter
            if status and metadata.get("status") != status:
                continue
            # Apply user filter
            if user_id and metadata.get("user_id") != user_id:
                continue
            sessions.append(session_id)
        
        if user_id and not sessions and not status:
            return list(self.active_sessions.keys())

        return sessions

    def delete_session(self, session_id: str) -> Dict[str, Any]:
        """Delete a fusion session and all associated data."""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            return {
                "session_id": session_id,
                "deleted": True,
                "deleted_at": datetime.utcnow().isoformat(),
            }
        else:
            return {
                "session_id": session_id,
                "deleted": False,
                "error": "Session not found",
            }

    def update_modality_weights(self, new_weights: Dict[str, float]) -> Dict[str, Any]:
        """Update modality weights for fusion engine."""
        # Validate weights
        total_weight = sum(new_weights.values())
        if abs(total_weight - 1.0) > 0.01:
            return {
                "error": "Weights must sum to 1.0",
                "current_sum": total_weight,
                "provided_sum": sum(new_weights.values()),
            }

        # Update fusion engine weights
        previous_weights = self.fusion_engine.modality_weights.copy()
        self.fusion_engine.modality_weights = new_weights
        
        logger.info(f"Updated modality weights: {new_weights}")
        return {
            "updated_weights": new_weights,
            "previous_weights": previous_weights,
            "updated_at": datetime.utcnow().isoformat(),
        }

    def get_modality_weights(self) -> Dict[str, float]:
        """Get current modality weights."""
        return self.fusion_engine.modality_weights.copy()

    def get_feature_version(self) -> str:
        """Get current feature version."""
        return self.fusion_engine.feature_version
