"""Integration tests for the complete NLP pipeline."""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from modules.knowledge.nlp.cv_analyzer import CVAnalyzer
from modules.knowledge.nlp.confidence_scorer import ConfidenceScorer
from modules.knowledge.nlp.taxonomy_mapper import TaxonomyMapper


class TestCVAnalysisIntegration:
    """Integration tests for complete CV analysis workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = CVAnalyzer()
        
        # Complete sample CV
        self.sample_cv = """
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
    
    def test_complete_cv_analysis(self):
        """Test complete CV analysis pipeline."""
        result = self.analyzer.analyze_cv(self.sample_cv)
        
        # Verify structure
        assert 'skills' in result
        assert 'education' in result
        assert 'experience' in result
        assert 'certifications' in result
        assert 'metadata' in result
        
        # Verify metadata
        metadata = result['metadata']
        assert 'analysis_timestamp' in metadata
        assert 'language_detected' in metadata
        assert 'total_sections_found' in metadata
        assert 'overall_confidence' in metadata
        
        # Verify overall confidence is within bounds
        assert 0 <= metadata['overall_confidence'] <= 1
    
    def test_skills_extraction_with_confidence(self):
        """Test skills extraction with confidence scoring."""
        result = self.analyzer.analyze_cv(self.sample_cv)
        
        skills = result['skills']
        assert len(skills) > 0
        
        # Each skill should have required fields
        for skill in skills:
            assert 'name' in skill
            assert 'confidence' in skill
            assert 'context' in skill
            assert 'position' in skill
            assert 0 <= skill['confidence'] <= 1
        
        # Should find expected skills
        skill_names = [skill['name'] for skill in skills]
        expected_skills = ['Python', 'JavaScript', 'React', 'FastAPI']
        
        for expected_skill in expected_skills:
            assert any(expected_skill.lower() in skill.lower() 
                      for skill in skill_names)
    
    def test_education_extraction_with_confidence(self):
        """Test education extraction with confidence scoring."""
        result = self.analyzer.analyze_cv(self.sample_cv)
        
        education = result['education']
        assert len(education) > 0
        
        # Each education entry should have required fields
        for edu in education:
            assert 'name' in edu
            assert 'confidence' in edu
            assert 'degree' in edu
            assert 'institution' in edu
            assert 0 <= edu['confidence'] <= 1
        
        # Should find Stanford University
        institutions = [edu['institution'] for edu in education]
        assert any('Stanford' in inst for inst in institutions)
    
    def test_experience_extraction_with_confidence(self):
        """Test experience extraction with confidence scoring."""
        result = self.analyzer.analyze_cv(self.sample_cv)
        
        experience = result['experience']
        assert len(experience) > 0
        
        # Each experience entry should have required fields
        for exp in experience:
            assert 'name' in exp
            assert 'confidence' in exp
            assert 'title' in exp
            assert 'company' in exp
            assert 0 <= exp['confidence'] <= 1
        
        # Should find Tech Corp
        companies = [exp['company'] for exp in experience]
        assert any('Tech Corp' in company for company in companies)
    
    def test_certifications_extraction_with_confidence(self):
        """Test certification extraction with confidence scoring."""
        result = self.analyzer.analyze_cv(self.sample_cv)
        
        certifications = result['certifications']
        assert len(certifications) > 0
        
        # Each certification should have required fields
        for cert in certifications:
            assert 'name' in cert
            assert 'confidence' in cert
            assert 0 <= cert['confidence'] <= 1
        
        # Should find AWS certification
        cert_names = [cert['name'] for cert in certifications]
        assert any('AWS' in cert for cert in cert_names)
    
    def test_taxonomy_mapping_integration(self):
        """Test taxonomy mapping integration."""
        result = self.analyzer.analyze_cv(self.sample_cv)
        
        # Test that skills can be mapped to taxonomy
        mapper = TaxonomyMapper()
        
        skills = result['skills']
        mapped_skills = []
        
        for skill in skills[:5]:  # Test first 5 skills
            mapping_result = mapper.map_skill(skill['name'])
            mapped_skills.append(mapping_result)
        
        # Should have some mapped skills
        mapped_count = sum(1 for ms in mapped_skills if ms.match_type != 'no_match')
        assert mapped_count > 0
        
        # All results should be valid
        for mapping_result in mapped_skills:
            assert hasattr(mapping_result, 'original_value')
            assert hasattr(mapping_result, 'mapped_value')
            assert hasattr(mapping_result, 'match_type')
            assert hasattr(mapping_result, 'confidence')
            assert 0 <= mapping_result.confidence <= 1
    
    def test_confidence_scoring_integration(self):
        """Test confidence scoring integration."""
        result = self.analyzer.analyze_cv(self.sample_cv)
        
        scorer = ConfidenceScorer()
        
        # Test overall confidence calculation
        overall_confidence = scorer.calculate_overall_confidence(result)
        assert 0 <= overall_confidence <= 1
        
        # Should match the metadata confidence
        assert abs(overall_confidence - result['metadata']['overall_confidence']) < 0.1
    
    def test_multilingual_support(self):
        """Test multilingual CV support."""
        french_cv = """
        Jean Dupont
        Ingénieur Logiciel
        
        ÉDUCATION
        Licence en Informatique
        Université de Paris, 2015-2019
        
        EXPÉRIENCE
        Développeur Senior chez Tech France (2020-Présent)
        - Développement d'API REST avec Python
        - Équipe de 5 développeurs
        
        COMPÉTENCES
        Programmation: Python, JavaScript
        Frameworks: React, Django
        """
        
        result = self.analyzer.analyze_cv(french_cv)
        
        # Should detect French language
        assert result['metadata']['language_detected'] == 'fr'
        
        # Should still extract sections
        assert len(result['skills']) > 0
        assert len(result['experience']) > 0
        assert len(result['education']) > 0
    
    def test_error_handling(self):
        """Test error handling for edge cases."""
        # Empty CV
        with pytest.raises(ValueError):
            self.analyzer.analyze_cv("")
        
        with pytest.raises(ValueError):
            self.analyzer.analyze_cv("   ")
        
        # Very short CV
        with pytest.raises(ValueError):
            self.analyzer.analyze_cv("Short")
        
        # Malformed CV (should not raise but return minimal analysis)
        malformed_cv = "asdfghjkl;qwertyuiop" * 10
        result = self.analyzer.analyze_cv(malformed_cv)
        
        assert 'metadata' in result
        assert result['metadata']['language_detected'] in ['en', 'unknown']
        assert result['metadata']['total_sections_found'] == 0
    
    def test_performance_with_large_cv(self):
        """Test performance with large CV content."""
        # Create a large CV
        large_cv = self.sample_cv + "\n"
        
        # Add many skills
        skills = ["Python", "JavaScript", "Java", "C++", "React", "Angular", "Vue.js", 
                 "Node.js", "Django", "Flask", "FastAPI", "Spring", ".NET", "PHP", "Ruby",
                 "Go", "Rust", "Swift", "Kotlin", "Scala", "TypeScript", "SQL", "NoSQL",
                 "MongoDB", "PostgreSQL", "MySQL", "Redis", "Docker", "Kubernetes"]
        
        large_cv += "ADDITIONAL SKILLS\n"
        large_cv += ", ".join(skills) + "\n"
        
        # Add many experiences
        for i in range(10):
            large_cv += f"""
        Experience {i+1}: Developer at Company {i+1}
        - Worked on various projects
        - Used {skills[i%len(skills)]} extensively
        """
        
        # Should still process without issues
        result = self.analyzer.analyze_cv(large_cv)
        
        assert 'metadata' in result
        # CV analyzer normalizes whitespace aggressively; ensure word count remains substantially larger than baseline (~250+ words)
        assert result['metadata']['word_count'] >= 250
        assert result['metadata']['language_detected'] == 'en'


