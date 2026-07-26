"""Psychometric questionnaire for Habits (H) assessment.

Based on validated psychological models:
- Big Five Personality Traits (OCEAN): Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism
- Grit Scale (Duckworth): passion and perseverance for long-term goals
- Self-Discipline Scale: habits, routine, consistency

Each question is scored on a 5-point Likert scale (1=Strongly Disagree, 5=Strongly Agree).
Reverse-scored items are marked with 'reverse: true'.
"""

PSYCHOMETRIC_QUESTIONS = [
    # ── Big Five — Conscientiousness (discipline, organization) ──
    {
        "id": "psy_q1",
        "text": "Je m'organise toujours à l'avance et je planifie mes tâches.",
        "dimension": "conscientiousness",
        "subscale": "organization",
        "reverse": False,
    },
    {
        "id": "psy_q2",
        "text": "Je laisse souvent les choses en désordre et je m'y perds.",
        "dimension": "conscientiousness",
        "subscale": "organization",
        "reverse": True,
    },
    {
        "id": "psy_q3",
        "text": "Je mémorise mes échéances et je respecte mes deadlines.",
        "dimension": "conscientiousness",
        "subscale": "discipline",
        "reverse": False,
    },
    {
        "id": "psy_q4",
        "text": "Je procrastine souvent et je reporte les tâches importantes.",
        "dimension": "conscientiousness",
        "subscale": "discipline",
        "reverse": True,
    },
    # ── Big Five — Neuroticism (stress, emotional stability) ──
    {
        "id": "psy_q5",
        "text": "Je reste calme et maître de moi même dans les situations difficiles.",
        "dimension": "neuroticism",
        "subscale": "emotional_stability",
        "reverse": False,
    },
    {
        "id": "psy_q6",
        "text": "Je me laisse facilement submerger par le stress et l'anxiété.",
        "dimension": "neuroticism",
        "subscale": "anxiety",
        "reverse": True,
    },
    # ── Big Five — Openness (curiosity, learning) ──
    {
        "id": "psy_q7",
        "text": "J'aime explorer de nouvelles idées et apprendre de nouveaux sujets.",
        "dimension": "openness",
        "subscale": "intellectual_curiosity",
        "reverse": False,
    },
    {
        "id": "psy_q8",
        "text": "Je préfère rester dans ma zone de confort plutôt que d'essayer de nouvelles choses.",
        "dimension": "openness",
        "subscale": "openness_to_experience",
        "reverse": True,
    },
    # ── Big Five — Extraversion (energy, social engagement) ──
    {
        "id": "psy_q9",
        "text": "Je me sens énergisé quand je travaille en équipe et je communique facilement.",
        "dimension": "extraversion",
        "subscale": "sociability",
        "reverse": False,
    },
    {
        "id": "psy_q10",
        "text": "Je préfère travailler seul et j'évite les interactions sociales quand je peux.",
        "dimension": "extraversion",
        "subscale": "sociability",
        "reverse": True,
    },
    # ── Big Five — Agreeableness (cooperation, empathy) ──
    {
        "id": "psy_q11",
        "text": "Je prends en compte les opinions des autres avant de prendre une décision.",
        "dimension": "agreeableness",
        "subscale": "cooperation",
        "reverse": False,
    },
    {
        "id": "psy_q12",
        "text": "Je trouve difficile de travailler avec des personnes qui ne partagent pas mon avis.",
        "dimension": "agreeableness",
        "subscale": "cooperation",
        "reverse": True,
    },
    # ── Grit Scale (Duckworth) — passion & perseverance ──
    {
        "id": "psy_q13",
        "text": "Je termine toujours ce que je commence, même quand c'est difficile.",
        "dimension": "grit",
        "subscale": "perseverance",
        "reverse": False,
    },
    {
        "id": "psy_q14",
        "text": "J'ai souvent de nouveaux projets mais j'en abandonne la plupart rapidement.",
        "dimension": "grit",
        "subscale": "perseverance",
        "reverse": True,
    },
    {
        "id": "psy_q15",
        "text": "Je reste fidèle à mes objectifs à long terme, même sans résultats immédiats.",
        "dimension": "grit",
        "subscale": "consistency",
        "reverse": False,
    },
    {
        "id": "psy_q16",
        "text": "Mes intérêts changent souvent et j'ai du mal à maintenir une direction.",
        "dimension": "grit",
        "subscale": "consistency",
        "reverse": True,
    },
    # ── Self-Discipline & Habits ──
    {
        "id": "psy_q17",
        "text": "J'ai une routine quotidienne que je suis avec régularité.",
        "dimension": "self_discipline",
        "subscale": "routine",
        "reverse": False,
    },
    {
        "id": "psy_q18",
        "text": "Je travaille sur mes objectifs même quand je n'en ai pas envie.",
        "dimension": "self_discipline",
        "subscale": "willpower",
        "reverse": False,
    },
    {
        "id": "psy_q19",
        "text": "Je me laisse souvent distraire par mon téléphone ou les réseaux sociaux.",
        "dimension": "self_discipline",
        "subscale": "focus",
        "reverse": True,
    },
    {
        "id": "psy_q20",
        "text": "Je tiens un journal de bord ou un tracker pour suivre mes progrès.",
        "dimension": "self_discipline",
        "subscale": "self_monitoring",
        "reverse": False,
    },
]

