import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from modules.knowledge.nlp.cv_analyzer import CVAnalyzer
from modules.knowledge.quiz.orchestrator import QuizOrchestrator
from modules.knowledge.scoring.api import ScoringAPI


@pytest.fixture
def sample_cv_text():
    return """
    John Doe
    Software Engineer
    
    SKILLS
    Programming: Python, JavaScript, Java, SQL
    Frameworks: React, FastAPI, Django
    Tools: Docker, Kubernetes, Git
    """


class TestScoringIntegration:
    def setup_method(self):
        self.cv_analyzer = CVAnalyzer()
        self.quiz_orchestrator = QuizOrchestrator()
        self.scoring_api = ScoringAPI()

    def test_end_to_end_scoring_flow(self, sample_cv_text):
        # Step 1: Extract skills from CV
        cv_analysis = self.cv_analyzer.analyze_cv(sample_cv_text)
        skills = cv_analysis.get("skills", [])
        assert len(skills) > 0

        # Step 2: Generate quiz questions and answers (simulate all correct)
        questions = self.quiz_orchestrator.mapper.generate_questions(skills)
        answers = [{"correct": True}] * len(questions)
        quiz_result = self.quiz_orchestrator.run_quiz(skills, answers, user_id=123)

        # Step 3: Compute unified knowledge score
        cv_insights = {"score": cv_analysis["metadata"]["overall_confidence"]}
        taxonomy_confidence = {"confidence": 0.75}  # mock enrichment confidence
        quiz_mastery = quiz_result["scoring"]

        unified = self.scoring_api.get_score(
            cv_insights=cv_insights,
            taxonomy_confidence=taxonomy_confidence,
            quiz_mastery=quiz_mastery,
            user_id=123,
        )

        # Validate unified score
        assert "knowledge_score" in unified
        assert 0 <= unified["knowledge_score"] <= 1
        assert "breakdown" in unified
        assert "confidence_interval" in unified
        assert "diagnostics" in unified

        # Verify breakdown includes expected components
        breakdown = unified["breakdown"]
        expected_components = {"cv_insights", "taxonomy_confidence", "quiz_mastery"}
        assert all(comp in breakdown for comp in expected_components)

    def test_scoring_with_missing_quiz_data(self, sample_cv_text):
        # Simulate scenario where quiz data is temporarily unavailable
        cv_analysis = self.cv_analyzer.analyze_cv(sample_cv_text)
        cv_insights = {"score": cv_analysis["metadata"]["overall_confidence"]}
        taxonomy_confidence = {"confidence": 0.75}
        quiz_mastery = {"score": 0.0, "mastery": "low"}  # fallback/missing

        unified = self.scoring_api.get_score(
            cv_insights=cv_insights,
            taxonomy_confidence=taxonomy_confidence,
            quiz_mastery=quiz_mastery,
            user_id=999,
        )

        # Should still produce a valid score
        assert 0 <= unified["knowledge_score"] <= 1
        assert unified["diagnostics"]["user_id"] == 999

    def test_scoring_cache_behavior(self, sample_cv_text):
        cv_analysis = self.cv_analyzer.analyze_cv(sample_cv_text)
        cv_insights = {"score": cv_analysis["metadata"]["overall_confidence"]}
        taxonomy_confidence = {"confidence": 0.75}
        quiz_mastery = {"score": 0.9, "mastery": "high"}

        # First call
        result1 = self.scoring_api.get_score(
            cv_insights=cv_insights,
            taxonomy_confidence=taxonomy_confidence,
            quiz_mastery=quiz_mastery,
            user_id=777,
        )

        # Second call (should hit cache)
        result2 = self.scoring_api.get_score(
            cv_insights=cv_insights,
            taxonomy_confidence=taxonomy_confidence,
            quiz_mastery=quiz_mastery,
            user_id=777,
        )

        assert result1["knowledge_score"] == result2["knowledge_score"]
        assert self.scoring_api.get_stats()["cache_size"] > 0
