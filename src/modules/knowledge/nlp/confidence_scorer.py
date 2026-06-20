"""Confidence scoring for CV analysis results."""

from typing import Dict, List, Any, Optional
import re

from src.core.logging import get_logger
from .utils import ConfidenceMetrics

logger = get_logger(__name__)


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
        """
        Calculate confidence score for extracted skill.
        
        Args:
            skill_data: Dictionary containing skill information
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
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
    
    def calculate_education_confidence(self, education_data: Dict[str, Any]) -> float:
        """
        Calculate confidence score for education entry.
        
        Args:
            education_data: Dictionary containing education information
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        base_confidence = 0.3
        
        # Boost for complete information
        if education_data.get('degree'):
            base_confidence += 0.2
        if education_data.get('institution'):
            base_confidence += 0.2
        if education_data.get('dates'):
            base_confidence += 0.15
        if education_data.get('gpa'):
            base_confidence += 0.1
        
        # Boost for recognized degree types
        degree = education_data.get('degree', '').lower()
        if self._is_recognized_degree(degree):
            base_confidence += 0.1
        
        # Boost for recognized institutions
        institution = education_data.get('institution', '').lower()
        if self._is_recognized_institution(institution):
            base_confidence += 0.1
        
        # Penalty for incomplete information
        completeness = self._calculate_education_completeness(education_data)
        base_confidence *= completeness
        
        return max(0.0, min(1.0, base_confidence))
    
    def calculate_experience_confidence(self, experience_data: Dict[str, Any]) -> float:
        """
        Calculate confidence score for work experience entry.
        
        Args:
            experience_data: Dictionary containing experience information
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        base_confidence = 0.3
        
        # Boost for complete information
        if experience_data.get('title'):
            base_confidence += 0.2
        if experience_data.get('company'):
            base_confidence += 0.2
        if experience_data.get('dates'):
            base_confidence += 0.15
        if experience_data.get('description'):
            base_confidence += 0.1
        
        # Boost for achievements
        achievements = experience_data.get('achievements', [])
        if len(achievements) > 0:
            base_confidence += min(0.1, len(achievements) * 0.03)
        
        # Boost for recognized job levels
        title = experience_data.get('title', '').lower()
        if self._is_recognized_job_level(title):
            base_confidence += 0.1
        
        # Penalty for incomplete information
        completeness = self._calculate_experience_completeness(experience_data)
        base_confidence *= completeness
        
        return max(0.0, min(1.0, base_confidence))
    
    def calculate_certification_confidence(self, cert_data: Dict[str, Any]) -> float:
        """
        Calculate confidence score for certification entry.
        
        Args:
            cert_data: Dictionary containing certification information
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        base_confidence = 0.4
        
        # Boost for complete information
        if cert_data.get('name'):
            base_confidence += 0.2
        if cert_data.get('issuer'):
            base_confidence += 0.2
        if cert_data.get('date'):
            base_confidence += 0.1
        if cert_data.get('credential_id'):
            base_confidence += 0.1
        
        # Boost for recognized certifiers
        issuer_raw = cert_data.get('issuer')
        issuer = issuer_raw.lower() if isinstance(issuer_raw, str) else ''
        if self._is_recognized_certifier(issuer):
            base_confidence += 0.1
        
        # Penalty for incomplete information
        completeness = self._calculate_certification_completeness(cert_data)
        base_confidence *= completeness
        
        return max(0.0, min(1.0, base_confidence))
    
    def calculate_overall_confidence(self, cv_analysis: Dict[str, List[Dict]]) -> float:
        """
        Calculate overall confidence for the entire CV analysis.
        
        Args:
            cv_analysis: Complete CV analysis results
            
        Returns:
            Overall confidence score between 0.0 and 1.0
        """
        all_confidences = []
        
        for section in ['skills', 'education', 'experience', 'certifications']:
            items = cv_analysis.get(section, [])
            if items:
                section_confidences = [item.get('confidence', 0.0) for item in items]
                section_avg = sum(section_confidences) / len(section_confidences)
                all_confidences.append(section_avg)
        
        if not all_confidences:
            return 0.0
        
        # Weight sections differently
        weights = {
            'skills': 0.3,
            'education': 0.25,
            'experience': 0.35,
            'certifications': 0.1
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        section_names = ['skills', 'education', 'experience', 'certifications']
        for i, section_name in enumerate(section_names):
            if i < len(all_confidences):
                weight = weights.get(section_name, 0.25)
                weighted_sum += all_confidences[i] * weight
                total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        return weighted_sum / total_weight
    
    def detect_ambiguity(self, item_data: Dict[str, Any]) -> float:
        """
        Detect ambiguity in extracted item.
        
        Args:
            item_data: Dictionary containing item information
            
        Returns:
            Ambiguity score between 0.0 (no ambiguity) and 1.0 (high ambiguity)
        """
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
                ambiguity_score += 0.2
        
        # Check for lack of specific details
        if not item_data.get('explicit_mention', False):
            ambiguity_score += 0.3

        # Items outside dedicated skills section tend to be more ambiguous
        if item_data.get('position') != 'skills_section':
            ambiguity_score += 0.1
        
        return min(1.0, ambiguity_score)
    
    def validate_confidence_score(self, score: float) -> bool:
        """Validate confidence score is numeric and within 0-1."""
        return isinstance(score, (int, float)) and 0.0 <= score <= 1.0

    def get_confidence_level(self, score: float) -> str:
        """
        Get confidence level description.
        
        Args:
            score: Confidence score
            
        Returns:
            Confidence level string
        """
        if score >= self.confidence_thresholds['high']:
            return 'high'
        elif score >= self.confidence_thresholds['medium']:
            return 'medium'
        elif score >= self.confidence_thresholds['low']:
            return 'low'
        else:
            return 'very_low'
    
    def _is_specific_skill(self, skill_name: str) -> bool:
        """Check if skill name is specific."""
        specific_skills = [
            'python', 'javascript', 'java', 'c++', 'react', 'angular', 'vue',
            'node.js', 'django', 'flask', 'fastapi', 'spring', '.net',
            'postgresql', 'mysql', 'mongodb', 'redis', 'aws', 'azure',
            'docker', 'kubernetes', 'jenkins', 'git', 'agile', 'scrum'
        ]
        return skill_name.lower() in specific_skills
    
    def _is_recognized_degree(self, degree: str) -> bool:
        """Check if degree is recognized."""
        recognized_degrees = [
            'bachelor', 'master', 'phd', 'doctorate', 'b.s.', 'm.s.', 'ph.d.',
            'b.sc.', 'm.sc.', 'licence', 'master', 'doctorat'
        ]
        return any(recognized in degree for recognized in recognized_degrees)
    
    def _is_recognized_institution(self, institution: str) -> bool:
        """Check if institution is recognized."""
        recognized_indicators = [
            'university', 'college', 'institute', 'école', 'université',
            'institute of technology', 'polytechnic'
        ]
        return any(indicator in institution for indicator in recognized_indicators)
    
    def _is_recognized_job_level(self, title: str) -> bool:
        """Check if job title indicates recognized level."""
        level_indicators = [
            'senior', 'lead', 'principal', 'staff', 'junior', 'intern',
            'manager', 'director', 'head', 'chief', 'vp', 'vice president'
        ]
        return any(indicator in title for indicator in level_indicators)
    
    def _is_recognized_certifier(self, issuer: str) -> bool:
        issuer_raw = issuer
        issuer = issuer_raw.lower() if isinstance(issuer_raw, str) else ''
        recognized_certifiers = ['amazon web services', 'aws', 'google cloud', 'microsoft', 'oracle', 'cisco', 'pmp', 'scrum', 'ibm', 'azure', 'compTIA', 'pmi', 'isc2']
        return any(certifier in issuer for certifier in recognized_certifiers)
    
    def _calculate_education_completeness(self, education_data: Dict[str, Any]) -> float:
        """Calculate completeness score for education entry."""
        required_fields = ['degree', 'institution']
        optional_fields = ['dates', 'gpa', 'field_of_study']
        
        score = 0.0
        total_weight = len(required_fields) + len(optional_fields) * 0.5
        
        for field in required_fields:
            if education_data.get(field):
                score += 1.0
        
        for field in optional_fields:
            if education_data.get(field):
                score += 0.5
        
        return score / total_weight if total_weight > 0 else 0.0
    
    def _calculate_experience_completeness(self, experience_data: Dict[str, Any]) -> float:
        """Calculate completeness score for experience entry."""
        required_fields = ['title', 'company']
        optional_fields = ['dates', 'description', 'achievements']
        
        score = 0.0
        total_weight = len(required_fields) + len(optional_fields) * 0.5
        
        for field in required_fields:
            if experience_data.get(field):
                score += 1.0
        
        for field in optional_fields:
            if field == 'achievements':
                achievements = experience_data.get(field, [])
                if achievements:
                    score += 0.5
            elif experience_data.get(field):
                score += 0.5
        
        return score / total_weight if total_weight > 0 else 0.0
    
    def _calculate_certification_completeness(self, cert_data: Dict[str, Any]) -> float:
        """Calculate completeness score for certification entry."""
        required_fields = ['name']
        optional_fields = ['issuer', 'date', 'credential_id']
        
        score = 0.0
        total_weight = len(required_fields) + len(optional_fields) * 0.5
        
        for field in required_fields:
            if cert_data.get(field):
                score += 1.0
        
        for field in optional_fields:
            if cert_data.get(field):
                score += 0.5
        
        return score / total_weight if total_weight > 0 else 0.0
