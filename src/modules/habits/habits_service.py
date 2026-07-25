"""Habits module — central orchestration service for multimodal interview analysis."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import spacy
from spacy.language import Language

from src.core.logging import get_logger
from src.modules.habits.scoring.clarity_scorer import ClarityScorer
from src.modules.habits.scoring.composite_scorer import CompositeScorer
from src.modules.habits.scoring.relevance_scorer import RelevanceScorer
from src.modules.habits.interview_analyzer import InterviewAnalyzer
from src.modules.habits.schemas.interview_schemas import (
    BehavioralProfile,
    EmotionMetric,
    InterviewAnalysisRequest,
    InterviewAnalysisResponse,
    VoiceMetrics,
)

try:
    from src.modules.habits.face_analyzer import FaceAnalyzer
except Exception as exc:  # pragma: no cover - optional dependency fallback
    FaceAnalyzer = None
    _FACE_ANALYZER_IMPORT_ERROR = exc

try:
    from src.modules.habits.voice_analyzer import VoiceAnalyzer
except Exception as exc:  # pragma: no cover - optional dependency fallback
    VoiceAnalyzer = None
    _VOICE_ANALYZER_IMPORT_ERROR = exc

logger = get_logger(__name__)

# ── Constants ─────────────────────────────────────────────────

_OPTIMAL_ANSWER_LENGTH = 150  # words
_ACTION_VERB_LEMMAS = {
    # English
    "build", "create", "develop", "design", "implement", "solve",
    "lead", "manage", "organize", "plan", "deliver", "achieve",
    "improve", "optimize", "analyze", "research", "collaborate",
    "coordinate", "establish", "launch", "integrate", "automate",
    # French (lemmes)
    "construire", "creer", "developper", "concevoir", "implementer",
    "resoudre", "diriger", "gerer", "organiser", "planifier",
    "livrer", "ameliorer", "optimiser", "analyser", "rechercher",
    "collaborer", "coordonner", "etablir", "lancer", "integrer",
    "automatiser", "realiser", "mettre", "faire", "travailler",
}

_HEDGING_WORDS = {
    # English
    "maybe", "perhaps", "think", "guess", "probably", "possibly",
    "might", "could", "sort", "kinda", "hopefully", "suppose",
    "assume", "seems", "appear", "roughly", "approximately",
    # French
    "peut", "peut-etre", "probablement", "possiblement", "suppose",
    "imagine", "pense", "crois", "semble", "paraitre", "environ",
    "approximativement", "eventuellement", "sans", "doute",
}

# Composite weights (text-only mode)
_WEIGHTS_TEXT_ONLY = {
    "clarity": 0.30,
    "relevance": 0.30,
    "engagement": 0.25,
    "confidence": 0.15,
}

# Composite weights (text + voice mode)
_WEIGHTS_TEXT_VOICE = {
    "clarity": 0.25,
    "relevance": 0.25,
    "engagement": 0.20,
    "confidence": 0.20,
    "fluency": 0.10,
}

# Composite weights (text + voice + face mode)
_WEIGHTS_TEXT_VOICE_FACE = {
    "clarity": 0.20,
    "relevance": 0.20,
    "engagement": 0.15,
    "confidence_voice": 0.20,
    "confidence_face": 0.15,
    "fluency": 0.10,
}


class HabitsService:
    """Central service orchestrating the Habits (interview) assessment pipeline.

    Phase 1 implements text-only analysis using deterministic spaCy-based scorers.
    Voice and face modalities will be added in subsequent phases.
    """

    def __init__(self) -> None:
        self.nlp: Language = self._load_spacy_model()
        self.clarity_scorer = ClarityScorer(self.nlp)
        self.relevance_scorer = RelevanceScorer(self.nlp)
        self.composite_scorer = CompositeScorer()
        self.interview_analyzer = InterviewAnalyzer()
        self.voice_analyzer = VoiceAnalyzer() if VoiceAnalyzer is not None else None
        self.face_analyzer = FaceAnalyzer() if FaceAnalyzer is not None else None
        if self.voice_analyzer is None and "_VOICE_ANALYZER_IMPORT_ERROR" in globals():
            logger.warning("VoiceAnalyzer unavailable; audio analysis will be disabled: %s", _VOICE_ANALYZER_IMPORT_ERROR)
        if self.face_analyzer is None and "_FACE_ANALYZER_IMPORT_ERROR" in globals():
            logger.warning("FaceAnalyzer unavailable; video analysis will be disabled: %s", _FACE_ANALYZER_IMPORT_ERROR)
        logger.info("HabitsService initialised (nlp=%s)", self.nlp.meta.get("name", "unknown"))

    # ── Public API ─────────────────────────────────────────────

    def analyze_interview(
        self,
        request: InterviewAnalysisRequest,
        assessment_id: str,
    ) -> InterviewAnalysisResponse:
        """Run the full interview analysis pipeline (text-only for Phase 1).

        Args:
            request: Validated ``InterviewAnalysisRequest`` with answers and
                optional audio/video payloads.
            assessment_id: Pre-generated assessment UUID (string).

        Returns:
            Fully populated ``InterviewAnalysisResponse``.
        """
        t0 = time.perf_counter()

        answers = request.answers
        answer_texts = [a.answer_text for a in answers]
        qa_pairs = [(a.question_text, a.answer_text) for a in answers]

        # ── 1. Clarity ─────────────────────────────────────
        clarity_score = self.clarity_scorer.score_answers(answer_texts)

        # ── 2. Relevance ───────────────────────────────────
        relevance_score = self.relevance_scorer.score_answers(qa_pairs)

        # ── 3. Engagement ──────────────────────────────────
        engagement_score = self._engagement_score(answer_texts)

        voice_metrics: Optional[VoiceMetrics] = None
        fluency_score: Optional[float] = None
        emotions_detected: List[EmotionMetric] = []
        face_stress_indicator = 0.0
        voice_confidence_score: Optional[float] = None
        face_confidence_score: Optional[float] = None

        # ── 4. Confidence (textual) ────────────────────────
        text_confidence_score = self._text_confidence_score(answer_texts)

        # ── 5. Optional voice analysis ─────────────────────
        if request.audio_base64 and self.voice_analyzer is not None:
            voice_raw = self.voice_analyzer.analyze_audio(request.audio_base64)
            voice_metrics = VoiceMetrics(**voice_raw)
            fluency_score = float(voice_metrics.fluency_score)
            voice_confidence_score = self._combined_confidence_score(
                text_confidence_score=text_confidence_score,
                voice_metrics=voice_metrics,
            )
        
        # ── 6. Optional face analysis ──────────────────────
        if request.video_frames_base64 and len(request.video_frames_base64) > 0 and self.face_analyzer is not None:
            face_raw = self.face_analyzer.analyze_video_frames(request.video_frames_base64)
            emotions_detected = [EmotionMetric(**emotion) for emotion in face_raw]
            face_stress_indicator = self._face_stress_indicator(emotions_detected)
            face_confidence_score = self._face_confidence_score(emotions_detected)

        # ── 7. Confidence and composite selection ──────────
        if voice_confidence_score is not None and face_confidence_score is not None:
            confidence_score = self._combined_multimodal_confidence_score(
                text_confidence_score=text_confidence_score,
                confidence_voice=voice_confidence_score,
                confidence_face=face_confidence_score,
            )
        elif voice_confidence_score is not None:
            confidence_score = voice_confidence_score
        else:
            confidence_score = text_confidence_score

        modalities_used = ["text"]
        if request.audio_base64:
            modalities_used.append("voice")
        if request.video_frames_base64:
            modalities_used.append("face")

        face_confidence_for_composite = face_confidence_score if "face" in modalities_used else None
        composite, score_breakdown = self.composite_scorer.compute_score(
            clarity_score=clarity_score,
            relevance_score=relevance_score,
            engagement_score=engagement_score,
            confidence_score=voice_confidence_score if voice_confidence_score is not None else text_confidence_score,
            fluency_score=fluency_score,
            face_confidence_score=face_confidence_for_composite,
            modalities_used=modalities_used,
            industry=request.industry,
        )
        if face_confidence_score is not None:
            score_breakdown["face_stress"] = round(face_stress_indicator * 100.0, 1)

        # Preserve response confidence as a multimodal health signal.
        confidence_score = max(0.0, min(100.0, confidence_score))

        # ── 8. Strengths / weaknesses ──────────────────────
        strengths, improvement_areas = self._generate_insights(
            clarity_score,
            relevance_score,
            engagement_score,
            confidence_score,
            voice_metrics,
            emotions_detected,
        )

        # ── 9. Behavioral profile ───────────────────────────
        behavioral_profile = self._generate_behavioral_profile(
            answer_texts=answer_texts,
            voice_metrics=voice_metrics,
            emotions_detected=emotions_detected,
            industry=request.industry,
        )

        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        return InterviewAnalysisResponse(
            assessment_id=assessment_id,
            status="completed",
            clarity_score=round(clarity_score, 1),
            relevance_score=round(relevance_score, 1),
            confidence_score=round(confidence_score, 1),
            engagement_score=round(engagement_score, 1),
            emotions_detected=emotions_detected,
            voice_metrics=voice_metrics,
            composite_score=round(composite, 1),
            score_breakdown=score_breakdown,
            strengths=strengths,
            improvement_areas=improvement_areas,
            behavioral_profile=behavioral_profile,
            processing_time_ms=round(elapsed_ms, 1),
            modalities_used=modalities_used,
            created_at=datetime.utcnow(),
        )

    def _generate_behavioral_profile(
        self,
        *,
        answer_texts: List[str],
        voice_metrics: Optional[VoiceMetrics] = None,
        emotions_detected: Optional[List[EmotionMetric]] = None,
        industry: Optional[str] = None,
    ) -> BehavioralProfile:
        """Delegate deep behavioral profiling to the LLM-backed analyzer."""
        return self.interview_analyzer.analyze_behavioral_profile(
            answer_texts=answer_texts,
            voice_metrics=voice_metrics,
            emotions_detected=emotions_detected,
            industry=industry,
        )

    # ── Engagement score ────────────────────────────────────────

    def _engagement_score(self, texts: List[str]) -> float:
        """Heuristic engagement score.

        60% — length factor: answers approaching the optimal 150-word target
              score higher.  Both too-short and too-long answers are penalised.
        40% — action-verb density: proportion of action-verb lemmas relative
              to total content tokens.
        """
        if not texts:
            return 0.0

        total_score = 0.0
        for text in texts:
            doc = self.nlp(text)
            tokens = [t for t in doc if not t.is_space and not t.is_punct]
            word_count = len(tokens)

            # Length factor — bell curve centred on _OPTIMAL_ANSWER_LENGTH.
            if word_count == 0:
                length_factor = 0.0
            else:
                ratio = word_count / _OPTIMAL_ANSWER_LENGTH
                # Gaussian-like: 1.0 at ratio=1, 0.5 at ratio=0.5 or 2.0.
                length_factor = max(0.0, 1.0 - abs(ratio - 1.0) * 0.6)

            # Action-verb density.
            content_tokens = [
                t for t in tokens
                if t.pos_ in ("NOUN", "VERB", "ADJ") and not t.is_stop
            ]
            action_verbs = sum(
                1 for t in tokens
                if t.pos_ == "VERB" and t.lemma_.lower() in _ACTION_VERB_LEMMAS
            )
            verb_density = (
                action_verbs / max(1, len(content_tokens))
                if content_tokens
                else 0.0
            )
            # Cap verb_density at 0.3 → 100%.
            verb_factor = min(1.0, verb_density / 0.3)

            total_score += (length_factor * 0.6 + verb_factor * 0.4) * 100.0

        return total_score / len(texts)

    # ── Confidence score (textual) ──────────────────────────────

    def _text_confidence_score(self, texts: List[str]) -> float:
        """Textual confidence score.

        Starts at 100 and is penalised proportionally to the density of
        hedging / uncertainty markers (modalisateurs de doute).
        """
        if not texts:
            return 0.0

        total_score = 0.0
        for text in texts:
            doc = self.nlp(text)
            tokens = [t for t in doc if not t.is_space and not t.is_punct]
            if not tokens:
                total_score += 0.0
                continue

            # Count hedging tokens (check both lemma and lowercased text).
            hedge_count = 0
            for t in tokens:
                lemma_lower = t.lemma_.lower()
                text_lower = t.text.lower()
                if lemma_lower in _HEDGING_WORDS or text_lower in _HEDGING_WORDS:
                    hedge_count += 1

            # Penalty: each hedge word reduces score by 8 points, capped at 60 total.
            penalty = min(60.0, hedge_count * 8.0)
            total_score += 100.0 - penalty

        return max(0.0, min(100.0, total_score / len(texts)))

    # ── Insights derivation ─────────────────────────────────────

    @staticmethod
    def _generate_insights(
        clarity: float,
        relevance: float,
        engagement: float,
        confidence: float,
        voice_metrics: Optional[VoiceMetrics] = None,
        emotions_detected: Optional[List[EmotionMetric]] = None,
    ) -> Tuple[List[str], List[str]]:
        """Derive strengths and improvement areas from dimension scores."""
        strengths: List[str] = []
        improvements: List[str] = []

        if clarity >= 70:
            strengths.append("Structure claire et vocabulaire riche dans les réponses")
        elif clarity < 45:
            improvements.append("Améliorer la clarté: structurer les réponses en phrases de 12-28 mots")

        if relevance >= 60:
            strengths.append("Réponses bien alignées avec les questions posées")
        elif relevance < 40:
            improvements.append("Mieux cibler la réponse par rapport à la question posée")

        if engagement >= 65:
            strengths.append("Bon niveau d'engagement avec des exemples concrets et verbes d'action")
        elif engagement < 40:
            improvements.append("Enrichir les réponses avec plus d'exemples et de verbes d'action (~150 mots idéalement)")

        if confidence >= 70:
            strengths.append("Ton assuré et affirmé, peu de modalisateurs de doute")
        elif confidence < 50:
            improvements.append("Réduire les expressions de doute (peut-être, je pense, probablement)")

        if voice_metrics is not None:
            if voice_metrics.speech_rate > 155:
                improvements.append("Le débit semble un peu trop rapide : ralentir pour gagner en clarté")
            elif 0 < voice_metrics.speech_rate < 110:
                improvements.append("Le débit semble lent : viser un rythme plus naturel (120-150 mots/min)")
            else:
                strengths.append("Débit vocal dans une zone fluide et naturelle")

            if voice_metrics.pitch_variation < 20:
                improvements.append("Le ton paraît monotone : varier davantage l'intonation")
            elif voice_metrics.pitch_variation >= 35:
                strengths.append("Bonne variation d'intonation, rendant la prise de parole plus dynamique")

            if voice_metrics.volume_db < -30:
                improvements.append("La voix semble trop basse : projeter davantage la voix")
            elif voice_metrics.volume_db > -10:
                improvements.append("Le volume semble élevé : parler un peu moins fort pour plus de confort")

        if emotions_detected:
            dominant = max(emotions_detected, key=lambda e: e.confidence).emotion.lower()
            if dominant in {"happy", "neutral"}:
                strengths.append("Gestion émotionnelle stable face à la caméra")
            elif dominant == "fear":
                improvements.append("Le visage montre des signes de stress : respirer et relâcher les tensions")
            elif dominant in {"sad", "disgust"}:
                improvements.append("L'expression faciale suggère un inconfort : adopter une posture plus ouverte")

        if not strengths:
            strengths.append("Réponses fournies et complétées")
        if not improvements:
            improvements.append("Continuer à affiner la précision et la profondeur des réponses")

        return strengths, improvements

    def _combined_confidence_score(self, text_confidence_score: float, voice_metrics: VoiceMetrics) -> float:
        """Combine textual confidence with voice prosody indicators."""
        pitch_component = self._pitch_confidence_component(voice_metrics.pitch_variation)
        volume_component = self._volume_confidence_component(voice_metrics.volume_db)
        voice_confidence = (pitch_component * 0.5) + (volume_component * 0.5)
        return max(0.0, min(100.0, (text_confidence_score * 0.7) + (voice_confidence * 0.3)))

    def _combined_multimodal_confidence_score(
        self,
        text_confidence_score: float,
        confidence_voice: float,
        confidence_face: float,
    ) -> float:
        """Combine text, voice and face confidence into a single score."""
        face_weight = 0.35
        voice_weight = 0.35
        text_weight = 0.30
        return max(
            0.0,
            min(
                100.0,
                (text_confidence_score * text_weight)
                + (confidence_voice * voice_weight)
                + (confidence_face * face_weight),
            ),
        )

    @staticmethod
    def _face_stress_indicator(emotions_detected: List[EmotionMetric]) -> float:
        """Compute a 0-1 stress indicator from facial emotions."""
        if not emotions_detected:
            return 0.0
        dominant = max(emotions_detected, key=lambda e: e.confidence).emotion.lower()
        if dominant == "fear":
            return 1.0
        if dominant in {"sad", "disgust"}:
            return 0.8
        if dominant in {"angry"}:
            return 0.7
        if dominant in {"neutral", "happy"}:
            return 0.1
        return 0.3

    @staticmethod
    def _face_confidence_score(emotions_detected: List[EmotionMetric]) -> float:
        """Convert facial emotion stability into a confidence score."""
        if not emotions_detected:
            return 0.0
        dominant = max(emotions_detected, key=lambda e: e.confidence).emotion.lower()
        stress = HabitsService._face_stress_indicator(emotions_detected)
        if dominant in {"happy", "neutral"}:
            base = 90.0
        elif dominant in {"surprise"}:
            base = 75.0
        elif dominant in {"angry", "sad", "disgust", "fear"}:
            base = 55.0
        else:
            base = 65.0
        return max(0.0, min(100.0, base * (1.0 - (stress * 0.5))))

    @staticmethod
    def _compute_composite_score(
        clarity_score: float,
        relevance_score: float,
        engagement_score: float,
        confidence_score: float,
        fluency_score: Optional[float],
        emotions_detected: List[EmotionMetric],
        confidence_weights: Dict[str, float],
    ) -> float:
        """Compute the final composite score for text, voice, or text+voice+face."""
        base = (
            clarity_score * confidence_weights["clarity"]
            + relevance_score * confidence_weights["relevance"]
            + engagement_score * confidence_weights["engagement"]
        )

        if "confidence_voice" in confidence_weights:
            if "confidence_face" in confidence_weights and emotions_detected:
                # In full multimodal mode, the passed confidence_score already fuses
                # text/voice/face internally. We distribute it using the final table
                # and add fluency separately.
                base += confidence_score * confidence_weights["confidence_voice"]
                face_conf = HabitsService._face_confidence_score(emotions_detected)
                base += face_conf * confidence_weights["confidence_face"]
            else:
                base += confidence_score * confidence_weights["confidence_voice"]

        elif "confidence" in confidence_weights:
            base += confidence_score * confidence_weights["confidence"]

        if fluency_score is not None:
            base += fluency_score * confidence_weights.get("fluency", 0.0)

        return base

    @staticmethod
    def _pitch_confidence_component(pitch_variation: float) -> float:
        """Score pitch variation: moderate variation is best."""
        if pitch_variation <= 0:
            return 0.0
        if pitch_variation < 15:
            return max(0.0, (pitch_variation / 15.0) * 40.0)
        if pitch_variation <= 35:
            return 100.0
        if pitch_variation <= 60:
            return max(70.0, 100.0 - ((pitch_variation - 35.0) / 25.0) * 20.0)
        return max(0.0, 80.0 - ((pitch_variation - 60.0) / 60.0) * 80.0)

    @staticmethod
    def _volume_confidence_component(volume_db: float) -> float:
        """Score volume: comfortable speaking volume is around -20 dB."""
        target = -20.0
        distance = abs(volume_db - target)
        if distance >= 25:
            return 20.0
        return max(20.0, 100.0 - distance * 4.0)

    # ── Behavioral profile derivation ───────────────────────────

    @staticmethod
    def _derive_behavioral_profile(
        clarity: float,
        relevance: float,
        engagement: float,
        confidence: float,
        composite: float,
        emotions_detected: Optional[List[EmotionMetric]] = None,
    ) -> BehavioralProfile:
        """Derive a synthetic behavioral profile from dimension scores."""

        # Communication style: based on clarity + engagement.
        if clarity >= 70 and engagement >= 60:
            comm_style = "structured"
        elif clarity >= 55 and engagement >= 50:
            comm_style = "analytical"
        elif engagement >= 60:
            comm_style = "spontaneous"
        else:
            comm_style = "narrative"

        # Motivation level: based on engagement + confidence.
        if engagement >= 65 and confidence >= 60:
            motivation = "high"
        elif engagement >= 40:
            motivation = "medium"
        else:
            motivation = "low"

        # Self-awareness: based on relevance + clarity (ability to address
        # the question precisely shows self-awareness).
        if relevance >= 55 and clarity >= 55:
            self_awareness = "high"
        elif relevance >= 35:
            self_awareness = "medium"
        else:
            self_awareness = "low"

        # Stress indicators: inverse of confidence.
        if confidence >= 70:
            stress = "low"
        elif confidence >= 45:
            stress = "moderate"
        else:
            stress = "high"

        if emotions_detected:
            dominant = max(emotions_detected, key=lambda e: e.confidence).emotion.lower()
            if dominant in {"happy", "neutral"}:
                stress = "low" if stress != "high" else "moderate"
            elif dominant == "fear":
                stress = "high"
            elif dominant in {"sad", "disgust"} and stress != "high":
                stress = "moderate"

        # Overall recommendation: based on composite score.
        if composite >= 65:
            recommendation = "recommended"
        elif composite >= 45:
            recommendation = "borderline"
        else:
            recommendation = "not_recommended"

        return BehavioralProfile(
            communication_style=comm_style,
            motivation_level=motivation,
            self_awareness=self_awareness,
            stress_indicators=stress,
            overall_recommendation=recommendation,
        )

    # ── spaCy model loading ─────────────────────────────────────

    @staticmethod
    def _load_spacy_model() -> Language:
        """Load a spaCy model with a safe fallback chain.

        Tries (in order):
          1. ``en_core_web_sm``  (user-requested default)
          2. ``fr_core_news_md`` (installed in Docker, has vectors)
          3. ``spacy.blank("en")`` (last resort, no vectors)
        """
        for model_name in ("en_core_web_sm", "fr_core_news_md"):
            try:
                nlp = spacy.load(model_name)
                if "sentencizer" not in nlp.pipe_names and "parser" not in nlp.pipe_names:
                    nlp.add_pipe("sentencizer")
                logger.info("Loaded spaCy model: %s", model_name)
                return nlp
            except OSError:
                logger.debug("spaCy model '%s' not found, trying next", model_name)

        logger.warning("No spaCy model found, falling back to blank('en')")
        nlp = spacy.blank("en")
        if "sentencizer" not in nlp.pipe_names:
            nlp.add_pipe("sentencizer")
        return nlp
