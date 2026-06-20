"""Mock Whisper provider for development and testing."""

from typing import List, Dict, Any, Optional, AsyncGenerator
import asyncio
import uuid
from datetime import datetime

from ..provider_base import (
    TranscriptionProvider,
    TranscriptPackage,
    TranscriptSegment,
    TranscriptWord,
)


class MockWhisperProvider(TranscriptionProvider):
    """Mock implementation of Whisper-style transcription provider."""

    def __init__(self, model_size: str = "base", mode: str = "cloud"):
        """
        Initialize mock Whisper provider.

        Args:
            model_size: Model size (tiny, base, small, medium, large)
            mode: Provider mode (cloud or offline)
        """
        self.model_size = model_size
        self.mode = mode
        self._latency_ms = self._get_model_latency(model_size)

    @property
    def name(self) -> str:
        """Provider name."""
        return f"whisper-{self.model_size}-v3"

    @property
    def mode(self) -> str:
        """Provider mode."""
        return self._mode

    @mode.setter
    def mode(self, value: str) -> None:
        self._mode = value

    async def transcribe_batch(
        self,
        audio_data: bytes,
        metadata: Dict[str, Any],
    ) -> TranscriptPackage:
        """
        Transcribe audio in batch mode.

        Args:
            audio_data: Raw audio bytes
            metadata: Session/prompt metadata

        Returns:
            Structured transcript package
        """
        # Simulate processing time
        await asyncio.sleep(self._latency_ms / 1000)

        # Generate mock transcript based on metadata
        session_id = metadata.get("session_id", "unknown")
        prompt_id = metadata.get("prompt_id", "unknown")
        learner_id = metadata.get("learner_id", "unknown")
        language = metadata.get("language", "en-US")

        # Create mock segments
        segments = self._create_mock_segments(metadata)

        # Calculate aggregate confidence
        aggregate_confidence = self._calculate_aggregate_confidence(segments)

        # Provider info
        provider_info = {
            "name": self.name,
            "mode": self.mode,
            "model_size": self.model_size,
            "latency_ms": self._latency_ms,
            "fallback_used": False,
        }

        return TranscriptPackage(
            session_id=session_id,
            prompt_id=prompt_id,
            learner_id=learner_id,
            language=language,
            segments=segments,
            aggregate_confidence=aggregate_confidence,
            provider=provider_info,
            created_at=datetime.utcnow().isoformat(),
            qa_status="pending_review",
        )

    async def transcribe_stream(
        self,
        audio_stream: AsyncGenerator[bytes, None],
        metadata: Dict[str, Any],
    ) -> AsyncGenerator[TranscriptSegment, None]:
        """
        Transcribe streaming audio.

        Args:
            audio_stream: Async generator of audio chunks
            metadata: Session/prompt metadata

        Yields:
            Transcript segments as they become available
        """
        session_id = metadata.get("session_id", "unknown")
        language = metadata.get("language", "en-US")

        # Process audio chunks and yield segments
        chunk_count = 0
        async for chunk in audio_stream:
            chunk_count += 1
            
            # Simulate processing delay
            await asyncio.sleep(0.1)

            # Create a segment for this chunk
            segment = TranscriptSegment(
                segment_id=self._create_segment_id(),
                speaker="learner",
                start=chunk_count * 2.0,  # 2-second chunks
                end=(chunk_count + 1) * 2.0,
                text=f"This is segment {chunk_count} from the streaming audio.",
                confidence=0.92,
                words=[
                    TranscriptWord("This", chunk_count * 2.0, chunk_count * 2.0 + 0.2, 0.95),
                    TranscriptWord("is", chunk_count * 2.0 + 0.2, chunk_count * 2.0 + 0.4, 0.93),
                    TranscriptWord("segment", chunk_count * 2.0 + 0.4, chunk_count * 2.0 + 0.8, 0.91),
                    TranscriptWord(str(chunk_count), chunk_count * 2.0 + 0.8, chunk_count * 2.0 + 1.0, 0.94),
                ],
                noise_level=0.1,
                flags=[],
            )

            yield segment

    def get_provider_info(self) -> Dict[str, Any]:
        """Return provider capabilities and configuration."""
        return {
            "name": self.name,
            "mode": self.mode,
            "model_size": self.model_size,
            "supports_streaming": self.supports_streaming(),
            "supports_offline": self.supports_offline(),
            "languages": ["en-US", "es-ES", "fr-FR", "de-DE", "it-IT", "pt-BR"],
            "latency_ms": self._latency_ms,
            "max_audio_length_minutes": 30,
            "sample_rate": 16000,
        }

    def supports_streaming(self) -> bool:
        """Return True if provider supports real-time streaming."""
        return True

    def supports_offline(self) -> bool:
        """Return True if provider works without network."""
        return self.mode == "offline"

    def _create_mock_segments(self, metadata: Dict[str, Any]) -> List[TranscriptSegment]:
        """Create mock transcript segments."""
        segments = []
        
        # Get context from metadata
        prompt_text = metadata.get("prompt_text", "")
        duration_seconds = metadata.get("duration_seconds", 10.0)
        
        # Create segments based on duration
        num_segments = max(1, int(duration_seconds / 5.0))  # 5-second segments
        
        for i in range(num_segments):
            start_time = i * 5.0
            end_time = min((i + 1) * 5.0, duration_seconds)
            
            # Generate contextual text
            if prompt_text:
                text = f"In response to '{prompt_text[:30]}...', I would say this is segment {i+1}."
            else:
                text = f"This is mock transcript segment {i+1} demonstrating the transcription capability."

            # Create words with timestamps
            words = self._create_mock_words(text, start_time)

            segment = TranscriptSegment(
                segment_id=self._create_segment_id(),
                speaker="learner",
                start=start_time,
                end=end_time,
                text=text,
                confidence=0.85 + (i * 0.02),  # Slight variation
                words=words,
                noise_level=0.05 + (i * 0.01),
                flags=[],  # No flags in mock
            )

            segments.append(segment)

        return self._normalize_timestamps(segments)

    def _create_mock_words(self, text: str, start_time: float) -> List[TranscriptWord]:
        """Create mock word-level timestamps."""
        words = []
        word_list = text.split()
        words_per_second = len(word_list) / 5.0  # Assume 5-second segment
        
        for i, word in enumerate(word_list):
            word_start = start_time + (i / words_per_second)
            word_end = word_start + (1.0 / words_per_second)
            confidence = 0.88 + (i * 0.01)  # Slight variation
            
            words.append(TranscriptWord(
                text=word,
                start=word_start,
                end=word_end,
                confidence=min(confidence, 1.0),
            ))

        return words

    def _get_model_latency(self, model_size: str) -> int:
        """Get mock latency based on model size."""
        latencies = {
            "tiny": 500,
            "base": 1000,
            "small": 2000,
            "medium": 4000,
            "large": 8000,
        }
        return latencies.get(model_size, 1000)
