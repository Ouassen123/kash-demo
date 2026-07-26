"""Psychometric scoring engine for Habits (H) assessment.

Scores Big Five, Grit, and Self-Discipline dimensions from Likert-scale responses.
Produces a comprehensive habits profile with discipline level, routine strength,
and habit recommendations.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from src.core.logging import get_logger
from src.modules.habits.psychometric.questions import (
    PSYCHOMETRIC_QUESTIONS,
    DIMENSION_DESCRIPTIONS,
    DIMENSION_WEIGHTS,
)

logger = get_logger(__name__)


@dataclass
class HabitsDimensionScore:
    """Score for one psychometric dimension."""
    dimension: str
    label: str
    raw_score: float
    normalized_score: float
    subscale_scores: Dict[str, float]
    interpretation: str


@dataclass
class HabitsProfile:
    """Complete habits assessment profile."""
    overall_habits_score: float
    discipline_level: str
    routine_strength: float
    perseverance_score: float
    stress_management_capacity: float
    learning_openness: float
    social_engagement: str
    dimension_scores: Dict[str, float]
    strengths: List[str]
    improvement_areas: List[str]
    habit_recommendations: List[str]
    recommendation: str


class PsychometricScorer:
    """Scores psychometric questionnaire responses."""

    LIKERT_MIN = 1
    LIKERT_MAX = 5

    def score_questionnaire(
        self,
        responses: List[Dict[str, any]],
    ) -> HabitsProfile:
        """Score complete psychometric questionnaire.

        Args:
            responses: List of {question_id, answer (1-5)}

        Returns:
            HabitsProfile with all dimension scores and recommendations
        """
        response_map = {r["question_id"]: r.get("answer", 3) for r in responses}

        dimension_raw: Dict[str, List[Tuple[str, float]]] = {}
        for q in PSYCHOMETRIC_QUESTIONS:
            qid = q["id"]
            answer = response_map.get(qid, 3)
            answer = max(self.LIKERT_MIN, min(self.LIKERT_MAX, int(answer)))

            if q["reverse"]:
                score = self.LIKERT_MAX + 1 - answer
            else:
                score = answer

            dim = q["dimension"]
            subscale = q["subscale"]
            if dim not in dimension_raw:
                dimension_raw[dim] = []
            dimension_raw[dim].append((subscale, float(score)))

        dimension_scores: Dict[str, HabitsDimensionScore] = {}
        for dim, subscale_list in dimension_raw.items():
            all_scores = [s for _, s in subscale_list]
            raw_avg = sum(all_scores) / len(all_scores) if all_scores else 0
            normalized = (raw_avg - 1) / (self.LIKERT_MAX - 1) * 100

            subscale_map: Dict[str, List[float]] = {}
            for sub, sc in subscale_list:
                if sub not in subscale_map:
                    subscale_map[sub] = []
                subscale_map[sub].append(sc)

            subscale_avg = {k: sum(v) / len(v) for k, v in subscale_map.items()}

            desc = DIMENSION_DESCRIPTIONS.get(dim, {})
            interpretation = desc.get("high", "") if normalized >= 65 else desc.get("low", "")

            dimension_scores[dim] = HabitsDimensionScore(
                dimension=dim,
                label=desc.get("label", dim),
                raw_score=round(raw_avg, 2),
                normalized_score=round(normalized, 1),
                subscale_scores={k: round(v, 2) for k, v in subscale_avg.items()},
                interpretation=interpretation,
            )

        overall = sum(
            ds.normalized_score * DIMENSION_WEIGHTS.get(dim, 0)
            for dim, ds in dimension_scores.items()
        )
        overall = max(0.0, min(100.0, overall))

        discipline_level = self._derive_discipline_level(overall)
        routine_strength = dimension_scores.get("self_discipline", dimension_scores.get("conscientiousness")).normalized_score if dimension_scores else 50
        perseverance = dimension_scores.get("grit", dimension_scores.get("conscientiousness")).normalized_score if dimension_scores else 50
        stress_mgmt = dimension_scores.get("neuroticism").normalized_score if "neuroticism" in dimension_scores else 50
        openness = dimension_scores.get("openness").normalized_score if "openness" in dimension_scores else 50
        extraversion = dimension_scores.get("extraversion").normalized_score if "extraversion" in dimension_scores else 50

        social_engagement = "high" if extraversion >= 65 else ("medium" if extraversion >= 40 else "low")

        strengths, improvements = self._derive_strengths_improvements(dimension_scores)
        recommendations = self._generate_recommendations(dimension_scores)
        recommendation = "recommended" if overall >= 65 else ("borderline" if overall >= 45 else "needs_support")

        return HabitsProfile(
            overall_habits_score=round(overall, 1),
            discipline_level=discipline_level,
            routine_strength=round(routine_strength, 1),
            perseverance_score=round(perseverance, 1),
            stress_management_capacity=round(stress_mgmt, 1),
            learning_openness=round(openness, 1),
            social_engagement=social_engagement,
            dimension_scores={dim: ds.normalized_score for dim, ds in dimension_scores.items()},
            strengths=strengths,
            improvement_areas=improvements,
            habit_recommendations=recommendations,
            recommendation=recommendation,
        )

    def _derive_discipline_level(self, overall: float) -> str:
        if overall >= 80:
            return "excellent"
        elif overall >= 65:
            return "strong"
        elif overall >= 50:
            return "moderate"
        elif overall >= 35:
            return "developing"
        return "weak"

    def _derive_strengths_improvements(
        self, dimension_scores: Dict[str, HabitsDimensionScore]
    ) -> Tuple[List[str], List[str]]:
        sorted_dims = sorted(
            dimension_scores.items(),
            key=lambda x: x[1].normalized_score,
            reverse=True,
        )
        strengths = []
        for dim, ds in sorted_dims[:3]:
            if ds.normalized_score >= 65:
                strengths.append(f"{ds.label} ({ds.normalized_score:.0f}/100)")

        improvements = []
        for dim, ds in sorted_dims[-3:]:
            if ds.normalized_score < 55:
                improvements.append(f"{ds.label} ({ds.normalized_score:.0f}/100)")

        return strengths, improvements

    def _generate_recommendations(
        self, dimension_scores: Dict[str, HabitsDimensionScore]
    ) -> List[str]:
        recommendations = []

        consc = dimension_scores.get("conscientiousness")
        if consc and consc.normalized_score < 55:
            recommendations.append("Mettre en place un système de planification hebdomadaire (todo list, calendrier)")
            recommendations.append("Utiliser la méthode Pomodoro pour structurer les sessions de travail")

        grit = dimension_scores.get("grit")
        if grit and grit.normalized_score < 55:
            recommendations.append("Définir un objectif à long terme et le décomposer en étapes mensuelles")
            recommendations.append("Tenir un journal de progression pour visualiser les avancées")

        neuro = dimension_scores.get("neuroticism")
        if neuro and neuro.normalized_score < 55:
            recommendations.append("Pratiquer des exercices de respiration ou méditation 10 min/jour")
            recommendations.append("Identifier les déclencheurs de stress et préparer des stratégies de coping")

        disc = dimension_scores.get("self_discipline")
        if disc and disc.normalized_score < 55:
            recommendations.append("Créer une routine matinale fixe (réveil, exercice, planification)")
            recommendations.append("Utiliser un blocker d'applications pendant les sessions de travail")

        open_ = dimension_scores.get("openness")
        if open_ and open_.normalized_score < 50:
            recommendations.append("Lire un article ou regarder une conférence sur un nouveau sujet chaque semaine")

        if not recommendations:
            recommendations.append("Maintenir les bonnes habitudes actuelles et viser l'excellence continue")

        return recommendations[:6]
