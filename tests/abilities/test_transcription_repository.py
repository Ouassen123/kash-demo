"""Tests for transcription repository."""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime

from src.modules.abilities.transcription.provider_base import (
    TranscriptPackage,
    TranscriptSegment,
    TranscriptWord,
)
from src.modules.abilities.transcription.repository import TranscriptRepository


class TestTranscriptRepository:
    """Test transcript repository operations."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def repository(self, temp_dir):
        """Create repository instance with temporary storage."""
        return TranscriptRepository(storage_path=temp_dir, encryption_key="test_key")

    @pytest.fixture
    def sample_transcript(self):
        """Create sample transcript package."""
        segments = [
            TranscriptSegment(
                segment_id="seg_1",
                speaker="learner",
                start=0.0,
                end=2.5,
                text="Hello, this is a test transcript.",
                confidence=0.92,
                words=[
                    TranscriptWord("Hello", 0.0, 0.5, 0.95),
                    TranscriptWord("this", 0.5, 0.8, 0.90),
                    TranscriptWord("is", 0.8, 1.0, 0.93),
                    TranscriptWord("a", 1.0, 1.2, 0.88),
                    TranscriptWord("test", 1.2, 1.6, 0.94),
                    TranscriptWord("transcript", 1.6, 2.5, 0.91),
                ],
                noise_level=0.05,
                flags=[],
            )
        ]

        return TranscriptPackage(
            session_id="session_123",
            prompt_id="prompt_456",
            learner_id="learner_789",
            language="en-US",
            segments=segments,
            aggregate_confidence=0.92,
            provider={
                "name": "whisper-base",
                "mode": "cloud",
                "latency_ms": 1200,
                "fallback_used": False,
            },
            created_at="2026-02-24T10:00:00Z",
            qa_status="pending_review",
        )

    @pytest.mark.asyncio
    async def test_store_transcript(self, repository, sample_transcript):
        """Test storing a transcript."""
        result = await repository.store_transcript(
            sample_transcript,
            audio_hash="audio_hash_123",
        )

        assert result["status"] == "stored"
        assert "transcript_id" in result
        assert "storage_meta" in result

        transcript_id = result["transcript_id"]
        storage_meta = result["storage_meta"]

        assert storage_meta["session_id"] == "session_123"
        assert storage_meta["prompt_id"] == "prompt_456"
        assert storage_meta["learner_id"] == "learner_789"
        assert storage_meta["audio_hash"] == "audio_hash_123"
        assert storage_meta["qa_status"] == "pending_review"
        assert "structured" in storage_meta["file_paths"]
        assert "plain_text" in storage_meta["file_paths"]

        # Check files were created
        json_path = Path(storage_meta["file_paths"]["structured"])
        txt_path = Path(storage_meta["file_paths"]["plain_text"])
        assert json_path.exists()
        assert txt_path.exists()

    @pytest.mark.asyncio
    async def test_retrieve_transcript(self, repository, sample_transcript):
        """Test retrieving a transcript."""
        # Store transcript first
        store_result = await repository.store_transcript(sample_transcript)
        transcript_id = store_result["transcript_id"]

        # Retrieve transcript
        retrieved = await repository.retrieve_transcript(transcript_id)

        assert retrieved is not None
        assert retrieved.session_id == sample_transcript.session_id
        assert retrieved.prompt_id == sample_transcript.prompt_id
        assert retrieved.learner_id == sample_transcript.learner_id
        assert retrieved.language == sample_transcript.language
        assert len(retrieved.segments) == len(sample_transcript.segments)
        assert retrieved.aggregate_confidence == sample_transcript.aggregate_confidence
        assert retrieved.provider["name"] == sample_transcript.provider["name"]
        assert retrieved.qa_status == sample_transcript.qa_status

        # Check segment details
        segment = retrieved.segments[0]
        original_segment = sample_transcript.segments[0]
        assert segment.segment_id == original_segment.segment_id
        assert segment.speaker == original_segment.speaker
        assert segment.text == original_segment.text
        assert segment.confidence == original_segment.confidence
        assert len(segment.words) == len(original_segment.words)

    @pytest.mark.asyncio
    async def test_retrieve_nonexistent_transcript(self, repository):
        """Test retrieving a transcript that doesn't exist."""
        result = await repository.retrieve_transcript("nonexistent_id")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_transcripts(self, repository, sample_transcript):
        """Test listing transcripts with filters."""
        # Store multiple transcripts
        transcripts = [
            sample_transcript,
            TranscriptPackage(
                session_id="session_456",
                prompt_id="prompt_789",
                learner_id="learner_123",
                language="en-US",
                segments=[],
                aggregate_confidence=0.88,
                provider={"name": "offline-rnn", "mode": "offline"},
                created_at="2026-02-24T11:00:00Z",
            ),
        ]

        stored_ids = []
        for transcript in transcripts:
            result = await repository.store_transcript(transcript)
            stored_ids.append(result["transcript_id"])

        # List all transcripts
        all_transcripts = await repository.list_transcripts()
        assert len(all_transcripts) == 2

        # Filter by session_id
        session_transcripts = await repository.list_transcripts(session_id="session_123")
        assert len(session_transcripts) == 1
        assert session_transcripts[0]["session_id"] == "session_123"

        # Filter by learner_id
        learner_transcripts = await repository.list_transcripts(learner_id="learner_789")
        assert len(learner_transcripts) == 1
        assert learner_transcripts[0]["learner_id"] == "learner_789"

        # Filter by QA status
        qa_transcripts = await repository.list_transcripts(qa_status="pending_review")
        assert len(qa_transcripts) == 2

    @pytest.mark.asyncio
    async def test_update_qa_status(self, repository, sample_transcript):
        """Test updating QA status."""
        # Store transcript
        store_result = await repository.store_transcript(sample_transcript)
        transcript_id = store_result["transcript_id"]

        # Update QA status
        success = await repository.update_qa_status(
            transcript_id,
            "approved",
            updated_by="reviewer_123",
        )
        assert success is True

        # Check updated status
        transcripts = await repository.list_transcripts(transcript_id=transcript_id)
        assert transcripts[0]["qa_status"] == "approved"
        assert transcripts[0]["qa_updated_by"] == "reviewer_123"
        assert "qa_updated_at" in transcripts[0]

        # Test updating nonexistent transcript
        success = await repository.update_qa_status("nonexistent", "approved")
        assert success is False

    @pytest.mark.asyncio
    async def test_purge_session(self, repository, sample_transcript):
        """Test purging all transcripts for a session."""
        # Store multiple transcripts for the same session
        session_id = "session_to_purge"
        
        transcript1 = TranscriptPackage(
            session_id=session_id,
            prompt_id="prompt_1",
            learner_id="learner_1",
            language="en-US",
            segments=[],
            aggregate_confidence=0.9,
            provider={"name": "test", "mode": "cloud"},
            created_at="2026-02-24T10:00:00Z",
        )

        transcript2 = TranscriptPackage(
            session_id=session_id,
            prompt_id="prompt_2",
            learner_id="learner_1",
            language="en-US",
            segments=[],
            aggregate_confidence=0.85,
            provider={"name": "test", "mode": "cloud"},
            created_at="2026-02-24T10:05:00Z",
        )

        # Store transcripts
        result1 = await repository.store_transcript(transcript1)
        result2 = await repository.store_transcript(transcript2)

        # Verify they exist
        transcripts_before = await repository.list_transcripts(session_id=session_id)
        assert len(transcripts_before) == 2

        # Purge session
        purge_result = await repository.purge_session(session_id)

        assert purge_result["status"] == "completed"
        assert purge_result["session_id"] == session_id
        assert purge_result["deleted_count"] == 2
        assert len(purge_result["errors"]) == 0

        # Verify they're gone
        transcripts_after = await repository.list_transcripts(session_id=session_id)
        assert len(transcripts_after) == 0

        # Verify files are deleted
        for result in [result1, result2]:
            storage_meta = result["storage_meta"]
            for file_path in storage_meta["file_paths"].values():
                assert not Path(file_path).exists()

    @pytest.mark.asyncio
    async def test_encryption_decryption(self, repository):
        """Test data encryption and decryption."""
        test_data = "sensitive transcript data"

        encrypted = repository._encrypt_data(test_data)
        decrypted = repository._decrypt_data(encrypted)

        assert decrypted == test_data
        assert encrypted != test_data
        assert encrypted.startswith("enc_")

    def test_serialization_deserialization(self, repository, sample_transcript):
        """Test transcript serialization and deserialization."""
        # Serialize
        json_str = repository._serialize_transcript(sample_transcript)
        assert isinstance(json_str, str)

        # Parse JSON to verify structure
        data = json.loads(json_str)
        assert data["session_id"] == sample_transcript.session_id
        assert data["prompt_id"] == sample_transcript.prompt_id
        assert len(data["segments"]) == len(sample_transcript.segments)

        # Deserialize
        deserialized = repository._deserialize_transcript(json_str)
        assert deserialized.session_id == sample_transcript.session_id
        assert deserialized.prompt_id == sample_transcript.prompt_id
        assert len(deserialized.segments) == len(sample_transcript.segments)

    def test_plain_text_extraction(self, repository, sample_transcript):
        """Test plain text extraction for QA."""
        plain_text = repository._extract_plain_text(sample_transcript)

        assert isinstance(plain_text, str)
        assert "[0.00-2.50]" in plain_text
        assert "learner:" in plain_text
        assert "Hello, this is a test transcript." in plain_text

    def test_transcript_id_generation(self, repository):
        """Test transcript ID generation."""
        id1 = repository._generate_transcript_id("session_1", "prompt_1")
        id2 = repository._generate_transcript_id("session_1", "prompt_1")
        id3 = repository._generate_transcript_id("session_2", "prompt_1")

        # Should be unique
        assert id1 != id2
        assert id1 != id3

        # Should follow naming convention
        assert id1.startswith("transcript_")
        assert id2.startswith("transcript_")
        assert id3.startswith("transcript_")
