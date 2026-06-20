"""Extended Abilities service with transcription integration."""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import uuid

from src.core.database import get_db
from src.core.logging import get_logger
from .abilities_service import AbilitiesService
from .transcription.integration import TranscriptionIntegration
from .audio.qa_manager import QAManager

logger = get_logger(__name__)


class AbilitiesServiceWithTranscription(AbilitiesService):
    """Extended abilities service with speech-to-text transcription capabilities."""

    def __init__(self, db: Session):
        """Initialize extended abilities service."""
        super().__init__(db)
        
        # Initialize transcription components
        self.qa_manager = QAManager()
        self.transcription_integration = TranscriptionIntegration(
            audio_qa_manager=self.qa_manager,
            storage_path="./transcripts"
        )
        
        # Audio processor with transcription integration
        from .audio.processor import AudioProcessor
        self.audio_processor = AudioProcessor(
            encryption_key="abilities_transcription_key",
            transcription_integration=self.transcription_integration
        )

    async def start_transcription_services(self, num_workers: int = 3) -> Dict[str, Any]:
        """
        Start transcription services.

        Args:
            num_workers: Number of transcription workers

        Returns:
            Service startup status
        """
        try:
            await self.transcription_integration.start(num_workers)
            
            logger.info(f"Transcription services started with {num_workers} workers")
            return {
                "status": "started",
                "workers": num_workers,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to start transcription services: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def stop_transcription_services(self) -> Dict[str, Any]:
        """
        Stop transcription services.

        Returns:
            Service shutdown status
        """
        try:
            await self.transcription_integration.stop()
            
            logger.info("Transcription services stopped")
            return {
                "status": "stopped",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to stop transcription services: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def process_audio_response(
        self,
        user_id: str,
        session_id: str,
        prompt_id: str,
        audio_blob: bytes,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process audio response with transcription.

        Args:
            user_id: User identifier
            session_id: Assessment session ID
            prompt_id: Prompt identifier
            audio_blob: Audio data
            metadata: Additional metadata

        Returns:
            Processing result with transcription status
        """
        try:
            # Prepare metadata
            audio_metadata = metadata or {}
            audio_metadata.update({
                "session_id": session_id,
                "prompt_id": prompt_id,
                "learner_id": user_id,
                "uploaded_at": datetime.utcnow().isoformat(),
            })

            # Process audio through AudioProcessor (triggers transcription)
            audio_result = self.audio_processor.process_audio_upload(
                audio_blob=audio_blob,
                metadata=audio_metadata,
                session_id=session_id,
            )

            # Get transcription status
            transcription_status = await self.transcription_integration.get_transcription_status(session_id)

            return {
                "status": "processed",
                "session_id": session_id,
                "prompt_id": prompt_id,
                "audio_processing": audio_result,
                "transcription": transcription_status,
                "processed_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to process audio response for session {session_id}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "session_id": session_id,
            }

    async def get_session_with_transcripts(
        self,
        user_id: str,
        session_id: str,
    ) -> Dict[str, Any]:
        """
        Get session data including approved transcripts.

        Args:
            user_id: User identifier
            session_id: Session identifier

        Returns:
            Session data with transcripts
        """
        try:
            # Get base session data
            session_status = await self.get_assessment_status(user_id, session_id)
            if not session_status:
                return {"error": "Session not found"}

            # Get approved transcripts for fusion
            transcripts = await self.transcription_integration.get_approved_transcripts_for_fusion(session_id)

            return {
                "session": session_status,
                "transcripts": transcripts,
                "has_transcripts": transcripts["status"] == "success" and transcripts["transcript_count"] > 0,
                "retrieved_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get session with transcripts for {session_id}: {e}")
            return {
                "error": str(e),
                "session_id": session_id,
            }

    async def get_transcription_health(self) -> Dict[str, Any]:
        """
        Get transcription service health status.

        Returns:
            Health status information
        """
        try:
            return await self.transcription_integration.get_integration_health()
        except Exception as e:
            logger.error(f"Failed to get transcription health: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def get_qa_dashboard(self) -> Dict[str, Any]:
        """
        Get QA dashboard for transcripts.

        Returns:
            QA dashboard data
        """
        try:
            return await self.transcription_integration.qa_hooks.get_qa_dashboard()
        except Exception as e:
            logger.error(f"Failed to get QA dashboard: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def cleanup_session_data(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """
        Clean up all data for a session (privacy compliance).

        Args:
            user_id: User identifier
            session_id: Session identifier

        Returns:
            Cleanup result
        """
        try:
            # Purge transcripts
            purge_result = await self.transcription_integration.repository.purge_session(session_id)
            
            # Delete audio data
            audio_deleted = self.audio_processor.delete_session(session_id)
            
            # Delete QA session
            qa_deleted = False
            if session_id in self.qa_manager.sessions:
                del self.qa_manager.sessions[session_id]
                qa_deleted = True

            logger.info(f"Cleaned up session data for {session_id}")
            return {
                "status": "completed",
                "session_id": session_id,
                "transcripts_purged": purge_result.get("deleted_count", 0),
                "audio_deleted": audio_deleted,
                "qa_deleted": qa_deleted,
                "cleaned_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to cleanup session data for {session_id}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "session_id": session_id,
            }
