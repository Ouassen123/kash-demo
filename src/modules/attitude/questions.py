"""Attitude interview questions — behavioral and stress-management scenarios.

Questions are designed to elicit responses that reveal:
- Stress management style
- Emotional regulation
- Adaptability and resilience
- Communication approach under pressure
- Self-awareness and reflection
- Team dynamics and conflict resolution
"""

INTERVIEW_QUESTIONS = [
    {
        "id": "att_q1",
        "text": "Décris une situation où tu as dû travailler sous une forte pression. Comment as-tu géré le stress ?",
        "category": "stress_management",
        "expected_signals": ["planning", "prioritization", "calm", "delegation", "time_management"],
    },
    {
        "id": "att_q2",
        "text": "Raconte un moment où tu as échoué. Qu'as-tu appris et comment t'es-tu relevé ?",
        "category": "resilience",
        "expected_signals": ["self_reflection", "learning", "growth_mindset", "persistence"],
    },
    {
        "id": "att_q3",
        "text": "Comment réagis-tu quand tu es en désaccord avec un membre de ton équipe ?",
        "category": "conflict_resolution",
        "expected_signals": ["empathy", "communication", "compromise", "active_listening", "respect"],
    },
    {
        "id": "att_q4",
        "text": "Décris une situation où tu as dû t'adapter à un changement majeur. Comment l'as-tu vécu ?",
        "category": "adaptability",
        "expected_signals": ["flexibility", "open_mindedness", "proactive", "problem_solving"],
    },
    {
        "id": "att_q5",
        "text": "Qu'est-ce qui te motive au quotidien ? Comment maintiens-tu ta motivation quand les choses deviennent difficiles ?",
        "category": "motivation",
        "expected_signals": ["intrinsic_motivation", "goals", "passion", "perseverance", "self_discipline"],
    },
    {
        "id": "att_q6",
        "text": "Décris un moment où tu as dû prendre une décision difficile avec peu d'informations. Quel a été ton raisonnement ?",
        "category": "decision_making",
        "expected_signals": ["analytical_thinking", "risk_assessment", "decisiveness", "intuition", "judgment"],
    },
]

CATEGORY_WEIGHTS = {
    "stress_management": 0.25,
    "resilience": 0.20,
    "conflict_resolution": 0.15,
    "adaptability": 0.15,
    "motivation": 0.15,
    "decision_making": 0.10,
}

SIGNAL_KEYWORDS = {
    "planning": ["plan", "organize", "schedule", "prepare", "strategy", "prioritize"],
    "prioritization": ["priority", "important", "urgent", "first", "critical", "focus"],
    "calm": ["calm", "composed", "relax", "breathe", "steady", "control", "serene"],
    "delegation": ["delegate", "assign", "team", "share", "distribute", "collaborate"],
    "time_management": ["time", "deadline", "efficient", "manage", "schedule"],
    "self_reflection": ["reflect", "learn", "mistake", "realize", "understand", "growth"],
    "learning": ["learn", "improve", "lesson", "knowledge", "skill", "develop"],
    "growth_mindset": ["grow", "improve", "better", "progress", "develop", "evolve"],
    "persistence": ["persist", "continue", "try again", "keep going", "persevere", "not give up"],
    "empathy": ["understand", "feel", "perspective", "listen", "empathy", "care"],
    "communication": ["communicate", "discuss", "talk", "explain", "express", "dialogue"],
    "compromise": ["compromise", "agree", "middle ground", "negotiate", "consensus"],
    "active_listening": ["listen", "hear", "understand", "consider", "acknowledge"],
    "respect": ["respect", "value", "appreciate", "professional", "courteous"],
    "flexibility": ["flexible", "adapt", "adjust", "change", "pivot", "modify"],
    "open_mindedness": ["open", "consider", "explore", "willing", "curious", "new"],
    "proactive": ["proactive", "initiative", "ahead", "anticipate", "prepare", "action"],
    "problem_solving": ["solve", "solution", "fix", "address", "resolve", "tackle"],
    "intrinsic_motivation": ["passion", "love", "enjoy", "fulfilling", "meaningful", "purpose"],
    "goals": ["goal", "objective", "target", "aim", "ambition", "vision"],
    "perseverance": ["persevere", "persist", "endure", "overcome", "push through", "determination"],
    "self_discipline": ["discipline", "routine", "habit", "consistent", "committed", "dedicated"],
    "analytical_thinking": ["analyze", "evaluate", "assess", "data", "evidence", "logical"],
    "risk_assessment": ["risk", "consequence", "impact", "probability", "weigh", "evaluate"],
    "decisiveness": ["decide", "decision", "commit", "confident", "firm", "choose"],
    "intuition": ["intuition", "instinct", "gut", "feel", "sense"],
    "judgment": ["judgment", "reasoning", "rationale", "justification", "basis"],
}
