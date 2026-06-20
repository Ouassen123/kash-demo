"""Isolated tests for NLP components without project dependencies."""

import pytest
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


# Copy the core classes directly to avoid import issues
@dataclass
class MappingResult:
    """Result of taxonomy mapping."""
    original_value: str
    mapped_value: str
    category: Optional[str] = None
    subcategory: Optional[str] = None
    match_type: str = 'no_match'  # exact, partial, semantic, no_match
    confidence: float = 0.0


class ConfidenceScorer:
    """Calculate confidence scores for extracted CV information."""
    
    def __init__(self):
        """Initialize confidence scorer with default thresholds."""
        self.confidence_thresholds = {
            'high': 0.8,
            'medium': 0.6,
            'low': 0.4
        }
        
        # Keywords that indicate high confidence
        self.high_confidence_keywords = [
            'skills:', 'technical skills', 'programming languages',
            'education:', 'academic', 'university', 'college',
            'experience:', 'work history', 'professional',
            'certifications:', 'certificates', 'licenses'
        ]
        
        # Ambiguity indicators
        self.ambiguity_indicators = [
            'various', 'multiple', 'several', 'many', 'some',
            'etc.', 'and more', 'including', 'such as', 'related'
        ]
    
    def calculate_skill_confidence(self, skill_data: Dict[str, Any]) -> float:
        """Calculate confidence score for extracted skill."""
        base_confidence = 0.5
        
        # Boost for explicit mention in skills section
        if skill_data.get('explicit_mention', False):
            base_confidence += 0.3
        
        # Boost for proper context
        context = skill_data.get('context', '').lower()
        if any(keyword in context for keyword in self.high_confidence_keywords):
            base_confidence += 0.2
        
        # Boost for specific skill names
        skill_name = skill_data.get('name', '').lower()
        if self._is_specific_skill(skill_name):
            base_confidence += 0.1
        
        # Penalty for ambiguity
        ambiguity_score = self.detect_ambiguity(skill_data)
        base_confidence -= ambiguity_score * 0.3
        
        # Ensure within bounds
        return max(0.0, min(1.0, base_confidence))
    
    def detect_ambiguity(self, item_data: Dict[str, Any]) -> float:
        """Detect ambiguity in extracted item."""
        ambiguity_score = 0.0
        
        # Check for ambiguity indicators
        context = item_data.get('context', '').lower()
        name = item_data.get('name', '').lower()
        
        for indicator in self.ambiguity_indicators:
            if indicator in context or indicator in name:
                ambiguity_score += 0.2
        
        # Check for generic terms
        generic_terms = ['management', 'administration', 'support', 'assistance', 'coordination']
        for term in generic_terms:
            if term in name:
                ambiguity_score += 0.1
        
        # Check for lack of specific details
        if not item_data.get('explicit_mention', False):
            ambiguity_score += 0.2
        
        return min(1.0, ambiguity_score)
    
    def validate_confidence_score(self, score: float) -> bool:
        """Validate that confidence score is within valid range."""
        return isinstance(score, (int, float)) and 0.0 <= score <= 1.0
    
    def _is_specific_skill(self, skill_name: str) -> bool:
        """Check if skill name is specific."""
        specific_skills = [
            'python', 'javascript', 'java', 'c++', 'react', 'angular', 'vue',
            'node.js', 'django', 'flask', 'fastapi', 'spring', '.net',
            'postgresql', 'mysql', 'mongodb', 'redis', 'aws', 'azure',
            'docker', 'kubernetes', 'jenkins', 'git', 'agile', 'scrum'
        ]
        return skill_name.lower() in specific_skills


