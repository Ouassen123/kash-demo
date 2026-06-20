"""Main evaluation interface app (mock UI)."""

from typing import Dict, Any, List, Optional
from dataclasses import asdict

from .components import EvaluationPanel, DataCard, ActionButton
from .api_client import EvaluationAPIClient


class EvaluationInterface:
    """Mock UI app for Knowledge evaluation."""

    def __init__(self, api_client: Optional[EvaluationAPIClient] = None):
        self.api = api_client or EvaluationAPIClient()
        self.state: Dict[str, Any] = {}

    def load_evaluation(self, cv_text: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Load full evaluation for a given CV."""
        # Step 1: CV analysis
        cv_analysis = self.api.fetch_cv_analysis(cv_text)
        self.state["cv_analysis"] = cv_analysis

        # Step 2: Taxonomy enrichment (mock from skills)
        skills = cv_analysis.get("skills", [])
        taxonomy = self.api.fetch_taxonomy_enrichment([s.get("name", "") for s in skills])
        self.state["taxonomy"] = taxonomy

        # Step 3: Quiz generation (mock)
        quiz_questions = self.api.fetch_quiz_questions(skills)
        self.state["quiz_questions"] = quiz_questions

        # Step 4: Mock quiz answers (all correct for demo)
        answers = [{"correct": True}] * len(quiz_questions.get("questions", []))
        quiz_scoring = self.api.submit_quiz_answers(answers)
        self.state["quiz_scoring"] = quiz_scoring

        # Step 5: Unified knowledge score
        knowledge_score = self.api.fetch_knowledge_score(
            cv_insights=cv_analysis,
            taxonomy_confidence=taxonomy,
            quiz_mastery=quiz_scoring,
            user_id=user_id,
        )
        self.state["knowledge_score"] = knowledge_score

        return self.state

    def render_panels(self) -> List[Dict[str, Any]]:
        """Render UI panels for current state."""
        panels = []
        if "cv_analysis" in self.state:
            panels.append(EvaluationPanel.cv_analysis_panel(self.state["cv_analysis"]))
        if "taxonomy" in self.state:
            panels.append(EvaluationPanel.taxonomy_panel(self.state["taxonomy"]))
        if "quiz_scoring" in self.state:
            panels.append(EvaluationPanel.quiz_panel(self.state["quiz_scoring"]))
        if "knowledge_score" in self.state:
            panels.append(EvaluationPanel.knowledge_score_panel(self.state["knowledge_score"]))
        return panels

    def get_actions(self) -> List[ActionButton]:
        """Get available action buttons for current context."""
        actions = [
            ActionButton("Re-run NLP", "/api/cv/rerun", method="POST"),
            ActionButton("Flag for QA", "/api/qa/flag", method="POST"),
        ]
        return actions

    def get_help_text(self, panel_type: str) -> str:
        """Get contextual help for a panel."""
        help_map = {
            "cv_analysis": "Extracted skills, education, experience, and certifications from the CV with confidence scores.",
            "taxonomy": "Enrichment via ESCO/O*NET linking CV skills to standardized taxonomy concepts.",
            "quiz": "Adaptive quiz performance including score, mastery, and confidence metrics.",
            "knowledge_score": "Unified knowledge score aggregating CV, taxonomy, and quiz signals with confidence intervals.",
        }
        return help_map.get(panel_type, "No help available for this panel.")
