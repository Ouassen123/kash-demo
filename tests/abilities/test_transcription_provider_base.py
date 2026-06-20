"""Tests for transcription provider base classes."""

import pytest
from datetime import datetime
from src.modules.abilities.transcription.provider_base import (
    TranscriptWord,
    TranscriptSegment,
    TranscriptPackage,
    TranscriptionProvider,
)


class MockTranscriptionProvider(TranscriptionProvider):
    """Mock provider for testing base class functionality."""

    def __init__(self, name: str = "mock", mode: str = "cloud"):
        self._name = name
        self._mode = mode

    @property
    def name(self) -> str:
        return self._name

    @property
    def mode(self) -> str:
        return self._mode

    async def transcribe_batch(self, audio_data: bytes, metadata: dict) -> TranscriptPackage:
        # Mock implementation
        return TranscriptPackage(
            session_id="test_session",
            prompt_id="test_prompt",
            learner_id="test_learner",
            language="en-US",
            segments=[],
            aggregate_confidence=0.9,
            provider={"name": self.name, "mode": self.mode},
            created_at=datetime.utcnow().isoformat(),
        )

    async def transcribe_stream(self, audio_stream, metadata: dict):
        # Mock implementation
        return

    def get_provider_info(self) -> dict:
        return {"name": self.name, "mode": self.mode}

    def supports_streaming(self) -> bool:
        return True

    def supports_offline(self) -> bool:
        return self.mode == "offline"


class TestTranscriptWord:
    """Test TranscriptWord dataclass."""

    def test_transcript_word_creation(self):
        """Test creating a transcript word."""
        word = TranscriptWord(
            text="hello",
            start=1.0,
            end=1.5,
            confidence=0.95,
        )

        assert word.text == "hello"
        assert word.start == 1.0
        assert word.end == 1.5
        assert word.confidence == 0.95


class TestTranscriptSegment:
    """Test TranscriptSegment dataclass."""

    def test_transcript_segment_creation(self):
        """Test creating a transcript segment."""
        words = [
            TranscriptWord("hello", 0.0, 0.5, 0.95),
            TranscriptWord("world", 0.5, 1.0, 0.92),
        ]

        segment = TranscriptSegment(
            segment_id="seg_1",
            speaker="user",
            start=0.0,
            end=1.0,
            text="hello world",
            confidence=0.93,
            words=words,
            noise_level=0.1,
            flags=[],
        )

        assert segment.segment_id == "seg_1"
        assert segment.speaker == "user"
        assert segment.start == 0.0
        assert segment.end == 1.0
        assert segment.text == "hello world"
        assert segment.confidence == 0.93
        assert len(segment.words) == 2
        assert segment.noise_level == 0.1
        assert segment.flags == []


class TestTranscriptPackage:
    """Test TranscriptPackage dataclass."""

    def test_transcript_package_creation(self):
        """Test creating a transcript package."""
        segments = [
            TranscriptSegment(
                segment_id="seg_1",
                speaker="user",
                start=0.0,
                end=2.0,
                text="test segment",
                confidence=0.9,
                words=[],
                noise_level=0.1,
                flags=[],
            )
        ]

        package = TranscriptPackage(
            session_id="session_123",
            prompt_id="prompt_456",
            learner_id="learner_789",
            language="en-US",
            segments=segments,
            aggregate_confidence=0.9,
            provider={"name": "test_provider", "mode": "cloud"},
            created_at="2026-02-24T10:00:00Z",
            qa_status="pending_review",
        )

        assert package.session_id == "session_123"
        assert package.prompt_id == "prompt_456"
        assert package.learner_id == "learner_789"
        assert package.language == "en-US"
        assert len(package.segments) == 1
        assert package.aggregate_confidence == 0.9
        assert package.provider["name"] == "test_provider"
        assert package.created_at == "2026-02-24T10:00:00Z"
        assert package.qa_status == "pending_review"


class TestTranscriptionProvider:
    """Test TranscriptionProvider base class."""

    def test_provider_properties(self):
        """Test provider property access."""
        provider = MockTranscriptionProvider("test_provider", "offline")

        assert provider.name == "test_provider"
        assert provider.mode == "offline"
        assert provider.supports_streaming()
        assert provider.supports_offline()

    def test_segment_id_generation(self):
        """Test segment ID generation."""
        provider = MockTranscriptionProvider()

        id1 = provider._create_segment_id()
        id2 = provider._create_segment_id()

        assert id1 != id2
        assert id1.startswith("seg_")
        assert id2.startswith("seg_")

    def test_aggregate_confidence_calculation(self):
        """Test aggregate confidence calculation."""
        provider = MockTranscriptionProvider()

        # Test with segments
        segments = [
            TranscriptSegment("seg_1", "user", 0, 1, "text1", 0.9, [], 0.1, []),
            TranscriptSegment("seg_2", "user", 1, 2, "text2", 0.8, [], 0.1, []),
            TranscriptSegment("seg_3", "user", 2, 3, "text3", 0.95, [], 0.1, []),
        ]

        confidence = provider._calculate_aggregate_confidence(segments)
        expected = (0.9 + 0.8 + 0.95) / 3
        assert abs(confidence - expected) < 0.001

        # Test with empty segments
        empty_confidence = provider._calculate_aggregate_confidence([])
        assert empty_confidence == 0.0

    def test_timestamp_normalization(self):
        """Test timestamp normalization."""
        provider = MockTranscriptionProvider()

        # Test with unsorted and negative timestamps
        segments = [
            TranscriptSegment("seg_3", "user", 5, 6, "text3", 0.9, [], 0.1, []),
            TranscriptSegment("seg_1", "user", -1, 0.5, "text1", 0.9, [], 0.1, []),
            TranscriptSegment("seg_2", "user", 0.5, 1.5, "text2", 0.9, [], 0.1, []),
        ]

        normalized = provider._normalize_timestamps(segments)

        # Should be sorted by start time
        assert normalized[0].segment_id == "seg_1"
        assert normalized[1].segment_id == "seg_2"
        assert normalized[2].segment_id == "seg_3"

        # No negative timestamps
        assert normalized[0].start >= 0

        # Monotonic ordering
        assert normalized[0].end <= normalized[1].start
        assert normalized[1].end <= normalized[2].start

        # Test with empty segments
        empty_normalized = provider._normalize_timestamps([])
        assert empty_normalized == []

    def test_provider_info_contract(self):
        """Test provider info method contract."""
        provider = MockTranscriptionProvider()

        info = provider.get_provider_info()
        assert isinstance(info, dict)
        assert "name" in info
        assert "mode" in info

    @pytest.mark.asyncio
    async def test_batch_transcription_contract(self):
        """Test batch transcription method contract."""
        provider = MockTranscriptionProvider()

        result = await provider.transcribe_batch(b"test_audio", {"session_id": "test"})

        assert isinstance(result, TranscriptPackage)
        assert result.session_id == "test_session"
        assert result.provider["name"] == "mock"

    @pytest.mark.asyncio
    async def test_stream_transcription_contract(self):
        """Test stream transcription method contract."""
        provider = MockTranscriptionProvider()

        # Mock audio stream
        async def mock_audio_stream():
            yield b"chunk1"
            yield b"chunk2"

        result = provider.transcribe_stream(mock_audio_stream(), {"session_id": "test"})
        
        # Should be an async generator
        assert hasattr(result, "__anext__")
        assert hasattr(result, "__aiter__")
