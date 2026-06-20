"""SHAP-based explainability for KASH scoring and career recommendations."""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import uuid
from enum import Enum

from src.core.logging import get_logger

logger = get_logger(__name__)


class ExplanationType(str, Enum):
    """Types of explanations available."""
    FEATURE_IMPORTANCE = "feature_importance"
    CAREER_PATH = "career_path"
    SKILL_GAP = "skill_gap"
    ASSESSMENT_IMPACT = "assessment_impact"
    RECOMMENDATION_REASONING = "recommendation_reasoning"


@dataclass
class FeatureImportance:
    """Feature importance with SHAP values."""
    feature_name: str
    feature_value: float
    shap_value: float
    contribution_percentage: float
    direction: str  # positive, negative, neutral
    explanation: str


@dataclass
class CareerPathExplanation:
    """Explanation for career path recommendation."""
    career_path: str
    match_score: float
    key_factors: List[str]
    skill_gaps: List[str]
    alignment_reasons: List[str]
    development_needs: List[str]


@dataclass
class SkillGapAnalysis:
    """Analysis of skill gaps for target role."""
    target_role: str
    current_skills: Dict[str, float]
    required_skills: Dict[str, float]
    skill_gaps: Dict[str, float]
    priority_gaps: List[str]
    development_timeline: Dict[str, str]


@dataclass
class AssessmentImpact:
    """Impact of specific assessment on overall score."""
    assessment_type: str
    assessment_name: str
    score_contribution: float
    confidence_impact: float
    improvement_potential: float


