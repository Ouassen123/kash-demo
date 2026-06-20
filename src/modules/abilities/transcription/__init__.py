"""Speech-to-Text transcription module for Abilities."""

from .pipeline import SpeechToTextPipeline
from .provider_base import TranscriptionProvider, TranscriptPackage
from .repository import TranscriptRepository
from .qa_hooks import QAReviewHooks
from .fallback_orchestrator import FallbackOrchestrator
from .telemetry_recorder import TelemetryRecorder

__all__ = [
    "SpeechToTextPipeline",
    "TranscriptionProvider",
    "TranscriptPackage",
    "TranscriptRepository",
    "QAReviewHooks",
    "FallbackOrchestrator",
    "TelemetryRecorder",
]
