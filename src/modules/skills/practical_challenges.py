"""Domain-adaptive practical challenges for Skills (S) assessment.

Each challenge is tailored to a specific domain detected from the CV analysis:
- programming: coding exercises (existing)
- electrical: circuit analysis, PLC logic
- mechanical: design problems, material selection
- quality: ISO compliance, root cause analysis
- logistics: supply chain optimization
- management: project planning, resource allocation

Non-programming challenges use a Q&A format with expected answers that are
scored using semantic similarity and keyword matching.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any


@dataclass(frozen=True)
class PracticalTestCase:
    """A single test case for a practical challenge."""
    name: str
    question: str
    expected_answer: str
    keywords: List[str]
    min_score: float = 0.5


@dataclass(frozen=True)
class PracticalChallenge:
    """A domain-specific practical challenge."""
    id: str
    title: str
    domain: str
    statement: str
    difficulty: str
    estimated_time_minutes: int
    test_cases: List[PracticalTestCase]
    is_coding: bool
    coding_templates: Dict[str, str] = field(default_factory=dict)
    coding_tests: List[Any] = field(default_factory=list)
    supported_languages: List[str] = field(default_factory=list)


# ── Electrical challenges ──────────────────────────────────────

def _electrical_ohms_law_challenge() -> PracticalChallenge:
    return PracticalChallenge(
        id="elec-ohms-law-v1",
        title="Loi d'Ohm et Analyse de Circuit",
        domain="electrical",
        difficulty="easy",
        estimated_time_minutes=10,
        is_coding=False,
        statement=(
            "Un circuit comprend une source de tension de 12V connectée à deux résistances "
            "en série : R1 = 4Ω et R2 = 8Ω.\n\n"
            "Questions:\n"
            "1. Quelle est la résistance équivalente du circuit ?\n"
            "2. Quelle est l'intensité du courant qui traverse le circuit ?\n"
            "3. Quelle est la tension aux bornes de R2 ?\n"
            "4. Quelle est la puissance dissipée par R1 ?"
        ),
        test_cases=[
            PracticalTestCase(
                name="resistance_eq",
                question="Quelle est la résistance équivalente ?",
                expected_answer="La résistance équivalente est R1 + R2 = 4 + 8 = 12 ohms (Ω). En série, les résistances s'additionnent.",
                keywords=["12", "ohm", "série", "addition", "r1+r2"],
                min_score=0.4,
            ),
            PracticalTestCase(
                name="current",
                question="Quelle est l'intensité du courant ?",
                expected_answer="I = U / R = 12 / 12 = 1 ampère (A). Selon la loi d'Ohm, I = V/R.",
                keywords=["1", "ampère", "ampere", "u/r", "v/r", "loi", "ohm"],
                min_score=0.4,
            ),
            PracticalTestCase(
                name="voltage_r2",
                question="Quelle est la tension aux bornes de R2 ?",
                expected_answer="U_R2 = R2 × I = 8 × 1 = 8 volts (V). La tension aux bornes d'une résistance est U = R × I.",
                keywords=["8", "volt", "r*i", "r2*i", "r2×i"],
                min_score=0.4,
            ),
            PracticalTestCase(
                name="power_r1",
                question="Quelle est la puissance dissipée par R1 ?",
                expected_answer="P = R1 × I² = 4 × 1² = 4 watts (W). La puissance dissipée est P = R × I².",
                keywords=["4", "watt", "r*i²", "r1*i²", "puissance", "r*i*i"],
                min_score=0.4,
            ),
        ],
    )


def _electrical_plc_challenge() -> PracticalChallenge:
    return PracticalChallenge(
        id="elec-plc-logic-v1",
        title="Logique PLC — Contrôle de Moteur",
        domain="electrical",
        difficulty="medium",
        estimated_time_minutes=15,
        is_coding=False,
        statement=(
            "Un automate PLC contrôle un moteur avec les conditions suivantes:\n"
            "- Le moteur démarre quand le bouton START est pressé ET le capteur de sécurité est actif\n"
            "- Le moteur s'arrête quand le bouton STOP est pressé OU le capteur de température détecte une surchauffe\n"
            "- Un voyant vert s'allume quand le moteur tourne\n"
            "- Un voyant rouge s'allume en cas de surchauffe\n\n"
            "Questions:\n"
            "1. Écris l'équation booléenne pour la sortie MOTEUR\n"
            "2. Écris l'équation booléenne pour le voyant VERT\n"
            "3. Écris l'équation booléenne pour le voyant ROUGE\n"
            "4. Quel type de mémoire faut-il utiliser pour le bouton START ?"
        ),
        test_cases=[
            PracticalTestCase(
                name="motor_eq",
                question="Équation booléenne pour MOTEUR",
                expected_answer="Moteur = (START · Safety) + (Moteur · ¬STOP · ¬Overheat). Utilise un latch/mémoire SR pour maintenir l'état.",
                keywords=["start", "safety", "stop", "overheat", "latch", "mémoire", "memory", "·", "and", "or"],
                min_score=0.3,
            ),
            PracticalTestCase(
                name="green_light",
                question="Équation booléenne pour voyant VERT",
                expected_answer="Vert = Moteur (le voyant vert s'allume quand le moteur tourne)",
                keywords=["moteur", "motor", "=", "vert"],
                min_score=0.5,
            ),
            PracticalTestCase(
                name="red_light",
                question="Équation booléenne pour voyant ROUGE",
                expected_answer="Rouge = Overheat (le voyant rouge s'allume en cas de surchauffe)",
                keywords=["overheat", "surchauffe", "rouge", "="],
                min_score=0.5,
            ),
            PracticalTestCase(
                name="memory_type",
                question="Type de mémoire pour START",
                expected_answer="Il faut utiliser un bistable (SR flip-flop ou Set-Reset) car le bouton START est impulsionnel et le moteur doit continuer à tourner après le relâchement.",
                keywords=["bistable", "sr", "set", "reset", "flip-flop", "latch", "mémoire", "maintien"],
                min_score=0.3,
            ),
        ],
    )


# ── Mechanical challenges ──────────────────────────────────────

def _mechanical_material_challenge() -> PracticalChallenge:
    return PracticalChallenge(
        id="mech-material-selection-v1",
        title="Sélection de Matériau pour Structure",
        domain="mechanical",
        difficulty="medium",
        estimated_time_minutes=15,
        is_coding=False,
        statement=(
            "Tu dois concevoir un arbre de transmission pour un système industriel.\n"
            "Le couple transmis est de 500 Nm, la vitesse de rotation est de 1500 tr/min.\n"
            "L'arbre doit résister à la fatigue et travailler à 80°C en continu.\n\n"
            "Questions:\n"
            "1. Quels matériaux pourrais-tu envisager pour cet arbre ?\n"
            "2. Quel critère de résistance est le plus important ici ?\n"
            "3. Comment vérifier la résistance à la fatigue ?\n"
            "4. Quel traitement thermique recommanderais-tu ?"
        ),
        test_cases=[
            PracticalTestCase(
                name="materials",
                question="Quels matériaux envisager ?",
                expected_answer="Acier de traitement (42CrMo4, 30CrNiMo8), acier inoxydable pour corrosion. L'acier allié offre bonne résistance mécanique et fatigue.",
                keywords=["acier", "42crmo4", "30crnimo8", "alliage", "traitement", "inoxydable"],
                min_score=0.3,
            ),
            PracticalTestCase(
                name="criterion",
                question="Critère de résistance le plus important",
                expected_answer="La résistance à la fatigue (limite d'endurance) car l'arbre subit des charges cycliques. Le critère de Goodman ou Gerber peut être utilisé.",
                keywords=["fatigue", "endurance", "goodman", "gerber", "cyclique", "alternance"],
                min_score=0.3,
            ),
            PracticalTestCase(
                name="fatigue_check",
                question="Comment vérifier la résistance à la fatigue ?",
                expected_answer="Calculer la contrainte alternée (σa) et moyenne (σm), puis utiliser le diagramme de Goodman modifié: σa / σe + σm / σu ≤ 1/n, où σe est la limite d'endurance, σu la résistance ultime, n le coefficient de sécurité.",
                keywords=["goodman", "contrainte", "endurance", "sécurité", "alternée", "moyenne", "diagramme"],
                min_score=0.3,
            ),
            PracticalTestCase(
                name="heat_treatment",
                question="Traitement thermique recommandé",
                expected_answer="Trempe + revenu pour améliorer la résistance et la ténacité. Nitruration possible pour améliorer la résistance superficielle à la fatigue.",
                keywords=["trempe", "revenu", "nitruration", "ténacité", "surface", "durcissement"],
                min_score=0.3,
            ),
        ],
    )


# ── Quality challenges ─────────────────────────────────────────

def _quality_root_cause_challenge() -> PracticalChallenge:
    return PracticalChallenge(
        id="qual-root-cause-v1",
        title="Analyse de Cause Racine (Ishikawa)",
        domain="quality",
        difficulty="medium",
        estimated_time_minutes=15,
        is_coding=False,
        statement=(
            "Dans une usine de production, le taux de défauts sur une ligne d'assemblage "
            "est passé de 2% à 7% en deux semaines.\n\n"
            "Questions:\n"
            "1. Quelles sont les 5M de la méthode Ishikawa ?\n"
            "2. Comment procéder pour identifier la cause racine ?\n"
            "3. Quel outil statistique utiliser pour prioriser les causes ?\n"
            "4. Décris la démarche PDCA pour résoudre ce problème"
        ),
        test_cases=[
            PracticalTestCase(
                name="5m",
                question="Quelles sont les 5M ?",
                expected_answer="Méthodes, Matières, Machines, Main d'œuvre, Milieu. Parfois un 6e M est ajouté: Management.",
                keywords=["méthodes", "matières", "machines", "main", "milieu", "management"],
                min_score=0.4,
            ),
            PracticalTestCase(
                name="root_cause_method",
                question="Comment identifier la cause racine ?",
                expected_answer="Utiliser le diagramme Ishikawa (poisson) pour catégoriser les causes, puis les 5 Pourquoi (5 Whys) pour creuser jusqu'à la cause racine. Combiner avec un brainstorming d'équipe.",
                keywords=["ishikawa", "5 pourquoi", "5 whys", "brainstorming", "diagramme", "poisson"],
                min_score=0.3,
            ),
            PracticalTestCase(
                name="pareto",
                question="Outil statistique pour prioriser ?",
                expected_answer="Le diagramme de Pareto (80/20) permet de prioriser les causes: 80% des défauts proviennent de 20% des causes. On peut aussi utiliser une matrice de criticité.",
                keywords=["pareto", "80/20", "priorit", "criticité", "matrice"],
                min_score=0.4,
            ),
            PracticalTestCase(
                name="pdca",
                question="Démarche PDCA",
                expected_answer="Plan: analyser le problème et définir un plan d'action. Do: mettre en œuvre le plan. Check: vérifier les résultats et mesurer l'impact. Act: standardiser si efficace, sinon ajuster.",
                keywords=["plan", "do", "check", "act", "standardiser", "mesurer"],
                min_score=0.3,
            ),
        ],
    )


# ── Logistics challenges ───────────────────────────────────────

def _logistics_optimization_challenge() -> PracticalChallenge:
    return PracticalChallenge(
        id="logi-supply-chain-v1",
        title="Optimisation de Chaîne Logistique",
        domain="logistics",
        difficulty="medium",
        estimated_time_minutes=15,
        is_coding=False,
        statement=(
            "Une entreprise a 3 entrepôts (A, B, C) qui doivent livrer 4 clients (1, 2, 3, 4).\n"
            "Capacités: A=100, B=150, C=200 unités\n"
            "Demandes: 1=80, 2=120, 3=100, 4=150 unités\n"
            "Coûts de transport (dh/unité):\n"
            "  A→1:4, A→2:8, A→3:8, A→4:7\n"
            "  B→1:16, B→2:24, B→3:16, B→4:16\n"
            "  C→1:8, C→2:16, C→3:24, C→4:24\n\n"
            "Questions:\n"
            "1. Quelle méthode utiliser pour résoudre ce problème ?\n"
            "2. Quelle est la solution initiale avec la méthode du coin nord-ouest ?\n"
            "3. Comment optimiser la solution ?\n"
            "4. Quel est le coût total minimal approximatif ?"
        ),
        test_cases=[
            PracticalTestCase(
                name="method",
                question="Quelle méthode utiliser ?",
                expected_answer="La méthode de transport (programmation linéaire). On peut utiliser la méthode du coin nord-ouest pour une solution initiale, puis la méthode stepping-stone ou MODI pour optimiser.",
                keywords=["transport", "linéaire", "coin", "nord-ouest", "stepping", "stone", "modi", "optimis"],
                min_score=0.3,
            ),
            PracticalTestCase(
                name="initial_solution",
                question="Solution initiale (coin nord-ouest) ?",
                expected_answer="A→1:80, A→2:20, B→2:100, B→3:50, C→3:50, C→4:150. On remplit en partant du coin supérieur gauche.",
                keywords=["80", "20", "100", "50", "150", "nord-ouest", "a→1"],
                min_score=0.3,
            ),
            PracticalTestCase(
                name="optimize",
                question="Comment optimiser ?",
                expected_answer="Utiliser la méthode MODI (Modified Distribution) ou stepping-stone: calculer les coûts marginaux pour les cases non occupées et identifier les améliorations possibles en effectuant un cycle.",
                keywords=["modi", "stepping", "stone", "marginal", "cycle", "coût", "amélioration"],
                min_score=0.3,
            ),
            PracticalTestCase(
                name="min_cost",
                question="Coût total minimal approximatif ?",
                expected_answer="Le coût optimal est d'environ 5920 dh. Solution: A→1:80 (320), A→2:20 (160), B→3:100 (1600), C→2:100 (1600), C→4:100 (2400) — total variable selon la solution exacte.",
                keywords=["5920", "320", "160", "1600", "2400", "coût", "total"],
                min_score=0.2,
            ),
        ],
    )


# ── Management challenges ──────────────────────────────────────

def _management_project_challenge() -> PracticalChallenge:
    return PracticalChallenge(
        id="mgmt-project-planning-v1",
        title="Planification de Projet — Diagramme de Gantt",
        domain="management",
        difficulty="medium",
        estimated_time_minutes=15,
        is_coding=False,
        statement=(
            "Tu dois planifier un projet de développement d'un nouveau produit.\n"
            "Tâches:\n"
            "- A: Étude de marché (3 semaines)\n"
            "- B: Conception (4 semaines, dépend de A)\n"
            "- C: Prototypage (3 semaines, dépend de B)\n"
            "- D: Tests (2 semaines, dépend de C)\n"
            "- E: Marketing (2 semaines, dépend de A)\n"
            "- F: Lancement (1 semaine, dépend de D et E)\n\n"
            "Questions:\n"
            "1. Quelle est la durée totale du projet ?\n"
            "2. Quel est le chemin critique ?\n"
            "3. Quelles tâches ont une marge libre ?\n"
            "4. Comment réduire la durée du projet ?"
        ),
        test_cases=[
            PracticalTestCase(
                name="total_duration",
                question="Durée totale du projet ?",
                expected_answer="La durée totale est de 13 semaines (A=3 + B=4 + C=3 + D=2 + F=1 = 13). Le chemin critique passe par A→B→C→D→F.",
                keywords=["13", "semaines", "chemin", "critique"],
                min_score=0.4,
            ),
            PracticalTestCase(
                name="critical_path",
                question="Chemin critique ?",
                expected_answer="Le chemin critique est A → B → C → D → F (3+4+3+2+1 = 13 semaines). C'est le plus long chemin, tout retard sur ces tâches retarde le projet.",
                keywords=["a", "b", "c", "d", "f", "critique", "13"],
                min_score=0.3,
            ),
            PracticalTestCase(
                name="free_slack",
                question="Tâches avec marge libre ?",
                expected_answer="La tâche E (Marketing) a une marge libre. E prend 2 semaines après A (semaine 3), donc E se termine à la semaine 5. Mais F démarre à la semaine 13 (après D), donc E a une marge de 8 semaines.",
                keywords=["e", "marketing", "marge", "libre", "8"],
                min_score=0.3,
            ),
            PracticalTestCase(
                name="reduce_duration",
                question="Comment réduire la durée ?",
                expected_answer="Fast-tracking: exécuter B et E en parallèle. Crashing: ajouter des ressources sur les tâches du chemin critique (B ou C). On peut aussi réduire la portée ou utiliser des méthodes agiles.",
                keywords=["fast", "tracking", "crashing", "parallèle", "ressources", "agile", "critique"],
                min_score=0.3,
            ),
        ],
    )


# ── Registry ───────────────────────────────────────────────────

_DOMAIN_CHALLENGES: List[PracticalChallenge] = [
    _electrical_ohms_law_challenge(),
    _electrical_plc_challenge(),
    _mechanical_material_challenge(),
    _quality_root_cause_challenge(),
    _logistics_optimization_challenge(),
    _management_project_challenge(),
]


def get_challenges_by_domain(domain: str) -> List[PracticalChallenge]:
    """Get all practical challenges for a given domain.

    Args:
        domain: Domain key (electrical, mechanical, quality, logistics, management, programming)

    Returns:
        List of challenges matching the domain
    """
    domain_lower = domain.lower().strip()
    matches = [c for c in _DOMAIN_CHALLENGES if c.domain == domain_lower]
    if not matches:
        matches = [c for c in _DOMAIN_CHALLENGES if domain_lower in c.domain or c.domain in domain_lower]
    return matches


def get_all_practical_challenges() -> List[PracticalChallenge]:
    """Get all available practical challenges."""
    return _DOMAIN_CHALLENGES


def get_challenge_by_id(challenge_id: str) -> Optional[PracticalChallenge]:
    """Get a specific challenge by ID."""
    for c in _DOMAIN_CHALLENGES:
        if c.id == challenge_id:
            return c
    return None


def score_practical_challenge(
    challenge: PracticalChallenge,
    answers: Dict[str, str],
) -> Dict[str, Any]:
    """Score a practical challenge submission.

    Args:
        challenge: The practical challenge
        answers: Dict of {test_case_name: answer_text}

    Returns:
        Scoring results with per-question scores and overall
    """
    results = []
    total_score = 0.0

    for tc in challenge.test_cases:
        answer = answers.get(tc.name, "")
        score = _score_text_answer(answer, tc.expected_answer, tc.keywords)
        passed = score >= tc.min_score
        results.append({
            "name": tc.name,
            "question": tc.question,
            "score": round(score, 3),
            "passed": passed,
            "min_required": tc.min_score,
            "feedback": "Correct" if passed else "Incomplete — review the key concepts",
        })
        total_score += score

    overall = total_score / len(challenge.test_cases) if challenge.test_cases else 0
    passed_count = sum(1 for r in results if r["passed"])

    return {
        "challenge_id": challenge.id,
        "challenge_title": challenge.title,
        "domain": challenge.domain,
        "overall_score": round(overall * 100, 1),
        "passed": passed_count,
        "total": len(challenge.test_cases),
        "results": results,
        "recommendation": "excellent" if overall >= 0.8 else ("good" if overall >= 0.6 else ("borderline" if overall >= 0.4 else "needs_improvement")),
    }


def _score_text_answer(answer: str, expected: str, keywords: List[str]) -> float:
    """Score a text answer against expected answer and keywords.

    Returns score in [0, 1].
    """
    if not answer or not answer.strip():
        return 0.0

    answer_lower = answer.lower()
    expected_lower = expected.lower()

    keyword_hits = sum(1 for kw in keywords if kw.lower() in answer_lower)
    keyword_score = keyword_hits / max(len(keywords), 1)

    answer_words = set(answer_lower.split())
    expected_words = set(expected_lower.split())
    if not expected_words:
        overlap_score = 0
    else:
        overlap = len(answer_words & expected_words) / len(expected_words)
        overlap_score = min(overlap, 1.0)

    final = keyword_score * 0.6 + overlap_score * 0.4
    return min(final, 1.0)
