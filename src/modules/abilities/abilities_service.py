"""Abilities module service for adaptive assessments and cognitive evaluation."""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import uuid

from src.core.database import get_db
from src.core.logging import get_logger
from src.models.user import User
from src.models.assessment import UserAssessment, AbilitiesAssessment
from src.modules.abilities.quiz_engine import (
    QuizEngine, 
    QuizSession, 
    CognitiveDomain, 
    QuestionType,
    DifficultyLevel
)

logger = get_logger(__name__)


_quiz_engine_instance = None


def _get_quiz_engine() -> QuizEngine:
    """Get or create a singleton QuizEngine instance."""
    global _quiz_engine_instance
    if _quiz_engine_instance is None:
        _quiz_engine_instance = QuizEngine()
    return _quiz_engine_instance


class AbilitiesService:
    """Service for abilities domain operations including adaptive assessments."""
    
    def __init__(self, db: Session):
        self.db = db
        self.quiz_engine = _get_quiz_engine()
    
    async def start_assessment(
        self, 
        user_id: str, 
        quiz_type: str, 
        domain: CognitiveDomain,
        num_questions: int = 20,
        adaptive: bool = True
    ) -> Dict[str, Any]:
        """
        Start a new abilities assessment.
        
        Args:
            user_id: User UUID
            quiz_type: Type of quiz (cognitive, behavioral, technical)
            domain: Cognitive domain to assess
            num_questions: Number of questions
            adaptive: Whether to use adaptive difficulty
            
        Returns:
            Dictionary with session information and first question
        """
        logger.info(f"Starting abilities assessment for user {user_id} in domain {domain}")
        
        try:
            # Create quiz session
            session = self.quiz_engine.create_quiz_session(
                user_id=user_id,
                quiz_type=quiz_type,
                domain=domain,
                num_questions=num_questions,
                adaptive=adaptive
            )
            
            # Create user assessment record
            assessment = UserAssessment(
                id=uuid.uuid4(),
                user_id=user_id,
                assessment_type='abilities',
                assessment_name=f'{domain.value.capitalize()} Assessment',
                assessment_version='1.0',
                status='in_progress',
                created_at=datetime.now(),
                started_at=datetime.now(),
                input_data={
                    'quiz_type': quiz_type,
                    'domain': domain.value,
                    'num_questions': num_questions,
                    'adaptive': adaptive,
                    'session_id': session.id
                }
            )
            
            self.db.add(assessment)
            self.db.flush()  # Get the assessment ID
            
            # Create abilities-specific assessment record
            abilities_assessment = AbilitiesAssessment(
                id=uuid.uuid4(),
                assessment_id=assessment.id,
                quiz_type=quiz_type,
                difficulty_level=session.adaptive_difficulty.value,
                question_count=num_questions
            )
            
            self.db.add(abilities_assessment)
            self.db.commit()
            
            # Get first question
            first_question = session.get_current_question()
            
            return {
                'assessment_id': str(assessment.id),
                'session_id': session.id,
                'quiz_type': quiz_type,
                'domain': domain.value,
                'total_questions': num_questions,
                'adaptive': adaptive,
                'current_question': self._question_to_dict(first_question) if first_question else None,
                'question_number': 1,
                'time_limit_seconds': first_question.time_limit_seconds if first_question else 60
            }
            
        except Exception as e:
            logger.error(f"Failed to start abilities assessment for user {user_id}: {e}")
            self.db.rollback()
            raise
    
    async def submit_answer(
        self, 
        user_id: str, 
        session_id: str, 
        question_id: str, 
        answer: Any,
        response_time_ms: float
    ) -> Dict[str, Any]:
        """
        Submit answer to current question.
        
        Args:
            user_id: User UUID
            session_id: Quiz session ID
            question_id: Question being answered
            answer: User's answer
            response_time_ms: Time taken to answer
            
        Returns:
            Dictionary with answer result and next question
        """
        logger.info(f"Submitting answer for session {session_id}")
        
        try:
            # Submit to quiz engine
            is_correct, next_question = self.quiz_engine.submit_response(
                session_id=session_id,
                question_id=question_id,
                user_answer=answer,
                response_time_ms=response_time_ms
            )
            
            # Get session
            session = self.quiz_engine.get_session(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")
            
            # Update assessment record - find the in-progress abilities assessment for this user
            assessment = self.db.query(UserAssessment).filter(
                UserAssessment.user_id == user_id,
                UserAssessment.assessment_type == 'abilities',
                UserAssessment.status == 'in_progress'
            ).order_by(UserAssessment.created_at.desc()).first()
            
            if assessment:
                # Update progress
                progress = session.get_progress()
                assessment.input_data['progress'] = progress
                
                # Store response data
                if 'responses' not in assessment.input_data:
                    assessment.input_data['responses'] = []
                
                assessment.input_data['responses'].append({
                    'question_id': question_id,
                    'answer': answer,
                    'is_correct': is_correct,
                    'response_time_ms': response_time_ms,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Flag the JSON column as modified so SQLAlchemy detects the change
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(assessment, 'input_data')
                self.db.commit()
            
            # Prepare response
            response = {
                'is_correct': is_correct,
                'question_number': session.current_question_index + 1,
                'total_questions': len(session.questions),
                'progress': session.get_progress(),
                'quiz_completed': session.is_completed
            }
            
            if next_question:
                response['next_question'] = self._question_to_dict(next_question)
                response['time_limit_seconds'] = next_question.time_limit_seconds
            else:
                # Quiz completed, calculate final results
                results = self.quiz_engine.complete_session(session_id)
                if assessment:
                    await self._finalize_assessment(assessment, session, results)
                response['results'] = results
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to submit answer for session {session_id}: {e}")
            raise
    
    async def get_assessment_status(
        self, 
        user_id: str, 
        assessment_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get current status of an assessment.
        
        Args:
            user_id: User UUID
            assessment_id: Assessment UUID
            
        Returns:
            Assessment status or None if not found
        """
        assessment = self.db.query(UserAssessment).filter(
            UserAssessment.id == assessment_id,
            UserAssessment.user_id == user_id,
            UserAssessment.assessment_type == 'abilities'
        ).first()
        
        if not assessment:
            return None
        
        session_id = assessment.input_data.get('session_id')
        session = self.quiz_engine.get_session(session_id) if session_id else None
        
        status = {
            'assessment_id': str(assessment.id),
            'status': assessment.status,
            'quiz_type': assessment.input_data.get('quiz_type'),
            'domain': assessment.input_data.get('domain'),
            'created_at': assessment.created_at.isoformat(),
            'started_at': assessment.started_at.isoformat() if assessment.started_at else None,
            'completed_at': assessment.completed_at.isoformat() if assessment.completed_at else None
        }
        
        if session and not session.is_completed:
            status.update({
                'current_question_number': session.current_question_index + 1,
                'total_questions': len(session.questions),
                'progress': session.get_progress(),
                'time_spent_seconds': session.get_time_spent(),
                'adaptive_difficulty': session.adaptive_difficulty.value
            })
        elif assessment.status == 'completed':
            # Include final results
            status['results'] = assessment.result_data
        
        return status
    
    async def get_assessment_results(
        self, 
        user_id: str, 
        assessment_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed results for a completed assessment.
        
        Args:
            user_id: User UUID
            assessment_id: Assessment UUID
            
        Returns:
            Assessment results or None if not found
        """
        assessment = self.db.query(UserAssessment).filter(
            UserAssessment.id == assessment_id,
            UserAssessment.user_id == user_id,
            UserAssessment.assessment_type == 'abilities'
        ).first()
        
        if not assessment or assessment.status != 'completed':
            return None
        
        # Get abilities assessment details
        abilities_assessment = self.db.query(AbilitiesAssessment).filter(
            AbilitiesAssessment.assessment_id == assessment.id
        ).first()
        
        results = assessment.result_data or {}
        
        # Add detailed abilities assessment data
        if abilities_assessment:
            results['abilities_details'] = {
                'quiz_type': abilities_assessment.quiz_type,
                'difficulty_level': abilities_assessment.difficulty_level,
                'total_questions': abilities_assessment.total_questions,
                'correct_answers': abilities_assessment.correct_answers,
                'time_spent_minutes': abilities_assessment.time_spent_minutes,
                'cognitive_scores': abilities_assessment.cognitive_scores,
                'behavioral_scores': abilities_assessment.behavioral_scores,
                'technical_scores': abilities_assessment.technical_scores
            }
        
        return results
    
    async def get_user_abilities_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive abilities profile for a user.
        
        Args:
            user_id: User UUID
            
        Returns:
            User's abilities profile with aggregated data
        """
        assessments = self.db.query(UserAssessment).filter(
            UserAssessment.user_id == user_id,
            UserAssessment.assessment_type == 'abilities',
            UserAssessment.status == 'completed'
        ).order_by(UserAssessment.completed_at.desc()).all()
        
        if not assessments:
            return {
                'user_id': user_id,
                'total_assessments': 0,
                'domain_scores': {},
                'overall_performance': {},
                'recommendations': [],
                'recent_activity': [],
                'last_assessment': None
            }
        
        # Aggregate domain scores
        domain_scores = {}
        domain_counts = {}
        
        for assessment in assessments:
            results = assessment.result_data or {}
            domain = assessment.input_data.get('domain', 'unknown')
            percentage = results.get('percentage', 0)
            
            if domain not in domain_scores:
                domain_scores[domain] = 0
                domain_counts[domain] = 0
            
            domain_scores[domain] += percentage
            domain_counts[domain] += 1
        
        # Calculate averages
        for domain in domain_scores:
            domain_scores[domain] = domain_scores[domain] / domain_counts[domain]
        
        # Overall performance metrics
        all_percentages = [ass.result_data.get('percentage', 0) for ass in assessments if ass.result_data]
        overall_performance = {
            'average_score': sum(all_percentages) / len(all_percentages) if all_percentages else 0,
            'best_score': max(all_percentages) if all_percentages else 0,
            'total_assessments': len(assessments),
            'improvement_trend': self._calculate_improvement_trend(assessments)
        }
        
        # Generate recommendations
        recommendations = self._generate_profile_recommendations(domain_scores, overall_performance)
        
        # Recent activity
        recent_activity = []
        for assessment in assessments[:5]:  # Last 5 assessments
            recent_activity.append({
                'assessment_id': str(assessment.id),
                'domain': assessment.input_data.get('domain'),
                'score': assessment.result_data.get('percentage', 0),
                'completed_at': assessment.completed_at.isoformat() if assessment.completed_at else None
            })
        
        return {
            'user_id': user_id,
            'total_assessments': len(assessments),
            'domain_scores': domain_scores,
            'overall_performance': overall_performance,
            'recommendations': recommendations,
            'recent_activity': recent_activity,
            'last_assessment': assessments[0].completed_at.isoformat() if assessments[0].completed_at else None
        }
    
    async def get_available_assessments(self) -> List[Dict[str, Any]]:
        """
        Get list of available assessment types.
        
        Returns:
            List of available assessments with descriptions
        """
        assessments = []
        
        for domain in CognitiveDomain:
            assessments.append({
                'domain': domain.value,
                'display_name': self._get_domain_display_name(domain),
                'description': self._get_domain_description(domain),
                'estimated_time_minutes': 15,
                'question_count': 20,
                'adaptive': True,
                'difficulty_levels': [d.value for d in DifficultyLevel]
            })
        
        return assessments
    
    async def _finalize_assessment(
        self, 
        assessment: UserAssessment, 
        session: QuizSession, 
        results: Dict[str, Any]
    ):
        """Finalize assessment with results."""
        try:
            # Update assessment
            assessment.status = 'completed'
            assessment.completed_at = datetime.now()
            assessment.normalized_score = results.get('percentage', 0)
            assessment.confidence_score = self._calculate_confidence_score(session, results)
            assessment.result_data = results
            
            # Update abilities assessment
            abilities_assessment = self.db.query(AbilitiesAssessment).filter(
                AbilitiesAssessment.assessment_id == assessment.id
            ).first()
            
            if abilities_assessment:
                abilities_assessment.total_questions = len(session.questions)
                abilities_assessment.correct_answers = results.get('correct_answers', 0)
                abilities_assessment.time_spent_minutes = results.get('time_spent_seconds', 0) / 60
                
                # Calculate cognitive scores based on domain
                domain_scores = results.get('domain_scores', {})
                if session.domain.value in domain_scores:
                    domain_data = domain_scores[session.domain.value]
                    
                    if session.domain == CognitiveDomain.MEMORY:
                        abilities_assessment.cognitive_scores = {
                            'short_term_memory': domain_data.get('score', 0),
                            'working_memory': domain_data.get('score', 0) * 0.9,  # Slight variation
                            'long_term_memory': domain_data.get('score', 0) * 0.85
                        }
                    elif session.domain == CognitiveDomain.ATTENTION:
                        abilities_assessment.cognitive_scores = {
                            'selective_attention': domain_data.get('score', 0),
                            'divided_attention': domain_data.get('score', 0) * 0.9,
                            'sustained_attention': domain_data.get('score', 0) * 0.95
                        }
                    elif session.domain == CognitiveDomain.PROCESSING_SPEED:
                        abilities_assessment.cognitive_scores = {
                            'visual_processing': domain_data.get('score', 0),
                            'auditory_processing': domain_data.get('score', 0) * 0.9,
                            'cognitive_processing': domain_data.get('score', 0)
                        }
                    elif session.domain == CognitiveDomain.PROBLEM_SOLVING:
                        abilities_assessment.cognitive_scores = {
                            'analytical_reasoning': domain_data.get('score', 0),
                            'creative_problem_solving': domain_data.get('score', 0) * 0.85,
                            'critical_thinking': domain_data.get('score', 0) * 0.9
                        }
            
            self.db.commit()
            logger.info(f"Finalized abilities assessment {assessment.id}")
            
        except Exception as e:
            logger.error(f"Failed to finalize assessment {assessment.id}: {e}")
            self.db.rollback()
            raise
    
    def _question_to_dict(self, question) -> Dict[str, Any]:
        """Convert Question object to dictionary."""
        return {
            'id': question.id,
            'type': question.type.value,
            'domain': question.domain.value,
            'difficulty': str(question.difficulty.value),
            'question_text': question.question_text,
            'options': question.options,
            'time_limit_seconds': question.time_limit_seconds,
            'points_possible': question.points_possible
        }
    
    def _calculate_confidence_score(self, session: QuizSession, results: Dict[str, Any]) -> float:
        """Calculate confidence score for assessment results."""
        base_confidence = 0.7
        
        # Adjust based on response consistency
        if len(session.responses) >= 5:
            response_times = [r.response_time_ms for r in session.responses]
            time_variance = sum((t - sum(response_times)/len(response_times))**2 for t in response_times) / len(response_times)
            time_consistency = max(0, 1 - (time_variance / 1000000))  # Normalize
            
            base_confidence += time_consistency * 0.2
        
        # Adjust based on adaptive algorithm confidence
        adaptive_results = results.get('adaptive_results', {})
        if 'ability_uncertainty' in adaptive_results:
            uncertainty = adaptive_results['ability_uncertainty']
            base_confidence += max(0, 1 - uncertainty) * 0.1
        
        return min(base_confidence, 1.0)
    
    def _calculate_improvement_trend(self, assessments: List[UserAssessment]) -> str:
        """Calculate improvement trend over recent assessments."""
        if len(assessments) < 2:
            return "insufficient_data"
        
        # Take last 5 assessments
        recent_assessments = assessments[:5]
        scores = [ass.result_data.get('percentage', 0) for ass in recent_assessments if ass.result_data]
        
        if len(scores) < 2:
            return "insufficient_data"
        
        # Calculate trend
        first_half = scores[:len(scores)//2]
        second_half = scores[len(scores)//2:]
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        if second_avg > first_avg + 5:
            return "improving"
        elif second_avg < first_avg - 5:
            return "declining"
        else:
            return "stable"
    
    def _generate_profile_recommendations(
        self, 
        domain_scores: Dict[str, float], 
        overall_performance: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on profile."""
        recommendations = []
        
        # Overall performance recommendations
        avg_score = overall_performance.get('average_score', 0)
        if avg_score >= 85:
            recommendations.append("Excellent performance! Consider advanced assessments.")
        elif avg_score >= 70:
            recommendations.append("Good performance! Continue practicing to maintain consistency.")
        elif avg_score >= 55:
            recommendations.append("Fair performance. Focus on weaker domains.")
        else:
            recommendations.append("Consider foundational exercises to build core abilities.")
        
        # Domain-specific recommendations
        for domain, score in domain_scores.items():
            if score < 60:
                recommendations.append(f"Focus on improving {domain} abilities with targeted practice.")
            elif score > 85:
                recommendations.append(f"Excellent {domain} skills! Consider advanced challenges.")
        
        # Trend-based recommendations
        trend = overall_performance.get('improvement_trend')
        if trend == "declining":
            recommendations.append("Recent performance shows decline. Consider reviewing fundamentals.")
        elif trend == "improving":
            recommendations.append("Great improvement trend! Keep up the momentum.")
        
        return recommendations
    
    def _get_domain_display_name(self, domain: CognitiveDomain) -> str:
        """Get display name for cognitive domain."""
        display_names = {
            CognitiveDomain.MEMORY: "Memory & Recall",
            CognitiveDomain.ATTENTION: "Attention & Focus",
            CognitiveDomain.PROCESSING_SPEED: "Processing Speed",
            CognitiveDomain.EXECUTIVE_FUNCTION: "Executive Function",
            CognitiveDomain.LANGUAGE: "Language Skills",
            CognitiveDomain.VISUAL_SPATIAL: "Visual-Spatial Reasoning",
            CognitiveDomain.PROBLEM_SOLVING: "Problem Solving",
            CognitiveDomain.CREATIVITY: "Creativity & Innovation"
        }
        return display_names.get(domain, domain.value.title())
    
    def _get_domain_description(self, domain: CognitiveDomain) -> str:
        """Get description for cognitive domain."""
        descriptions = {
            CognitiveDomain.MEMORY: "Assesses short-term, working, and long-term memory capabilities",
            CognitiveDomain.ATTENTION: "Evaluates selective, divided, and sustained attention skills",
            CognitiveDomain.PROCESSING_SPEED: "Measures speed of visual, auditory, and cognitive processing",
            CognitiveDomain.EXECUTIVE_FUNCTION: "Tests planning, organization, and cognitive flexibility",
            CognitiveDomain.LANGUAGE: "Assesses verbal comprehension, expression, and reasoning",
            CognitiveDomain.VISUAL_SPATIAL: "Evaluates visual perception and spatial reasoning abilities",
            CognitiveDomain.PROBLEM_SOLVING: "Tests analytical reasoning and creative problem-solving",
            CognitiveDomain.CREATIVITY: "Measures divergent thinking and innovative capabilities"
        }
        return descriptions.get(domain, "Assessment of cognitive abilities")
