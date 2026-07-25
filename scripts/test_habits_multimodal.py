"""Smoke test for the Habits multimodal interview endpoint.

This script posts a realistic multimodal payload (answers + audio + video frames)
against the local FastAPI backend and verifies the response shape.

Usage:
    python scripts/test_habits_multimodal.py
    python scripts/test_habits_multimodal.py --url http://localhost:8000/api/v1/habits/interview/analyze
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import math
import struct
import sys
import wave
from typing import Any, Dict, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_URL = "http://localhost:8000/api/v1/habits/interview/analyze"
TEST_FRAME_BASE64 = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO2L1I0AAAAASUVORK5CYII="
)


def build_wav_base64(duration_seconds: float = 0.8, sample_rate: int = 22050) -> str:
    """Create a tiny deterministic WAV payload for voice analysis."""
    buffer = io.BytesIO()
    n_samples = max(1, int(duration_seconds * sample_rate))

    frames = bytearray()
    for index in range(n_samples):
        amplitude = 0.18 * math.sin(2.0 * math.pi * 220.0 * (index / sample_rate))
        frames.extend(struct.pack("<h", int(amplitude * 32767)))

    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(bytes(frames))

    return base64.b64encode(buffer.getvalue()).decode("ascii")


def build_payload() -> Dict[str, Any]:
    """Build a realistic Habits interview payload with 3 answers."""
    audio_base64 = build_wav_base64()

    return {
        "answers": [
            {
                "question_id": "q1_motivation",
                "question_text": "Présente ton objectif académique ou professionnel principal.",
                "answer_text": "Je souhaite devenir ingénieur data et contribuer à des projets utiles avec une vraie méthode.",
            },
            {
                "question_id": "q2_challenge",
                "question_text": "Décris un défi que tu as résolu et ce que tu as appris.",
                "answer_text": "J'ai dû structurer un projet complexe avec peu de temps, ce qui m'a appris à prioriser et communiquer clairement.",
            },
            {
                "question_id": "q3_growth",
                "question_text": "Quelles compétences veux-tu améliorer dans les 3 prochains mois ?",
                "answer_text": "Je veux améliorer ma prise de parole, mon autonomie technique et ma capacité à présenter mes idées simplement.",
            },
        ],
        "audio_base64": f"data:audio/wav;base64,{audio_base64}",
        "video_frames_base64": [TEST_FRAME_BASE64] * 3,
        "industry": "technology",
    }


def post_json(url: str, payload: Dict[str, Any], timeout: int = 60) -> Tuple[int, str]:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            return response.status, body
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        return exc.code, body or str(exc.reason)
    except URLError as exc:
        raise RuntimeError(str(exc.reason)) from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test the Habits multimodal interview endpoint.")
    parser.add_argument("--url", default=DEFAULT_URL, help="Full endpoint URL")
    args = parser.parse_args()

    payload = build_payload()
    print("Habits multimodal smoke test")
    print(f"- URL: {args.url}")
    print(f"- Answers: {len(payload['answers'])}")
    print(f"- Audio: {'yes' if payload['audio_base64'] else 'no'}")
    print(f"- Video frames: {len(payload['video_frames_base64'])}")
    print()

    try:
        status_code, body = post_json(args.url, payload)
    except Exception as exc:
        print(f"[FAIL] Request error: {exc}")
        return 1

    print(f"HTTP {status_code}")
    print(body[:800])

    if status_code != 200:
        print("\n[FAIL] Habits multimodal endpoint rejected the payload.")
        return 1

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        print("\n[FAIL] Response is not valid JSON.")
        return 1

    required_keys = ["assessment_id", "status", "composite_score", "modalities_used", "behavioral_profile"]
    missing = [key for key in required_keys if key not in data]
    if missing:
        print(f"\n[FAIL] Missing response keys: {', '.join(missing)}")
        return 1

    modalities = set(str(item) for item in data.get("modalities_used", []))
    expected_modalities = {"text", "voice", "face"}
    if not expected_modalities.issubset(modalities):
        print(f"\n[FAIL] Unexpected modalities_used: {sorted(modalities)}")
        return 1

    print("\n[OK] Habits multimodal endpoint accepted the full interview payload.")
    print(f"[OK] composite_score={data.get('composite_score')} | status={data.get('status')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
