import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from modules.knowledge.nlp.cv_analyzer import CVAnalyzer
from modules.knowledge.quiz.orchestrator import QuizOrchestrator


@pytest.fixture
def sample_cv_text():
    return """
    John Doe
    Software Engineer
    
    EDUCATION
    Bachelor of Science in Computer Science
    Stanford University, 2015-2019
    GPA: 3.8/4.0
    
    EXPERIENCE
    Senior Software Engineer at Tech Corp (2020-Present)
    - Developed RESTful APIs using Python and FastAPI
    - Led team of 5 developers
    - Improved system performance by 40%
    
    Software Engineer at StartupXYZ (2019-2020)
    - Built web applications with React and Node.js
    - Implemented CI/CD pipelines
    
    SKILLS
    Programming: Python, JavaScript, Java, SQL
    Frameworks: React, FastAPI, Django
    Tools: Docker, Kubernetes, Git
    
    CERTIFICATIONS
    AWS Certified Solutions Architect (2022)
    Google Cloud Professional Developer (2021)
    """


class TestCVQuizIntegration:
    def setup_method(self):
        self.analyzer = CVAnalyzer()
        self.orchestrator = QuizOrchestrator()

    def test_cv_to_quiz_questions_flow(self, sample_cv_text):
        # Step 1: Extract skills from CV
        analysis = self.analyzer.analyze_cv(sample_cv_text)
        skills = analysis.get("skills", [])
        assert len(skills) > 0

        # Step 2: Generate quiz questions from extracted skills
        questions = self.orchestrator.mapper.generate_questions(skills)
        assert len(questions) > 0
        assert all("question_text" in q for q in questions)
        assert all("skill_name" in q for q in questions)

        # Verify at least one question references a known skill
        skill_names = {s["name"].lower() for s in skills}
        question_skills = {q["skill_name"].lower() for q in questions}
        assert skill_names.intersection(question_skills)

    def test_cv_to_full_quiz_pipeline(self, sample_cv_text):
        # Extract skills
        analysis = self.analyzer.analyze_cv(sample_cv_text)
        skills = analysis.get("skills", [])

        # Simulate answers (all correct for simplicity)
        answers = [{"correct": True}] * len(skills)

        # Run full quiz pipeline
        result = self.orchestrator.run_quiz(skills, answers, user_id=123)

        # Validate structure
        assert "questions" in result
        assert "scoring" in result
        assert "stored" in result
        assert result["user_id"] == 123

        # Validate scoring
        scoring = result["scoring"]
        assert 0 <= scoring["score"] <= 1
        assert scoring["mastery"] in {"low", "medium", "high"}

        # Validate storage
        assert result["stored"] is True

    def test_cv_to_quiz_without_user_id(self, sample_cv_text):
        analysis = self.analyzer.analyze_cv(sample_cv_text)
        skills = analysis.get("skills", [])
        answers = [{"correct": True}] * len(skills)

        result = self.orchestrator.run_quiz(skills, answers, user_id=None)

        assert result["stored"] is False
        assert result["user_id"] is None
