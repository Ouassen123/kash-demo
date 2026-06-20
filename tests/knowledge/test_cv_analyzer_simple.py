"""Simple tests for CV Analyzer NLP pipeline without complex dependencies."""

import pytest
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from modules.knowledge.nlp.confidence_scorer import ConfidenceScorer
from modules.knowledge.nlp.taxonomy_mapper import TaxonomyMapper


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
        assert 0 <= confidence <= 1  # Within valid range
        
        # Low confidence skill (inferred)
        inferred_skill = {
            'name': 'Programming',
            'context': 'Built web applications',
            'position': 'experience_description',
            'explicit_mention': False
        }
        
        confidence = self.scorer.calculate_skill_confidence(inferred_skill)
        assert confidence < 0.7  # Lower confidence for inferred skills
        assert 0 <= confidence <= 1  # Within valid range
    
    def test_ambiguity_detection(self):
        """Test ambiguity detection."""
        # Ambiguous skill
        ambiguous_skill = {
            'name': 'Management',
            'context': 'Involved in project management',
            'position': 'experience_description',
            'explicit_mention': False
        }
        
        ambiguity_score = self.scorer.detect_ambiguity(ambiguous_skill)
        assert ambiguity_score > 0.5  # Should be flagged as ambiguous
        assert 0 <= ambiguity_score <= 1  # Within valid range
        
        # Clear skill
        clear_skill = {
            'name': 'Python Programming',
            'context': 'Skills: Python Programming, Java',
            'position': 'skills_section',
            'explicit_mention': True
        }
        
        ambiguity_score = self.scorer.detect_ambiguity(clear_skill)
        assert ambiguity_score < 0.3  # Should not be ambiguous
        assert 0 <= ambiguity_score <= 1  # Within valid range
    
    def test_confidence_validation(self):
        """Test confidence score validation."""
        # Test valid scores
        assert self.scorer.validate_confidence_score(0.0) == True
        assert self.scorer.validate_confidence_score(0.5) == True
        assert self.scorer.validate_confidence_score(1.0) == True
        
        # Test invalid scores
        assert self.scorer.validate_confidence_score(-0.1) == False
        assert self.scorer.validate_confidence_score(1.1) == False
        assert self.scorer.validate_confidence_score(None) == False


class TestTaxonomyMapper:
    """Test suite for taxonomy mapping functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mapper = TaxonomyMapper()
        
        # Sample taxonomy data
        self.sample_taxonomy = {
            'skills': {
                'programming': {
                    'languages': ['Python', 'JavaScript', 'Java', 'C++'],
                    'frameworks': ['React', 'FastAPI', 'Django', 'Spring']
                }
            }
        }
    
    def test_skill_mapping_exact_match(self):
        """Test exact skill matching to taxonomy."""
        user_skill = 'Python'
        
        result = self.mapper.map_skill(user_skill, self.sample_taxonomy)
        
        assert result is not None
        assert result.mapped_skill == 'Python'
        assert result.category == 'programming'
        assert result.subcategory == 'languages'
        assert result.match_type == 'exact'
        assert result.confidence >= 0.9
        assert 0 <= result.confidence <= 1
    
    def test_skill_mapping_no_match(self):
        """Test handling of skills with no match."""
        user_skill = 'Completely Unknown Skill'
        
        result = self.mapper.map_skill(user_skill, self.sample_taxonomy)
        
        assert result is not None
        assert result.mapped_skill == user_skill  # Returns original
        assert result.match_type == 'no_match'
        assert result.confidence <= 0.3
        assert 0 <= result.confidence <= 1
    
    def test_taxonomy_validation(self):
        """Test taxonomy structure validation."""
        # Valid taxonomy
        assert self.mapper.validate_taxonomy(self.sample_taxonomy) == True
        
        # Invalid taxonomy (missing required sections)
        invalid_taxonomy = {'skills': {}}
        assert self.mapper.validate_taxonomy(invalid_taxonomy) == False
        
        # Empty taxonomy
        assert self.mapper.validate_taxonomy({}) == False
        assert self.mapper.validate_taxonomy(None) == False
    
    def test_mapping_statistics(self):
        """Test mapping statistics calculation."""
        user_skills = ['Python', 'JavaScript', 'Unknown Skill 1', 'Unknown Skill 2']
        
        results = self.mapper.map_skills_batch(user_skills, self.sample_taxonomy)
        stats = self.mapper.calculate_mapping_statistics(results)
        
        assert stats['total_skills'] == 4
        assert stats['mapped_skills'] == 2
        assert stats['unmapped_skills'] == 2
        assert stats['mapping_rate'] == 0.5
        assert 'average_confidence' in stats
        assert 'match_type_distribution' in stats
        assert 0 <= stats['average_confidence'] <= 1


class TestCVAnalyzerBasic:
    """Basic tests for CV analyzer without external dependencies."""
    
    def test_text_cleaning(self):
        """Test text cleaning functionality."""
        # Import here to avoid dependency issues
        from modules.knowledge.nlp.cv_analyzer import CVAnalyzer
        
        analyzer = CVAnalyzer()
        
        # Test basic cleaning
        dirty_text = "  This   is a   test   with  extra   spaces  "
        cleaned = analyzer._clean_text(dirty_text)
        
        assert cleaned == "This is a test with extra spaces"
        assert len(cleaned.strip()) > 0
    
    def test_language_detection(self):
        """Test language detection."""
        from modules.knowledge.nlp.cv_analyzer import CVAnalyzer
        
        analyzer = CVAnalyzer()
        
        # Test English
        english_text = "I am a software engineer with experience in Python"
        language = analyzer._detect_language(english_text)
        assert language == 'en'
        
        # Test French
        french_text = "Je suis ingénieur logiciel avec expérience en Python"
        language = analyzer._detect_language(french_text)
        assert language == 'fr'
    
    def test_section_extraction(self):
        """Test CV section extraction."""
        from modules.knowledge.nlp.cv_analyzer import CVAnalyzer
        
        analyzer = CVAnalyzer()
        
        cv_text = """
        SKILLS: Python, JavaScript, Java
        
        EXPERIENCE: Software Engineer at Tech Corp
        
        EDUCATION: Bachelor of Science in Computer Science
        """
        
        skills_section = analyzer._extract_section(cv_text, 'skills')
        assert skills_section is not None
        assert 'Python' in skills_section
        
        experience_section = analyzer._extract_section(cv_text, 'experience')
        assert experience_section is not None
        assert 'Software Engineer' in experience_section
        
        education_section = analyzer._extract_section(cv_text, 'education')
        assert education_section is not None
        assert 'Bachelor' in education_section


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
