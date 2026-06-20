import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from modules.knowledge.ui.evaluation.app import EvaluationInterface
from modules.knowledge.ui.evaluation.components import EvaluationPanel, DataCard, ActionButton
from modules.knowledge.ui.evaluation.api_client import EvaluationAPIClient


@pytest.fixture
def sample_cv_text():
    return """
    Jane Doe
    Data Scientist
    
    SKILLS
    Programming: Python, R, SQL
    Machine Learning: TensorFlow, PyTorch
    Tools: Docker, Git
    """


class TestEvaluationUI:
    def setup_method(self):
        self.ui = EvaluationInterface()

    def test_load_evaluation_flow(self, sample_cv_text):
        state = self.ui.load_evaluation(sample_cv_text, user_id=42)

        # Verify all steps loaded
        assert "cv_analysis" in state
        assert "taxonomy" in state
        assert "quiz_questions" in state
        assert "quiz_scoring" in state
        assert "knowledge_score" in state

        # Verify structure
        assert "mock" in state["cv_analysis"]
        assert "mock" in state["taxonomy"]
        assert "mock" in state["quiz_questions"]
        assert "mock" in state["quiz_scoring"]
        assert "mock" in state["knowledge_score"]

    def test_render_panels(self, sample_cv_text):
        self.ui.load_evaluation(sample_cv_text)
        panels = self.ui.render_panels()

        assert len(panels) == 4
        panel_titles = {p["title"] for p in panels}
        expected = {"CV Analysis", "Taxonomy Enrichment", "Quiz Diagnostics", "Knowledge Score"}
        assert expected.issubset(panel_titles)

        # Verify each panel has cards
        for panel in panels:
            assert "cards" in panel
            assert isinstance(panel["cards"], list)

    def test_action_buttons(self):
        actions = self.ui.get_actions()
        assert len(actions) >= 2
        labels = {a.label for a in actions}
        assert "Re-run NLP" in labels
        assert "Flag for QA" in labels

    def test_help_text(self):
        for panel_type in ["cv_analysis", "taxonomy", "quiz", "knowledge_score"]:
            help_text = self.ui.get_help_text(panel_type)
            assert isinstance(help_text, str)
            assert len(help_text) > 0

    def test_evaluation_panel_builders(self):
        # Mock data
        cv_data = {"skills": [{"name": "Python", "confidence": 0.9}]}
        taxonomy_data = {"Python": [{"description": "Programming language", "confidence": 0.85, "source": "ESCO"}]}
        quiz_data = {"scoring": {"score": 0.8, "mastery": "high", "confidence": 0.75}}
        score_data = {"knowledge_score": 0.82, "confidence_interval": {"lower": 0.78, "upper": 0.86}}

        cv_panel = EvaluationPanel.cv_analysis_panel(cv_data)
        assert cv_panel["title"] == "CV Analysis"
        assert len(cv_panel["cards"]) > 0
        assert isinstance(cv_panel["cards"][0], DataCard)

        tax_panel = EvaluationPanel.taxonomy_panel(taxonomy_data)
        assert tax_panel["title"] == "Taxonomy Enrichment"
        assert len(tax_panel["cards"]) > 0

        quiz_panel = EvaluationPanel.quiz_panel(quiz_data)
        assert quiz_panel["title"] == "Quiz Diagnostics"
        assert len(quiz_panel["cards"]) > 0

        score_panel = EvaluationPanel.knowledge_score_panel(score_data)
        assert score_panel["title"] == "Knowledge Score"
        assert len(score_panel["cards"]) > 0
