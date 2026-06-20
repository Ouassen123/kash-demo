"""Integration layer for connecting transcription pipeline with existing audio processing."""

from typing import Dict, Any, Optional
import asyncio
from datetime import datetime

from src.core.logging import get_logger
from .pipeline import SpeechToTextPipeline
from .repository import TranscriptRepository
from .qa_hooks import QAReviewHooks
from .fallback_orchestrator import FallbackOrchestrator
from .telemetry_recorder import TelemetryRecorder
from .providers.mock_provider import MockWhisperProvider
from .providers.offline_provider import OfflineRNNProvider

logger = get_logger(__name__)


class TranscriptionIntegration:
    """Integration layer that connects transcription pipeline with AudioProcessor."""

    def __init__(self, audio_qa_manager, storage_path: Optional[str] = None):
        """
        Initialize transcription integration.

        Args:
            audio_qa_manager: Existing QAManager from audio module
            storage_path: Optional custom storage path for transcripts
        """
        self.audio_qa_manager = audio_qa_manager
        
        # Initialize transcription components
        self.repository = TranscriptRepository(storage_path=storage_path)
        self.qa_hooks = QAReviewHooks(audio_qa_manager)
        self.fallback_orchestrator = FallbackOrchestrator()
        self.telemetry_recorder = TelemetryRecorder()
        
        # Initialize providers
        self.primary_providers = [
            MockWhisperProvider(model_size="base", mode="cloud"),
            MockWhisperProvider(model_size="small", mode="cloud"),
        ]
        self.offline_providers = [
            OfflineRNNProvider(model_name="rnn-t-small"),
        ]
        
        # Register provider policies
        self._register_provider_policies()
        
        # Initialize pipeline
        self.pipeline = SpeechToTextPipeline(
            repository=self.repository,
            qa_hooks=self.qa_hooks,
            fallback_orchestrator=self.fallback_orchestrator,
            telemetry_recorder=self.telemetry_recorder,
            primary_providers=self.primary_providers,
            offline_providers=self.offline_providers,
        )
        
        # Pipeline state
        self._workers_started = False

    def _register_provider_policies(self) -> None:
        """Register provider policies with the fallback orchestrator."""
        from .fallback_orchestrator import ProviderPolicy

        # Primary cloud providers
        for i, provider in enumerate(self.primary_providers):
            policy = ProviderPolicy(
                name=provider.name,
                priority=10 - i,  # Higher priority for first provider
                max_latency_ms=5000,
                min_confidence=0.8,
                bandwidth_requirement_kbps=500,
                supports_streaming=True,
                supports_offline=False,
                cost_per_minute=0.01,
                languages=["en-US", "es-ES", "fr-FR"],
            )
            self.fallback_orchestrator.register_provider_policy(provider.name, policy)

        # Offline providers
        for provider in self.offline_providers:
            policy = ProviderPolicy(
                name=provider.name,
                priority=5,  # Lower priority than cloud
                max_latency_ms=2000,
                min_confidence=0.7,
                bandwidth_requirement_kbps=None,  # No bandwidth requirement
                supports_streaming=True,
                supports_offline=True,
                cost_per_minute=0.0,
                languages=["en-US"],  # Limited language support
            )
            self.fallback_orchestrator.register_provider_policy(provider.name, policy)

    async def start(self, num_workers: int = 3) -> None:
        """
        Start the transcription integration.

        Args:
            num_workers: Number of background workers
        """
        if self._workers_started:
            logger.warning("Transcription integration already started")
            return

        # Start pipeline workers
        await self.pipeline.start_workers(num_workers)
        self._workers_started = True

        logger.info(f"Transcription integration started with {num_workers} workers")

    async def stop(self) -> None:
        """Stop the transcription integration."""
        if not self._workers_started:
            return

        await self.pipeline.stop_workers()
        self._workers_started = False

        logger.info("Transcription integration stopped")

    async def handle_audio_pipeline_trigger(
        self,
        session_id: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Handle pipeline trigger from AudioProcessor.

        Args:
            session_id: Session ID from audio processing
            metadata: Audio processing metadata

        Returns:
            Transcription job submission result
        """
        try:
            # Extract required fields from metadata
            prompt_id = metadata.get("prompt_id")
            learner_id = metadata.get("learner_id")
            audio_hash = metadata.get("audio_hash")
            
            if not all([prompt_id, learner_id, audio_hash]):
                return {
                    "status": "error",
                    "error": "Missing required metadata fields",
                    "missing_fields": [
                        field for field in ["prompt_id", "learner_id", "audio_hash"]
                        if not metadata.get(field)
                    ],
                }

            # Create audio pointer (in production, this would be a storage reference)
            audio_pointer = f"audio://{session_id}/{audio_hash}"

            # Prepare transcription metadata
            transcription_metadata = {
                "session_id": session_id,
                "prompt_id": prompt_id,
                "learner_id": learner_id,
                "language": metadata.get("language", "en-US"),
                "duration_seconds": metadata.get("duration_seconds", 0),
                "noise_level": metadata.get("noise_level", 0.0),
                "device_info": metadata.get("device_info", {}),
                "uploaded_at": metadata.get("uploaded_at", datetime.utcnow().isoformat()),
                "audio_quality_score": metadata.get("quality_score", 0.0),
            }

            # Update network status based on metadata
            network_available = metadata.get("network_available", True)
            bandwidth_kbps = metadata.get("bandwidth_kbps")
            self.fallback_orchestrator.update_network_status(network_available, bandwidth_kbps)

            # Enqueue transcription job
            result = await self.pipeline.enqueue_job(
                session_id=session_id,
                prompt_id=prompt_id,
                learner_id=learner_id,
                audio_hash=audio_hash,
                audio_pointer=audio_pointer,
                metadata=transcription_metadata,
                priority=1,  # Normal priority
            )

            logger.info(f"Transcription job enqueued for session {session_id}: {result.get('job_id')}")
            return result

        except Exception as e:
            logger.error(f"Failed to handle audio pipeline trigger for session {session_id}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "session_id": session_id,
            }

    async def get_transcription_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get transcription status for a session.

        Args:
            session_id: Session ID

        Returns:
            Transcription status information
        """
        try:
            # Get transcripts for session
            transcripts = await self.repository.list_transcripts(session_id=session_id)
            
            if not transcripts:
                return {
                    "session_id": session_id,
                    "status": "not_found",
                    "transcripts": [],
                }

            # Get detailed information for each transcript
            transcript_details = []
            for transcript_meta in transcripts:
                transcript_id = transcript_meta["transcript_id"]
                transcript = await self.repository.retrieve_transcript(transcript_id)
                
                if transcript:
                    transcript_details.append({
                        "transcript_id": transcript_id,
                        "prompt_id": transcript.prompt_id,
                        "qa_status": transcript.qa_status,
                        "aggregate_confidence": transcript.aggregate_confidence,
                        "provider": transcript.provider,
                        "segment_count": len(transcript.segments),
                        "created_at": transcript.created_at,
                        "stored_at": transcript_meta.get("stored_at"),
                    })

            return {
                "session_id": session_id,
                "status": "found",
                "transcript_count": len(transcript_details),
                "transcripts": transcript_details,
            }

        except Exception as e:
            logger.error(f"Failed to get transcription status for session {session_id}: {e}")
            return {
                "session_id": session_id,
                "status": "error",
                "error": str(e),
            }

    async def get_approved_transcripts_for_fusion(self, session_id: str) -> Dict[str, Any]:
        """
        Get approved transcripts ready for multimodal fusion.

        Args:
            session_id: Session ID

        Returns:
            Approved transcripts in fusion-ready format
        """
        try:
            # Get approved transcripts for session
            transcripts = await self.repository.list_transcripts(
                session_id=session_id,
                qa_status="approved",
            )

            if not transcripts:
                return {
                    "session_id": session_id,
                    "status": "no_approved_transcripts",
                    "transcripts": [],
                }

            # Convert to fusion format
            fusion_transcripts = []
            for transcript_meta in transcripts:
                transcript = await self.repository.retrieve_transcript(transcript_meta["transcript_id"])
                
                if transcript:
                    fusion_transcripts.append({
                        "modality": "text_from_audio",
                        "session_id": transcript.session_id,
                        "prompt_id": transcript.prompt_id,
                        "timestamp": transcript.created_at,
                        "content": {
                            "text": " ".join(seg.text for seg in transcript.segments),
                            "segments": [
                                {
                                    "segment_id": seg.segment_id,
                                    "speaker": seg.speaker,
                                    "start": seg.start,
                                    "end": seg.end,
                                    "text": seg.text,
                                    "confidence": seg.confidence,
                                    "noise_level": seg.noise_level,
                                }
                                for seg in transcript.segments
                            ],
                            "aggregate_confidence": transcript.aggregate_confidence,
                            "provider": transcript.provider,
                        },
                        "metadata": {
                            "source": "transcription",
                            "qa_approved": True,
                            "qa_approved_at": transcript_meta.get("qa_updated_at"),
                            "audio_hash": transcript_meta.get("audio_hash"),
                        },
                    })

            return {
                "session_id": session_id,
                "status": "success",
                "transcript_count": len(fusion_transcripts),
                "transcripts": fusion_transcripts,
            }

        except Exception as e:
            logger.error(f"Failed to get approved transcripts for fusion for session {session_id}: {e}")
            return {
                "session_id": session_id,
                "status": "error",
                "error": str(e),
            }

    async def get_integration_health(self) -> Dict[str, Any]:
        """
        Get overall integration health status.

        Returns:
            Health status information
        """
        try:
            # Get pipeline status
            pipeline_status = self.pipeline.get_queue_status()
            
            # Get system health from telemetry
            system_health = self.telemetry_recorder.get_system_health(hours_back=1)
            
            # Get provider recommendations
            provider_recommendations = self.fallback_orchestrator.get_provider_recommendations(
                metadata={"language": "en-US"},
                primary_providers=self.primary_providers,
                offline_providers=self.offline_providers,
            )

            # Get QA dashboard
            qa_dashboard = await self.qa_hooks.get_qa_dashboard()

            return {
                "status": "healthy" if system_health.get("status") == "healthy" else "degraded",
                "workers_started": self._workers_started,
                "pipeline": pipeline_status,
                "system_health": system_health,
                "providers": {
                    "primary_count": len(self.primary_providers),
                    "offline_count": len(self.offline_providers),
                    "recommendations": provider_recommendations[:3],  # Top 3
                },
                "qa": qa_dashboard,
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get integration health: {e}")
            return {
                "status": "error",
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat(),
            }
