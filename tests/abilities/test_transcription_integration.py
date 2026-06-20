"""Tests for transcription integration with audio processing."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.modules.abilities.transcription.integration import TranscriptionIntegration
from src.modules.abilities.audio.processor import AudioProcessor


class TestTranscriptionIntegration:
    """Test transcription integration functionality."""

    @pytest.fixture
    def mock_qa_manager(self):
        """Create mock QA manager."""
        return MagicMock()

    @pytest.fixture
    def integration(self, mock_qa_manager):
        """Create transcription integration instance."""
        return TranscriptionIntegration(audio_qa_manager=mock_qa_manager)

    @pytest.mark.asyncio
    async def test_integration_start_stop(self, integration):
        """Test starting and stopping the integration."""
        # Start integration
        await integration.start(num_workers=2)
        assert integration._workers_started is True

        # Stop integration
        await integration.stop()
        assert integration._workers_started is False

    @pytest.mark.asyncio
    async def test_handle_audio_pipeline_trigger(self, integration):
        """Test handling audio pipeline trigger."""
        # Start integration
        await integration.start()

        # Prepare trigger data
        session_id = "test_session_123"
        metadata = {
            "prompt_id": "prompt_456",
            "learner_id": "learner_789",
            "audio_hash": "hash_123",
            "language": "en-US",
            "duration_seconds": 15.5,
            "noise_level": 0.12,
            "network_available": True,
            "bandwidth_kbps": 1000,
        }

        # Handle trigger
        result = await integration.handle_audio_pipeline_trigger(session_id, metadata)

        assert result["status"] == "queued"
        assert "job_id" in result
        assert result["queue_size"] == 1

        # Stop integration
        await integration.stop()

    @pytest.mark.asyncio
    async def test_handle_audio_pipeline_trigger_missing_fields(self, integration):
        """Test handling trigger with missing required fields."""
        metadata = {
            "prompt_id": "prompt_456",
            # Missing learner_id and audio_hash
        }

        result = await integration.handle_audio_pipeline_trigger("session_123", metadata)

        assert result["status"] == "error"
        assert "Missing required metadata fields" in result["error"]
        assert "learner_id" in result["missing_fields"]
        assert "audio_hash" in result["missing_fields"]

    @pytest.mark.asyncio
    async def test_get_transcription_status(self, integration):
        """Test getting transcription status for a session."""
        # Mock repository response
        integration.repository.list_transcripts.return_value = [
            {
                "transcript_id": "transcript_1",
                "session_id": "session_123",
                "prompt_id": "prompt_456",
                "qa_status": "approved",
                "stored_at": "2026-02-24T10:00:00Z",
            }
        ]

        # Mock transcript retrieval
        from src.modules.abilities.transcription.provider_base import TranscriptPackage, TranscriptSegment
        mock_transcript = TranscriptPackage(
            session_id="session_123",
            prompt_id="prompt_456",
            learner_id="learner_789",
            language="en-US",
            segments=[
                TranscriptSegment(
                    segment_id="seg_1",
                    speaker="learner",
                    start=0.0,
                    end=2.5,
                    text="Test transcript",
                    confidence=0.9,
                    words=[],
                    noise_level=0.1,
                    flags=[],
                )
            ],
            aggregate_confidence=0.9,
            provider={"name": "test_provider", "mode": "cloud"},
            created_at="2026-02-24T10:00:00Z",
            qa_status="approved",
        )
        integration.repository.retrieve_transcript.return_value = mock_transcript

        result = await integration.get_transcription_status("session_123")

        assert result["status"] == "found"
        assert result["transcript_count"] == 1
        assert len(result["transcripts"]) == 1

        transcript_detail = result["transcripts"][0]
        assert transcript_detail["transcript_id"] == "transcript_1"
        assert transcript_detail["qa_status"] == "approved"
        assert transcript_detail["aggregate_confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_get_transcription_status_not_found(self, integration):
        """Test getting transcription status when no transcripts found."""
        integration.repository.list_transcripts.return_value = []

        result = await integration.get_transcription_status("session_123")

        assert result["status"] == "not_found"
        assert result["transcripts"] == []

    @pytest.mark.asyncio
    async def test_get_approved_transcripts_for_fusion(self, integration):
        """Test getting approved transcripts in fusion format."""
        # Mock repository response
        integration.repository.list_transcripts.return_value = [
            {
                "transcript_id": "transcript_1",
                "qa_status": "approved",
                "qa_updated_at": "2026-02-24T10:05:00Z",
                "audio_hash": "hash_123",
            }
        ]

        # Mock transcript retrieval
        from src.modules.abilities.transcription.provider_base import TranscriptPackage, TranscriptSegment
        mock_transcript = TranscriptPackage(
            session_id="session_123",
            prompt_id="prompt_456",
            learner_id="learner_789",
            language="en-US",
            segments=[
                TranscriptSegment(
                    segment_id="seg_1",
                    speaker="learner",
                    start=0.0,
                    end=2.5,
                    text="Hello world",
                    confidence=0.9,
                    words=[],
                    noise_level=0.1,
                    flags=[],
                )
            ],
            aggregate_confidence=0.9,
            provider={"name": "test_provider", "mode": "cloud"},
            created_at="2026-02-24T10:00:00Z",
            qa_status="approved",
        )
        integration.repository.retrieve_transcript.return_value = mock_transcript

        result = await integration.get_approved_transcripts_for_fusion("session_123")

        assert result["status"] == "success"
        assert result["transcript_count"] == 1
        assert len(result["transcripts"]) == 1

        fusion_transcript = result["transcripts"][0]
        assert fusion_transcript["modality"] == "text_from_audio"
        assert fusion_transcript["session_id"] == "session_123"
        assert fusion_transcript["prompt_id"] == "prompt_456"
        assert fusion_transcript["content"]["text"] == "Hello world"
        assert fusion_transcript["metadata"]["source"] == "transcription"
        assert fusion_transcript["metadata"]["qa_approved"] is True

    @pytest.mark.asyncio
    async def test_get_integration_health(self, integration):
        """Test getting integration health status."""
        # Start integration
        await integration.start()

        # Mock telemetry response
        integration.telemetry_recorder.get_system_health.return_value = {
            "status": "healthy",
            "success_rate": 0.95,
            "total_jobs": 10,
        }

        # Mock QA dashboard
        integration.qa_hooks.get_qa_dashboard.return_value = {
            "total_transcripts": 5,
            "pending_review": 1,
            "approved": 4,
        }

        result = await integration.get_integration_health()

        assert result["status"] == "healthy"
        assert result["workers_started"] is True
        assert "pipeline" in result
        assert "system_health" in result
        assert "providers" in result
        assert "qa" in result

        # Stop integration
        await integration.stop()


class TestAudioProcessorIntegration:
    """Test AudioProcessor integration with transcription."""

    @pytest.fixture
    def mock_transcription_integration(self):
        """Create mock transcription integration."""
        integration = AsyncMock()
        integration.handle_audio_pipeline_trigger.return_value = {
            "status": "queued",
            "job_id": "test_job_123",
        }
        return integration

    @pytest.fixture
    def audio_processor(self, mock_transcription_integration):
        """Create AudioProcessor with transcription integration."""
        return AudioProcessor(
            encryption_key="test_key",
            transcription_integration=mock_transcription_integration,
        )

    def test_processor_with_transcription_integration(self, audio_processor):
        """Test AudioProcessor initialization with transcription integration."""
        assert audio_processor.transcription_integration is not None

    def test_processor_without_transcription_integration(self):
        """Test AudioProcessor initialization without transcription integration."""
        processor = AudioProcessor(encryption_key="test_key")
        assert processor.transcription_integration is None

    @patch('src.modules.abilities.audio.processor.asyncio.run')
    def test_trigger_pipelines_with_integration(self, mock_asyncio_run, audio_processor, mock_transcription_integration):
        """Test triggering pipelines with transcription integration available."""
        session_id = "test_session"
        metadata = {
            "prompt_id": "prompt_123",
            "learner_id": "learner_123",
            "audio_hash": "hash_123",
        }

        # Mock asyncio.run to return the async result
        mock_asyncio_run.return_value = mock_transcription_integration.handle_audio_pipeline_trigger.return_value

        result = audio_processor._trigger_pipelines(session_id, metadata)

        # Verify transcription pipeline was called
        mock_asyncio_run.assert_called_once()
        call_args = mock_asyncio_run.call_args[0][0]
        # The call should be a coroutine
        assert asyncio.iscoroutinefunction(call_args)

        # Verify response includes transcription result
        assert "transcription" in result
        assert result["transcription"]["status"] == "queued"
        assert result["transcription"]["job_id"] == "test_job_123"

    def test_trigger_pipelines_without_integration(self):
        """Test triggering pipelines without transcription integration."""
        processor = AudioProcessor(encryption_key="test_key")
        session_id = "test_session"
        metadata = {}

        result = processor._trigger_pipelines(session_id, metadata)

        # Should return mock response
        assert "transcription" in result
        assert result["transcription"]["status"] == "queued"
        assert result["transcription"]["estimated_time"] == 30

    @patch('src.modules.abilities.audio.processor.asyncio.run')
    def test_trigger_pipelines_integration_error(self, mock_asyncio_run, audio_processor):
        """Test triggering pipelines when transcription integration fails."""
        # Mock asyncio.run to raise an exception
        mock_asyncio_run.side_effect = Exception("Transcription service unavailable")

        session_id = "test_session"
        metadata = {
            "prompt_id": "prompt_123",
            "learner_id": "learner_123",
            "audio_hash": "hash_123",
        }

        result = audio_processor._trigger_pipelines(session_id, metadata)

        # Should handle error gracefully
        assert "transcription" in result
        assert result["transcription"]["status"] == "error"
        assert "Transcription service unavailable" in result["transcription"]["error"]

    def test_process_audio_upload_triggers_transcription(self, audio_processor, mock_transcription_integration):
        """Test that audio upload triggers transcription pipeline."""
        with patch('src.modules.abilities.audio.processor.asyncio.run') as mock_asyncio_run:
            mock_asyncio_run.return_value = {
                "status": "queued",
                "job_id": "test_job_123",
            }

            audio_blob = b"test_audio_data"
            metadata = {
                "session_id": "session_123",
                "prompt_id": "prompt_123",
                "learner_id": "learner_123",
                "audio_hash": "hash_123",
            }
            session_id = "session_123"

            result = audio_processor.process_audio_upload(audio_blob, metadata, session_id)

            # Verify transcription was triggered
            assert "pipeline_status" in result
            assert "transcription" in result["pipeline_status"]
            assert result["pipeline_status"]["transcription"]["status"] == "queued"