DIMENSION_DESCRIPTIONS = {
    "conscientiousness": {
        "label": "Conscience et Discipline",
        "description": "Capacité à s'organiser, planifier, et respecter ses engagements",
        "high": "Très organisé, fiable, discipliné — respecte les deadlines et planifie à l'avance",
        "low": "Désorganisé, procrastine — difficulté à maintenir une structure",
    },
    "neuroticism": {
        "label": "Stabilité Émotionnelle",
        "description": "Capacité à gérer le stress et rester émotionnellement stable",
        "high": "Stable émotionnellement, calme sous pression, gère bien le stress",
        "low": "Sensible au stress, anxieux — peut se laisser submerger émotionnellement",
    },
    "openness": {
        "label": "Ouverture et Curiosité",
        "description": "Curiosité intellectuelle et ouverture aux nouvelles expériences",
        "high": "Curieux, créatif, aime apprendre — ouvert aux nouvelles idées",
        "low": "Préfère la routine et les approches connues — peu d'intérêt pour la nouveauté",
    },
    "extraversion": {
        "label": "Extraversion et Sociabilité",
        "description": "Énergie sociale et facilité de communication",
        "high": "Énergique en groupe, communique facilement, sociable",
        "low": "Préfère le travail solitaire, réservé — s'épuise en groupe",
    },
    "agreeableness": {
        "label": "Coopération et Empathie",
        "description": "Capacité à collaborer et prendre en compte les autres",
        "high": "Coopératif, empathique, bon esprit d'équipe",
        "low": "Indépendant, peut être conflictuel — difficulté avec le consensus",
    },
    "grit": {
        "label": "Détermination (Grit)",
        "description": "Passion et persévérance pour les objectifs à long terme",
        "high": "Persévérant, termine ce qu'il commence, fidèle à ses objectifs",
        "low": "Abandonne facilement, change souvent de direction — peu de constance",
    },
    "self_discipline": {
        "label": "Autodiscipline et Habitudes",
        "description": "Régularité, routine, force de volonté et gestion des distractions",
        "high": "Routine solide, travaille même sans motivation, gère les distractions",
        "low": "Distrait, manque de routine — difficulté à maintenir l'effort sans pression externe",
    },
}

DIMENSION_WEIGHTS = {
    "conscientiousness": 0.22,
    "neuroticism": 0.18,
    "openness": 0.12,
    "extraversion": 0.10,
    "agreeableness": 0.10,
    "grit": 0.18,
    "self_discipline": 0.10,
}