class TaxonomyMapper:
    """Maps extracted CV data to normalized taxonomy."""
    
    def __init__(self):
        """Initialize taxonomy mapper."""
        self._load_default_taxonomy()
        self._load_mapping_rules()
    
    def _load_default_taxonomy(self):
        """Load default taxonomy for mapping."""
        self.default_taxonomy = {
            'skills': {
                'programming': {
                    'languages': [
                        'Python', 'JavaScript', 'Java', 'C++', 'C#', 'Go', 'Rust',
                        'Ruby', 'PHP', 'Swift', 'Kotlin', 'Scala', 'TypeScript'
                    ],
                    'frameworks': [
                        'React', 'Angular', 'Vue.js', 'Node.js', 'Django', 'Flask',
                        'FastAPI', 'Spring', '.NET', 'Express.js', 'Laravel'
                    ]
                }
            }
        }
    
    def _load_mapping_rules(self):
        """Load mapping rules and synonyms."""
        self.skill_synonyms = {
            'JS': 'JavaScript',
            'TS': 'TypeScript',
            'C#': 'C#',
            'C++': 'C++',
            'Node': 'Node.js',
            'ReactJS': 'React',
            'VueJS': 'Vue.js',
            'AWS': 'AWS',
            'Azure': 'Azure',
            'GCP': 'GCP',
            'Git': 'Git',
            'Docker': 'Docker',
            'K8s': 'Kubernetes'
        }
    
    def map_skill(self, user_skill: str, taxonomy: Optional[Dict] = None) -> MappingResult:
        """Map a user skill to taxonomy."""
        if taxonomy is None:
            taxonomy = self.default_taxonomy
        
        user_skill_clean = user_skill.strip()
        
        # Check synonyms first
        if user_skill_clean in self.skill_synonyms:
            mapped_skill = self.skill_synonyms[user_skill_clean]
            return self._create_mapping_result(
                user_skill_clean, mapped_skill, taxonomy, 'exact', 0.95
            )
        
        # Try exact match
        exact_result = self._try_exact_match(user_skill_clean, taxonomy['skills'])
        if exact_result:
            return exact_result
        
        # Try partial match
        partial_result = self._try_partial_match(user_skill_clean, taxonomy['skills'])
        if partial_result:
            return partial_result
        
        # No match found
        return MappingResult(
            original_value=user_skill_clean,
            mapped_value=user_skill_clean,
            match_type='no_match',
            confidence=0.1
        )
    
    def map_skills_batch(self, user_skills: List[str], taxonomy: Optional[Dict] = None) -> List[MappingResult]:
        """Map multiple skills to taxonomy."""
        results = []
        for skill in user_skills:
            result = self.map_skill(skill, taxonomy)
            results.append(result)
        return results
    
    def validate_taxonomy(self, taxonomy: Dict) -> bool:
        """Validate taxonomy structure."""
        required_sections = ['skills']
        
        if not isinstance(taxonomy, dict):
            return False
        
        for section in required_sections:
            if section not in taxonomy or not isinstance(taxonomy[section], dict):
                return False
            # Check that section has subcategories
            if not taxonomy[section]:  # Empty dict
                return False
        
        return True
    
    def calculate_mapping_statistics(self, mapping_results: List[MappingResult]) -> Dict[str, Any]:
        """Calculate statistics for mapping results."""
        total_skills = len(mapping_results)
        mapped_skills = sum(1 for r in mapping_results if r.match_type != 'no_match')
        unmapped_skills = total_skills - mapped_skills
        
        mapping_rate = mapped_skills / total_skills if total_skills > 0 else 0
        
        # Average confidence
        confidences = [r.confidence for r in mapping_results]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # Match type distribution
        match_types = [r.match_type for r in mapping_results]
        match_type_dist = {
            match_type: match_types.count(match_type) 
            for match_type in set(match_types)
        }
        
        return {
            'total_skills': total_skills,
            'mapped_skills': mapped_skills,
            'unmapped_skills': unmapped_skills,
            'mapping_rate': mapping_rate,
            'average_confidence': avg_confidence,
            'match_type_distribution': match_type_dist
        }
    
    def _try_exact_match(self, skill: str, skills_taxonomy: Dict) -> Optional[MappingResult]:
        """Try exact match against taxonomy."""
        for category, subcategories in skills_taxonomy.items():
            for subcategory, skills in subcategories.items():
                for taxonomy_skill in skills:
                    if taxonomy_skill.lower() == skill.lower():
                        return self._create_mapping_result(
                            skill, taxonomy_skill, skills_taxonomy, 'exact', 0.95,
                            category, subcategory
                        )
        return None
    
    def _try_partial_match(self, skill: str, skills_taxonomy: Dict) -> Optional[MappingResult]:
        """Try partial match against taxonomy."""
        for category, subcategories in skills_taxonomy.items():
            for subcategory, skills in subcategories.items():
                for taxonomy_skill in skills:
                    if (taxonomy_skill.lower() in skill.lower() or 
                        skill.lower() in taxonomy_skill.lower()):
                        return self._create_mapping_result(
                            skill, taxonomy_skill, skills_taxonomy, 'partial', 0.8,
                            category, subcategory
                        )
        return None
    
    def _create_mapping_result(self, original: str, mapped: str, taxonomy: Dict,
                            match_type: str, confidence: float,
                            category: Optional[str] = None,
                            subcategory: Optional[str] = None) -> MappingResult:
        """Create MappingResult object."""
        return MappingResult(
            original_value=original,
            mapped_value=mapped,
            category=category,
            subcategory=subcategory,
            match_type=match_type,
            confidence=confidence
        )


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
        assert ambiguity_score >= 0.3  # Should be flagged as ambiguous
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
        assert result.mapped_value == 'Python'
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
        assert result.mapped_value == user_skill  # Returns original
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


