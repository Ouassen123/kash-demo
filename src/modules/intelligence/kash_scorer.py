"""KASH scoring engine for comprehensive career intelligence assessment."""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import uuid
from enum import Enum

from src.core.logging import get_logger

logger = get_logger(__name__)


class ScoreComponent(str, Enum):
    """KASH scoring components."""
    KNOWLEDGE = "knowledge"
    ABILITIES = "abilities" 
    SKILLS = "skills"
    EXPERIENCE = "experience"


@dataclass
class KASHScore:
    """KASH domain score with metadata."""
    domain: ScoreComponent
    raw_score: float
    normalized_score: float
    confidence: float
    weight: float
    breakdown: Dict[str, float]
    evidence: List[str]
    last_updated: datetime


@dataclass
class CareerReadinessScore:
    """Career readiness assessment score."""
    overall_score: float
    knowledge_score: float
    abilities_score: float
    skills_score: float
    experience_score: float
    confidence: float
    strengths: List[str]
    improvement_areas: List[str]
    career_stage: str
    recommendations: List[str]


class KASHScorer:
    """Advanced KASH scoring engine with weighted components and explainability."""
    
    def __init__(self):
        # KASH domain weights (configurable based on career goals)
        self.default_weights = {
            ScoreComponent.KNOWLEDGE: 0.25,
            ScoreComponent.ABILITIES: 0.25,
            ScoreComponent.SKILLS: 0.30,
            ScoreComponent.EXPERIENCE: 0.20
        }
        
        # Career stage thresholds
        self.career_stages = {
            'explorer': (0, 40),
            'beginner': (40, 55),
            'intermediate': (55, 70),
            'advanced': (70, 85),
            'expert': (85, 100)
        }
        
        # Industry-specific weight adjustments
        self.industry_weights = {
            'technology': {
                ScoreComponent.SKILLS: 0.35,
                ScoreComponent.KNOWLEDGE: 0.25,
                ScoreComponent.ABILITIES: 0.20,
                ScoreComponent.EXPERIENCE: 0.20
            },
            'healthcare': {
                ScoreComponent.KNOWLEDGE: 0.35,
                ScoreComponent.ABILITIES: 0.25,
                ScoreComponent.SKILLS: 0.20,
                ScoreComponent.EXPERIENCE: 0.20
            },
            'business': {
                ScoreComponent.ABILITIES: 0.30,
                ScoreComponent.EXPERIENCE: 0.25,
                ScoreComponent.KNOWLEDGE: 0.25,
                ScoreComponent.SKILLS: 0.20
            },
            'education': {
                ScoreComponent.KNOWLEDGE: 0.30,
                ScoreComponent.ABILITIES: 0.30,
                ScoreComponent.SKILLS: 0.20,
                ScoreComponent.EXPERIENCE: 0.20
            }
        }
        
        # Component scoring models
        self.scoring_models = {
            ScoreComponent.KNOWLEDGE: self._score_knowledge,
            ScoreComponent.ABILITIES: self._score_abilities,
            ScoreComponent.SKILLS: self._score_skills,
            ScoreComponent.EXPERIENCE: self._score_experience
        }
    
    def calculate_comprehensive_score(
        self,
        user_assessments: Dict[str, List[Dict[str, Any]]],
        industry: Optional[str] = None,
        career_goals: Optional[List[str]] = None,
        custom_weights: Optional[Dict[str, float]] = None
    ) -> CareerReadinessScore:
        """
        Calculate comprehensive KASH score from user assessments.
        
        Args:
            user_assessments: Dictionary of assessments by domain
            industry: Target industry for weight adjustment
            career_goals: List of career goals for scoring adjustment
            custom_weights: Optional custom weight overrides
            
        Returns:
            CareerReadinessScore with detailed breakdown
        """
        logger.info(f"Calculating comprehensive KASH score for user")
        
        try:
            # Get appropriate weights
            weights = self._get_weights(industry, custom_weights)
            
            # Calculate domain scores
            domain_scores = {}
            for component in ScoreComponent:
                assessments = user_assessments.get(component.value, [])
                domain_scores[component] = self._calculate_domain_score(
                    component, assessments, weights[component]
                )
            
            # Calculate overall score
            overall_score = sum(
                score.normalized_score * score.weight 
                for score in domain_scores.values()
            )
            
            # Calculate overall confidence
            overall_confidence = np.mean([
                score.confidence for score in domain_scores.values()
            ])
            
            # Determine career stage
            career_stage = self._determine_career_stage(overall_score)
            
            # Generate insights and recommendations
            strengths, improvements = self._analyze_strengths_weaknesses(domain_scores)
            recommendations = self._generate_recommendations(
                domain_scores, career_stage, industry, career_goals
            )
            
            return CareerReadinessScore(
                overall_score=overall_score,
                knowledge_score=domain_scores[ScoreComponent.KNOWLEDGE].normalized_score,
                abilities_score=domain_scores[ScoreComponent.ABILITIES].normalized_score,
                skills_score=domain_scores[ScoreComponent.SKILLS].normalized_score,
                experience_score=domain_scores[ScoreComponent.EXPERIENCE].normalized_score,
                confidence=overall_confidence,
                strengths=strengths,
                improvement_areas=improvements,
                career_stage=career_stage,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"KASH scoring failed: {e}")
            raise
    
    def _get_weights(
        self, 
        industry: Optional[str], 
        custom_weights: Optional[Dict[str, float]]
    ) -> Dict[ScoreComponent, float]:
        """Get scoring weights with industry and custom adjustments."""
        weights = self.default_weights.copy()
        
        # Apply industry-specific weights
        if industry and industry.lower() in self.industry_weights:
            industry_weights = self.industry_weights[industry.lower()]
            weights.update(industry_weights)
        
        # Apply custom weight overrides
        if custom_weights:
            for component_str, weight in custom_weights.items():
                try:
                    component = ScoreComponent(component_str)
                    weights[component] = weight
                except ValueError:
                    logger.warning(f"Invalid weight component: {component_str}")
        
        # Normalize weights to sum to 1.0
        total_weight = sum(weights.values())
        if total_weight != 1.0:
            weights = {k: v / total_weight for k, v in weights.items()}
        
        return weights
    
    def _calculate_domain_score(
        self, 
        component: ScoreComponent, 
        assessments: List[Dict[str, Any]], 
        weight: float
    ) -> KASHScore:
        """Calculate score for a specific KASH domain."""
        if not assessments:
            return KASHScore(
                domain=component,
                raw_score=0.0,
                normalized_score=0.0,
                confidence=0.0,
                weight=weight,
                breakdown={},
                evidence=[f"No {component.value} assessments available"],
                last_updated=datetime.now()
            )
        
        # Use appropriate scoring model
        scoring_function = self.scoring_models[component]
        return scoring_function(assessments, weight)
    
    def _score_knowledge(
        self, 
        assessments: List[Dict[str, Any]], 
        weight: float
    ) -> KASHScore:
        """Score knowledge domain from CV and ESCO assessments."""
        if not assessments:
            return self._empty_score(ScoreComponent.KNOWLEDGE, weight)
        
        # Extract knowledge metrics
        cv_scores = []
        skill_mappings = []
        occupation_matches = []
        
        for assessment in assessments:
            result_data = assessment.get('result_data', {})
            
            # CV analysis scores
            if 'cv_analysis' in result_data:
                cv_analysis = result_data['cv_analysis']
                cv_scores.append(cv_analysis.get('overall_score', 0))
            
            # ESCO skill mappings
            if 'skill_mapping' in result_data:
                skill_mapping = result_data['skill_mapping']
                skill_mappings.append(len(skill_mapping.get('mapped_skills', [])))
            
            # Occupation matches
            if 'occupation_suggestions' in result_data:
                occupations = result_data['occupation_suggestions']
                occupation_matches.append(len(occupations.get('suggestions', [])))
        
        # Calculate knowledge score
        avg_cv_score = np.mean(cv_scores) if cv_scores else 0
        total_skills_mapped = sum(skill_mappings)
        total_occupation_matches = sum(occupation_matches)
        
        # Weighted knowledge score
        knowledge_score = (
            avg_cv_score * 0.6 +
            min(total_skills_mapped * 2, 100) * 0.2 +
            min(total_occupation_matches * 5, 100) * 0.2
        )
        
        # Calculate confidence based on data quality
        confidence = min(
            0.3 + (len(assessments) * 0.2) +
            (len(cv_scores) * 0.2) +
            (total_skills_mapped * 0.01) +
            (total_occupation_matches * 0.01),
            1.0
        )
        
        # Create breakdown
        breakdown = {
            'cv_analysis_score': avg_cv_score,
            'skills_mapped_count': total_skills_mapped,
            'occupation_matches_count': total_occupation_matches,
            'assessment_count': len(assessments)
        }
        
        # Generate evidence
        evidence = [
            f"Analyzed {len(cv_scores)} CV assessments",
            f"Mapped {total_skills_mapped} skills to ESCO framework",
            f"Found {total_occupation_matches} occupation matches"
        ]
        
        return KASHScore(
            domain=ScoreComponent.KNOWLEDGE,
            raw_score=knowledge_score,
            normalized_score=min(knowledge_score, 100),
            confidence=confidence,
            weight=weight,
            breakdown=breakdown,
            evidence=evidence,
            last_updated=datetime.now()
        )
    
    def _score_abilities(
        self, 
        assessments: List[Dict[str, Any]], 
        weight: float
    ) -> KASHScore:
        """Score abilities domain from adaptive quiz assessments."""
        if not assessments:
            return self._empty_score(ScoreComponent.ABILITIES, weight)
        
        # Extract abilities metrics
        cognitive_scores = {}
        quiz_scores = []
        domain_mastery = {}
        
        for assessment in assessments:
            result_data = assessment.get('result_data', {})
            
            # Quiz scores - support both 'quiz_results' wrapper and flat structure
            if 'quiz_results' in result_data:
                quiz_results = result_data['quiz_results']
                quiz_scores.append(quiz_results.get('final_score', 0))
            elif 'percentage' in result_data:
                quiz_scores.append(result_data['percentage'])
            elif 'total_score' in result_data:
                quiz_scores.append(result_data['total_score'])
            
            # Cognitive domain scores
            if 'domain_scores' in result_data:
                domain_scores = result_data['domain_scores']
                for domain, score in domain_scores.items():
                    if domain not in cognitive_scores:
                        cognitive_scores[domain] = []
                    # score can be a dict with 'score' key or a raw number
                    if isinstance(score, dict):
                        cognitive_scores[domain].append(score.get('score', 0))
                    else:
                        cognitive_scores[domain].append(score)
            
            # Domain mastery levels
            if 'domain_mastery' in result_data:
                mastery = result_data['domain_mastery']
                for domain, level in mastery.items():
                    if domain not in domain_mastery:
                        domain_mastery[domain] = []
                    domain_mastery[domain].append(level)
        
        # Calculate abilities score
        avg_quiz_score = np.mean(quiz_scores) if quiz_scores else 0
        
        # Calculate domain averages
        domain_averages = {}
        for domain, scores in cognitive_scores.items():
            domain_averages[domain] = np.mean(scores)
        
        # Calculate mastery bonus
        mastery_bonus = 0
        if domain_mastery:
            advanced_count = sum(
                1 for domain_levels in domain_mastery.values()
                for level in domain_levels
                if level in ['advanced', 'expert']
            )
            mastery_bonus = min(advanced_count * 5, 25)
        
        # Weighted abilities score
        abilities_score = (
            avg_quiz_score * 0.5 +
            (np.mean(list(domain_averages.values())) if domain_averages else 0) * 0.3 +
            mastery_bonus * 0.2
        )
        
        # Calculate confidence
        confidence = min(
            0.3 + (len(assessments) * 0.15) +
            (len(quiz_scores) * 0.2) +
            (len(domain_averages) * 0.1) +
            (mastery_bonus * 0.01),
            1.0
        )
        
        # Create breakdown
        breakdown = {
            'quiz_average_score': avg_quiz_score,
            'domain_averages': domain_averages,
            'mastery_bonus': mastery_bonus,
            'assessment_count': len(assessments),
            'domains_assessed': len(domain_averages)
        }
        
        # Generate evidence
        evidence = [
            f"Completed {len(quiz_scores)} adaptive assessments",
            f"Assessed {len(domain_averages)} cognitive domains",
            f"Achieved mastery in {mastery_bonus//5} advanced domains"
        ]
        
        return KASHScore(
            domain=ScoreComponent.ABILITIES,
            raw_score=abilities_score,
            normalized_score=min(abilities_score, 100),
            confidence=confidence,
            weight=weight,
            breakdown=breakdown,
            evidence=evidence,
            last_updated=datetime.now()
        )
    
    def _score_skills(
        self, 
        assessments: List[Dict[str, Any]], 
        weight: float
    ) -> KASHScore:
        """Score skills domain from GitHub and code analysis."""
        if not assessments:
            return self._empty_score(ScoreComponent.SKILLS, weight)
        
        # Extract skills metrics
        technical_scores = []
        skill_diversity = []
        code_quality_scores = []
        project_complexities = []
        collaboration_scores = []
        
        for assessment in assessments:
            result_data = assessment.get('result_data', {})
            
            # Skills scores
            if 'skills_scores' in result_data:
                skills_scores = result_data['skills_scores']
                technical_scores.append(skills_scores.get('normalized_score', 0))
            
            # Technical skills diversity
            if 'technical_skills' in result_data:
                tech_skills = result_data['technical_skills']
                skill_diversity.append(len(tech_skills))
            
            # Code quality
            if 'overall_scores' in result_data:
                overall_scores = result_data['overall_scores']
                code_quality_scores.append(overall_scores.get('code_quality', 0))
                project_complexities.append(overall_scores.get('overall_score', 0))
            
            # Collaboration indicators
            if 'collaboration_indicators' in result_data:
                collaboration = result_data['collaboration_indicators']
                if collaboration.get('is_collaborative', False):
                    collaboration_scores.append(80)
                else:
                    collaboration_scores.append(40)
        
        # Calculate skills score
        avg_technical_score = np.mean(technical_scores) if technical_scores else 0
        avg_code_quality = np.mean(code_quality_scores) if code_quality_scores else 0
        avg_project_complexity = np.mean(project_complexities) if project_complexities else 0
        avg_collaboration = np.mean(collaboration_scores) if collaboration_scores else 0
        
        # Skill diversity bonus
        diversity_bonus = min(sum(skill_diversity) * 2, 30)
        
        # Weighted skills score
        skills_score = (
            avg_technical_score * 0.4 +
            avg_code_quality * 0.25 +
            avg_project_complexity * 0.2 +
            avg_collaboration * 0.15 +
            diversity_bonus * 0.1
        )
        
        # Calculate confidence
        confidence = min(
            0.3 + (len(assessments) * 0.15) +
            (len(technical_scores) * 0.2) +
            (diversity_bonus * 0.01) +
            (avg_collaboration * 0.01),
            1.0
        )
        
        # Create breakdown
        breakdown = {
            'technical_average_score': avg_technical_score,
            'code_quality_average': avg_code_quality,
            'project_complexity_average': avg_project_complexity,
            'collaboration_score': avg_collaboration,
            'diversity_bonus': diversity_bonus,
            'total_unique_skills': sum(skill_diversity),
            'assessment_count': len(assessments)
        }
        
        # Generate evidence
        evidence = [
            f"Analyzed {len(technical_scores)} technical assessments",
            f"Identified {sum(skill_diversity)} unique technical skills",
            f"Average code quality: {avg_code_quality:.1f}/100",
            f"Collaboration score: {avg_collaboration:.1f}/100"
        ]
        
        return KASHScore(
            domain=ScoreComponent.SKILLS,
            raw_score=skills_score,
            normalized_score=min(skills_score, 100),
            confidence=confidence,
            weight=weight,
            breakdown=breakdown,
            evidence=evidence,
            last_updated=datetime.now()
        )
    
    def _score_experience(
        self, 
        assessments: List[Dict[str, Any]], 
        weight: float
    ) -> KASHScore:
        """Score experience domain from work history and projects."""
        if not assessments:
            return self._empty_score(ScoreComponent.EXPERIENCE, weight)

        # If an assessment provides a direct experience score (e.g. derived from interview answers),
        # use it as the primary signal.
        direct_scores = []
        direct_confidences = []
        for assessment in assessments:
            result_data = assessment.get('result_data', {})
            if isinstance(result_data, dict) and 'experience_score' in result_data:
                try:
                    direct_scores.append(float(result_data.get('experience_score') or 0))
                    direct_confidences.append(float(assessment.get('confidence_score') or 0))
                except Exception:
                    pass

        if direct_scores:
            experience_score = float(np.mean(direct_scores))
            confidence = float(np.mean(direct_confidences)) if direct_confidences else 0.5
            breakdown = {
                'experience_score': experience_score,
                'signal': 'interview_derived',
                'assessment_count': len(direct_scores),
            }
            evidence = [
                f"Derived from interview responses ({len(direct_scores)} signal(s))",
            ]
            return KASHScore(
                domain=ScoreComponent.EXPERIENCE,
                raw_score=experience_score,
                normalized_score=min(experience_score, 100),
                confidence=min(max(confidence, 0.0), 1.0),
                weight=weight,
                breakdown=breakdown,
                evidence=evidence,
                last_updated=datetime.now()
            )
        
        # Extract experience metrics
        experience_years = []
        project_counts = []
        leadership_indicators = []
        achievement_scores = []
        
        for assessment in assessments:
            result_data = assessment.get('result_data', {})
            
            # Work experience
            if 'work_experience' in result_data:
                work_exp = result_data['work_experience']
                experience_years.append(work_exp.get('total_years', 0))
            
            # Project experience
            if 'projects' in result_data:
                projects = result_data['projects']
                project_counts.append(len(projects))
            
            # Leadership indicators
            if 'leadership' in result_data:
                leadership = result_data['leadership']
                if leadership.get('has_leadership_experience', False):
                    leadership_indicators.append(80)
                else:
                    leadership_indicators.append(40)
            
            # Achievement scores
            if 'achievements' in result_data:
                achievements = result_data['achievements']
                achievement_scores.append(len(achievements) * 10)
        
        # Calculate experience score
        avg_experience_years = np.mean(experience_years) if experience_years else 0
        total_projects = sum(project_counts)
        avg_leadership = np.mean(leadership_indicators) if leadership_indicators else 40
        avg_achievements = np.mean(achievement_scores) if achievement_scores else 0
        
        # Experience years score (capped at 20 years)
        years_score = min(avg_experience_years * 5, 100)
        
        # Project diversity score
        project_score = min(total_projects * 3, 100)
        
        # Weighted experience score
        experience_score = (
            years_score * 0.4 +
            project_score * 0.3 +
            avg_leadership * 0.2 +
            avg_achievements * 0.1
        )
        
        # Calculate confidence
        confidence = min(
            0.3 + (len(assessments) * 0.15) +
            (len(experience_years) * 0.2) +
            (total_projects * 0.01) +
            (avg_leadership * 0.01),
            1.0
        )
        
        # Create breakdown
        breakdown = {
            'experience_years_score': years_score,
            'project_diversity_score': project_score,
            'leadership_score': avg_leadership,
            'achievement_score': avg_achievements,
            'total_projects': total_projects,
            'average_years_experience': avg_experience_years,
            'assessment_count': len(assessments)
        }
        
        # Generate evidence
        evidence = [
            f"Total experience: {avg_experience_years:.1f} years",
            f"Completed {total_projects} projects",
            f"Leadership score: {avg_leadership:.1f}/100",
            f"Achievement score: {avg_achievements:.1f}/100"
        ]
        
        return KASHScore(
            domain=ScoreComponent.EXPERIENCE,
            raw_score=experience_score,
            normalized_score=min(experience_score, 100),
            confidence=confidence,
            weight=weight,
            breakdown=breakdown,
            evidence=evidence,
            last_updated=datetime.now()
        )
    
    def _empty_score(self, component: ScoreComponent, weight: float) -> KASHScore:
        """Create empty score for missing assessments."""
        return KASHScore(
            domain=component,
            raw_score=0.0,
            normalized_score=0.0,
            confidence=0.0,
            weight=weight,
            breakdown={},
            evidence=[f"No {component.value} assessments available"],
            last_updated=datetime.now()
        )
    
    def _determine_career_stage(self, overall_score: float) -> str:
        """Determine career stage based on overall score."""
        for stage, (min_score, max_score) in self.career_stages.items():
            if min_score <= overall_score < max_score:
                return stage
        return 'expert'
    
    def _analyze_strengths_weaknesses(
        self, 
        domain_scores: Dict[ScoreComponent, KASHScore]
    ) -> Tuple[List[str], List[str]]:
        """Analyze strengths and improvement areas."""
        strengths = []
        improvements = []
        
        # Sort domains by score
        sorted_domains = sorted(
            domain_scores.items(), 
            key=lambda x: x[1].normalized_score, 
            reverse=True
        )
        
        # Top 2 strengths
        for component, score in sorted_domains[:2]:
            if score.normalized_score >= 70:
                strengths.append(
                    f"Strong {component.value} performance ({score.normalized_score:.1f}/100)"
                )
        
        # Bottom 2 improvement areas
        for component, score in sorted_domains[-2:]:
            if score.normalized_score < 60:
                improvements.append(
                    f"Improve {component.value} domain ({score.normalized_score:.1f}/100)"
                )
        
        return strengths, improvements
    
    def _generate_recommendations(
        self,
        domain_scores: Dict[ScoreComponent, KASHScore],
        career_stage: str,
        industry: Optional[str],
        career_goals: Optional[List[str]]
    ) -> List[str]:
        """Generate personalized recommendations."""
        recommendations = []
        
        # Career stage recommendations
        stage_recommendations = {
            'explorer': [
                "Focus on building foundational knowledge across all domains",
                "Explore different career paths through assessments",
                "Develop basic technical and soft skills"
            ],
            'beginner': [
                "Deepen knowledge in chosen field",
                "Build practical skills through projects",
                "Develop problem-solving abilities"
            ],
            'intermediate': [
                "Specialize in advanced technical skills",
                "Develop leadership and collaboration abilities",
                "Build portfolio of complex projects"
            ],
            'advanced': [
                "Master advanced concepts and technologies",
                "Develop mentoring and leadership capabilities",
                "Contribute to industry innovations"
            ],
            'expert': [
                "Focus on thought leadership and innovation",
                "Mentor others and share knowledge",
                "Drive strategic initiatives"
            ]
        }
        
        recommendations.extend(stage_recommendations.get(career_stage, []))
        
        # Domain-specific recommendations
        for component, score in domain_scores.items():
            if score.normalized_score < 50:
                if component == ScoreComponent.KNOWLEDGE:
                    recommendations.append("Expand theoretical knowledge through courses and reading")
                elif component == ScoreComponent.ABILITIES:
                    recommendations.append("Practice cognitive skills through targeted exercises")
                elif component == ScoreComponent.SKILLS:
                    recommendations.append("Build practical technical skills through hands-on projects")
                elif component == ScoreComponent.EXPERIENCE:
                    recommendations.append("Gain real-world experience through internships or projects")
        
        # Industry-specific recommendations
        if industry:
            industry_recommendations = {
                'technology': [
                    "Stay updated with latest technologies and frameworks",
                    "Build strong portfolio on GitHub",
                    "Contribute to open-source projects"
                ],
                'healthcare': [
                    "Maintain current certifications and licenses",
                    "Develop patient care and communication skills",
                    "Stay updated with medical advancements"
                ],
                'business': [
                    "Develop analytical and strategic thinking",
                    "Build network of professional contacts",
                    "Gain experience in different business functions"
                ],
                'education': [
                    "Develop teaching and mentoring skills",
                    "Stay current with educational methodologies",
                    "Build subject matter expertise"
                ]
            }
            
            recommendations.extend(industry_recommendations.get(industry.lower(), []))
        
        return recommendations[:8]  # Top 8 recommendations
