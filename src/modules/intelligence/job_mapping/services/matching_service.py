"""Job matching service for KASH → Job mapping."""

import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass

from ..models import (
    JobProfile,
    JobMatchResult,
    JobMatchingRequest,
    JobMatchingResponse,
    CompetencyMatch,
    DomainMatchResult,
    ConfidenceMetrics,
    AlternativeSuggestion,
    KASHDomainEnum,
    CompetencyLevel,
    ConfidenceLevel
)
from .job_profile_service import JobProfileService


@dataclass
class LearnerKASHProfile:
    """Learner KASH profile for matching."""
    learner_id: str
    knowledge: Dict[str, CompetencyLevel] = None
    abilities: Dict[str, CompetencyLevel] = None
    skills: Dict[str, CompetencyLevel] = None
    habits: Dict[str, CompetencyLevel] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.knowledge is None:
            self.knowledge = {}
        if self.abilities is None:
            self.abilities = {}
        if self.skills is None:
            self.skills = {}
        if self.habits is None:
            self.habits = {}
        if self.metadata is None:
            self.metadata = {}
    
    def get_competency_level(self, domain: KASHDomainEnum, competency_name: str) -> CompetencyLevel:
        """Get competency level for a specific domain and competency."""
        domain_map = {
            KASHDomainEnum.KNOWLEDGE: self.knowledge,
            KASHDomainEnum.ABILITIES: self.abilities,
            KASHDomainEnum.SKILLS: self.skills,
            KASHDomainEnum.HABITS: self.habits,
        }
        return domain_map.get(domain, {}).get(competency_name, CompetencyLevel.NONE)
    
    def has_competency(self, domain: KASHDomainEnum, competency_name: str) -> bool:
        """Check if learner has a specific competency."""
        return self.get_competency_level(domain, competency_name) != CompetencyLevel.NONE


