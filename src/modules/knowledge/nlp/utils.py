"""Utility functions for NLP CV analysis."""

import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from src.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ConfidenceMetrics:
    """Confidence scoring metrics."""
    base_confidence: float
    context_boost: float
    completeness_bonus: float
    ambiguity_penalty: float
    final_confidence: float


@dataclass
class MappingResult:
    """Result of taxonomy mapping."""
    original_value: str
    mapped_value: str
    category: Optional[str] = None
    subcategory: Optional[str] = None
    match_type: str = 'no_match'  # exact, partial, semantic, no_match
    confidence: float = 0.0

    @property
    def mapped_skill(self) -> str:
        """Backward-compatible alias for legacy tests."""
        return self.mapped_value

    @mapped_skill.setter
    def mapped_skill(self, value: str) -> None:
        self.mapped_value = value


def validate_cv_input(cv_text: str) -> None:
    """
    Validate CV text input.
    
    Args:
        cv_text: Raw CV text content
        
    Raises:
        ValueError: If input is invalid
    """
    if not cv_text or len(cv_text.strip()) < 100:
        raise ValueError("CV text must be at least 100 characters long")
    
    if len(cv_text) > 50000:
        raise ValueError("CV text too long (max 50,000 characters)")
    
    # Check for potentially malicious content
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',  # JavaScript URLs
        r'data:text/html',  # HTML data URIs
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, cv_text, re.IGNORECASE):
            raise ValueError("CV text contains potentially malicious content")


def calculate_text_statistics(text: str) -> Dict[str, int]:
    """
    Calculate basic text statistics.
    
    Args:
        text: Text to analyze
        
    Returns:
        Dictionary with text statistics
    """
    return {
        'word_count': len(text.split()),
        'line_count': len(text.split('\n')),
        'character_count': len(text),
        'sentence_count': len(re.split(r'[.!?]+', text))
    }


def normalize_skill_name(skill_name: str) -> str:
    """
    Normalize skill name for consistent matching.
    
    Args:
        skill_name: Original skill name
        
    Returns:
        Normalized skill name
    """
    # Remove common prefixes/suffixes
    prefixes = ['Senior ', 'Junior ', 'Lead ']
    suffixes = [' (Senior)', '(Junior)', '(Lead)']
    
    normalized = skill_name.strip()
    
    for prefix in prefixes:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):]
            break
    
    for suffix in suffixes:
        if normalized.endswith(suffix):
            normalized = normalized[:-len(suffix)]
            break
    
    return normalized.strip()


def extract_years_from_text(text: str) -> Optional[float]:
    """
    Extract years of experience from text.
    
    Args:
        text: Text containing experience information
        
    Returns:
        Years of experience as float, or None if not found
    """
    # Look for patterns like "5 years", "3+ years", "10+ years experience"
    patterns = [
        r'(\d+)\s*\+?\s*years?',
        r'(\d+)\s*\+?\s*years?\s*experience',
        r'(\d+)\s*\+?\s*yr',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                years = float(match.group(1))
                return years
            except ValueError:
                continue
    
    return None


def detect_experience_level(title: str) -> Optional[str]:
    """
    Detect experience level from job title.
    
    Args:
        title: Job title string
        
    Returns:
        Experience level (entry, mid, senior, management) or None
    """
    title_lower = title.lower()
    
    if any(keyword in title_lower for keyword in ['intern', 'trainee', 'junior', 'entry']):
        return 'entry'
    elif any(keyword in title_lower for keyword in ['senior', 'lead', 'principal', 'staff']):
        return 'senior'
    elif any(keyword in title_lower for keyword in ['manager', 'director', 'head', 'chief']):
        return 'management'
    elif any(keyword in title_lower for keyword in ['engineer', 'developer', 'analyst', 'specialist']):
        return 'mid'
    
    return None


def format_confidence_score(score: float) -> str:
    """
    Format confidence score for display.
    
    Args:
        score: Confidence score (0-1)
        
    Returns:
        Formatted confidence string
    """
    if score >= 0.8:
        return f"{score:.0%} (High)"
    elif score >= 0.6:
        return f"{score:.0%} (Medium)"
    elif score >= 0.4:
        return f"{score:.0%} (Low)"
    else:
        return f"{score:.0%} (Very Low)"


def merge_analysis_results(primary: Dict[str, Any], secondary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two analysis results, keeping higher confidence values.
    
    Args:
        primary: Primary analysis results
        secondary: Secondary analysis results
        
    Returns:
        Merged analysis results
    """
    merged = primary.copy()
    
    for section in ['skills', 'education', 'experience', 'certifications']:
        if section in secondary:
            merged[section] = merge_extracted_items(
                primary.get(section, []),
                secondary.get(section, [])
            )
    
    # Merge metadata, keeping most recent timestamp
    if 'metadata' in secondary:
        merged['metadata'].update(secondary['metadata'])
    
    return merged


def merge_extracted_items(primary_items: List[Dict], secondary_items: List[Dict]) -> List[Dict]:
    """
    Merge extracted items, keeping higher confidence values.
    
    Args:
        primary_items: Primary extracted items
        secondary_items: Secondary extracted items
        
    Returns:
        Merged extracted items
    """
    merged = {}
    
    # Add primary items
    for item in primary_items:
        key = item['name'].lower()
        merged[key] = item
    
    # Add secondary items if higher confidence
    for item in secondary_items:
        key = item['name'].lower()
        if key not in merged or item['confidence'] > merged[key]['confidence']:
            merged[key] = item
    
    return list(merged.values())
