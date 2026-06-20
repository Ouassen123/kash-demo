"""Intelligence module service for KASH scoring and career recommendations."""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import uuid
import numpy as np

from src.core.database import get_db
from src.core.logging import get_logger
from src.models.user import User
from src.models.assessment import UserAssessment, IntelligenceAssessment
from src.modules.intelligence.kash_scorer import KASHScorer, ScoreComponent
from src.modules.intelligence.shap_explainer import SHAPExplainer, ExplanationType

logger = get_logger(__name__)


class IntelligenceService:
    """Service for intelligence domain operations including KASH scoring and explainability."""
    
    def __init__(self, db: Session):
        self.db = db
        self.kash_scorer = KASHScorer()
        self.shap_explainer = SHAPExplainer()
    
    async def generate_comprehensive_intelligence(
        self,
        user_id: str,
        industry: Optional[str] = None,
        career_goals: Optional[List[str]] = None,
        custom_weights: Optional[Dict[str, float]] = None
    ) -> UserAssessment:
        """
        Generate comprehensive intelligence assessment with KASH scoring and explainability.
        
        Args:
            user_id: User UUID
            industry: Target industry for weight adjustment
            career_goals: List of career goals
            custom_weights: Optional custom weight overrides
            
        Returns:
            UserAssessment with complete intelligence analysis
        """
        logger.info(f"Generating comprehensive intelligence for user {user_id}")
        start_time = datetime.now()
        
        try:
            # Collect all user assessments
            user_assessments = await self._collect_user_assessments(user_id)
            
            # Calculate KASH scores
            kash_score = self.kash_scorer.calculate_comprehensive_score(
                user_assessments=user_assessments,
                industry=industry,
                career_goals=career_goals,
                custom_weights=custom_weights
            )
            
            # Generate SHAP explanations
            feature_values = await self._extract_feature_values(user_assessments)
            domain_scores = {
                'knowledge': kash_score.knowledge_score,
                'abilities': kash_score.abilities_score,
                'skills': kash_score.skills_score,
                'experience': kash_score.experience_score
            }
            
            feature_importance = self.shap_explainer.explain_kash_score(
                kash_score=kash_score.overall_score,
                domain_scores=domain_scores,
                feature_values=feature_values
            )
            
            # Generate career path explanations
            career_explanations = await self._generate_career_explanations(
                user_assessments, kash_score, industry
            )
            
            # Generate skill gap analysis
            skill_gap_analysis = await self._generate_skill_gap_analysis(
                user_assessments, career_goals
            )
            
            # Generate assessment impact analysis
            assessment_impacts = self.shap_explainer.explain_assessment_impact(
                assessments=self._flatten_assessments(user_assessments),
                overall_score=kash_score.overall_score
            )
            
            # Generate recommendation explanations
            recommendation_explanations = self.shap_explainer.explain_recommendations(
                recommendations=kash_score.recommendations,
                user_profile={
                    'domain_scores': domain_scores,
                    'technical_skills': await self._extract_technical_skills(user_assessments)
                },
                domain_scores=domain_scores
            )
            
            # Create user assessment record
            assessment = UserAssessment(
                id=uuid.uuid4(),
                user_id=user_id,
                assessment_type='intelligence',
                assessment_name='Comprehensive KASH Intelligence Assessment',
                assessment_version='1.0',
                status='completed',
                raw_score=kash_score.overall_score,
                normalized_score=kash_score.overall_score,
                confidence_score=kash_score.confidence,
                input_data={
                    'industry': industry,
                    'career_goals': career_goals,
                    'custom_weights': custom_weights,
                    'assessment_sources': {
                        domain: len(assessments) for domain, assessments in user_assessments.items()
                    }
                },
                result_data={
                    'kash_score': {
                        'overall_score': kash_score.overall_score,
                        'knowledge_score': kash_score.knowledge_score,
                        'abilities_score': kash_score.abilities_score,
                        'skills_score': kash_score.skills_score,
                        'experience_score': kash_score.experience_score,
                        'confidence': kash_score.confidence,
                        'career_stage': kash_score.career_stage,
                        'strengths': kash_score.strengths,
                        'improvement_areas': kash_score.improvement_areas,
                        'recommendations': kash_score.recommendations
                    },
                    'feature_importance': [
                        {
                            'feature_name': fi.feature_name,
                            'feature_value': fi.feature_value,
                            'shap_value': fi.shap_value,
                            'contribution_percentage': fi.contribution_percentage,
                            'direction': fi.direction,
                            'explanation': fi.explanation
                        }
                        for fi in feature_importance
                    ],
                    'career_explanations': career_explanations,
                    'skill_gap_analysis': skill_gap_analysis,
                    'assessment_impacts': [
                        {
                            'assessment_type': ai.assessment_type,
                            'assessment_name': ai.assessment_name,
                            'score_contribution': ai.score_contribution,
                            'confidence_impact': ai.confidence_impact,
                            'improvement_potential': ai.improvement_potential
                        }
                        for ai in assessment_impacts
                    ],
                    'recommendation_explanations': recommendation_explanations
                },
                created_at=datetime.now(),
                started_at=datetime.now(),
                completed_at=datetime.now()
            )
            
            self.db.add(assessment)
            self.db.flush()  # Get the assessment ID
            
            # Create intelligence-specific assessment record
            intelligence_assessment = IntelligenceAssessment(
                id=uuid.uuid4(),
                assessment_id=assessment.id,
                kash_weights=self.kash_scorer._get_weights(industry, custom_weights),
                feature_importance_data=[
                    {
                        'feature_name': fi.feature_name,
                        'feature_value': fi.feature_value,
                        'shap_value': fi.shap_value,
                        'contribution_percentage': fi.contribution_percentage,
                        'direction': fi.direction,
                        'explanation': fi.explanation
                    }
                    for fi in feature_importance
                ],
                career_path_explanations=career_explanations,
                skill_gap_analysis=skill_gap_analysis,
                assessment_impact_data=[
                    {
                        'assessment_type': ai.assessment_type,
                        'assessment_name': ai.assessment_name,
                        'score_contribution': ai.score_contribution,
                        'confidence_impact': ai.confidence_impact,
                        'improvement_potential': ai.improvement_potential
                    }
                    for ai in assessment_impacts
                ],
                recommendation_explanations=recommendation_explanations,
                model_version='1.0',
                analysis_date=datetime.now()
            )
            
            self.db.add(intelligence_assessment)
            self.db.commit()
            
            logger.info(f"Comprehensive intelligence generated in {(datetime.now() - start_time).total_seconds():.2f}s")
            return assessment
            
        except Exception as e:
            logger.error(f"Comprehensive intelligence generation failed: {e}")
            self.db.rollback()
            raise
    
    async def get_intelligence_assessment(
        self,
        assessment_id: str,
        user_id: str
    ) -> Optional[UserAssessment]:
        """
        Get intelligence assessment by ID for a specific user.
        
        Args:
            assessment_id: Assessment UUID
            user_id: User UUID
            
        Returns:
            UserAssessment or None if not found
        """
        assessment = self.db.query(UserAssessment).filter(
            UserAssessment.id == assessment_id,
            UserAssessment.user_id == user_id,
            UserAssessment.assessment_type == 'intelligence'
        ).first()
        
        if assessment:
            # Load related intelligence assessment
            intelligence_assessment = self.db.query(IntelligenceAssessment).filter(
                IntelligenceAssessment.assessment_id == assessment.id
            ).first()
            
            if intelligence_assessment:
                # Add detailed data to result
                assessment.result_data.update({
                    'intelligence_assessment': {
                        'kash_weights': intelligence_assessment.kash_weights,
                        'feature_importance_data': intelligence_assessment.feature_importance_data,
                        'career_path_explanations': intelligence_assessment.career_path_explanations,
                        'skill_gap_analysis': intelligence_assessment.skill_gap_analysis,
                        'assessment_impact_data': intelligence_assessment.assessment_impact_data,
                        'recommendation_explanations': intelligence_assessment.recommendation_explanations,
                        'model_version': intelligence_assessment.model_version,
                        'analysis_date': intelligence_assessment.analysis_date.isoformat() if intelligence_assessment.analysis_date else None
                    }
                })
        
        return assessment
    
    async def get_user_intelligence_assessments(self, user_id: str, limit: int = 10) -> List[UserAssessment]:
        """
        Get all intelligence assessments for a user.
        
        Args:
            user_id: User UUID
            limit: Maximum number of assessments to return
            
        Returns:
            List of UserAssessment records
        """
        assessments = self.db.query(UserAssessment).filter(
            UserAssessment.user_id == user_id,
            UserAssessment.assessment_type == 'intelligence'
        ).order_by(UserAssessment.created_at.desc()).limit(limit).all()
        
        return assessments
    
    async def get_user_intelligence_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive intelligence profile for a user.
        
        Args:
            user_id: User UUID
            
        Returns:
            User's intelligence profile with aggregated data
        """
        assessments = self.db.query(UserAssessment).filter(
            UserAssessment.user_id == user_id,
            UserAssessment.assessment_type == 'intelligence',
            UserAssessment.status == 'completed'
        ).order_by(UserAssessment.created_at.desc()).all()
        
        if not assessments:
            return {
                'user_id': user_id,
                'total_assessments': 0,
                'current_kash_score': None,
                'kash_trend': [],
                'career_insights': {},
                'feature_importance_trends': {},
                'recommendation_history': [],
                'skill_development_progress': {},
                'last_assessment': None,
                'career_stage': None,
                'confidence': None
            }
        
        # Get latest assessment
        latest_assessment = assessments[0]
        result_data = latest_assessment.result_data or {}
        
        # Extract KASH scores
        kash_score = result_data.get('kash_score', {})
        current_scores = {
            'overall': kash_score.get('overall_score', 0),
            'knowledge': kash_score.get('knowledge_score', 0),
            'abilities': kash_score.get('abilities_score', 0),
            'skills': kash_score.get('skills_score', 0),
            'experience': kash_score.get('experience_score', 0)
        }
        
        # Calculate KASH trend
        kash_trend = self._calculate_kash_trend(assessments)
        
        # Aggregate career insights
        career_insights = self._aggregate_career_insights(assessments)
        
        # Aggregate feature importance trends
        feature_trends = self._aggregate_feature_importance_trends(assessments)
        
        # Aggregate recommendation history
        recommendation_history = self._aggregate_recommendation_history(assessments)
        
        # Calculate skill development progress
        skill_progress = self._calculate_skill_development_progress(assessments)
        
        return {
            'user_id': user_id,
            'total_assessments': len(assessments),
            'current_kash_score': current_scores,
            'kash_trend': kash_trend,
            'career_insights': career_insights,
            'feature_importance_trends': feature_trends,
            'recommendation_history': recommendation_history,
            'skill_development_progress': skill_progress,
            'last_assessment': latest_assessment.created_at.isoformat(),
            'career_stage': kash_score.get('career_stage', 'unknown'),
            'confidence': kash_score.get('confidence', 0)
        }
    
    async def explain_career_path(
        self,
        user_id: str,
        target_career: str
    ) -> Dict[str, Any]:
        """
        Generate detailed career path explanation.
        
        Args:
            user_id: User UUID
            target_career: Target career path
            
        Returns:
            Detailed career path explanation
        """
        try:
            # Get user profile
            user_assessments = await self._collect_user_assessments(user_id)
            
            # Get latest KASH scores
            latest_intelligence = await self.get_user_intelligence_assessments(user_id, 1)
            if not latest_intelligence:
                raise ValueError("No intelligence assessments found for user")
            
            latest_assessment = latest_intelligence[0]
            result_data = latest_assessment.result_data or {}
            kash_score = result_data.get('kash_score', {})
            
            # Create user profile
            user_profile = {
                'domain_scores': {
                    'knowledge': kash_score.get('knowledge_score', 0),
                    'abilities': kash_score.get('abilities_score', 0),
                    'skills': kash_score.get('skills_score', 0),
                    'experience': kash_score.get('experience_score', 0)
                },
                'technical_skills': await self._extract_technical_skills(user_assessments)
            }
            
            # Generate career path explanation
            career_explanation = self.shap_explainer.explain_career_path(
                user_profile=user_profile,
                target_career=target_career,
                current_kash_score=kash_score.get('overall_score', 0)
            )
            
            return {
                'career_path': target_career,
                'explanation': {
                    'match_score': career_explanation.match_score,
                    'key_factors': career_explanation.key_factors,
                    'skill_gaps': career_explanation.skill_gaps,
                    'alignment_reasons': career_explanation.alignment_reasons,
                    'development_needs': career_explanation.development_needs
                },
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Career path explanation failed: {e}")
            raise
    
    async def analyze_skill_gaps(
        self,
        user_id: str,
        target_role: str,
        experience_level: str = "intermediate"
    ) -> Dict[str, Any]:
        """
        Analyze skill gaps for target role.
        
        Args:
            user_id: User UUID
            target_role: Target role name
            experience_level: Required experience level
            
        Returns:
            Detailed skill gap analysis
        """
        try:
            # Get user skills
            user_assessments = await self._collect_user_assessments(user_id)
            current_skills = await self._extract_technical_skills(user_assessments)
            
            # Generate skill gap analysis
            skill_gap_analysis = self.shap_explainer.analyze_skill_gaps(
                current_skills=current_skills,
                target_role=target_role,
                experience_level=experience_level
            )
            
            return {
                'target_role': target_role,
                'experience_level': experience_level,
                'analysis': {
                    'current_skills': skill_gap_analysis.current_skills,
                    'required_skills': skill_gap_analysis.required_skills,
                    'skill_gaps': skill_gap_analysis.skill_gaps,
                    'priority_gaps': skill_gap_analysis.priority_gaps,
                    'development_timeline': skill_gap_analysis.development_timeline
                },
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Skill gap analysis failed: {e}")
            raise
    
    async def _collect_user_assessments(self, user_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Collect all user assessments by domain."""
        assessments = self.db.query(UserAssessment).filter(
            UserAssessment.user_id == user_id,
            UserAssessment.status == 'completed'
        ).all()
        
        # Group by assessment type
        grouped_assessments = {
            'knowledge': [],
            'abilities': [],
            'skills': [],
            # Experience is derived from the interview step and stored in user.profile_data.
            'experience': []
        }
        
        for assessment in assessments:
            assessment_type = assessment.assessment_type
            if assessment_type in grouped_assessments:
                grouped_assessments[assessment_type].append({
                    'id': str(assessment.id),
                    'assessment_name': assessment.assessment_name,
                    'normalized_score': assessment.normalized_score or 0,
                    'confidence_score': assessment.confidence_score or 0,
                    'result_data': assessment.result_data or {},
                    'created_at': assessment.created_at
                })

        # Experience signal (4th test) derived from the interview step saved into user.profile_data.
        # We do this instead of persisting a new DB enum value, to avoid enum migrations.
        user_pk = user_id
        try:
            user_pk = uuid.UUID(user_id)
        except Exception:
            pass

        user = self.db.query(User).filter(User.id == user_pk).first()
        profile_data = (user.profile_data or {}) if user else {}
        interview = profile_data.get('interview') if isinstance(profile_data, dict) else None

        if isinstance(interview, dict):
            answers = interview.get('answers')
            if isinstance(answers, list) and any(str(a or '').strip() for a in answers):
                text = "\n".join([str(a or "").strip() for a in answers])
                words = [w for w in text.replace('\n', ' ').split(' ') if w.strip()]
                word_count = len(words)

                # 0..100 rubric: more detailed answers -> higher score.
                experience_score = min(100.0, max(0.0, (word_count / 220.0) * 100.0))
                confidence = min(1.0, 0.3 + (min(word_count, 500) / 1000.0))

                grouped_assessments['experience'].append({
                    'id': 'interview',
                    'assessment_name': 'Interview & Motivation',
                    'normalized_score': experience_score,
                    'confidence_score': confidence,
                    'result_data': {
                        'experience_score': experience_score,
                        'interview': {
                            'answers': answers,
                            'word_count': word_count,
                            'created_at': interview.get('created_at'),
                        }
                    },
                    'created_at': datetime.now(),
                })
        
        return grouped_assessments
    
    async def _extract_feature_values(self, user_assessments: Dict[str, List[Dict[str, Any]]]) -> Dict[str, float]:
        """Extract feature values from assessments for SHAP analysis."""
        feature_values = {}
        
        # Knowledge features
        knowledge_assessments = user_assessments.get('knowledge', [])
        if knowledge_assessments:
            feature_values['knowledge_cv_completeness'] = 0.8  # Placeholder
            feature_values['knowledge_skill_coverage'] = min(len(knowledge_assessments) * 0.2, 1.0)
            feature_values['knowledge_education_level'] = 0.7  # Placeholder
            feature_values['knowledge_certification_count'] = min(len(knowledge_assessments) * 0.1, 1.0)
        
        # Abilities features
        abilities_assessments = user_assessments.get('abilities', [])
        if abilities_assessments:
            feature_values['abilities_problem_solving'] = 0.7  # Placeholder
            feature_values['abilities_critical_thinking'] = 0.6  # Placeholder
            feature_values['abilities_creativity'] = 0.5  # Placeholder
            feature_values['abilities_communication'] = 0.6  # Placeholder
        
        # Skills features
        skills_assessments = user_assessments.get('skills', [])
        if skills_assessments:
            feature_values['skills_technical_proficiency'] = np.mean([a['normalized_score'] for a in skills_assessments]) / 100
            feature_values['skills_practical_experience'] = min(len(skills_assessments) * 0.15, 1.0)
            feature_values['skills_project_complexity'] = 0.6  # Placeholder
            feature_values['skills_collaboration_skills'] = 0.5  # Placeholder
        
        # Experience features
        experience_assessments = user_assessments.get('experience', [])
        if experience_assessments:
            feature_values['experience_years_experience'] = 0.6  # Placeholder
            feature_values['experience_project_diversity'] = min(len(experience_assessments) * 0.1, 1.0)
            feature_values['experience_leadership_experience'] = 0.4  # Placeholder
            feature_values['experience_growth_trajectory'] = 0.5  # Placeholder
        
        return feature_values
    
    async def _extract_technical_skills(self, user_assessments: Dict[str, List[Dict[str, Any]]]) -> Dict[str, float]:
        """Extract technical skills from assessments."""
        technical_skills = {}
        
        skills_assessments = user_assessments.get('skills', [])
        for assessment in skills_assessments:
            result_data = assessment.get('result_data', {})
            technical_skills_list = result_data.get('technical_skills', [])
            
            for skill in technical_skills_list:
                skill_name = skill.get('name', '').lower()
                confidence = skill.get('confidence', 0)
                
                if skill_name and confidence > 0:
                    if skill_name not in technical_skills:
                        technical_skills[skill_name] = []
                    technical_skills[skill_name].append(confidence)
        
        # Average confidence for each skill
        for skill_name in technical_skills:
            technical_skills[skill_name] = np.mean(technical_skills[skill_name])
        
        return technical_skills
    
    async def _generate_career_explanations(
        self,
        user_assessments: Dict[str, List[Dict[str, Any]]],
        kash_score,
        industry: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Generate career path explanations for common careers."""
        careers = ['software_engineer', 'data_scientist', 'product_manager', 'ux_designer', 'devops_engineer']
        
        user_profile = {
            'domain_scores': {
                'knowledge': kash_score.knowledge_score,
                'abilities': kash_score.abilities_score,
                'skills': kash_score.skills_score,
                'experience': kash_score.experience_score
            },
            'technical_skills': await self._extract_technical_skills(user_assessments)
        }
        
        explanations = []
        for career in careers:
            explanation = self.shap_explainer.explain_career_path(
                user_profile=user_profile,
                target_career=career,
                current_kash_score=kash_score.overall_score
            )
            
            explanations.append({
                'career': career,
                'match_score': explanation.match_score,
                'key_factors': explanation.key_factors,
                'skill_gaps': explanation.skill_gaps
            })
        
        return explanations
    
    async def _generate_skill_gap_analysis(
        self,
        user_assessments: Dict[str, List[Dict[str, Any]]],
        career_goals: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """Generate skill gap analysis for career goals."""
        if not career_goals:
            return []
        
        current_skills = await self._extract_technical_skills(user_assessments)
        analyses = []
        
        for goal in career_goals:
            try:
                analysis = self.shap_explainer.analyze_skill_gaps(
                    current_skills=current_skills,
                    target_role=goal,
                    experience_level="intermediate"
                )
                
                analyses.append({
                    'target_role': goal,
                    'skill_gaps': analysis.skill_gaps,
                    'priority_gaps': analysis.priority_gaps,
                    'development_timeline': analysis.development_timeline
                })
            except Exception as e:
                logger.warning(f"Failed to analyze skill gaps for {goal}: {e}")
        
        return analyses
    
    def _flatten_assessments(self, user_assessments: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Flatten grouped assessments into a single list."""
        flattened = []
        for assessments in user_assessments.values():
            flattened.extend(assessments)
        return flattened
    
    def _calculate_kash_trend(self, assessments: List[UserAssessment]) -> List[Dict[str, Any]]:
        """Calculate KASH score trend over time."""
        trend = []
        
        for assessment in assessments:
            result_data = assessment.result_data or {}
            kash_score = result_data.get('kash_score', {})
            
            trend.append({
                'date': assessment.created_at.isoformat(),
                'overall_score': kash_score.get('overall_score', 0),
                'knowledge_score': kash_score.get('knowledge_score', 0),
                'abilities_score': kash_score.get('abilities_score', 0),
                'skills_score': kash_score.get('skills_score', 0),
                'experience_score': kash_score.get('experience_score', 0)
            })
        
        return trend
    
    def _aggregate_career_insights(self, assessments: List[UserAssessment]) -> Dict[str, Any]:
        """Aggregate career insights from multiple assessments."""
        if not assessments:
            return {}
        
        latest_assessment = assessments[0]
        result_data = latest_assessment.result_data or {}
        
        return {
            'career_stage': result_data.get('kash_score', {}).get('career_stage', 'unknown'),
            'strengths': result_data.get('kash_score', {}).get('strengths', []),
            'improvement_areas': result_data.get('kash_score', {}).get('improvement_areas', []),
            'career_explanations': result_data.get('career_explanations', [])
        }
    
    def _aggregate_feature_importance_trends(self, assessments: List[UserAssessment]) -> Dict[str, Any]:
        """Aggregate feature importance trends."""
        if not assessments:
            return {}
        
        latest_assessment = assessments[0]
        result_data = latest_assessment.result_data or {}
        
        return {
            'current_importance': result_data.get('feature_importance', []),
            'top_features': result_data.get('feature_importance', [])[:5]
        }
    
    def _aggregate_recommendation_history(self, assessments: List[UserAssessment]) -> List[Dict[str, Any]]:
        """Aggregate recommendation history."""
        history = []
        
        for assessment in assessments:
            result_data = assessment.result_data or {}
            kash_score = result_data.get('kash_score', {})
            
            history.append({
                'date': assessment.created_at.isoformat(),
                'recommendations': kash_score.get('recommendations', []),
                'career_stage': kash_score.get('career_stage', 'unknown')
            })
        
        return history
    
    def _calculate_skill_development_progress(self, assessments: List[UserAssessment]) -> Dict[str, Any]:
        """Calculate skill development progress over time."""
        if len(assessments) < 2:
            return {}
        
        # Compare latest with earliest assessment
        earliest = assessments[-1]
        latest = assessments[0]
        
        earliest_data = earliest.result_data or {}
        latest_data = latest.result_data or {}
        
        earliest_kash = earliest_data.get('kash_score', {})
        latest_kash = latest_data.get('kash_score', {})
        
        progress = {
            'overall_improvement': latest_kash.get('overall_score', 0) - earliest_kash.get('overall_score', 0),
            'domain_progress': {
                'knowledge': latest_kash.get('knowledge_score', 0) - earliest_kash.get('knowledge_score', 0),
                'abilities': latest_kash.get('abilities_score', 0) - earliest_kash.get('abilities_score', 0),
                'skills': latest_kash.get('skills_score', 0) - earliest_kash.get('skills_score', 0),
                'experience': latest_kash.get('experience_score', 0) - earliest_kash.get('experience_score', 0)
            },
            'time_period_days': (latest.created_at - earliest.created_at).days
        }
        
        return progress