class JobMatchingService:
    """Service for matching learners to job profiles based on KASH competencies."""
    
    def __init__(self, job_profile_service: Optional[JobProfileService] = None):
        self.job_profile_service = job_profile_service or JobProfileService()
        self.level_hierarchy = {
            CompetencyLevel.NONE: 0,
            CompetencyLevel.BASIC: 1,
            CompetencyLevel.INTERMEDIATE: 2,
            CompetencyLevel.ADVANCED: 3,
            CompetencyLevel.EXPERT: 4
        }
    
    def _calculate_competency_match(self, learner_profile: LearnerKASHProfile, 
                                  job_competency) -> CompetencyMatch:
        """Calculate match score for a single competency."""
        learner_level = learner_profile.get_competency_level(
            job_competency.domain, 
            job_competency.name
        )
        
        # Calculate match score based on level difference
        required_level_value = self.level_hierarchy[job_competency.required_level]
        learner_level_value = self.level_hierarchy[learner_level]
        
        if learner_level_value >= required_level_value:
            # Learner meets or exceeds requirements
            match_score = 1.0
        else:
            # Partial match based on how close they are
            level_diff = required_level_value - learner_level_value
            match_score = max(0.0, 1.0 - (level_diff * 0.3))  # 30% penalty per level
        
        # Generate gap analysis
        gap_analysis = self._generate_gap_analysis(learner_level, job_competency.required_level)
        
        # Generate improvement suggestions
        improvement_suggestions = self._generate_improvement_suggestions(
            learner_level, job_competency.required_level, job_competency
        )
        
        return CompetencyMatch(
            competency_name=job_competency.name,
            domain=job_competency.domain,
            required_level=job_competency.required_level,
            learner_level=learner_level,
            match_score=match_score,
            weight=job_competency.weight,
            weighted_score=match_score * job_competency.weight,
            gap_analysis=gap_analysis,
            improvement_suggestions=improvement_suggestions
        )
    
    def _generate_gap_analysis(self, learner_level: CompetencyLevel, 
                             required_level: CompetencyLevel) -> str:
        """Generate analysis of the gap between learner and required levels."""
        if learner_level == required_level:
            return "Learner meets the required level exactly."
        elif self.level_hierarchy[learner_level] > self.level_hierarchy[required_level]:
            return f"Learner exceeds requirements ({learner_level} vs {required_level})."
        else:
            gap_levels = self.level_hierarchy[required_level] - self.level_hierarchy[learner_level]
            return f"Learner needs {gap_levels} level(s) of development ({learner_level} → {required_level})."
    
    def _generate_improvement_suggestions(self, learner_level: CompetencyLevel, 
                                        required_level: CompetencyLevel, 
                                        job_competency) -> List[str]:
        """Generate improvement suggestions for competency gaps."""
        suggestions = []
        
        if self.level_hierarchy[learner_level] < self.level_hierarchy[required_level]:
            # General improvement suggestions
            if learner_level == CompetencyLevel.NONE:
                suggestions.append(f"Start learning {job_competency.name} fundamentals")
            elif learner_level == CompetencyLevel.BASIC:
                suggestions.append(f"Practice intermediate {job_competency.name} exercises")
            elif learner_level == CompetencyLevel.INTERMEDIATE:
                suggestions.append(f"Work on advanced {job_competency.name} projects")
            
            # Specific suggestions based on job competency success signals
            for signal in job_competency.success_signals:
                suggestions.append(f"Develop ability to: {signal}")
        
        return suggestions
    
    def _calculate_domain_match(self, learner_profile: LearnerKASHProfile, 
                              job_profile: JobProfile, 
                              domain: KASHDomainEnum) -> DomainMatchResult:
        """Calculate match result for a specific KASH domain."""
        job_competencies = job_profile.get_competencies_by_domain(domain)
        competency_matches = []
        
        for job_comp in job_competencies:
            comp_match = self._calculate_competency_match(learner_profile, job_comp)
            competency_matches.append(comp_match)
        
        # Calculate overall domain score
        if competency_matches:
            total_weighted_score = sum(match.weighted_score for match in competency_matches)
            total_weight = sum(match.weight for match in competency_matches)
            overall_score = total_weighted_score / total_weight if total_weight > 0 else 0.0
        else:
            overall_score = 0.0
        
        # Identify strengths and weaknesses
        strengths = [match.competency_name for match in competency_matches if match.is_met]
        weaknesses = [match.competency_name for match in competency_matches if not match.is_met]
        
        # Generate recommendations
        recommendations = []
        if weaknesses:
            recommendations.append(f"Focus on developing: {', '.join(weaknesses[:3])}")
        if strengths:
            recommendations.append(f"Leverage strengths in: {', '.join(strengths[:3])}")
        
        return DomainMatchResult(
            domain=domain,
            overall_score=overall_score,
            competency_matches=competency_matches,
            total_weight=sum(match.weight for match in competency_matches),
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations
        )
    
    def _calculate_overall_match_score(self, domain_results: Dict[KASHDomainEnum, DomainMatchResult]) -> float:
        """Calculate overall match score across all KASH domains."""
        if not domain_results:
            return 0.0
        
        total_score = 0.0
        total_weight = 0.0
        
        for domain_result in domain_results.values():
            total_score += domain_result.overall_score * domain_result.total_weight
            total_weight += domain_result.total_weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def _generate_match_summary(self, overall_score: float, job_title: str) -> str:
        """Generate a summary of the match result."""
        if overall_score >= 0.8:
            return f"Strong match for {job_title}. Learner demonstrates most required competencies and shows high potential for success."
        elif overall_score >= 0.6:
            return f"Good match for {job_title} with some development areas. Learner has solid foundation and needs targeted skill development."
        else:
            return f"Potential match for {job_title} requiring significant development. Learner needs substantial skill building in key areas."
    
    def _identify_key_strengths(self, domain_results: Dict[KASHDomainEnum, DomainMatchResult]) -> List[str]:
        """Identify key strengths across all domains."""
        strengths = []
        for domain_result in domain_results.values():
            for match in domain_result.met_competencies:
                if match.match_score >= 0.8:  # High-performing competencies
                    strengths.append(f"{match.domain.value}: {match.competency_name}")
        return strengths[:5]  # Top 5 strengths
    
    def _identify_development_areas(self, domain_results: Dict[KASHDomainEnum, DomainMatchResult]) -> List[str]:
        """Identify areas needing development."""
        development_areas = []
        for domain_result in domain_results.values():
            for match in domain_result.unmet_competencies:
                if match.weight >= 0.7:  # High-weight missing competencies
                    development_areas.append(f"{match.domain.value}: {match.competency_name}")
        return development_areas[:5]  # Top 5 development areas
    
    def _generate_next_steps(self, overall_score: float, domain_results: Dict[KASHDomainEnum, DomainMatchResult], job_profile: JobProfile) -> List[str]:
        """Generate recommended next steps."""
        next_steps = []
        
        if overall_score >= 0.8:
            next_steps.append("Start applying for entry-level positions in this field")
            next_steps.append("Build portfolio showcasing relevant projects")
        elif overall_score >= 0.6:
            next_steps.append("Focus on developing key competencies identified in gaps")
            next_steps.append("Seek internships or junior opportunities")
        else:
            next_steps.append("Enroll in courses to build foundational skills")
            next_steps.append("Work on personal projects to gain practical experience")
        
        # Add domain-specific next steps
        for domain_result in domain_results.values():
            if domain_result.recommendations:
                next_steps.extend(domain_result.recommendations[:2])
        
        return next_steps[:6]  # Top 6 next steps
    
    def _estimate_readiness_timeline(self, overall_score: float) -> str:
        """Estimate timeline to be ready for this role."""
        if overall_score >= 0.8:
            return "Ready to apply now"
        elif overall_score >= 0.7:
            return "3-6 months of focused development"
        elif overall_score >= 0.5:
            return "6-12 months of skill building"
        else:
            return "12+ months of comprehensive development"
    
    def _calculate_confidence_metrics(self, overall_score: float, job_profile: JobProfile,
                                    learner_profile: LearnerKASHProfile) -> ConfidenceMetrics:
        """Calculate confidence metrics for the match."""
        # Data completeness - how complete is the learner's KASH profile
        total_possible_competencies = 20  # Estimated average per profile
        learner_competencies = (
            len(learner_profile.knowledge) + 
            len(learner_profile.abilities) + 
            len(learner_profile.skills) + 
            len(learner_profile.habits)
        )
        data_completeness = min(1.0, learner_competencies / total_possible_competencies)
        
        # Profile coverage - how well the job profile covers required competencies
        total_job_competencies = len(job_profile.all_competencies)
        profile_coverage = min(1.0, total_job_competencies / 10)  # Assuming 10 is ideal
        
        # Uncertainty factors
        uncertainty_factors = []
        if data_completeness < 0.5:
            uncertainty_factors.append("Limited learner data")
        if overall_score < 0.6:
            uncertainty_factors.append("Low match score")
        if total_job_competencies < 5:
            uncertainty_factors.append("Limited job profile data")
        
        return ConfidenceMetrics.calculate_confidence(
            match_score=overall_score,
            data_completeness=data_completeness,
            profile_coverage=profile_coverage,
            uncertainty_factors=uncertainty_factors
        )
    
    def _find_alternative_suggestions(self, learner_profile: LearnerKASHProfile,
                                     primary_match: JobMatchResult, 
                                     max_suggestions: int = 3) -> List[AlternativeSuggestion]:
        """Find alternative job suggestions."""
        alternatives = []
        
        # Get similar profiles from job profile service
        similar_profiles = self.job_profile_service.get_similar_profiles(
            primary_match.job_profile.job_id, 
            limit=max_suggestions * 2
        )
        
        for similar_data in similar_profiles[:max_suggestions]:
            similar_profile = similar_data["profile"]
            
            # Calculate match for alternative
            alternative_match = self.match_learner_to_job(learner_profile, similar_profile)
            
            # Generate reasoning
            reasoning_parts = []
            if similar_data["sector_similarity"] > 0.5:
                reasoning_parts.append(f"Same sector ({similar_data['sector_similarity']:.1%} overlap)")
            if similar_data["competency_similarity"] > 0.5:
                reasoning_parts.append(f"Similar competency requirements ({similar_data['competency_similarity']:.1%} overlap)")
            
            # Determine transition difficulty
            score_diff = primary_match.overall_match_score - alternative_match.overall_match_score
            if score_diff <= 0.1:
                transition_difficulty = "Low - very similar requirements"
            elif score_diff <= 0.2:
                transition_difficulty = "Medium - some additional skills needed"
            else:
                transition_difficulty = "High - significant skill development required"
            
            alternative = AlternativeSuggestion(
                job_profile=similar_profile,
                match_score=alternative_match.overall_match_score,
                confidence_level=alternative_match.confidence_metrics.overall_confidence,
                reasoning=". ".join(reasoning_parts) if reasoning_parts else "Similar role with comparable requirements",
                similarity_factors=[
                    f"Sector similarity: {similar_data['sector_similarity']:.1%}",
                    f"Competency overlap: {similar_data['competency_similarity']:.1%}",
                    f"Seniority alignment: {similar_data['seniority_similarity']:.1%}"
                ],
                transition_difficulty=transition_difficulty
            )
            
            alternatives.append(alternative)
        
        return alternatives
    
    def match_learner_to_job(self, learner_profile: LearnerKASHProfile, 
                           job_profile: JobProfile) -> JobMatchResult:
        """Match a learner to a specific job profile."""
        # Calculate domain-specific matches
        domain_results = {}
        for domain in KASHDomainEnum:
            domain_result = self._calculate_domain_match(learner_profile, job_profile, domain)
            domain_results[domain] = domain_result
        
        # Calculate overall match score
        overall_score = self._calculate_overall_match_score(domain_results)
        
        # Generate analysis components
        match_summary = self._generate_match_summary(overall_score, job_profile.title)
        key_strengths = self._identify_key_strengths(domain_results)
        development_areas = self._identify_development_areas(domain_results)
        next_steps = self._generate_next_steps(overall_score, domain_results, job_profile)
        readiness_timeline = self._estimate_readiness_timeline(overall_score)
        
        # Create match result
        match_result = JobMatchResult(
            learner_id=learner_profile.learner_id,
            job_profile=job_profile,
            overall_match_score=overall_score,
            domain_results=domain_results,
            confidence_metrics=self._calculate_confidence_metrics(
                overall_score, job_profile, learner_profile
            ),
            alternative_suggestions=[],  # Will be populated later
            match_summary=match_summary,
            key_strengths=key_strengths,
            development_areas=development_areas,
            next_steps=next_steps,
            estimated_readiness_timeline=readiness_timeline
        )
        
        return match_result
    
    def find_job_matches(self, request: JobMatchingRequest) -> JobMatchingResponse:
        """Find job matches for a learner based on their KASH profile."""
        start_time = datetime.utcnow()
        
        # Parse learner KASH profile
        learner_profile = LearnerKASHProfile(
            learner_id=request.learner_id,
            knowledge=request.learner_kash_profile.get("knowledge", {}),
            abilities=request.learner_kash_profile.get("abilities", {}),
            skills=request.learner_kash_profile.get("skills", {}),
            habits=request.learner_kash_profile.get("habits", {}),
            metadata=request.learner_kash_profile.get("metadata", {})
        )
        
        # Get candidate job profiles
        all_profiles = self.job_profile_service.get_all_profiles()
        
        # Apply filters if specified
        if request.target_sectors:
            # Filter by sectors (would need to convert string to enum)
            pass
        
        if request.seniority_preference:
            # Filter by seniority (would need to convert string to enum)
            pass
        
        # Calculate matches for all profiles
        match_results = []
        for job_profile in all_profiles:
            match_result = self.match_learner_to_job(learner_profile, job_profile)
            match_results.append(match_result)
        
        # Sort by match score (descending)
        match_results.sort(key=lambda x: x.overall_match_score, reverse=True)
        
        # Add alternative suggestions to top matches
        if request.include_alternatives and match_results:
            top_match = match_results[0]
            alternatives = self._find_alternative_suggestions(
                learner_profile, top_match, request.max_alternatives
            )
            top_match.alternative_suggestions = alternatives
        
        # Calculate processing time
        end_time = datetime.utcnow()
        processing_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        return JobMatchingResponse(
            request_id=str(uuid.uuid4()),
            learner_id=request.learner_id,
            primary_matches=match_results,
            total_candidates_evaluated=len(all_profiles),
            processing_time_ms=processing_time_ms,
            algorithm_version="1.0",
            generated_at=end_time
        )