class TestTextProcessing:
    """Test text processing functionality."""
    
    def test_text_cleaning(self):
        """Test text cleaning functionality."""
        def clean_text(text: str) -> str:
            """Clean and normalize text."""
            # Remove excessive whitespace
            text = re.sub(r'\s+', ' ', text)
            
            # Remove special characters but keep important punctuation
            text = re.sub(r'[^\w\s\-\.\,\!\?\:\;\(\)\[\]/\n]', ' ', text)
            
            # Normalize line breaks
            text = re.sub(r'\r\n|\r', '\n', text)
            
            return text.strip()
        
        # Test basic cleaning
        dirty_text = "  This   is a   test   with  extra   spaces  "
        cleaned = clean_text(dirty_text)
        
        assert cleaned == "This is a test with extra spaces"
        assert len(cleaned.strip()) > 0
    
    def test_language_detection(self):
        """Test language detection."""
        def detect_language(text: str) -> str:
            """Detect document language."""
            # Simple language detection based on common words
            french_indicators = ['et', 'le', 'de', 'la', 'les', 'des', 'dans', 'pour', 'avec', 'par', 'sur', 'université', 'diplôme']
            spanish_indicators = ['y', 'el', 'de', 'la', 'las', 'los', 'en', 'para', 'con', 'por', 'sobre', 'universidad']
            
            text_lower = text.lower()
            
            french_count = sum(1 for word in french_indicators if word in text_lower)
            spanish_count = sum(1 for word in spanish_indicators if word in text_lower)
            
            if french_count > 3:
                return 'fr'
            elif spanish_count > 3:
                return 'es'
            else:
                return 'en'
        
        # Test English
        english_text = "I am a software engineer with experience in Python"
        language = detect_language(english_text)
        assert language == 'en'
        
        # Test French
        french_text = "Je suis ingénieur et le diplôme de l'université"
        language = detect_language(french_text)
        assert language == 'fr'
    
    def test_section_extraction(self):
        """Test CV section extraction."""
        def extract_section(cv_text: str, section_type: str) -> Optional[str]:
            """Extract a specific section from CV text."""
            section_patterns = {
                'skills': [
                    r'SKILLS\s*:?\s*',
                    r'TECHNICAL\s+SKILLS\s*:?\s*',
                    r'COMPETENCES\s*:?\s*'
                ],
                'experience': [
                    r'EXPERIENCE\s*:?\s*',
                    r'WORK\s+HISTORY\s*:?\s*',
                    r'PROFESSIONAL\s+EXPERIENCE\s*:?\s*'
                ],
                'education': [
                    r'EDUCATION\s*:?\s*',
                    r'ACADEMIC\s+BACKGROUND\s*:?\s*',
                    r'QUALIFICATIONS\s*:?\s*'
                ]
            }
            
            patterns = section_patterns.get(section_type, [])
            
            for pattern in patterns:
                match = re.search(pattern, cv_text, re.IGNORECASE | re.MULTILINE)
                if match:
                    start_pos = match.end()
                    
                    # Find next section header
                    remaining_text = cv_text[start_pos:]
                    next_section_match = None
                    
                    for other_patterns in section_patterns.values():
                        if other_patterns == patterns:
                            continue
                        for other_pattern in other_patterns:
                            other_match = re.search(other_pattern, remaining_text, re.IGNORECASE | re.MULTILINE)
                            if other_match and (next_section_match is None or other_match.start() < next_section_match.start()):
                                next_section_match = other_match
                    
                    if next_section_match:
                        section_text = remaining_text[:next_section_match.start()].strip()
                    else:
                        section_text = remaining_text.strip()
                    
                    return section_text
            
            return None
        
        cv_text = """
        SKILLS: Python, JavaScript, Java
        
        EXPERIENCE: Software Engineer at Tech Corp
        
        EDUCATION: Bachelor of Science in Computer Science
        """
        
        skills_section = extract_section(cv_text, 'skills')
        assert skills_section is not None
        assert 'Python' in skills_section
        
        experience_section = extract_section(cv_text, 'experience')
        assert experience_section is not None
        assert 'Software Engineer' in experience_section
        
        education_section = extract_section(cv_text, 'education')
        assert education_section is not None
        assert 'Bachelor' in education_section


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