class SHAPExplainer:
    """SHAP-based explainability engine for KASH career intelligence."""
    
    def __init__(self):
        # Feature importance weights for different domains
        self.feature_weights = {
            'knowledge': {
                'cv_completeness': 0.15,
                'skill_coverage': 0.20,
                'education_level': 0.15,
                'certification_count': 0.10,
                'language_proficiency': 0.10,
                'industry_knowledge': 0.15,
                'theoretical_understanding': 0.15
            },
            'abilities': {
                'problem_solving': 0.20,
                'critical_thinking': 0.15,
                'creativity': 0.15,
                'communication': 0.15,
                'leadership': 0.10,
                'teamwork': 0.10,
                'adaptability': 0.10,
                'emotional_intelligence': 0.05
            },
            'skills': {
                'technical_proficiency': 0.25,
                'practical_experience': 0.20,
                'project_complexity': 0.15,
                'tool_mastery': 0.10,
                'code_quality': 0.10,
                'collaboration_skills': 0.10,
                'continuous_learning': 0.10
            },
            'experience': {
                'years_experience': 0.20,
                'project_diversity': 0.15,
                'leadership_experience': 0.15,
                'industry_experience': 0.15,
                'achievement_impact': 0.10,
                'responsibility_level': 0.10,
                'growth_trajectory': 0.15
            }
        }
        
        # Career path templates with required skill levels
        self.career_templates = {
            'software_engineer': {
                'required_skills': {
                    'programming': 0.8,
                    'problem_solving': 0.7,
                    'algorithms': 0.7,
                    'system_design': 0.6,
                    'collaboration': 0.6
                },
                'preferred_kash_weights': {
                    'knowledge': 0.2,
                    'abilities': 0.25,
                    'skills': 0.4,
                    'experience': 0.15
                }
            },
            'data_scientist': {
                'required_skills': {
                    'statistics': 0.8,
                    'machine_learning': 0.7,
                    'programming': 0.7,
                    'data_analysis': 0.8,
                    'communication': 0.6
                },
                'preferred_kash_weights': {
                    'knowledge': 0.35,
                    'abilities': 0.25,
                    'skills': 0.3,
                    'experience': 0.1
                }
            },
            'product_manager': {
                'required_skills': {
                    'strategic_thinking': 0.8,
                    'communication': 0.8,
                    'market_analysis': 0.7,
                    'leadership': 0.7,
                    'technical_understanding': 0.6
                },
                'preferred_kash_weights': {
                    'knowledge': 0.25,
                    'abilities': 0.4,
                    'skills': 0.2,
                    'experience': 0.15
                }
            },
            'ux_designer': {
                'required_skills': {
                    'design_thinking': 0.8,
                    'user_research': 0.7,
                    'prototyping': 0.7,
                    'visual_design': 0.6,
                    'collaboration': 0.7
                },
                'preferred_kash_weights': {
                    'knowledge': 0.3,
                    'abilities': 0.35,
                    'skills': 0.25,
                    'experience': 0.1
                }
            },
            'devops_engineer': {
                'required_skills': {
                    'infrastructure': 0.8,
                    'automation': 0.7,
                    'monitoring': 0.7,
                    'security': 0.6,
                    'collaboration': 0.6
                },
                'preferred_kash_weights': {
                    'knowledge': 0.2,
                    'abilities': 0.25,
                    'skills': 0.45,
                    'experience': 0.1
                }
            }
        }
        
        # Skill development timelines (in weeks)
        self.development_timelines = {
            'beginner_to_intermediate': 12,
            'intermediate_to_advanced': 24,
            'advanced_to_expert': 48,
            'new_skill_foundation': 8,
            'skill_enhancement': 6
        }
    
    def explain_kash_score(
        self,
        kash_score: float,
        domain_scores: Dict[str, float],
        feature_values: Dict[str, float],
        baseline_score: float = 50.0
    ) -> List[FeatureImportance]:
        """
        Explain KASH score using SHAP-like feature importance.
        
        Args:
            kash_score: Final KASH score
            domain_scores: Scores for each KASH domain
            feature_values: Raw feature values
            baseline_score: Expected baseline score
            
        Returns:
            List of feature importance explanations
        """
        logger.info(f"Generating SHAP explanation for KASH score: {kash_score}")
        
        try:
            # Calculate SHAP-like values for each feature
            feature_importances = []
            
            # Domain-level contributions
            for domain, score in domain_scores.items():
                domain_weight = self.feature_weights.get(domain, {})
                
                for feature, weight in domain_weight.items():
                    feature_name = f"{domain}_{feature}"
                    feature_value = feature_values.get(feature_name, 0)
                    
                    # Calculate SHAP value (simplified)
                    expected_value = baseline_score * weight
                    actual_value = score * weight * feature_value
                    shap_value = actual_value - expected_value
                    
                    # Calculate contribution percentage
                    contribution_percentage = abs(shap_value) / abs(kash_score - baseline_score) * 100 if kash_score != baseline_score else 0
                    
                    # Determine direction
                    direction = 'positive' if shap_value > 0 else 'negative' if shap_value < 0 else 'neutral'
                    
                    # Generate explanation
                    explanation = self._generate_feature_explanation(
                        feature_name, feature_value, shap_value, direction
                    )
                    
                    feature_importances.append(FeatureImportance(
                        feature_name=feature_name,
                        feature_value=feature_value,
                        shap_value=shap_value,
                        contribution_percentage=contribution_percentage,
                        direction=direction,
                        explanation=explanation
                    ))
            
            # Sort by absolute contribution
            feature_importances.sort(
                key=lambda x: abs(x.shap_value), 
                reverse=True
            )
            
            return feature_importances[:10]  # Top 10 features
            
        except Exception as e:
            logger.error(f"SHAP explanation failed: {e}")
            raise
    
    def explain_career_path(
        self,
        user_profile: Dict[str, Any],
        target_career: str,
        current_kash_score: float
    ) -> CareerPathExplanation:
        """
        Explain career path recommendation.
        
        Args:
            user_profile: Complete user profile
            target_career: Target career path
            current_kash_score: Current KASH score
            
        Returns:
            Detailed career path explanation
        """
        logger.info(f"Explaining career path recommendation for {target_career}")
        
        try:
            # Get career template
            career_template = self.career_templates.get(target_career.lower().replace(' ', '_'), {})
            required_skills = career_template.get('required_skills', {})
            preferred_weights = career_template.get('preferred_kash_weights', {})
            
            # Calculate match score
            match_score = self._calculate_career_match_score(
                user_profile, required_skills, preferred_weights
            )
            
            # Identify key factors
            key_factors = self._identify_key_factors(user_profile, required_skills)
            
            # Analyze skill gaps
            skill_gaps = self._analyze_skill_gaps(user_profile, required_skills)
            
            # Generate alignment reasons
            alignment_reasons = self._generate_alignment_reasons(
                user_profile, required_skills, match_score
            )
            
            # Identify development needs
            development_needs = self._identify_development_needs(skill_gaps)
            
            return CareerPathExplanation(
                career_path=target_career,
                match_score=match_score,
                key_factors=key_factors,
                skill_gaps=skill_gaps,
                alignment_reasons=alignment_reasons,
                development_needs=development_needs
            )
            
        except Exception as e:
            logger.error(f"Career path explanation failed: {e}")
            raise
    
    def analyze_skill_gaps(
        self,
        current_skills: Dict[str, float],
        target_role: str,
        experience_level: str = "intermediate"
    ) -> SkillGapAnalysis:
        """
        Analyze skill gaps for target role.
        
        Args:
            current_skills: Current skill levels
            target_role: Target role name
            experience_level: Required experience level
            
        Returns:
            Detailed skill gap analysis
        """
        logger.info(f"Analyzing skill gaps for {target_role}")
        
        try:
            # Get required skills for target role
            career_template = self.career_templates.get(target_role.lower().replace(' ', '_'), {})
            required_skills = career_template.get('required_skills', {})
            
            # Adjust required skills based on experience level
            adjusted_required = self._adjust_skills_for_experience(
                required_skills, experience_level
            )
            
            # Calculate skill gaps
            skill_gaps = {}
            for skill, required_level in adjusted_required.items():
                current_level = current_skills.get(skill, 0)
                gap = max(0, required_level - current_level)
                skill_gaps[skill] = gap
            
            # Identify priority gaps
            priority_gaps = sorted(
                skill_gaps.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]  # Top 5 priority gaps
            priority_gaps = [gap[0] for gap in priority_gaps]
            
            # Generate development timeline
            development_timeline = self._generate_development_timeline(skill_gaps)
            
            return SkillGapAnalysis(
                target_role=target_role,
                current_skills=current_skills,
                required_skills=adjusted_required,
                skill_gaps=skill_gaps,
                priority_gaps=priority_gaps,
                development_timeline=development_timeline
            )
            
        except Exception as e:
            logger.error(f"Skill gap analysis failed: {e}")
            raise
    
    def explain_assessment_impact(
        self,
        assessments: List[Dict[str, Any]],
        overall_score: float
    ) -> List[AssessmentImpact]:
        """
        Explain impact of each assessment on overall score.
        
        Args:
            assessments: List of completed assessments
            overall_score: Current overall KASH score
            
        Returns:
            List of assessment impact explanations
        """
        logger.info(f"Explaining assessment impact for {len(assessments)} assessments")
        
        try:
            impacts = []
            
            for assessment in assessments:
                assessment_type = assessment.get('assessment_type', 'unknown')
                assessment_name = assessment.get('assessment_name', 'Unnamed Assessment')
                score = assessment.get('normalized_score', 0)
                confidence = assessment.get('confidence_score', 0)
                
                # Calculate contribution to overall score
                domain_weight = self._get_domain_weight(assessment_type)
                score_contribution = score * domain_weight
                
                # Calculate confidence impact
                confidence_impact = confidence * 0.1  # Confidence affects score reliability
                
                # Calculate improvement potential
                improvement_potential = (100 - score) * domain_weight
                
                impacts.append(AssessmentImpact(
                    assessment_type=assessment_type,
                    assessment_name=assessment_name,
                    score_contribution=score_contribution,
                    confidence_impact=confidence_impact,
                    improvement_potential=improvement_potential
                ))
            
            # Sort by contribution
            impacts.sort(key=lambda x: x.score_contribution, reverse=True)
            
            return impacts
            
        except Exception as e:
            logger.error(f"Assessment impact explanation failed: {e}")
            raise
    
    def explain_recommendations(
        self,
        recommendations: List[str],
        user_profile: Dict[str, Any],
        domain_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Explain why specific recommendations were made.
        
        Args:
            recommendations: List of recommendations
            user_profile: User profile data
            domain_scores: KASH domain scores
            
        Returns:
            Detailed recommendation explanations
        """
        logger.info(f"Explaining {len(recommendations)} recommendations")
        
        try:
            explanations = {}
            
            for i, recommendation in enumerate(recommendations):
                # Determine recommendation type
                rec_type = self._classify_recommendation(recommendation)
                
                # Generate explanation based on type
                if rec_type == 'knowledge':
                    explanation = self._explain_knowledge_recommendation(
                        recommendation, domain_scores.get('knowledge', 0), user_profile
                    )
                elif rec_type == 'abilities':
                    explanation = self._explain_abilities_recommendation(
                        recommendation, domain_scores.get('abilities', 0), user_profile
                    )
                elif rec_type == 'skills':
                    explanation = self._explain_skills_recommendation(
                        recommendation, domain_scores.get('skills', 0), user_profile
                    )
                elif rec_type == 'experience':
                    explanation = self._explain_experience_recommendation(
                        recommendation, domain_scores.get('experience', 0), user_profile
                    )
                else:
                    explanation = self._explain_general_recommendation(
                        recommendation, domain_scores, user_profile
                    )
                
                explanations[f"recommendation_{i+1}"] = {
                    'recommendation': recommendation,
                    'type': rec_type,
                    'explanation': explanation,
                    'priority': self._calculate_recommendation_priority(
                        recommendation, domain_scores, user_profile
                    ),
                    'expected_impact': self._estimate_recommendation_impact(
                        recommendation, domain_scores
                    )
                }
            
            return explanations
            
        except Exception as e:
            logger.error(f"Recommendation explanation failed: {e}")
            raise
    
    def _generate_feature_explanation(
        self, 
        feature_name: str, 
        feature_value: float, 
        shap_value: float, 
        direction: str
    ) -> str:
        """Generate human-readable explanation for feature importance."""
        
        domain = feature_name.split('_')[0]
        feature = '_'.join(feature_name.split('_')[1:])
        
        if direction == 'positive':
            return f"Strong {feature} in {domain} domain positively impacts your score by {abs(shap_value):.1f} points"
        elif direction == 'negative':
            return f"Weak {feature} in {domain} domain reduces your score by {abs(shap_value):.1f} points"
        else:
            return f"{feature} in {domain} domain has neutral impact on your score"
    
    def _calculate_career_match_score(
        self,
        user_profile: Dict[str, Any],
        required_skills: Dict[str, float],
        preferred_weights: Dict[str, float]
    ) -> float:
        """Calculate career match score."""
        
        # Get user skills
        user_skills = user_profile.get('technical_skills', {})
        
        # Calculate skill match
        skill_matches = []
        for skill, required_level in required_skills.items():
            user_level = user_skills.get(skill, 0)
            match_score = min(user_level / required_level, 1.0) if required_level > 0 else 0
            skill_matches.append(match_score)
        
        skill_match_score = np.mean(skill_matches) if skill_matches else 0
        
        # Calculate KASH alignment
        domain_scores = user_profile.get('domain_scores', {})
        kash_alignment = 0
        for domain, weight in preferred_weights.items():
            domain_score = domain_scores.get(domain, 0)
            kash_alignment += domain_score * weight
        
        # Combine scores
        overall_match = (skill_match_score * 0.6) + (kash_alignment / 100 * 0.4)
        
        return overall_match * 100  # Convert to percentage
    
    def _identify_key_factors(
        self, 
        user_profile: Dict[str, Any], 
        required_skills: Dict[str, float]
    ) -> List[str]:
        """Identify key factors for career match."""
        factors = []
        
        user_skills = user_profile.get('technical_skills', {})
        
        # Strong matches
        for skill, required_level in required_skills.items():
            user_level = user_skills.get(skill, 0)
            if user_level >= required_level * 0.8:  # 80% match
                factors.append(f"Strong {skill} foundation")
        
        # High-scoring domains
        domain_scores = user_profile.get('domain_scores', {})
        top_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)[:2]
        for domain, score in top_domains:
            if score >= 70:
                factors.append(f"Excellent {domain} capabilities")
        
        return factors[:5]  # Top 5 factors
    
    def _analyze_skill_gaps(
        self, 
        user_profile: Dict[str, Any], 
        required_skills: Dict[str, float]
    ) -> List[str]:
        """Analyze skill gaps for target career."""
        gaps = []
        
        user_skills = user_profile.get('technical_skills', {})
        
        for skill, required_level in required_skills.items():
            user_level = user_skills.get(skill, 0)
            gap = required_level - user_level
            
            if gap > 0.3:  # Significant gap
                if gap > 0.5:
                    gaps.append(f"Critical gap in {skill}")
                else:
                    gaps.append(f"Develop {skill} skills")
        
        return gaps[:5]  # Top 5 gaps
    
    def _generate_alignment_reasons(
        self,
        user_profile: Dict[str, Any],
        required_skills: Dict[str, float],
        match_score: float
    ) -> List[str]:
        """Generate reasons for career alignment."""
        reasons = []
        
        if match_score >= 80:
            reasons.append("Excellent alignment with career requirements")
        elif match_score >= 60:
            reasons.append("Good alignment with some development needed")
        else:
            reasons.append("Partial alignment requiring significant development")
        
        # Domain-specific reasons
        domain_scores = user_profile.get('domain_scores', {})
        if domain_scores.get('skills', 0) >= 70:
            reasons.append("Strong technical foundation")
        if domain_scores.get('abilities', 0) >= 70:
            reasons.append("Well-developed cognitive abilities")
        if domain_scores.get('knowledge', 0) >= 70:
            reasons.append("Solid theoretical knowledge")
        
        return reasons
    
    def _identify_development_needs(self, skill_gaps: List[str]) -> List[str]:
        """Identify specific development needs."""
        needs = []
        
        for gap in skill_gaps:
            if 'Critical' in gap:
                needs.append(f"Priority: {gap.lower()}")
            else:
                needs.append(gap.lower())
        
        return needs
    
    def _adjust_skills_for_experience(
        self, 
        required_skills: Dict[str, float], 
        experience_level: str
    ) -> Dict[str, float]:
        """Adjust required skills based on experience level."""
        adjusted = required_skills.copy()
        
        multipliers = {
            'beginner': 0.6,
            'intermediate': 0.8,
            'advanced': 1.0,
            'expert': 1.2
        }
        
        multiplier = multipliers.get(experience_level.lower(), 0.8)
        
        for skill in adjusted:
            adjusted[skill] = min(adjusted[skill] * multiplier, 1.0)
        
        return adjusted
    
    def _generate_development_timeline(self, skill_gaps: Dict[str, float]) -> Dict[str, str]:
        """Generate development timeline for skill gaps."""
        timeline = {}
        
        for skill, gap in skill_gaps.items():
            if gap > 0.7:
                timeline[skill] = "6-12 months (extensive development needed)"
            elif gap > 0.4:
                timeline[skill] = "3-6 months (focused development)"
            elif gap > 0.2:
                timeline[skill] = "1-3 months (skill enhancement)"
            else:
                timeline[skill] = "2-4 weeks (quick improvement)"
        
        return timeline
    
    def _get_domain_weight(self, assessment_type: str) -> float:
        """Get weight for assessment type."""
        weights = {
            'knowledge': 0.25,
            'abilities': 0.25,
            'skills': 0.30,
            'experience': 0.20
        }
        return weights.get(assessment_type, 0.25)
    
    def _classify_recommendation(self, recommendation: str) -> str:
        """Classify recommendation type."""
        recommendation_lower = recommendation.lower()
        
        if any(keyword in recommendation_lower for keyword in ['knowledge', 'learn', 'study', 'education']):
            return 'knowledge'
        elif any(keyword in recommendation_lower for keyword in ['abilities', 'skills', 'practice', 'develop']):
            return 'abilities'
        elif any(keyword in recommendation_lower for keyword in ['technical', 'programming', 'code', 'project']):
            return 'skills'
        elif any(keyword in recommendation_lower for keyword in ['experience', 'work', 'internship', 'real-world']):
            return 'experience'
        else:
            return 'general'
    
    def _explain_knowledge_recommendation(
        self, 
        recommendation: str, 
        knowledge_score: float, 
        user_profile: Dict[str, Any]
    ) -> str:
        """Explain knowledge-based recommendation."""
        if knowledge_score < 50:
            return f"Your knowledge score ({knowledge_score:.1f}/100) indicates need for foundational learning in this area"
        elif knowledge_score < 70:
            return f"With a knowledge score of {knowledge_score:.1f}/100, expanding your theoretical understanding will significantly boost your overall profile"
        else:
            return f"Your strong knowledge foundation ({knowledge_score:.1f}/100) suggests you're ready for advanced topics in this area"
    
    def _explain_abilities_recommendation(
        self, 
        recommendation: str, 
        abilities_score: float, 
        user_profile: Dict[str, Any]
    ) -> str:
        """Explain abilities-based recommendation."""
        if abilities_score < 50:
            return f"Your abilities score ({abilities_score:.1f}/100) shows room for developing core cognitive and soft skills"
        elif abilities_score < 70:
            return f"Improving your abilities from {abilities_score:.1f}/100 will enhance your problem-solving and adaptability"
        else:
            return f"Your strong abilities ({abilities_score:.1f}/100) indicate readiness for leadership and complex challenges"
    
    def _explain_skills_recommendation(
        self, 
        recommendation: str, 
        skills_score: float, 
        user_profile: Dict[str, Any]
    ) -> str:
        """Explain skills-based recommendation."""
        if skills_score < 50:
            return f"Your skills score ({skills_score:.1f}/100) suggests need for practical, hands-on experience"
        elif skills_score < 70:
            return f"Building your technical skills from {skills_score:.1f}/100 will increase your marketability"
        else:
            return f"Your strong technical skills ({skills_score:.1f}/100) position you well for advanced roles"
    
    def _explain_experience_recommendation(
        self, 
        recommendation: str, 
        experience_score: float, 
        user_profile: Dict[str, Any]
    ) -> str:
        """Explain experience-based recommendation."""
        if experience_score < 50:
            return f"Your experience score ({experience_score:.1f}/100) indicates need for more real-world application"
        elif experience_score < 70:
            return f"Gaining diverse experience will raise your score from {experience_score:.1f}/100 and build credibility"
        else:
            return f"Your solid experience ({experience_score:.1f}/100) provides a strong foundation for career advancement"
    
    def _explain_general_recommendation(
        self, 
        recommendation: str, 
        domain_scores: Dict[str, float], 
        user_profile: Dict[str, Any]
    ) -> str:
        """Explain general recommendation."""
        lowest_domain = min(domain_scores.items(), key=lambda x: x[1])
        return f"This recommendation addresses your lowest-performing domain ({lowest_domain[0]}: {lowest_domain[1]:.1f}/100)"
    
    def _calculate_recommendation_priority(
        self, 
        recommendation: str, 
        domain_scores: Dict[str, float], 
        user_profile: Dict[str, Any]
    ) -> str:
        """Calculate priority level for recommendation."""
        rec_type = self._classify_recommendation(recommendation)
        domain_score = domain_scores.get(rec_type, 50)
        
        if domain_score < 40:
            return 'high'
        elif domain_score < 60:
            return 'medium'
        else:
            return 'low'
    
    def _estimate_recommendation_impact(
        self, 
        recommendation: str, 
        domain_scores: Dict[str, float]
    ) -> Dict[str, float]:
        """Estimate potential impact of recommendation."""
        rec_type = self._classify_recommendation(recommendation)
        current_score = domain_scores.get(rec_type, 50)
        
        # Estimate potential improvement
        if current_score < 40:
            potential_improvement = 20.0
        elif current_score < 60:
            potential_improvement = 15.0
        else:
            potential_improvement = 10.0
        
        # Calculate impact on overall score
        domain_weight = self._get_domain_weight(rec_type)
        overall_impact = potential_improvement * domain_weight
        
        return {
            'domain_improvement': potential_improvement,
            'overall_impact': overall_impact,
            'confidence': 0.7  # Estimated confidence
        }
