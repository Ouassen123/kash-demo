"""Face analyzer for the Habits module (emotion detection baseline)."""

from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from src.core.logging import get_logger

logger = get_logger(__name__)

try:  # pragma: no cover - optional heavy dependency
    from deepface import DeepFace
except Exception as exc:  # pragma: no cover - fallback if dependency unavailable
    DeepFace = None
    _DEEPFACE_IMPORT_ERROR = exc


_NEGATIVE_EMOTIONS = {"fear", "sad", "disgust", "angry"}


@dataclass
class FaceAnalysisDefaults:
    """Neutral fallback when face analysis cannot run safely."""

    emotions: List[Dict[str, float]]
    stress_indicator: float


class FaceAnalyzer:
    """Emotion-based face analyzer using OpenCV + DeepFace.

    The implementation is defensive: any decode / detection / model-loading
    failure returns an empty result or a neutral emotion so the pipeline never
    crashes.
    """

    def __init__(self) -> None:
        if DeepFace is None:
            logger.warning("DeepFace unavailable; face analysis will use fallback only: %s", _DEEPFACE_IMPORT_ERROR)

    def analyze_video_frames(self, frames_base64: List[str]) -> List[dict]:
        """Analyze a list of base64-encoded JPEG frames and aggregate emotions.

        Args:
            frames_base64: List of base64 JPEG frame strings.

        Returns:
            List of emotion dictionaries compatible with ``EmotionMetric``.
            The list is aggregated and averaged across all valid frames.
        """
        try:
            if not frames_base64:
                return []

            emotion_scores: Dict[str, List[float]] = {}
            valid_frame_count = 0
            stress_accumulator = 0.0

            for frame_b64 in frames_base64:
                frame = self._decode_frame(frame_b64)
                if frame is None:
                    continue

                valid_frame_count += 1

                if DeepFace is None:
                    # Neutral fallback frame if model is not available.
                    emotion_scores.setdefault("neutral", []).append(1.0)
                    continue

                try:
                    analysis = DeepFace.analyze(
                        img_path=frame,
                        actions=["emotion"],
                        enforce_detection=False,
                    )

                    # DeepFace may return either a dict or a list of dicts.
                    if isinstance(analysis, list):
                        analysis = analysis[0] if analysis else {}

                    if not isinstance(analysis, dict):
                        continue

                    emotions = analysis.get("emotion", {}) or {}
                    if not emotions:
                        emotion_scores.setdefault("neutral", []).append(1.0)
                        continue

                    frame_total = float(sum(max(0.0, float(v)) for v in emotions.values())) or 1.0
                    for emotion_name, value in emotions.items():
                        normalized = max(0.0, float(value)) / frame_total
                        emotion_scores.setdefault(str(emotion_name).lower(), []).append(normalized)

                    # Stress indicator: sum of negative emotions on this frame.
                    stress_accumulator += sum(
                        max(0.0, float(emotions.get(emotion, 0.0))) for emotion in _NEGATIVE_EMOTIONS
                    )

                except Exception as exc:
                    logger.warning("DeepFace failed on one frame; falling back to neutral emotion: %s", exc)
                    emotion_scores.setdefault("neutral", []).append(1.0)

            if valid_frame_count == 0:
                return []

            aggregated: List[dict] = []
            for emotion_name, values in emotion_scores.items():
                confidence = float(np.mean(values)) if values else 0.0
                aggregated.append(
                    {
                        "emotion": emotion_name,
                        "confidence": round(max(0.0, min(1.0, confidence)), 3),
                        "timestamp_ms": None,
                    }
                )

            # If everything collapses to nothing, provide a neutral fallback.
            if not aggregated:
                aggregated = [{"emotion": "neutral", "confidence": 1.0, "timestamp_ms": None}]

            # Stress can be derived by downstream consumers from negative emotions;
            # we keep the computation here for future Phase 4+ uses.
            self._last_stress_indicator = self._compute_stress_indicator(aggregated, stress_accumulator, valid_frame_count)
            return aggregated

        except Exception as exc:
            logger.warning("Face analysis failed; returning neutral fallback: %s", exc)
            return [{"emotion": "neutral", "confidence": 1.0, "timestamp_ms": None}]

    # ── Helpers ───────────────────────────────────────────────

    @staticmethod
    def _decode_frame(frame_base64: str) -> Optional[np.ndarray]:
        """Decode a base64 JPEG frame into an OpenCV BGR image."""
        if not frame_base64:
            return None

        try:
            if "," in frame_base64 and frame_base64.strip().startswith("data:"):
                frame_base64 = frame_base64.split(",", 1)[1]
            raw = base64.b64decode(frame_base64 + ("=" * (-len(frame_base64) % 4)))
            arr = np.frombuffer(raw, dtype=np.uint8)
            frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            return frame
        except (binascii.Error, ValueError, cv2.error):
            return None

    @staticmethod
    def _compute_stress_indicator(aggregated: List[dict], stress_accumulator: float, valid_frame_count: int) -> float:
        """Compute a simple 0-1 facial stress indicator from negative emotions."""
        negative_sum = 0.0
        positive_sum = 0.0
        for item in aggregated:
            emotion = str(item.get("emotion", "")).lower()
            conf = float(item.get("confidence", 0.0))
            if emotion in _NEGATIVE_EMOTIONS:
                negative_sum += conf
            elif emotion in {"happy", "surprise", "neutral"}:
                positive_sum += conf

        base = negative_sum + (stress_accumulator / max(1, valid_frame_count) / 100.0)
        denom = max(0.001, negative_sum + positive_sum)
        return max(0.0, min(1.0, base / denom))

    @property
    def last_stress_indicator(self) -> float:
        return getattr(self, "_last_stress_indicator", 0.0)
