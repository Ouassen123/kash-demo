"""Abstract base for transcription providers."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass
import uuid
from datetime import datetime


@dataclass
class TranscriptWord:
    text: str
    start: float
    end: float
    confidence: float


@dataclass
class TranscriptSegment:
    segment_id: str
    speaker: str
    start: float
    end: float
    text: str
    confidence: float
    words: List[TranscriptWord]
    noise_level: float
    flags: List[str]


@dataclass
class TranscriptPackage:
    session_id: str
    prompt_id: str
    learner_id: str
    language: str
    segments: List[TranscriptSegment]
    aggregate_confidence: float
    provider: Dict[str, Any]
    created_at: str
    qa_status: str = "pending_review"


class TranscriptionProvider(ABC):
    """Abstract contract for speech-to-text providers."""

    @abstractmethod
    async def transcribe_batch(
        self,
        audio_data: bytes,
        metadata: Dict[str, Any],
    ) -> TranscriptPackage:
        """
        Transcribe a full audio blob in batch mode.

        Args:
            audio_data: Raw audio bytes
            metadata: Session/prompt metadata

        Returns:
            Structured transcript package
        """
        ...

    @abstractmethod
    async def transcribe_stream(
        self,
        audio_stream: AsyncGenerator[bytes, None],
        metadata: Dict[str, Any],
    ) -> AsyncGenerator[TranscriptSegment, None]:
        """
        Transcribe streaming audio chunks.

        Args:
            audio_stream: Async generator of audio chunks
            metadata: Session/prompt metadata

        Yields:
            Transcript segments as they become available
        """
        ...

    @abstractmethod
    def get_provider_info(self) -> Dict[str, Any]:
        """Return provider capabilities and configuration."""
        ...

    @abstractmethod
    def supports_streaming(self) -> bool:
        """Return True if provider supports real-time streaming."""
        ...

    @abstractmethod
    def supports_offline(self) -> bool:
        """Return True if provider works without network."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""
        ...

    @property
    @abstractmethod
    def mode(self) -> str:
        """Provider mode: 'cloud' or 'offline'."""
        ...

    def _create_segment_id(self) -> str:
        """Generate a unique segment identifier."""
        return f"seg_{uuid.uuid4().hex[:8]}"

    def _calculate_aggregate_confidence(self, segments: List[TranscriptSegment]) -> float:
        """Calculate overall confidence from segments."""
        if not segments:
            return 0.0
        total_confidence = sum(seg.confidence for seg in segments)
        return round(total_confidence / len(segments), 3)

    def _normalize_timestamps(self, segments: List[TranscriptSegment]) -> List[TranscriptSegment]:
        """Ensure timestamps are monotonic and non-negative."""
        if not segments:
            return segments

        # Sort by start time
        sorted_segments = sorted(segments, key=lambda s: s.start)

        # Ensure no negative times and monotonic ordering
        current_time = 0.0
        for seg in sorted_segments:
            if seg.start < current_time:
                seg.start = current_time
            if seg.end <= seg.start:
                seg.end = seg.start + 0.1  # Minimum duration
            current_time = seg.end

        return sorted_segments
