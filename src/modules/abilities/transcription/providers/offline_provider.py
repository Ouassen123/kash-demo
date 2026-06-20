"""Mock offline RNN provider for fallback scenarios."""

from typing import List, Dict, Any, Optional, AsyncGenerator
import asyncio
from datetime import datetime

from ..provider_base import (
    TranscriptionProvider,
    TranscriptPackage,
    TranscriptSegment,
    TranscriptWord,
)


class OfflineRNNProvider(TranscriptionProvider):
    """Mock offline RNN transcription provider for network fallback."""

    def __init__(self, model_name: str = "rnn-t-small"):
        """
        Initialize offline RNN provider.

        Args:
            model_name: Model name/size
        """
        self.model_name = model_name
        self._mode = "offline"

    @property
    def name(self) -> str:
        """Provider name."""
        return f"offline-{self.model_name}"

    @property
    def mode(self) -> str:
        """Provider mode."""
        return self._mode

    async def transcribe_batch(
        self,
        audio_data: bytes,
        metadata: Dict[str, Any],
    ) -> TranscriptPackage:
        """
        Transcribe audio in batch mode (offline).

        Args:
            audio_data: Raw audio bytes
            metadata: Session/prompt metadata

        Returns:
            Structured transcript package
        """
        # Simulate offline processing (faster but potentially less accurate)
        await asyncio.sleep(0.5)

        # Generate transcript with lower confidence than cloud models
        session_id = metadata.get("session_id", "unknown")
        prompt_id = metadata.get("prompt_id", "unknown")
        learner_id = metadata.get("learner_id", "unknown")
        language = metadata.get("language", "en-US")

        # Create segments with offline characteristics
        segments = self._create_offline_segments(metadata)

        # Lower confidence for offline model
        aggregate_confidence = self._calculate_aggregate_confidence(segments) * 0.85

        # Provider info
        provider_info = {
            "name": self.name,
            "mode": self.mode,
            "model_name": self.model_name,
            "latency_ms": 500,
            "fallback_used": True,
            "offline_reason": metadata.get("offline_reason", "network_unavailable"),
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
        Transcribe streaming audio (offline).

        Args:
            audio_stream: Async generator of audio chunks
            metadata: Session/prompt metadata

        Yields:
            Transcript segments as they become available
        """
        session_id = metadata.get("session_id", "unknown")
        language = metadata.get("language", "en-US")

        chunk_count = 0
        async for chunk in audio_stream:
            chunk_count += 1
            
            # Faster processing for offline
            await asyncio.sleep(0.05)

            # Create segment with offline characteristics
            segment = TranscriptSegment(
                segment_id=self._create_segment_id(),
                speaker="learner",
                start=chunk_count * 2.0,
                end=(chunk_count + 1) * 2.0,
                text=f"Offline transcript segment {chunk_count}",
                confidence=0.75,  # Lower confidence for offline
                words=[
                    TranscriptWord("Offline", chunk_count * 2.0, chunk_count * 2.0 + 0.3, 0.78),
                    TranscriptWord("transcript", chunk_count * 2.0 + 0.3, chunk_count * 2.0 + 0.8, 0.73),
                    TranscriptWord("segment", chunk_count * 2.0 + 0.8, chunk_count * 2.0 + 1.3, 0.74),
                    TranscriptWord(str(chunk_count), chunk_count * 2.0 + 1.3, chunk_count * 2.0 + 1.5, 0.76),
                ],
                noise_level=0.15,  # Higher noise tolerance
                flags=["offline_mode"],  # Flag to indicate offline processing
            )

            yield segment

    def get_provider_info(self) -> Dict[str, Any]:
        """Return provider capabilities and configuration."""
        return {
            "name": self.name,
            "mode": self.mode,
            "model_name": self.model_name,
            "supports_streaming": self.supports_streaming(),
            "supports_offline": self.supports_offline(),
            "languages": ["en-US"],  # Limited language support offline
            "latency_ms": 500,
            "max_audio_length_minutes": 10,  # Shorter max length for offline
            "sample_rate": 16000,
            "accuracy_vs_speed": "speed",  # Prioritize speed for offline
        }

    def supports_streaming(self) -> bool:
        """Return True if provider supports real-time streaming."""
        return True

    def supports_offline(self) -> bool:
        """Return True if provider works without network."""
        return True

    def _create_offline_segments(self, metadata: Dict[str, Any]) -> List[TranscriptSegment]:
        """Create offline-specific transcript segments."""
        segments = []
        
        duration_seconds = metadata.get("duration_seconds", 8.0)  # Shorter for offline
        num_segments = max(1, int(duration_seconds / 4.0))  # 4-second segments
        
        for i in range(num_segments):
            start_time = i * 4.0
            end_time = min((i + 1) * 4.0, duration_seconds)
            
            # Simulate offline transcription characteristics
            text = f"Offline processing segment {i+1} with reduced accuracy."
            
            # Create words with slightly less precise timing
            words = self._create_offline_words(text, start_time)

            segment = TranscriptSegment(
                segment_id=self._create_segment_id(),
                speaker="learner",
                start=start_time,
                end=end_time,
                text=text,
                confidence=0.70 + (i * 0.01),  # Lower base confidence
                words=words,
                noise_level=0.12,  # Higher noise tolerance
                flags=["offline_mode"] if i == 0 else [],  # Flag first segment
            )

            segments.append(segment)

        return self._normalize_timestamps(segments)

    def _create_offline_words(self, text: str, start_time: float) -> List[TranscriptWord]:
        """Create offline-specific word timestamps."""
        words = []
        word_list = text.split()
        words_per_second = len(word_list) / 4.0  # 4-second segments
        
        for i, word in enumerate(word_list):
            word_start = start_time + (i / words_per_second)
            word_end = word_start + (1.0 / words_per_second)
            # Lower confidence for offline processing
            confidence = 0.68 + (i * 0.005)
            
            words.append(TranscriptWord(
                text=word,
                start=word_start,
                end=word_end,
                confidence=min(confidence, 0.85),  # Cap at lower maximum
            ))

        return words
