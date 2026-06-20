"""Audio processing backend with secure transfer and pipeline triggering."""

from typing import Dict, Any, Optional, List
import json
import hashlib
import time
from datetime import datetime

from src.core.logging import get_logger

logger = get_logger(__name__)


class AudioProcessor:
    """Backend audio processing with secure transfer and pipeline triggering."""

    def __init__(self, encryption_key: Optional[str] = None, transcription_integration: Optional[Any] = None):
        """
        Initialize audio processor.

        Args:
            encryption_key: Optional encryption key for secure storage
            transcription_integration: Optional transcription integration instance
        """
        self.encryption_key = encryption_key or "default_key_mock"
        self.transcription_integration = transcription_integration
        self.storage: Dict[str, Dict[str, Any]] = {}
        self.pipeline_triggers: List[Dict[str, Any]] = []

    def process_audio_upload(
        self,
        audio_blob: bytes,
        metadata: Dict[str, Any],
        session_id: str,
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Process uploaded audio with encryption and pipeline triggering.

        Args:
            audio_blob: Raw audio data
            metadata: Recording metadata
            session_id: Session identifier
            retry_count: Current retry attempt

        Returns:
            Processing result with storage info and pipeline status.
        """
        try:
            # Validate inputs
            if not audio_blob:
                return {"error": "No audio data provided"}
            if not metadata or "session_id" not in metadata:
                return {"error": "Invalid metadata"}

            # Encrypt audio data (mock implementation)
            encrypted_audio = self._encrypt_audio(audio_blob)
            audio_hash = hashlib.sha256(audio_blob).hexdigest()

            # Store with metadata
            storage_entry = {
                "session_id": session_id,
                "prompt_id": metadata.get("prompt_id"),
                "learner_id": metadata.get("learner_id"),
                "audio_hash": audio_hash,
                "encrypted_audio": encrypted_audio,
                "metadata": metadata,
                "uploaded_at": datetime.utcnow().isoformat(),
                "retry_count": retry_count,
                "size_bytes": len(audio_blob),
            }
            self.storage[session_id] = storage_entry

            # Trigger downstream pipelines
            pipeline_result = self._trigger_pipelines(session_id, metadata)

            logger.info(f"Audio processed for session {session_id}, pipeline triggered")
            return {
                "status": "success",
                "session_id": session_id,
                "audio_hash": audio_hash,
                "size_bytes": len(audio_blob),
                "pipeline_status": pipeline_result,
                "uploaded_at": storage_entry["uploaded_at"],
            }

        except Exception as e:
            logger.error(f"Audio processing failed for session {session_id}: {e}")
            # Only retry if it's a processing error, not validation error
            if "No audio data provided" in str(e) or "Invalid metadata" in str(e):
                return {"error": str(e)}
            return self._handle_retry(session_id, audio_blob, metadata, retry_count, str(e))

    def _encrypt_audio(self, audio_blob: bytes) -> str:
        """Encrypt audio data (mock implementation)."""
        # Mock encryption - real implementation would use proper encryption
        return f"encrypted_{hashlib.sha256(audio_blob + self.encryption_key.encode()).hexdigest()}"

    def _trigger_pipelines(self, session_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger transcription and scoring pipelines."""
        pipeline_trigger = {
            "session_id": session_id,
            "triggered_at": datetime.utcnow().isoformat(),
            "pipelines": ["transcription", "scoring", "multimodal_fusion"],
            "metadata": metadata,
        }
        self.pipeline_triggers.append(pipeline_trigger)

        # Trigger transcription pipeline if integration is available
        transcription_result = None
        if self.transcription_integration:
            try:
                # Use asyncio to run the async transcription trigger
                import asyncio
                transcription_result = asyncio.run(
                    self.transcription_integration.handle_audio_pipeline_trigger(session_id, metadata)
                )
                logger.info(f"Transcription pipeline triggered for session {session_id}")
            except Exception as e:
                logger.error(f"Failed to trigger transcription pipeline for session {session_id}: {e}")
                transcription_result = {"status": "error", "error": str(e)}

        # Return pipeline responses
        responses = {
            "scoring": {"status": "queued", "estimated_time": 15},
            "multimodal_fusion": {"status": "queued", "estimated_time": 45},
        }

        if transcription_result:
            responses["transcription"] = transcription_result
        else:
            # Fallback mock response
            responses["transcription"] = {"status": "queued", "estimated_time": 30}

        return responses

    def _handle_retry(
        self,
        session_id: str,
        audio_blob: bytes,
        metadata: Dict[str, Any],
        retry_count: int,
        error: str,
    ) -> Dict[str, Any]:
        """Handle retry logic with exponential backoff."""
        max_retries = 3
        if retry_count >= max_retries:
            return {"error": f"Failed after {max_retries} retries: {error}"}

        # Exponential backoff (mock)
        backoff_seconds = 2 ** retry_count
        logger.warning(f"Retry {retry_count + 1} for session {session_id} in {backoff_seconds}s")

        # In real implementation, would schedule retry
        return {
            "status": "retry_scheduled",
            "session_id": session_id,
            "retry_count": retry_count + 1,
            "backoff_seconds": backoff_seconds,
            "error": error,
        }

    def get_audio_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve stored audio information."""
        return self.storage.get(session_id)

    def list_sessions(self, learner_id: Optional[int] = None) -> List[str]:
        """List session IDs, optionally filtered by learner."""
        if learner_id is None:
            return list(self.storage.keys())
        return [
            sid for sid, entry in self.storage.items()
            if entry.get("learner_id") == learner_id
        ]

    def get_pipeline_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get pipeline processing status for a session."""
        triggers = [t for t in self.pipeline_triggers if t["session_id"] == session_id]
        return triggers[-1] if triggers else None

    def delete_session(self, session_id: str) -> bool:
        """Delete audio data and associated records."""
        deleted = False
        if session_id in self.storage:
            del self.storage[session_id]
            deleted = True
        # Remove pipeline triggers
        self.pipeline_triggers = [
            t for t in self.pipeline_triggers if t["session_id"] != session_id
        ]
        return deleted

    def get_quality_metrics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get audio quality metrics for QA."""
        entry = self.storage.get(session_id)
        if not entry:
            return None

        metadata = entry.get("metadata", {})
        return {
            "session_id": session_id,
            "duration_seconds": metadata.get("duration_seconds"),
            "noise_level": metadata.get("noise_level"),
            "device_info": metadata.get("device_info"),
            "audio_size_bytes": entry.get("size_bytes"),
            "upload_timestamp": entry.get("uploaded_at"),
            "retry_count": entry.get("retry_count", 0),
            "quality_score": self._calculate_quality_score(metadata),
        }

    def _calculate_quality_score(self, metadata: Dict[str, Any]) -> float:
        """Calculate overall audio quality score."""
        duration = metadata.get("duration_seconds", 0)
        noise_level = metadata.get("noise_level", 1.0)
        
        # Simple quality calculation
        duration_score = min(duration / 30.0, 1.0)  # Ideal 30s
        noise_score = 1.0 - noise_level  # Lower noise is better
        
        return round((duration_score * 0.6 + noise_score * 0.4) * 100, 1)
