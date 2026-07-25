"""LLM-backed interview analyzer for generating deep behavioral profiles."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

from pydantic import BaseModel

from src.core.logging import get_logger
from src.modules.habits.schemas.interview_schemas import (
    BehavioralProfile,
    EmotionMetric,
    VoiceMetrics,
)

logger = get_logger(__name__)

try:  # pragma: no cover - optional runtime dependency
    import instructor
except Exception as exc:  # pragma: no cover - fallback if instructor is unavailable
    instructor = None
    _INSTRUCTOR_IMPORT_ERROR = exc

try:  # pragma: no cover - optional runtime dependency
    from openai import OpenAI
except Exception as exc:  # pragma: no cover - fallback if openai is unavailable
    OpenAI = None
    _OPENAI_IMPORT_ERROR = exc


@dataclass
class InterviewAnalysisContext:
    """Input context for the behavioral-profile generation step."""

    answer_texts: List[str]
    voice_metrics: Optional[VoiceMetrics] = None
    emotions_detected: Optional[List[EmotionMetric]] = None
    industry: Optional[str] = None

    def combined_text(self) -> str:
        return "\n\n".join(t.strip() for t in self.answer_texts if t and t.strip())

    def emotions_summary(self) -> Dict[str, float]:
        """Return the averaged emotion distribution over the detected frames."""
        if not self.emotions_detected:
            return {}

        values: Dict[str, List[float]] = {}
        for emotion in self.emotions_detected:
            values.setdefault(emotion.emotion.lower(), []).append(float(emotion.confidence))
        return {k: sum(v) / len(v) for k, v in values.items() if v}

    def voice_summary(self) -> Dict[str, float]:
        if not self.voice_metrics:
            return {}
        return self.voice_metrics.model_dump()


class _BehavioralProfileLLMResponse(BaseModel):
    """Structured response returned by the LLM via instructor."""

    behavioral_profile: BehavioralProfile


class InterviewAnalyzer:
    """Generate a deep behavioral profile using LLM + instructor.

    The class uses a structured prompt and forces the model to return a
    validated ``BehavioralProfile``. When the OpenAI API key is missing or the
    LLM call fails, it falls back to a deterministic heuristic mode using the
    Phase 1 spaCy-based signals.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        use_llm: Optional[bool] = None,
    ) -> None:
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.use_llm = use_llm if use_llm is not None else bool(self.api_key)

        self.client = None
        if self.use_llm and self.api_key and OpenAI is not None and instructor is not None:
            try:
                openai_client = OpenAI(api_key=self.api_key, base_url=self.base_url or None)
                self.client = instructor.from_openai(openai_client)
                logger.info("InterviewAnalyzer initialized with instructor-backed LLM (%s)", self.model)
            except Exception as exc:
                logger.warning("Failed to initialize instructor/OpenAI client; fallback will be used: %s", exc)
                self.client = None
                self.use_llm = False
        else:
            if not self.api_key:
                logger.info("OPENAI_API_KEY missing; InterviewAnalyzer will use heuristic fallback")
            elif OpenAI is None or instructor is None:
                logger.info("OpenAI/instructor unavailable; InterviewAnalyzer will use heuristic fallback")

    def analyze_behavioral_profile(
        self,
        answer_texts: Sequence[str],
        voice_metrics: Optional[VoiceMetrics] = None,
        emotions_detected: Optional[Sequence[EmotionMetric]] = None,
        industry: Optional[str] = None,
    ) -> BehavioralProfile:
        """Generate a deep behavioral profile from multimodal interview signals."""
        context = InterviewAnalysisContext(
            answer_texts=list(answer_texts),
            voice_metrics=voice_metrics,
            emotions_detected=list(emotions_detected) if emotions_detected else None,
            industry=industry,
        )

        if self.use_llm and self.client is not None:
            try:
                return self._analyze_with_llm(context)
            except Exception as exc:
                logger.warning("LLM behavioral analysis failed; falling back to heuristics: %s", exc)

        return self._heuristic_behavioral_profile(context)

    def _analyze_with_llm(self, context: InterviewAnalysisContext) -> BehavioralProfile:
        """Use instructor to force a valid BehavioralProfile response from the LLM."""
        prompt = self._build_prompt(context)
        response = self.client.chat.completions.create(
            model=self.model,
            response_model=_BehavioralProfileLLMResponse,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert interviewer and psychometric analyst. "
                        "Return a concise but deeply reasoned behavioral profile. "
                        "You must follow the schema exactly."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return response.behavioral_profile

    def _build_prompt(self, context: InterviewAnalysisContext) -> str:
        emotions = context.emotions_summary()
        voice = context.voice_summary()
        industry = context.industry or "unknown"

        return (
            "Analyze the candidate's interview behavior using the following inputs.\n\n"
            f"Industry target: {industry}\n\n"
            "Candidate answers:\n"
            f"{context.combined_text()}\n\n"
            "Voice metrics (if provided):\n"
            f"{json.dumps(voice, ensure_ascii=False, indent=2) if voice else 'No voice metrics provided'}\n\n"
            "Facial emotion distribution (if provided):\n"
            f"{json.dumps(emotions, ensure_ascii=False, indent=2) if emotions else 'No facial emotions provided'}\n\n"
            "Return a behavioral profile with these fields:\n"
            "- communication_style: structured | spontaneous | analytical | narrative\n"
            "- motivation_level: high | medium | low\n"
            "- self_awareness: high | medium | low\n"
            "- stress_indicators: low | moderate | high\n"
            "- overall_recommendation: recommended | borderline | not_recommended\n\n"
            "Use the voice and facial cues to refine the stress and motivation assessment."
        )

    def _heuristic_behavioral_profile(self, context: InterviewAnalysisContext) -> BehavioralProfile:
        """Fallback deterministic profile based on the Phase 1/4 heuristics."""
        text = context.combined_text()
        voice = context.voice_metrics
        emotions = list(context.emotions_detected or [])

        # Simple text heuristics (mirrors Phase 1 logic).
        word_count = len(text.split())
        clarity_hint = self._score_text_clarity_hint(text)
        relevance_hint = self._score_text_relevance_hint(text)
        engagement_hint = self._score_text_engagement_hint(text)
        confidence_hint = self._score_text_confidence_hint(text)

        if clarity_hint >= 70 and engagement_hint >= 60:
            communication_style = "structured"
        elif clarity_hint >= 55 and engagement_hint >= 50:
            communication_style = "analytical"
        elif engagement_hint >= 60:
            communication_style = "spontaneous"
        else:
            communication_style = "narrative"

        if engagement_hint >= 65 and confidence_hint >= 60:
            motivation_level = "high"
        elif engagement_hint >= 40:
            motivation_level = "medium"
        else:
            motivation_level = "low"

        if relevance_hint >= 55 and clarity_hint >= 55:
            self_awareness = "high"
        elif relevance_hint >= 35:
            self_awareness = "medium"
        else:
            self_awareness = "low"

        if confidence_hint >= 70:
            stress_indicators = "low"
        elif confidence_hint >= 45:
            stress_indicators = "moderate"
        else:
            stress_indicators = "high"

        stress_rank = {"low": 0, "moderate": 1, "high": 2}

        def raise_stress(current: str, candidate: str) -> str:
            return candidate if stress_rank.get(candidate, 0) > stress_rank.get(current, 0) else current

        # Voice adjustments.
        if voice is not None:
            if voice.speech_rate > 155 or voice.speech_rate < 110:
                stress_indicators = "high" if voice.pause_ratio > 0.25 else raise_stress(stress_indicators, "moderate")
            if voice.pitch_variation < 20:
                stress_indicators = raise_stress(stress_indicators, "moderate")
            if voice.volume_db < -30:
                stress_indicators = raise_stress(stress_indicators, "moderate")

        # Facial emotion adjustments.
        if emotions:
            dominant = max(emotions, key=lambda e: e.confidence).emotion.lower()
            if dominant in {"happy", "neutral"}:
                if stress_indicators == "high":
                    stress_indicators = "moderate"
                elif stress_indicators == "moderate":
                    stress_indicators = "low"
            elif dominant == "fear":
                stress_indicators = "high"
            elif dominant in {"sad", "disgust"} and stress_indicators != "high":
                stress_indicators = "moderate"

        # Overall recommendation.
        composite_hint = (clarity_hint * 0.25) + (relevance_hint * 0.25) + (engagement_hint * 0.25) + (confidence_hint * 0.25)
        if voice is not None:
            composite_hint = (composite_hint * 0.75) + (voice.fluency_score * 0.25)
        if emotions:
            dominant = max(emotions, key=lambda e: e.confidence).emotion.lower()
            if dominant == "fear":
                composite_hint -= 10
            elif dominant in {"happy", "neutral"}:
                composite_hint += 5

        if composite_hint >= 65:
            overall_recommendation = "recommended"
        elif composite_hint >= 45:
            overall_recommendation = "borderline"
        else:
            overall_recommendation = "not_recommended"

        logger.debug(
            "Heuristic behavioral profile: words=%s clarity=%s relevance=%s engagement=%s confidence=%s",
            word_count,
            clarity_hint,
            relevance_hint,
            engagement_hint,
            confidence_hint,
        )

        return BehavioralProfile(
            communication_style=communication_style,
            motivation_level=motivation_level,
            self_awareness=self_awareness,
            stress_indicators=stress_indicators,
            overall_recommendation=overall_recommendation,
        )

    # ── Text heuristics (Phase 1 fallback) ─────────────────────

    def _score_text_clarity_hint(self, text: str) -> float:
        """Approximate clarity from sentence length and lexical diversity."""
        if not text or not text.strip():
            return 0.0

        words = [w for w in text.split() if w.strip()]
        if not words:
            return 0.0
        unique = len({w.lower().strip(".,;:!?()[]{}\"'") for w in words})
        ttr = unique / len(words)
        ttr_score = min(100.0, (ttr / 0.6) * 100.0)

        sentences = [s.strip() for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()]
        if not sentences:
            return ttr_score * 0.5

        optimal = 0
        for sent in sentences:
            wc = len([w for w in sent.split() if w.strip()])
            if 12 <= wc <= 28:
                optimal += 1
        structure_score = (optimal / len(sentences)) * 100.0
        return max(0.0, min(100.0, (ttr_score * 0.5) + (structure_score * 0.5)))

    def _score_text_relevance_hint(self, text: str) -> float:
        """Approximate relevance from content-word density and overlap-style signals."""
        if not text or not text.strip():
            return 0.0

        words = [w.lower().strip(".,;:!?()[]{}\"'") for w in text.split() if w.strip()]
        if not words:
            return 0.0

        content_words = [w for w in words if len(w) > 3]
        ratio = len(content_words) / len(words)
        return max(0.0, min(100.0, ratio * 100.0))

    def _score_text_engagement_hint(self, text: str) -> float:
        if not text or not text.strip():
            return 0.0
        words = [w for w in text.split() if w.strip()]
        word_count = len(words)
        ratio = word_count / 150.0 if word_count else 0.0
        length_factor = max(0.0, 1.0 - abs(ratio - 1.0) * 0.6)
        action_verbs = sum(1 for w in words if w.lower().strip(".,;:!?()[]{}\"'") in {
            "build", "create", "develop", "design", "implement", "solve", "lead", "manage",
            "organize", "plan", "deliver", "achieve", "improve", "optimize", "analyze", "research",
            "collaborate", "coordinate", "establish", "launch", "integrate", "automate", "realiser",
            "developper", "analyser", "concevoir", "resoudre", "gerer", "organiser", "planifier",
        })
        verb_factor = min(1.0, action_verbs / max(1, len(words)) / 0.3)
        return max(0.0, min(100.0, ((length_factor * 0.6) + (verb_factor * 0.4)) * 100.0))

    def _score_text_confidence_hint(self, text: str) -> float:
        if not text or not text.strip():
            return 0.0
        words = [w.lower().strip(".,;:!?()[]{}\"'") for w in text.split() if w.strip()]
        if not words:
            return 0.0
        hedges = {
            "maybe", "perhaps", "think", "guess", "probably", "possibly", "might", "could",
            "sort", "kinda", "hopefully", "suppose", "assume", "seems", "appear", "roughly",
            "approximately", "peut", "peut-etre", "probablement", "possiblement", "suppose",
            "imagine", "pense", "crois", "semble", "paraitre", "environ", "approximativement",
            "eventuellement", "sans", "doute",
        }
        hedge_count = sum(1 for w in words if w in hedges)
        penalty = min(60.0, hedge_count * 8.0)
        return max(0.0, min(100.0, 100.0 - penalty))


__all__ = ["InterviewAnalyzer", "InterviewAnalysisContext"]
