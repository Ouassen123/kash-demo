"""Tests for speech-to-text pipeline."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from src.modules.abilities.transcription.pipeline import (
    SpeechToTextPipeline,
    TranscriptionJob,
)
from src.modules.abilities.transcription.provider_base import TranscriptPackage
from src.modules.abilities.transcription.repository import TranscriptRepository
from src.modules.abilities.transcription.qa_hooks import QAReviewHooks
from src.modules.abilities.transcription.fallback_orchestrator import FallbackOrchestrator
from src.modules.abilities.transcription.telemetry_recorder import TelemetryRecorder


class TestSpeechToTextPipeline:
    """Test speech-to-text pipeline orchestration."""

    @pytest.fixture
    def mock_repository(self):
        """Create mock repository."""
        repo = AsyncMock(spec=TranscriptRepository)
        repo.store_transcript.return_value = {
            "status": "stored",
            "transcript_id": "test_transcript_id",
            "storage_meta": {},
        }
        repo.list_transcripts.return_value = []  # No existing transcripts
        return repo

    @pytest.fixture
    def mock_qa_hooks(self):
        """Create mock QA hooks."""
        qa = AsyncMock(spec=QAReviewHooks)
        qa.register_for_review.return_value = {"status": "registered"}
        return qa

    @pytest.fixture
    def mock_fallback_orchestrator(self):
        """Create mock fallback orchestrator."""
        orchestrator = AsyncMock(spec=FallbackOrchestrator)
        orchestrator.select_provider.return_value = MagicMock()
        return orchestrator

    @pytest.fixture
    def mock_telemetry_recorder(self):
        """Create mock telemetry recorder."""
        telemetry = AsyncMock(spec=TelemetryRecorder)
        telemetry.record_transcription_success.return_value = None
        telemetry.record_transcription_failure.return_value = None
        return telemetry

    @pytest.fixture
    def mock_providers(self):
        """Create mock providers."""
        provider = MagicMock()
        provider.transcribe_batch = AsyncMock(return_value=TranscriptPackage(
            session_id="test_session",
            prompt_id="test_prompt",
            learner_id="test_learner",
            language="en-US",
            segments=[],
            aggregate_confidence=0.9,
            provider={"name": "test_provider", "mode": "cloud"},
            created_at=datetime.utcnow().isoformat(),
        ))
        provider.name = "test_provider"
        provider.mode = "cloud"
        return [provider]

    @pytest.fixture
    def pipeline(
        self,
        mock_repository,
        mock_qa_hooks,
        mock_fallback_orchestrator,
        mock_telemetry_recorder,
        mock_providers,
    ):
        """Create pipeline with mocked dependencies."""
        return SpeechToTextPipeline(
            repository=mock_repository,
            qa_hooks=mock_qa_hooks,
            fallback_orchestrator=mock_fallback_orchestrator,
            telemetry_recorder=mock_telemetry_recorder,
            primary_providers=mock_providers,
            offline_providers=[],
        )

    @pytest.mark.asyncio
    async def test_enqueue_job(self, pipeline, mock_repository):
        """Test enqueuing a transcription job."""
        result = await pipeline.enqueue_job(
            session_id="session_123",
            prompt_id="prompt_456",
            learner_id="learner_789",
            audio_hash="audio_hash_123",
            audio_pointer="audio_pointer_123",
            metadata={"language": "en-US"},
            priority=1,
        )

        assert result["status"] == "queued"
        assert "job_id" in result
        assert result["queue_size"] == 1

        # Verify job was added to queue
        job = await pipeline._job_queue.get()
        assert job.session_id == "session_123"
        assert job.prompt_id == "prompt_456"
        assert job.learner_id == "learner_789"
        assert job.audio_hash == "audio_hash_123"
        assert job.priority == 1

    @pytest.mark.asyncio
    async def test_enqueue_existing_transcript(self, pipeline, mock_repository):
        """Test enqueuing when transcript already exists."""
        # Mock existing transcript
        mock_repository.list_transcripts.return_value = [{"transcript_id": "existing_id"}]

        result = await pipeline.enqueue_job(
            session_id="session_123",
            prompt_id="prompt_456",
            learner_id="learner_789",
            audio_hash="audio_hash_123",
            audio_pointer="audio_pointer_123",
            metadata={},
        )

        assert result["status"] == "exists"
        assert result["transcript_id"] == "existing_id"
        assert result["job_id"] is None

    @pytest.mark.asyncio
    async def test_start_stop_workers(self, pipeline):
        """Test starting and stopping workers."""
        # Start workers
        await pipeline.start_workers(num_workers=2)
        assert pipeline._processing is True
        assert len(pipeline._workers) == 2

        # Stop workers
        await pipeline.stop_workers()
        assert pipeline._processing is False
        assert len(pipeline._workers) == 0

    @pytest.mark.asyncio
    async def test_process_job_success(
        self,
        pipeline,
        mock_fallback_orchestrator,
        mock_providers,
        mock_repository,
        mock_qa_hooks,
        mock_telemetry_recorder,
    ):
        """Test successful job processing."""
        # Setup mocks
        provider = mock_providers[0]
        mock_fallback_orchestrator.select_provider.return_value = provider

        # Create job
        job = TranscriptionJob(
            job_id="test_job",
            session_id="session_123",
            prompt_id="prompt_456",
            learner_id="learner_789",
            audio_hash="audio_hash_123",
            audio_pointer="audio_pointer_123",
            metadata={"language": "en-US"},
        )

        # Process job
        await pipeline._process_job(job, "test_worker")

        # Verify provider was selected
        mock_fallback_orchestrator.select_provider.assert_called_once()

        # Verify transcript was stored
        mock_repository.store_transcript.assert_called_once()

        # Verify QA hooks were called
        mock_qa_hooks.register_for_review.assert_called_once()

        # Verify telemetry was recorded
        mock_telemetry_recorder.record_transcription_success.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_job_no_provider(
        self,
        pipeline,
        mock_fallback_orchestrator,
        mock_telemetry_recorder,
    ):
        """Test job processing when no provider is available."""
        # Setup mock to return None
        mock_fallback_orchestrator.select_provider.return_value = None

        # Create job
        job = TranscriptionJob(
            job_id="test_job",
            session_id="session_123",
            prompt_id="prompt_456",
            learner_id="learner_789",
            audio_hash="audio_hash_123",
            audio_pointer="audio_pointer_123",
            metadata={},
        )

        # Process job
        await pipeline._process_job(job, "test_worker")

        # Verify failure was recorded
        mock_telemetry_recorder.record_transcription_failure.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_job_storage_failure(
        self,
        pipeline,
        mock_fallback_orchestrator,
        mock_providers,
        mock_repository,
        mock_telemetry_recorder,
    ):
        """Test job processing when storage fails."""
        # Setup mocks
        provider = mock_providers[0]
        mock_fallback_orchestrator.select_provider.return_value = provider
        mock_repository.store_transcript.return_value = {
            "status": "error",
            "error": "Storage failed",
        }

        # Create job
        job = TranscriptionJob(
            job_id="test_job",
            session_id="session_123",
            prompt_id="prompt_456",
            learner_id="learner_789",
            audio_hash="audio_hash_123",
            audio_pointer="audio_pointer_123",
            metadata={},
        )

        # Process job
        await pipeline._process_job(job, "test_worker")

        # Verify failure was recorded
        mock_telemetry_recorder.record_transcription_failure.assert_called_once()

    @pytest.mark.asyncio
    async def test_job_retry_logic(self, pipeline, mock_telemetry_recorder):
        """Test job retry logic."""
        # Create job
        job = TranscriptionJob(
            job_id="test_job",
            session_id="session_123",
            prompt_id="prompt_456",
            learner_id="learner_789",
            audio_hash="audio_hash_123",
            audio_pointer="audio_pointer_123",
            metadata={},
            retry_count=0,
        )

        # Handle failure (should retry)
        await pipeline._handle_job_failure(job, "Test error")

        # Verify job was re-queued
        assert pipeline._job_queue.qsize() == 1
        assert job.retry_count == 1

        # Get re-queued job
        retried_job = await pipeline._job_queue.get()
        assert retried_job.job_id == job.job_id
        assert retried_job.retry_count == 1

    @pytest.mark.asyncio
    async def test_job_max_retries(self, pipeline, mock_telemetry_recorder):
        """Test job max retries exceeded."""
        # Create job with max retries
        job = TranscriptionJob(
            job_id="test_job",
            session_id="session_123",
            prompt_id="prompt_456",
            learner_id="learner_789",
            audio_hash="audio_hash_123",
            audio_pointer="audio_pointer_123",
            metadata={},
            retry_count=3,  # Already at max
        )

        # Handle failure (should not retry)
        await pipeline._handle_job_failure(job, "Test error")

        # Verify job was not re-queued
        assert pipeline._job_queue.qsize() == 0

        # Verify failure was recorded
        mock_telemetry_recorder.record_transcription_failure.assert_called_once()

    def test_get_queue_status(self, pipeline):
        """Test getting queue status."""
        # Add some jobs to queue
        for i in range(3):
            pipeline._job_queue.put_nowait(f"job_{i}")

        status = pipeline.get_queue_status()

        assert status["queue_size"] == 3
        assert status["workers_active"] == 0
        assert status["processing"] is False

    @pytest.mark.asyncio
    async def test_get_job_status(self, pipeline):
        """Test getting job status."""
        status = await pipeline.get_job_status("test_job_id")

        assert status["job_id"] == "test_job_id"
        assert "status" in status
        assert "queue_size" in status

    def test_transcription_job_dataclass(self):
        """Test TranscriptionJob dataclass."""
        job = TranscriptionJob(
            job_id="job_123",
            session_id="session_456",
            prompt_id="prompt_789",
            learner_id="learner_123",
            audio_hash="hash_456",
            audio_pointer="pointer_789",
            metadata={"test": "value"},
            priority=2,
            retry_count=1,
        )

        assert job.job_id == "job_123"
        assert job.session_id == "session_456"
        assert job.prompt_id == "prompt_789"
        assert job.learner_id == "learner_123"
        assert job.audio_hash == "hash_456"
        assert job.audio_pointer == "pointer_789"
        assert job.metadata["test"] == "value"
        assert job.priority == 2
        assert job.retry_count == 1
        assert job.created_at != ""  # Should be set
