"""Main speech-to-text pipeline orchestrator."""

from typing import Dict, Any, Optional, List, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
import asyncio
import uuid

from src.core.logging import get_logger
from .provider_base import TranscriptionProvider, TranscriptPackage
from .repository import TranscriptRepository
from .qa_hooks import QAReviewHooks
from .fallback_orchestrator import FallbackOrchestrator
from .telemetry_recorder import TelemetryRecorder

logger = get_logger(__name__)


@dataclass
class TranscriptionJob:
    """Job definition for transcription pipeline."""
    job_id: str
    session_id: str
    prompt_id: str
    learner_id: str
    audio_hash: str
    audio_pointer: str  # Reference to encrypted audio storage
    metadata: Dict[str, Any]
    priority: int = 0
    retry_count: int = 0
    created_at: str = ""


class SpeechToTextPipeline:
    """Orchestrates transcription jobs with provider selection and fallbacks."""

    def __init__(
        self,
        repository: TranscriptRepository,
        qa_hooks: QAReviewHooks,
        fallback_orchestrator: FallbackOrchestrator,
        telemetry_recorder: TelemetryRecorder,
        primary_providers: List[TranscriptionProvider],
        offline_providers: List[TranscriptionProvider],
    ):
        """
        Initialize transcription pipeline.

        Args:
            repository: Transcript storage backend
            qa_hooks: QA review integration
            fallback_orchestrator: Provider fallback logic
            telemetry_recorder: Metrics and diagnostics
            primary_providers: List of preferred cloud providers
            offline_providers: List of offline/fallback providers
        """
        self.repository = repository
        self.qa_hooks = qa_hooks
        self.fallback_orchestrator = fallback_orchestrator
        self.telemetry_recorder = telemetry_recorder
        self.primary_providers = primary_providers
        self.offline_providers = offline_providers

        # Job queue and processing state
        self._job_queue: asyncio.Queue = asyncio.Queue()
        self._processing = False
        self._workers: List[asyncio.Task] = []

    async def start_workers(self, num_workers: int = 3) -> None:
        """Start background workers for processing transcription jobs."""
        if self._processing:
            logger.warning("Workers already started")
            return

        self._processing = True
        for i in range(num_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self._workers.append(worker)

        logger.info(f"Started {num_workers} transcription workers")

    async def stop_workers(self) -> None:
        """Stop all background workers."""
        self._processing = False

        # Cancel workers
        for worker in self._workers:
            worker.cancel()

        # Wait for completion
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

        logger.info("Stopped transcription workers")

    async def enqueue_job(
        self,
        session_id: str,
        prompt_id: str,
        learner_id: str,
        audio_hash: str,
        audio_pointer: str,
        metadata: Dict[str, Any],
        priority: int = 0,
    ) -> Dict[str, Any]:
        """
        Enqueue a transcription job.

        Args:
            session_id: Abilities session ID
            prompt_id: Quiz prompt identifier
            learner_id: Learner UUID
            audio_hash: Hash of source audio
            audio_pointer: Storage reference to audio data
            metadata: Additional job metadata
            priority: Job priority (higher = processed first)

        Returns:
            Job submission result
        """
        # Check for existing transcripts (deduplication)
        existing = await self.repository.list_transcripts(
            session_id=session_id,
            prompt_id=prompt_id,
        )
        if existing:
            logger.info(f"Transcript already exists for session {session_id}, prompt {prompt_id}")
            return {
                "status": "exists",
                "transcript_id": existing[0]["transcript_id"],
                "job_id": None,
            }

        # Create job
        job = TranscriptionJob(
            job_id=f"job_{uuid.uuid4().hex[:12]}",
            session_id=session_id,
            prompt_id=prompt_id,
            learner_id=learner_id,
            audio_hash=audio_hash,
            audio_pointer=audio_pointer,
            metadata=metadata,
            priority=priority,
            created_at=datetime.utcnow().isoformat(),
        )

        # Add to queue
        await self._job_queue.put(job)

        logger.info(f"Enqueued transcription job: {job.job_id}")
        return {
            "status": "queued",
            "job_id": job.job_id,
            "queue_size": self._job_queue.qsize(),
        }

    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a transcription job."""
        # This would require job state tracking - simplified for now
        return {
            "job_id": job_id,
            "status": "processing",
            "queue_size": self._job_queue.qsize(),
        }

    async def _worker(self, worker_name: str) -> None:
        """Background worker that processes transcription jobs."""
        logger.info(f"Transcription worker {worker_name} started")

        while self._processing:
            try:
                # Get next job with timeout
                job = await asyncio.wait_for(self._job_queue.get(), timeout=1.0)
                await self._process_job(job, worker_name)

            except asyncio.TimeoutError:
                # No job available, continue
                continue
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}")
                continue

        logger.info(f"Transcription worker {worker_name} stopped")

    async def _process_job(self, job: TranscriptionJob, worker_name: str) -> None:
        """Process a single transcription job."""
        logger.info(f"Processing job {job.job_id} in {worker_name}")

        try:
            # Select provider based on policy and conditions
            provider = await self.fallback_orchestrator.select_provider(
                job.metadata,
                self.primary_providers,
                self.offline_providers,
            )

            if not provider:
                await self._handle_job_failure(job, "No suitable provider available")
                return

            # Load audio data (mock - would retrieve from storage)
            audio_data = await self._load_audio_data(job.audio_pointer)

            # Transcribe
            transcript = await provider.transcribe_batch(audio_data, job.metadata)

            # Store transcript
            storage_result = await self.repository.store_transcript(
                transcript,
                audio_hash=job.audio_hash,
            )

            if storage_result["status"] != "stored":
                await self._handle_job_failure(job, f"Storage failed: {storage_result.get('error')}")
                return

            # Submit to QA hooks
            await self.qa_hooks.register_for_review(
                storage_result["transcript_id"],
                transcript,
                job.metadata,
            )

            # Record telemetry
            await self.telemetry_recorder.record_transcription_success(
                job.job_id,
                transcript,
                provider.name,
            )

            logger.info(f"Job {job.job_id} completed successfully")

        except Exception as e:
            logger.error(f"Job {job.job_id} failed: {e}")
            await self._handle_job_failure(job, str(e))

    async def _load_audio_data(self, audio_pointer: str) -> bytes:
        """Load audio data from storage (mock implementation)."""
        # In production, this would retrieve from encrypted storage
        # For now, return mock audio data
        return b"mock_audio_data_for_transcription"

    async def _handle_job_failure(self, job: TranscriptionJob, error: str) -> None:
        """Handle job failure with retry logic."""
        job.retry_count += 1

        if job.retry_count <= 3:
            # Retry with exponential backoff
            backoff = 2 ** job.retry_count
            logger.warning(f"Retrying job {job.job_id} in {backoff}s (attempt {job.retry_count})")
            await asyncio.sleep(backoff)
            await self._job_queue.put(job)
        else:
            # Max retries exceeded
            logger.error(f"Job {job.job_id} failed permanently: {error}")
            await self.telemetry_recorder.record_transcription_failure(job.job_id, error)

    async def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue and worker status."""
        return {
            "queue_size": self._job_queue.qsize(),
            "workers_active": len(self._workers),
            "processing": self._processing,
        }
