"""Voice analyzer for the Habits module (prosodic baseline)."""

from __future__ import annotations

import base64
import binascii
import os
import tempfile
from dataclasses import dataclass
from typing import Any, Dict, Optional

import librosa
import numpy as np
import soundfile as sf

from src.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class VoiceAnalysisDefaults:
    """Neutral fallback metrics used when audio decoding or analysis fails."""

    speech_rate: float = 0.0
    volume_db: float = -60.0
    pitch_variation: float = 0.0
    pause_ratio: float = 1.0
    fluency_score: float = 0.0


class VoiceAnalyzer:
    """Prosodic audio analyzer based on librosa heuristics.

    The analysis is intentionally deterministic and safe for Phase 3.
    If the provided audio is invalid or unsupported, the analyzer returns
    neutral metrics instead of raising, so the pipeline does not break.
    """

    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate

    def analyze_audio(self, audio_base64: str) -> Dict[str, float]:
        """Analyze a base64-encoded audio payload and return prosodic metrics.

        Args:
            audio_base64: Raw base64 string, optionally prefixed as a data URL.

        Returns:
            Dictionary with speech_rate, volume_db, pitch_variation, pause_ratio,
            and fluency_score.
        """
        temp_path: Optional[str] = None
        try:
            audio_bytes = self._decode_base64_audio(audio_base64)
            suffix = self._guess_suffix(audio_base64)

            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(audio_bytes)
                temp_path = tmp.name

            # Load with librosa. ``sr=None`` keeps original rate, but we resample
            # to a common sample rate for consistent heuristics.
            y, sr = librosa.load(temp_path, sr=self.sample_rate, mono=True)

            if y.size == 0:
                return self._default_metrics().__dict__

            rms = librosa.feature.rms(y=y)[0]
            volume_db = float(librosa.amplitude_to_db(np.mean(rms) + 1e-9, ref=1.0))

            # Pause ratio: proportion of frames below silence threshold.
            silence_threshold = max(0.01 * float(np.max(rms)), 0.002)
            pause_ratio = float(np.mean(rms < silence_threshold))
            pause_ratio = max(0.0, min(1.0, pause_ratio))

            # Fundamental frequency (F0) estimation and variation.
            f0 = librosa.yin(y, fmin=50, fmax=400, sr=sr)
            f0 = f0[np.isfinite(f0)]
            pitch_variation = float(np.std(f0)) if f0.size else 0.0

            # Speech rate heuristic:
            # Approximate voiced segments from energy peaks and convert to WPM.
            speech_rate = self._estimate_speech_rate(rms=rms, sr=sr, audio_duration=float(librosa.get_duration(y=y, sr=sr)))

            fluency_score = self._fluency_score(
                pause_ratio=pause_ratio,
                speech_rate=speech_rate,
            )

            return {
                "speech_rate": round(speech_rate, 1),
                "volume_db": round(volume_db, 1),
                "pitch_variation": round(pitch_variation, 1),
                "pause_ratio": round(pause_ratio, 3),
                "fluency_score": round(fluency_score, 1),
            }

        except Exception as exc:
            logger.warning("Voice analysis failed; returning neutral metrics: %s", exc)
            return self._default_metrics().__dict__
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    logger.debug("Could not remove temporary audio file: %s", temp_path)

    # ── Helpers ───────────────────────────────────────────────

    @staticmethod
    def _decode_base64_audio(audio_base64: str) -> bytes:
        """Decode a base64 audio string, handling data-URL prefixes."""
        if not audio_base64:
            raise ValueError("Empty audio payload")

        if "," in audio_base64 and audio_base64.strip().startswith("data:"):
            audio_base64 = audio_base64.split(",", 1)[1]

        try:
            return base64.b64decode(audio_base64, validate=True)
        except binascii.Error:
            # Some browsers may omit proper padding; try a lenient decode.
            padding = "=" * (-len(audio_base64) % 4)
            return base64.b64decode(audio_base64 + padding)

    @staticmethod
    def _guess_suffix(audio_base64: str) -> str:
        """Guess a file suffix for temporary storage.

        Defaults to ``.webm`` because browser recordings commonly arrive in
        WebM/Opus; wav files are also accepted by librosa/soundfile.
        """
        lower = audio_base64.lower()
        if "data:audio/wav" in lower or "data:audio/x-wav" in lower:
            return ".wav"
        if "data:audio/mp3" in lower or "data:audio/mpeg" in lower:
            return ".mp3"
        return ".webm"

    def _estimate_speech_rate(self, rms: np.ndarray, sr: int, audio_duration: float) -> float:
        """Estimate words per minute from energy peaks in the audio signal."""
        if rms.size == 0 or audio_duration <= 0:
            return 0.0

        # Count local maxima in the RMS envelope as a rough proxy for syllable/word bursts.
        peak_threshold = float(np.mean(rms) + 0.5 * np.std(rms))
        peak_indices = np.where(rms >= peak_threshold)[0]
        if peak_indices.size == 0:
            return 0.0

        # Collapse consecutive peaks into events.
        event_count = 1
        for i in range(1, len(peak_indices)):
            if peak_indices[i] - peak_indices[i - 1] > 2:
                event_count += 1

        minutes = audio_duration / 60.0
        if minutes <= 0:
            return 0.0

        # Heuristic conversion: 1 energy event roughly approximates 0.8 words.
        words_estimate = event_count * 0.8
        return words_estimate / minutes

    @staticmethod
    def _fluency_score(pause_ratio: float, speech_rate: float) -> float:
        """Compute a 0-100 fluency score from pause ratio and speaking rate."""
        pause_component = (1.0 - max(0.0, min(1.0, pause_ratio))) * 100.0

        # Ideal speech-rate range: 120-150 wpm.
        if speech_rate <= 0:
            rate_component = 0.0
        elif 120.0 <= speech_rate <= 150.0:
            rate_component = 100.0
        elif speech_rate < 120.0:
            rate_component = max(0.0, 100.0 - ((120.0 - speech_rate) / 120.0) * 100.0)
        else:
            rate_component = max(0.0, 100.0 - ((speech_rate - 150.0) / 150.0) * 100.0)

        # Weighted blend: pauses matter slightly more than rate.
        return (pause_component * 0.6) + (rate_component * 0.4)

    @staticmethod
    def _default_metrics() -> VoiceAnalysisDefaults:
        return VoiceAnalysisDefaults()