class TestConfidenceScorerIntegration:
    """Integration tests for confidence scoring."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scorer = ConfidenceScorer()
    
    def test_complete_confidence_workflow(self):
        """Test complete confidence scoring workflow."""
        cv_analysis = {
            'skills': [
                {'name': 'Python', 'confidence': 0.9},
                {'name': 'JavaScript', 'confidence': 0.8},
                {'name': 'Unknown Skill', 'confidence': 0.3}
            ],
            'education': [
                {'name': 'Bachelor of Science', 'confidence': 0.9}
            ],
            'experience': [
                {'name': 'Software Engineer', 'confidence': 0.8}
            ],
            'certifications': [
                {'name': 'AWS Certified', 'confidence': 0.9}
            ]
        }
        
        overall_confidence = self.scorer.calculate_overall_confidence(cv_analysis)
        
        assert 0 <= overall_confidence <= 1
        assert overall_confidence >= 0.5  # Should be reasonably high with good data
    
    def test_ambiguity_detection_workflow(self):
        """Test ambiguity detection in workflow."""
        ambiguous_items = [
            {
                'name': 'Management',
                'context': 'Various management tasks',
                'position': 'experience_description',
                'explicit_mention': False
            },
            {
                'name': 'Communication',
                'context': 'Good communication skills etc.',
                'position': 'skills_section',
                'explicit_mention': True
            }
        ]
        
        ambiguity_scores = [self.scorer.detect_ambiguity(item) for item in ambiguous_items]
        
        for score in ambiguity_scores:
            assert 0 <= score <= 1
        
        # First item should be more ambiguous
        assert ambiguity_scores[0] > ambiguity_scores[1]


class TestTaxonomyMapperIntegration:
    """Integration tests for taxonomy mapping."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mapper = TaxonomyMapper()
    
    def test_batch_mapping_workflow(self):
        """Test batch mapping workflow."""
        user_skills = [
            'Python', 'JavaScript', 'React', 'Unknown Skill 1',
            'Node.js', 'Django', 'Unknown Skill 2', 'Java'
        ]
        
        results = self.mapper.map_skills_batch(user_skills)
        
        assert len(results) == len(user_skills)
        
        # Calculate statistics
        stats = self.mapper.calculate_mapping_statistics(results)
        
        assert stats['total_skills'] == 8
        assert stats['mapped_skills'] > 0
        assert stats['unmapped_skills'] > 0
        assert 0 <= stats['mapping_rate'] <= 1
        assert 0 <= stats['average_confidence'] <= 1
        
        # Check match type distribution
        match_dist = stats['match_type_distribution']
        assert 'exact' in match_dist
        assert 'no_match' in match_dist
    
    def test_taxonomy_validation_workflow(self):
        """Test taxonomy validation workflow."""
        # Valid taxonomy
        valid_taxonomy = {
            'skills': {
                'programming': {
                    'languages': ['Python', 'JavaScript'],
                    'frameworks': ['React', 'Django']
                }
            }
        }
        
        assert self.mapper.validate_taxonomy(valid_taxonomy) == True
        
        # Invalid taxonomies
        invalid_taxonomies = [
            {},  # Empty
            {'other': {}},  # Missing skills
            {'skills': {}},  # Empty skills
            None  # None
        ]
        
        for invalid_taxonomy in invalid_taxonomies:
            assert self.mapper.validate_taxonomy(invalid_taxonomy) == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
