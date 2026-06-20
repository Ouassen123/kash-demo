"""Voice recording UI component with noise monitoring and prompt synchronization."""

from typing import Dict, Any, Optional, Callable
import json
import time
from datetime import datetime

from src.core.logging import get_logger

logger = get_logger(__name__)


class VoiceRecorder:
    """Recording UI component for Abilities scenarios."""

    def __init__(self, session_id: str, prompt_id: str, learner_id: Optional[int] = None):
        """
        Initialize voice recorder.

        Args:
            session_id: Shared session ID (aligned with text-based tests)
            prompt_id: Current prompt ID for synchronization
            learner_id: Optional learner identifier
        """
        self.session_id = session_id
        self.prompt_id = prompt_id
        self.learner_id = learner_id
        self.is_recording = False
        self.start_time: Optional[float] = None
        self.audio_blob: Optional[bytes] = None
        self.metadata: Dict[str, Any] = {
            "session_id": session_id,
            "prompt_id": prompt_id,
            "learner_id": learner_id,
            "device_info": self._get_device_info(),
            "created_at": datetime.utcnow().isoformat(),
        }

    def _get_device_info(self) -> Dict[str, Any]:
        """Collect device metadata for audio quality tracking."""
        # Mock device info - in real implementation would use browser APIs
        return {
            "user_agent": "mock-browser",
            "platform": "mock-platform",
            "audio_context": "web-audio-api",
            "sample_rate": 44100,
            "channels": 1,
        }

    def start_recording(self) -> Dict[str, Any]:
        """
        Start audio recording with noise monitoring.

        Returns:
            Status dict with recording state.
        """
        if self.is_recording:
            return {"error": "Already recording"}

        self.is_recording = True
        self.start_time = time.time()
        self.metadata["started_at"] = datetime.utcnow().isoformat()
        
        # Mock noise monitoring - real implementation would analyze audio stream
        noise_level = self._monitor_noise()
        self.metadata["noise_level"] = noise_level

        logger.info(f"Recording started for session {self.session_id}, prompt {self.prompt_id}")
        return {
            "status": "recording",
            "session_id": self.session_id,
            "prompt_id": self.prompt_id,
            "started_at": self.metadata["started_at"],
            "noise_level": noise_level,
        }

    def _monitor_noise(self) -> float:
        """Monitor background noise level (mock implementation)."""
        # Mock: return random noise level between 0.1 and 0.8
        import random
        return round(random.uniform(0.1, 0.8), 2)

    def stop_recording(self) -> Dict[str, Any]:
        """
        Stop recording and capture audio blob.

        Returns:
            Status dict with recording results.
        """
        if not self.is_recording:
            return {"error": "Not recording"}

        self.is_recording = False
        duration = time.time() - (self.start_time or 0)
        self.metadata["duration_seconds"] = round(duration, 2)
        self.metadata["stopped_at"] = datetime.utcnow().isoformat()

        # Mock audio blob - real implementation would capture from microphone
        self.audio_blob = b"mock_audio_data_" + str(int(time.time())).encode()

        logger.info(f"Recording stopped for session {self.session_id}, duration {duration:.2f}s")
        return {
            "status": "stopped",
            "session_id": self.session_id,
            "prompt_id": self.prompt_id,
            "duration_seconds": self.metadata["duration_seconds"],
            "audio_size_bytes": len(self.audio_blob) if self.audio_blob else 0,
            "stopped_at": self.metadata["stopped_at"],
        }

    def get_recording_state(self) -> Dict[str, Any]:
        """Get current recording state and metadata."""
        return {
            "is_recording": self.is_recording,
            "session_id": self.session_id,
            "prompt_id": self.prompt_id,
            "learner_id": self.learner_id,
            "metadata": self.metadata,
            "has_audio": self.audio_blob is not None,
        }

    def get_audio_data(self) -> Optional[bytes]:
        """Get recorded audio blob."""
        return self.audio_blob

    def get_metadata(self) -> Dict[str, Any]:
        """Get complete recording metadata."""
        return self.metadata.copy()

    def validate_recording(self) -> Dict[str, Any]:
        """
        Validate recording quality before submission.

        Returns:
            Validation result with recommendations.
        """
        if not self.audio_blob:
            return {"valid": False, "reason": "No audio data"}

        duration = self.metadata.get("duration_seconds", 0)
        noise_level = self.metadata.get("noise_level", 0)

        issues = []
        if duration < 1.0:
            issues.append("Too short")
        if duration > 300.0:
            issues.append("Too long")
        if noise_level > 0.7:
            issues.append("High background noise")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "recommendations": self._get_recommendations(issues),
        }

    def _get_recommendations(self, issues: list) -> list:
        """Get recommendations based on validation issues."""
        recommendations = []
        if "Too short" in issues:
            recommendations.append("Record for at least 1 second")
        if "Too long" in issues:
            recommendations.append("Keep recordings under 5 minutes")
        if "High background noise" in issues:
            recommendations.append("Reduce background noise")
        return recommendations
