"""Tests for Confidence Scorer."""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from modules.knowledge.nlp.confidence_scorer import ConfidenceScorer


class TestConfidenceScorer:
    """Test suite for confidence scoring functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scorer = ConfidenceScorer()
    
    def test_skill_confidence_calculation(self):
        """Test confidence calculation for extracted skills."""
        # High confidence skill (explicitly mentioned)
        skill_data = {
            'name': 'Python',
            'context': 'Skills: Python, JavaScript, Java',
            'position': 'skills_section',
            'explicit_mention': True
        }
        
        confidence = self.scorer.calculate_skill_confidence(skill_data)
        assert confidence >= 0.8  # High confidence for explicit skills
        
        # Low confidence skill (inferred)
        inferred_skill = {
            'name': 'Programming',
            'context': 'Built web applications',
            'position': 'experience_description',
            'explicit_mention': False
        }
        
        confidence = self.scorer.calculate_skill_confidence(inferred_skill)
        assert confidence < 0.7  # Lower confidence for inferred skills
    
    def test_education_confidence_calculation(self):
        """Test confidence calculation for education entries."""
        # High confidence education (complete information)
        education_data = {
            'degree': 'Bachelor of Science in Computer Science',
            'institution': 'Stanford University',
            'dates': '2015-2019',
            'gpa': '3.8/4.0',
            'section_type': 'education'
        }
        
        confidence = self.scorer.calculate_education_confidence(education_data)
        assert confidence >= 0.8
        
        # Low confidence education (partial information)
        partial_education = {
            'degree': 'Degree',
            'institution': 'University',
            'dates': None,
            'gpa': None,
            'section_type': 'education'
        }
        
        confidence = self.scorer.calculate_education_confidence(partial_education)
        assert confidence < 0.6
    
    def test_experience_confidence_calculation(self):
        """Test confidence calculation for work experience."""
        # High confidence experience (detailed)
        experience_data = {
            'title': 'Senior Software Engineer',
            'company': 'Tech Corp',
            'dates': '2020-Present',
            'description': 'Developed RESTful APIs using Python and FastAPI',
            'achievements': ['Led team of 5 developers', 'Improved performance by 40%'],
            'section_type': 'experience'
        }
        
        confidence = self.scorer.calculate_experience_confidence(experience_data)
        assert confidence >= 0.8
        
        # Low confidence experience (minimal)
        minimal_experience = {
            'title': 'Engineer',
            'company': 'Company',
            'dates': None,
            'description': None,
            'achievements': [],
            'section_type': 'experience'
        }
        
        confidence = self.scorer.calculate_experience_confidence(minimal_experience)
        assert confidence < 0.5
    
    def test_certification_confidence_calculation(self):
        """Test confidence calculation for certifications."""
        # High confidence certification (complete)
        cert_data = {
            'name': 'AWS Certified Solutions Architect',
            'issuer': 'Amazon Web Services',
            'date': '2022',
            'credential_id': 'AWS-ASA-123456',
            'section_type': 'certification'
        }
        
        confidence = self.scorer.calculate_certification_confidence(cert_data)
        assert confidence >= 0.9
        
        # Low confidence certification (partial)
        partial_cert = {
            'name': 'Certificate',
            'issuer': None,
            'date': None,
            'credential_id': None,
            'section_type': 'certification'
        }
        
        confidence = self.scorer.calculate_certification_confidence(partial_cert)
        assert confidence < 0.4
    
    def test_overall_cv_confidence(self):
        """Test overall CV confidence calculation."""
        cv_analysis = {
            'skills': [
                {'name': 'Python', 'confidence': 0.9},
                {'name': 'JavaScript', 'confidence': 0.8}
            ],
            'education': [
                {'degree': 'BS Computer Science', 'confidence': 0.9}
            ],
            'experience': [
                {'title': 'Software Engineer', 'confidence': 0.8}
            ],
            'certifications': [
                {'name': 'AWS Certified', 'confidence': 0.9}
            ]
        }
        
        overall_confidence = self.scorer.calculate_overall_confidence(cv_analysis)
        assert 0 <= overall_confidence <= 1
        assert overall_confidence >= 0.6  # Should be reasonably high with good data
    
    def test_ambiguity_detection(self):
        """Test detection of ambiguous entries."""
        # Ambiguous skill
        ambiguous_skill = {
            'name': 'Management',
            'context': 'Involved in project management',
            'position': 'experience_description',
            'explicit_mention': False
        }
        
        ambiguity_score = self.scorer.detect_ambiguity(ambiguous_skill)
        assert ambiguity_score >= 0.3  # Should be flagged as ambiguous
        
        # Clear skill
        clear_skill = {
            'name': 'Python Programming',
            'context': 'Skills: Python Programming, Java',
            'position': 'skills_section',
            'explicit_mention': True
        }
        
        ambiguity_score = self.scorer.detect_ambiguity(clear_skill)
        assert ambiguity_score <= 0.35  # Should not be ambiguous
    
    def test_confidence_threshold_validation(self):
        """Test confidence threshold validation."""
        # Test valid confidence scores
        assert self.scorer.validate_confidence_score(0.0) == True
        assert self.scorer.validate_confidence_score(0.5) == True
        assert self.scorer.validate_confidence_score(1.0) == True
        
        # Test invalid confidence scores
        assert self.scorer.validate_confidence_score(-0.1) == False
        assert self.scorer.validate_confidence_score(1.1) == False
        assert self.scorer.validate_confidence_score(None) == False
