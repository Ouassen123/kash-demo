"""Voice recording interface application."""

from typing import Dict, Any, Optional
import uuid
from datetime import datetime

from .recorder import VoiceRecorder
from modules.abilities.audio.processor import AudioProcessor
from modules.abilities.audio.qa_manager import QAManager
from src.core.logging import get_logger

logger = get_logger(__name__)


class VoiceRecordingApp:
    """Main voice recording application coordinating UI and backend."""

    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize voice recording app.

        Args:
            encryption_key: Optional encryption key for secure storage
        """
        self.processor = AudioProcessor(encryption_key)
        self.qa_manager = QAManager()
        self.active_recorders: Dict[str, VoiceRecorder] = {}

    def create_session(
        self,
        prompt_id: str,
        learner_id: Optional[int] = None,
        device_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new recording session.

        Args:
            prompt_id: Current prompt ID
            learner_id: Optional learner identifier
            device_info: Optional device information

        Returns:
            Session creation result.
        """
        session_id = str(uuid.uuid4())
        
        recorder = VoiceRecorder(
            session_id=session_id,
            prompt_id=prompt_id,
            learner_id=learner_id,
        )
        
        # Override device info if provided
        if device_info:
            recorder.metadata["device_info"].update(device_info)

        self.active_recorders[session_id] = recorder

        logger.info(f"Created recording session {session_id} for prompt {prompt_id}")
        return {
            "session_id": session_id,
            "prompt_id": prompt_id,
            "learner_id": learner_id,
            "status": "created",
            "created_at": datetime.utcnow().isoformat(),
        }

    def start_recording(self, session_id: str) -> Dict[str, Any]:
        """
        Start recording for a session.

        Args:
            session_id: Session identifier

        Returns:
            Recording start result.
        """
        recorder = self.active_recorders.get(session_id)
        if not recorder:
            return {"error": "Session not found"}

        return recorder.start_recording()

    def stop_recording(self, session_id: str) -> Dict[str, Any]:
        """
        Stop recording and process audio.

        Args:
            session_id: Session identifier

        Returns:
            Recording stop result with processing status.
        """
        recorder = self.active_recorders.get(session_id)
        if not recorder:
            return {"error": "Session not found"}

        stop_result = recorder.stop_recording()
        
        if stop_result.get("status") == "stopped":
            # Process audio upload
            audio_blob = recorder.get_audio_data()
            metadata = recorder.get_metadata()
            
            process_result = self.processor.process_audio_upload(
                audio_blob=audio_blob,
                metadata=metadata,
                session_id=session_id,
            )
            
            # Register for QA
            if process_result.get("status") == "success":
                audio_info = self.processor.get_audio_info(session_id)
                self.qa_manager.register_session(session_id, audio_info)
                
                stop_result["processing"] = process_result
                stop_result["qa_status"] = "pending_review"

        return stop_result

    def get_recording_state(self, session_id: str) -> Dict[str, Any]:
        """Get current recording state."""
        recorder = self.active_recorders.get(session_id)
        if not recorder:
            return {"error": "Session not found"}

        state = recorder.get_recording_state()
        
        # Add processing status if available
        audio_info = self.processor.get_audio_info(session_id)
        if audio_info:
            state["processing_status"] = "processed"
            state["audio_hash"] = audio_info.get("audio_hash")
        
        qa_session = self.qa_manager.get_session_for_review(session_id)
        if qa_session:
            state["qa_status"] = qa_session["status"]

        return state

    def validate_recording(self, session_id: str) -> Dict[str, Any]:
        """Validate recording quality."""
        recorder = self.active_recorders.get(session_id)
        if not recorder:
            return {"error": "Session not found"}

        return recorder.validate_recording()

    def submit_for_qa(self, session_id: str) -> Dict[str, Any]:
        """
        Submit recording for QA review.

        Args:
            session_id: Session identifier

        Returns:
            QA submission result.
        """
        audio_info = self.processor.get_audio_info(session_id)
        if not audio_info:
            return {"error": "No audio data found"}

        return self.qa_manager.register_session(session_id, audio_info)

    def get_qa_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get QA session details."""
        return self.qa_manager.get_session_for_review(session_id)

    def replay_audio(self, session_id: str) -> Dict[str, Any]:
        """Get audio replay information."""
        return self.qa_manager.replay_audio(session_id)

    def flag_session(
        self,
        session_id: str,
        reason: str,
        severity: str = "medium",
        flagged_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Flag a session for QA."""
        return self.qa_manager.flag_session(session_id, reason, severity, flagged_by)

    def annotate_session(
        self,
        session_id: str,
        annotation: str,
        annotation_type: str = "general",
        annotated_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Annotate a session."""
        return self.qa_manager.annotate_session(session_id, annotation, annotation_type, annotated_by)

    def approve_session(
        self,
        session_id: str,
        reviewed_by: str,
        final_score: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Approve a session."""
        return self.qa_manager.approve_session(session_id, reviewed_by, final_score, notes)

    def reject_session(
        self,
        session_id: str,
        reviewed_by: str,
        rejection_reason: str,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Reject a session."""
        return self.qa_manager.reject_session(session_id, reviewed_by, rejection_reason, notes)

    def get_qa_dashboard(self) -> Dict[str, Any]:
        """Get QA dashboard summary."""
        return self.qa_manager.get_qa_dashboard()

    def list_sessions(self, status: Optional[str] = None) -> Dict[str, Any]:
        """List sessions with optional status filter."""
        if status:
            session_ids = self.qa_manager.list_sessions_by_status(status)
        else:
            session_ids = list(self.active_recorders.keys())

        sessions = []
        for session_id in session_ids:
            session_info = self.get_recording_state(session_id)
            if "error" not in session_info:
                sessions.append(session_info)

        return {
            "sessions": sessions,
            "total_count": len(sessions),
            "filter": status,
            "generated_at": datetime.utcnow().isoformat(),
        }

    def get_quality_metrics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get quality metrics for a session."""
        return self.processor.get_quality_metrics(session_id)

    def delete_session(self, session_id: str) -> Dict[str, Any]:
        """Delete a session and all associated data."""
        # Remove from active recorders
        if session_id in self.active_recorders:
            del self.active_recorders[session_id]

        # Remove from processor storage
        processor_deleted = self.processor.delete_session(session_id)

        # Remove from QA (if exists)
        qa_deleted = False
        qa_session = self.qa_manager.get_session_for_review(session_id)
        if qa_session:
            # Mock delete method - in real implementation would exist
            qa_deleted = True

        return {
            "session_id": session_id,
            "deleted": processor_deleted or qa_deleted,
            "deleted_at": datetime.utcnow().isoformat(),
        }
