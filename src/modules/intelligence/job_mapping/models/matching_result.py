"""Matching result and confidence metrics models for KASH → Job mapping."""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum

from .job_profile import JobProfile, KASHDomainEnum, CompetencyLevel


class MatchScoreType(str, Enum):
    """Types of match scores."""
    OVERALL = "overall"
    KNOWLEDGE = "knowledge"
    ABILITIES = "abilities"
    SKILLS = "skills"
    HABITS = "habits"


class ConfidenceLevel(str, Enum):
    """Confidence level enumeration."""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class CompetencyMatch(BaseModel):
    """Individual competency matching result."""
    competency_name: str = Field(..., description="Name of the competency")
    domain: KASHDomainEnum = Field(..., description="KASH domain")
    required_level: CompetencyLevel = Field(..., description="Required level for the job")
    learner_level: CompetencyLevel = Field(..., description="Current learner level")
    match_score: float = Field(..., ge=0, le=1, description="Match score for this competency (0-1)")
    weight: float = Field(..., ge=0, le=1, description="Weight in overall score")
    weighted_score: float = Field(..., description="Weighted contribution to overall score")
    gap_analysis: str = Field(..., description="Analysis of the gap between required and current level")
    improvement_suggestions: List[str] = Field(default_factory=list, description="Suggestions to improve this competency")
    
    @property
    def is_met(self) -> bool:
        """Check if the learner meets the required level."""
        level_hierarchy = {
            CompetencyLevel.NONE: 0,
            CompetencyLevel.BASIC: 1,
            CompetencyLevel.INTERMEDIATE: 2,
            CompetencyLevel.ADVANCED: 3,
            CompetencyLevel.EXPERT: 4
        }
        
        return level_hierarchy.get(self.learner_level, 0) >= level_hierarchy.get(self.required_level, 0)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "competency_name": "python_programming",
                "domain": "skills",
                "required_level": "intermediate",
                "learner_level": "basic",
                "match_score": 0.6,
                "weight": 0.8,
                "weighted_score": 0.48,
                "gap_analysis": "Learner has basic Python knowledge but needs more practice with advanced concepts",
                "improvement_suggestions": [
                    "Complete intermediate Python tutorials",
                    "Build a small project using OOP concepts",
                    "Practice with data structures and algorithms"
                ]
            }
        }
    }


class DomainMatchResult(BaseModel):
    """Matching result for a specific KASH domain."""
    domain: KASHDomainEnum = Field(..., description="KASH domain")
    overall_score: float = Field(..., ge=0, le=1, description="Overall match score for this domain")
    competency_matches: List[CompetencyMatch] = Field(..., description="Individual competency matches")
    total_weight: float = Field(..., description="Total weight of competencies in this domain")
    strengths: List[str] = Field(default_factory=list, description="Strengths in this domain")
    weaknesses: List[str] = Field(default_factory=list, description="Weaknesses in this domain")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for improvement")
    
    @property
    def met_competencies(self) -> List[CompetencyMatch]:
        """Get competencies where learner meets requirements."""
        return [match for match in self.competency_matches if match.is_met]
    
    @property
    def unmet_competencies(self) -> List[CompetencyMatch]:
        """Get competencies where learner doesn't meet requirements."""
        return [match for match in self.competency_matches if not match.is_met]


class ConfidenceMetrics(BaseModel):
    """Confidence metrics for job matching."""
    overall_confidence: ConfidenceLevel = Field(..., description="Overall confidence level")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence score (0-1)")
    data_completeness: float = Field(..., ge=0, le=1, description="How complete the learner data is")
    profile_coverage: float = Field(..., ge=0, le=1, description="How well job profile covers required competencies")
    historical_accuracy: Optional[float] = Field(None, ge=0, le=1, description="Historical accuracy of similar matches")
    uncertainty_factors: List[str] = Field(default_factory=list, description="Factors contributing to uncertainty")
    confidence_rationale: str = Field(..., description="Explanation of confidence assessment")
    
    @classmethod
    def calculate_confidence(cls, match_score: float, data_completeness: float, 
                           profile_coverage: float, uncertainty_factors: List[str]) -> 'ConfidenceMetrics':
        """Calculate confidence metrics based on various factors."""
        # Base confidence from match score and data quality
        base_confidence = (match_score * 0.6 + data_completeness * 0.3 + profile_coverage * 0.1)
        
        # Adjust for uncertainty factors
        uncertainty_penalty = len(uncertainty_factors) * 0.05
        adjusted_confidence = max(0, base_confidence - uncertainty_penalty)
        
        # Determine confidence level
        if adjusted_confidence >= 0.9:
            confidence_level = ConfidenceLevel.VERY_HIGH
        elif adjusted_confidence >= 0.7:
            confidence_level = ConfidenceLevel.HIGH
        elif adjusted_confidence >= 0.5:
            confidence_level = ConfidenceLevel.MEDIUM
        elif adjusted_confidence >= 0.3:
            confidence_level = ConfidenceLevel.LOW
        else:
            confidence_level = ConfidenceLevel.VERY_LOW
        
        # Generate rationale
        rationale_parts = []
        if match_score >= 0.8:
            rationale_parts.append("Strong match score")
        elif match_score >= 0.6:
            rationale_parts.append("Moderate match score")
        else:
            rationale_parts.append("Lower match score")
            
        if data_completeness >= 0.8:
            rationale_parts.append("Complete learner data")
        elif data_completeness >= 0.6:
            rationale_parts.append("Adequate learner data")
        else:
            rationale_parts.append("Limited learner data")
        
        if uncertainty_factors:
            rationale_parts.append(f"Uncertainty factors: {', '.join(uncertainty_factors)}")
        
        return cls(
            overall_confidence=confidence_level,
            confidence_score=adjusted_confidence,
            data_completeness=data_completeness,
            profile_coverage=profile_coverage,
            uncertainty_factors=uncertainty_factors,
            confidence_rationale=". ".join(rationale_parts) + "."
        )


