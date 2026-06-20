"""Tests for Taxonomy Mapper."""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from modules.knowledge.nlp.taxonomy_mapper import TaxonomyMapper


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
                    'frameworks': ['React', 'FastAPI', 'Django', 'Spring'],
                    'databases': ['PostgreSQL', 'MongoDB', 'Redis']
                },
                'soft_skills': {
                    'leadership': ['Team Management', 'Project Leadership'],
                    'communication': ['Public Speaking', 'Written Communication']
                }
            },
            'education_levels': {
                'bachelor': ['Bachelor of Science', 'B.S.', 'B.Sc.', 'Licence'],
                'master': ['Master of Science', 'M.S.', 'M.Sc.', 'Master'],
                'phd': ['Doctor of Philosophy', 'Ph.D.', 'PhD']
            },
            'experience_levels': {
                'entry': ['Junior', 'Entry Level', 'Intern'],
                'mid': ['Software Engineer', 'Developer', 'Engineer'],
                'senior': ['Senior', 'Lead', 'Principal', 'Staff']
            }
        }
    
    def test_skill_mapping_exact_match(self):
        """Test exact skill matching to taxonomy."""
        user_skill = 'Python'
        
        result = self.mapper.map_skill(user_skill, self.sample_taxonomy)
        
        assert result is not None
        assert result.mapped_value == 'Python'
        assert result.category == 'programming'
        assert result.subcategory == 'languages'
        assert result.match_type == 'exact'
        assert result.confidence >= 0.9
    
    def test_skill_mapping_partial_match(self):
        """Test partial skill matching."""
        user_skill = 'Python Programming'
        
        result = self.mapper.map_skill(user_skill, self.sample_taxonomy)
        
        assert result is not None
        assert result.mapped_value == 'Python'
        assert result.match_type == 'partial'
        assert result.confidence >= 0.7
    
    def test_skill_mapping_semantic_match(self):
        """Test semantic skill matching."""
        user_skill = 'JS'  # Common abbreviation for JavaScript
        
        result = self.mapper.map_skill(user_skill, self.sample_taxonomy)
        
        assert result is not None
        assert result.mapped_value == 'JavaScript'
        assert result.match_type in ['semantic', 'exact']
        assert result.confidence >= 0.6
    
    def test_skill_mapping_no_match(self):
        """Test handling of skills with no match."""
        user_skill = 'Completely Unknown Skill'
        
        result = self.mapper.map_skill(user_skill, self.sample_taxonomy)
        
        assert result is not None
        assert result.mapped_value == user_skill  # Returns original
        assert result.match_type == 'no_match'
        assert result.confidence <= 0.3
    
    def test_education_level_mapping(self):
        """Test education level normalization."""
        # Test various degree formats
        test_cases = [
            ('Bachelor of Science in Computer Science', 'bachelor'),
            ('B.S. Computer Science', 'bachelor'),
            ('Master of Science', 'master'),
            ('M.S. Engineering', 'master'),
            ('Doctor of Philosophy', 'phd'),
            ('Ph.D. Computer Science', 'phd')
        ]
        
        for degree, expected_level in test_cases:
            result = self.mapper.map_education_level(degree, self.sample_taxonomy)
            assert result.category == expected_level
            assert result.confidence >= 0.6
    
    def test_experience_level_mapping(self):
        """Test experience level normalization."""
        test_cases = [
            ('Junior Software Engineer', 'entry'),
            ('Software Engineer', 'mid'),
            ('Senior Software Engineer', 'senior'),
            ('Lead Developer', 'senior'),
            ('Principal Engineer', 'senior')
        ]
        
        for title, expected_level in test_cases:
            result = self.mapper.map_experience_level(title, self.sample_taxonomy)
            assert result.category == expected_level
            assert result.confidence >= 0.7
    
    def test_batch_skill_mapping(self):
        """Test batch mapping of multiple skills."""
        user_skills = [
            'Python',
            'JavaScript',
            'React',
            'Unknown Skill',
            'Team Management'
        ]
        
        results = self.mapper.map_skills_batch(user_skills, self.sample_taxonomy)
        
        assert len(results) == len(user_skills)
        
        # Check that known skills are mapped correctly
        python_result = next(r for r in results if r.original_value == 'Python')
        assert python_result.mapped_value == 'Python'
        assert python_result.match_type == 'exact'
        
        # Check that unknown skills are handled gracefully
        unknown_result = next(r for r in results if r.original_value == 'Unknown Skill')
        assert unknown_result.match_type == 'no_match'
    
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
