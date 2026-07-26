"""Attitude scoring — mindset, comportment, stress management evaluation.

Score composition:
  - 30% Text signals: keyword-based behavioral signal detection
  - 25% Clarity: how well-structured the response is (spaCy)
  - 20% Emotional indicators: sentiment + stress markers in text
  - 15% Confidence: lexical certainty + assertiveness
  - 10% Response richness: vocabulary diversity

When multimodal data is available (video frames, audio):
  - Face emotion analysis contributes to emotional_regulation score
  - Voice pitch/volume contributes to stress_resistance score
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from src.core.logging import get_logger
from src.modules.attitude.questions import SIGNAL_KEYWORDS, CATEGORY_WEIGHTS

logger = get_logger(__name__)


@dataclass
class AttitudeDimensionScore:
    """Score for one attitude dimension."""
    name: str
    score: float
    signals_detected: List[str]
    evidence: str


@dataclass
class AttitudeProfile:
    """Complete attitude assessment profile."""
    stress_resistance: float
    emotional_regulation: float
    adaptability: float
    communication_style: str
    self_awareness: float
    motivation_level: str
    decision_making_style: str
    overall_attitude_score: float
    dimension_scores: Dict[str, float]
    strengths: List[str]
    improvement_areas: List[str]
    recommendation: str


class AttitudeScorer:
    """Scores attitude dimensions from interview responses."""

    STRESS_MARKERS = [
        "stress", "anxious", "nervous", "worried", "panic", "overwhelmed",
        "pressure", "tense", "afraid", "scared", "difficult", "hard",
        "stresse", "anxieux", "nerveux", "inquiet", "peur", "difficile",
    ]

    POSITIVE_COPING = [
        "calm", "relax", "breathe", "focus", "plan", "organize", "manage",
        "control", "confident", "ready", "prepare", "handle", "deal",
        "calme", "repos", "respirer", "concentre", "plan", "organise",
        "controle", "confiant", "pret", "prepare", "gere",
    ]

    ASSERTIVENESS_MARKERS = [
        "i decided", "i chose", "i believe", "i think", "i'm confident",
        "i'm sure", "certain", "definitely", "absolutely", "clearly",
        "j'ai decide", "je crois", "je pense", "je suis sur", "certain",
    ]

    def __init__(self, nlp=None):
        self.nlp = nlp

    def score_response(
        self,
        question_category: str,
        question_text: str,
        answer_text: str,
        expected_signals: List[str],
    ) -> Tuple[float, List[str], str]:
        """Score a single interview response.

        Returns:
            (score 0-100, signals_detected, evidence_text)
        """
        if not answer_text or not answer_text.strip():
            return 0.0, [], "No response provided"

        text_lower = answer_text.lower()
        signals_found = []

        for signal in expected_signals:
            keywords = SIGNAL_KEYWORDS.get(signal, [])
            if any(kw in text_lower for kw in keywords):
                signals_found.append(signal)

        signal_score = min(len(signals_found) / max(len(expected_signals), 1), 1.0) * 100

        stress_count = sum(1 for m in self.STRESS_MARKERS if m in text_lower)
        coping_count = sum(1 for m in self.POSITIVE_COPING if m in text_lower)
        if question_category == "stress_management":
            if stress_count > 0:
                coping_ratio = coping_count / max(stress_count, 1)
                stress_score = min(coping_ratio * 80 + 20, 100)
            else:
                stress_score = 60.0
        else:
            stress_score = 70.0

        assertive_count = sum(1 for m in self.ASSERTIVENESS_MARKERS if m in text_lower)
        confidence_score = min(assertive_count * 15 + 40, 100)

        word_count = len(answer_text.split())
        richness_score = min(word_count / 80 * 100, 100) if word_count > 0 else 0

        clarity_score = self._compute_clarity(answer_text)

        final = (
            signal_score * 0.30 +
            clarity_score * 0.25 +
            stress_score * 0.20 +
            confidence_score * 0.15 +
            richness_score * 0.10
        )
        final = max(0.0, min(100.0, final))

        evidence = f"Signals: {', '.join(signals_found) if signals_found else 'none'} | Stress markers: {stress_count} | Coping: {coping_count} | Assertive: {assertive_count} | Words: {word_count}"
        logger.debug("AttitudeScorer: category=%s score=%.1f signals=%s", question_category, final, signals_found)
        return final, signals_found, evidence

    def compute_profile(
        self,
        responses: List[Dict],
        face_emotions: Optional[List[Dict]] = None,
        voice_metrics: Optional[Dict] = None,
    ) -> AttitudeProfile:
        """Compute complete attitude profile from all responses.

        Args:
            responses: List of {category, question_text, answer_text, expected_signals}
            face_emotions: Optional list of emotion detections from video frames
            voice_metrics: Optional dict with pitch_variation, volume_db, speech_rate
        """
        category_scores: Dict[str, List[float]] = {}
        all_signals: List[str] = []
        all_evidence: List[str] = []

        for resp in responses:
            score, signals, evidence = self.score_response(
                resp.get("category", "general"),
                resp.get("question_text", ""),
                resp.get("answer_text", ""),
                resp.get("expected_signals", []),
            )
            cat = resp.get("category", "general")
            if cat not in category_scores:
                category_scores[cat] = []
            category_scores[cat].append(score)
            all_signals.extend(signals)
            all_evidence.append(evidence)

        category_averages: Dict[str, float] = {}
        for cat, scores in category_scores.items():
            category_averages[cat] = sum(scores) / len(scores)

        overall = 0.0
        for cat, avg in category_averages.items():
            weight = CATEGORY_WEIGHTS.get(cat, 0.1)
            overall += avg * weight

        if face_emotions:
            face_score = self._score_face_emotions(face_emotions)
            overall = overall * 0.75 + face_score * 0.25
        else:
            face_score = None

        if voice_metrics:
            voice_score = self._score_voice_stress(voice_metrics)
            overall = overall * 0.85 + voice_score * 0.15
        else:
            voice_score = None

        overall = max(0.0, min(100.0, overall))

        stress_resistance = category_averages.get("stress_management", 50)
        emotional_regulation = self._compute_emotional_regulation(category_averages, face_emotions)
        adaptability = category_averages.get("adaptability", 50)
        self_awareness = category_averages.get("resilience", 50)

        comm_style = self._derive_comm_style(overall, all_signals)
        motivation_level = self._derive_motivation(category_averages.get("motivation", 50))
        decision_style = self._derive_decision_style(category_averages.get("decision_making", 50))
        strengths, improvements = self._derive_strengths_improvements(category_averages)
        recommendation = "recommended" if overall >= 65 else ("borderline" if overall >= 45 else "not_recommended")

        return AttitudeProfile(
            stress_resistance=round(stress_resistance, 1),
            emotional_regulation=round(emotional_regulation, 1),
            adaptability=round(adaptability, 1),
            communication_style=comm_style,
            self_awareness=round(self_awareness, 1),
            motivation_level=motivation_level,
            decision_making_style=decision_style,
            overall_attitude_score=round(overall, 1),
            dimension_scores={k: round(v, 1) for k, v in category_averages.items()},
            strengths=strengths,
            improvement_areas=improvements,
            recommendation=recommendation,
        )

    def _compute_clarity(self, text: str) -> float:
        """Simple clarity heuristic: sentence length + word diversity."""
        words = text.split()
        if not words:
            return 0.0
        unique_ratio = len(set(w.lower() for w in words)) / len(words)
        word_count = len(words)
        if word_count < 15:
            length_score = word_count / 15 * 50
        elif word_count <= 100:
            length_score = 50 + (word_count - 15) / 85 * 50
        else:
            length_score = 100
        return min(unique_ratio * 60 + length_score * 0.4, 100)

    def _score_face_emotions(self, emotions: List[Dict]) -> float:
        """Score emotional regulation from face emotion detections."""
        if not emotions:
            return 50.0
        positive = 0
        negative = 0
        for emo in emotions:
            emotion = emo.get("emotion", "").lower()
            conf = emo.get("confidence", 0)
            if emotion in ("happy", "neutral", "surprise"):
                positive += conf
            elif emotion in ("fear", "angry", "sad", "disgust"):
                negative += conf
        total = positive + negative
        if total == 0:
            return 50.0
        return (positive / total) * 100

    def _score_voice_stress(self, metrics: Dict) -> float:
        """Score stress resistance from voice metrics."""
        pitch_var = metrics.get("pitch_variation", 20)
        volume = metrics.get("volume_db", -20)
        speech_rate = metrics.get("speech_rate", 150)

        pitch_score = 100 if 15 <= pitch_var <= 35 else max(0, 100 - abs(pitch_var - 25) * 2)
        volume_score = max(20, 100 - abs(volume - (-20)) * 4)
        rate_score = 100 if 120 <= speech_rate <= 180 else max(30, 100 - abs(speech_rate - 150) * 0.5)

        return (pitch_score + volume_score + rate_score) / 3

    def _compute_emotional_regulation(
        self, category_scores: Dict[str, float], face_emotions: Optional[List[Dict]]
    ) -> float:
        base = (category_scores.get("stress_management", 50) + category_scores.get("resilience", 50)) / 2
        if face_emotions:
            face = self._score_face_emotions(face_emotions)
            return base * 0.6 + face * 0.4
        return base

    def _derive_comm_style(self, overall: float, signals: List[str]) -> str:
        if "empathy" in signals and "communication" in signals:
            return "collaborative"
        elif "analytical_thinking" in signals:
            return "analytical"
        elif "assertiveness" in signals or any("decis" in s for s in signals):
            return "assertive"
        elif overall >= 60:
            return "balanced"
        return "reserved"

    def _derive_motivation(self, motivation_score: float) -> str:
        if motivation_score >= 65:
            return "high"
        elif motivation_score >= 40:
            return "medium"
        return "low"

    def _derive_decision_style(self, decision_score: float) -> str:
        if decision_score >= 70:
            return "decisive_analytical"
        elif decision_score >= 50:
            return "collaborative"
        elif decision_score >= 30:
            return "cautious"
        return "hesitant"

    def _derive_strengths_improvements(
        self, category_scores: Dict[str, float]
    ) -> Tuple[List[str], List[str]]:
        sorted_cats = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
        strengths = [f"Strong {cat.replace('_', ' ')} ({score:.1f}/100)" for cat, score in sorted_cats[:2] if score >= 60]
        improvements = [f"Improve {cat.replace('_', ' ')} ({score:.1f}/100)" for cat, score in sorted_cats[-2:] if score < 55]
        return strengths, improvements