class AlternativeSuggestion(BaseModel):
    """Alternative job suggestion."""
    job_profile: JobProfile = Field(..., description="Alternative job profile")
    match_score: float = Field(..., ge=0, le=1, description="Match score for alternative")
    confidence_level: ConfidenceLevel = Field(..., description="Confidence in this suggestion")
    reasoning: str = Field(..., description="Why this is a good alternative")
    similarity_factors: List[str] = Field(..., description="Factors making this similar to primary match")
    transition_difficulty: str = Field(..., description="Difficulty of transitioning to this role")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "match_score": 0.75,
                "confidence_level": "high",
                "reasoning": "Similar technical requirements but with more focus on frontend development",
                "similarity_factors": ["Programming skills", "Problem-solving abilities", "Team collaboration"],
                "transition_difficulty": "Low - mainly requires learning new frameworks"
            }
        }
    }


class JobMatchResult(BaseModel):
    """Complete job matching result for a learner."""
    learner_id: str = Field(..., description="Learner identifier")
    job_profile: JobProfile = Field(..., description="Matched job profile")
    overall_match_score: float = Field(..., ge=0, le=1, description="Overall match score (0-1)")
    
    # Domain-specific results
    domain_results: Dict[KASHDomainEnum, DomainMatchResult] = Field(..., description="Results by KASH domain")
    
    # Confidence and alternatives
    confidence_metrics: ConfidenceMetrics = Field(..., description="Confidence metrics")
    alternative_suggestions: List[AlternativeSuggestion] = Field(default_factory=list, description="Alternative job suggestions")
    
    # Analysis and recommendations
    match_summary: str = Field(..., description="Summary of the match")
    key_strengths: List[str] = Field(default_factory=list, description="Key strengths for this role")
    development_areas: List[str] = Field(default_factory=list, description="Areas needing development")
    next_steps: List[str] = Field(default_factory=list, description="Recommended next steps")
    estimated_readiness_timeline: Optional[str] = Field(None, description="Estimated timeline to be ready for this role")
    
    # Metadata
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    calculation_version: str = Field(default="1.0", description="Algorithm version used")
    
    @property
    def is_strong_match(self) -> bool:
        """Check if this is a strong match (score >= 0.8)."""
        return self.overall_match_score >= 0.8
    
    @property
    def is_moderate_match(self) -> bool:
        """Check if this is a moderate match (0.6 <= score < 0.8)."""
        return 0.6 <= self.overall_match_score < 0.8
    
    @property
    def needs_development(self) -> bool:
        """Check if this role needs significant development (score < 0.6)."""
        return self.overall_match_score < 0.6
    
    def get_domain_score(self, domain: KASHDomainEnum) -> Optional[float]:
        """Get match score for a specific domain."""
        return self.domain_results.get(domain, DomainMatchResult(
            domain=domain,
            overall_score=0.0,
            competency_matches=[],
            total_weight=0.0
        )).overall_score
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "learner_id": "learner_123",
                "overall_match_score": 0.78,
                "match_summary": "Strong candidate with good technical foundation, needs some experience with specific frameworks",
                "key_strengths": ["Strong programming fundamentals", "Good problem-solving skills", "Quick learner"],
                "development_areas": ["Specific framework experience", "Project management skills"],
                "next_steps": ["Build portfolio projects", "Learn React framework", "Gain internship experience"],
                "estimated_readiness_timeline": "6-12 months with focused development"
            }
        }
    }


class JobMatchingRequest(BaseModel):
    """Request for job matching."""
    learner_id: str = Field(..., description="Learner identifier")
    learner_kash_profile: Dict[str, Any] = Field(..., description="Learner's KASH profile")
    target_sectors: Optional[List[str]] = Field(None, description="Preferred sectors to focus on")
    seniority_preference: Optional[str] = Field(None, description="Preferred seniority level")
    include_alternatives: bool = Field(True, description="Whether to include alternative suggestions")
    max_alternatives: int = Field(default=3, ge=1, le=10, description="Maximum alternative suggestions")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "learner_id": "learner_123",
                "target_sectors": ["technology", "finance"],
                "seniority_preference": "mid_level",
                "include_alternatives": True,
                "max_alternatives": 3
            }
        }
    }


class JobMatchingResponse(BaseModel):
    """Response containing job matching results."""
    request_id: str = Field(..., description="Unique request identifier")
    learner_id: str = Field(..., description="Learner identifier")
    primary_matches: List[JobMatchResult] = Field(..., description="Primary job matches (ranked)")
    total_candidates_evaluated: int = Field(..., description="Total job profiles evaluated")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    algorithm_version: str = Field(..., description="Algorithm version used")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def top_match(self) -> Optional[JobMatchResult]:
        """Get the top match."""
        return self.primary_matches[0] if self.primary_matches else None
    
    @property
    def strong_matches(self) -> List[JobMatchResult]:
        """Get all strong matches (score >= 0.8)."""
        return [match for match in self.primary_matches if match.is_strong_match]
    
    @property
    def moderate_matches(self) -> List[JobMatchResult]:
        """Get all moderate matches (0.6 <= score < 0.8)."""
        return [match for match in self.primary_matches if match.is_moderate_match]
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "request_id": "req_456",
                "learner_id": "learner_123",
                "total_candidates_evaluated": 50,
                "processing_time_ms": 250,
                "algorithm_version": "1.0"
            }
        }
    }
