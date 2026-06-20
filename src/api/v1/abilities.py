"""Abilities module API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from src.core.database import get_db
from src.core.auth import get_current_user
from src.core.logging import get_logger
from src.models.user import User
from src.models.assessment import UserAssessment
from src.modules.abilities.abilities_service import AbilitiesService
from src.modules.abilities.quiz_engine import CognitiveDomain
from src.schemas.abilities import (
    StartAssessmentRequest,
    AssessmentStartResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    AssessmentStatus,
    AbilitiesAssessmentSummary,
    AbilitiesProfileResponse,
    AvailableAssessmentsResponse,
    QuizSessionInfo,
    ErrorResponse
)

router = APIRouter(prefix="/abilities", tags=["abilities"])
logger = get_logger(__name__)


@router.post("/start", response_model=AssessmentStartResponse)
async def start_assessment(
    request: StartAssessmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start a new abilities assessment.
    
    - **quiz_type**: Type of quiz (cognitive, behavioral, technical)
    - **domain**: Cognitive domain to assess
    - **num_questions**: Number of questions (5-50, default: 20)
    - **adaptive**: Use adaptive difficulty (default: true)
    
    Creates a new assessment session and returns the first question.
    """
    try:
        abilities_service = AbilitiesService(db)
        
        # Convert string enums to proper enums
        domain = CognitiveDomain(request.domain.value)
        
        result = await abilities_service.start_assessment(
            user_id=str(current_user.id),
            quiz_type=request.quiz_type.value,
            domain=domain,
            num_questions=request.num_questions,
            adaptive=request.adaptive
        )
        
        return AssessmentStartResponse(
            assessment_id=result['assessment_id'],
            session_id=result['session_id'],
            quiz_type=request.quiz_type,
            domain=request.domain,
            total_questions=result['total_questions'],
            adaptive=result['adaptive'],
            current_question=result['current_question'],
            question_number=result['question_number'],
            time_limit_seconds=result['time_limit_seconds']
        )
        
    except Exception as e:
        import traceback
        logger.error(f"Failed to start assessment for user {current_user.id}: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start assessment"
        )


@router.post("/submit-answer", response_model=SubmitAnswerResponse)
async def submit_answer(
    request: SubmitAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit answer to current question.
    
    - **session_id**: Quiz session ID
    - **question_id**: Question being answered
    - **answer**: User's answer
    - **response_time_ms**: Time taken in milliseconds
    
    Returns answer result and next question or final results.
    """
    try:
        abilities_service = AbilitiesService(db)
        
        result = await abilities_service.submit_answer(
            user_id=str(current_user.id),
            session_id=request.session_id,
            question_id=request.question_id,
            answer=request.answer,
            response_time_ms=request.response_time_ms
        )
        
        return SubmitAnswerResponse(
            is_correct=result['is_correct'],
            question_number=result['question_number'],
            total_questions=result['total_questions'],
            progress=result['progress'],
            quiz_completed=result['quiz_completed'],
            next_question=result.get('next_question'),
            time_limit_seconds=result.get('time_limit_seconds'),
            results=result.get('results')
        )
        
    except ValueError as e:
        logger.error(f"Invalid answer submission: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to submit answer for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit answer"
        )


@router.get("/assessments", response_model=List[AbilitiesAssessmentSummary])
async def get_abilities_assessments(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all abilities assessments for the current user.
    
    - **limit**: Maximum number of assessments to return (default: 10)
    """
    try:
        assessments = db.query(UserAssessment).filter(
            UserAssessment.user_id == current_user.id,
            UserAssessment.assessment_type == 'abilities'
        ).order_by(UserAssessment.created_at.desc()).limit(limit).all()
        
        summaries = []
        for assessment in assessments:
            input_data = assessment.input_data or {}
            result_data = assessment.result_data or {}
            
            # Get abilities assessment details
            abilities_assessment = db.query(UserAssessment).join(
                # This would be a proper join with AbilitiesAssessment in a real implementation
                # For now, we'll use the data from the main assessment
            ).filter(UserAssessment.id == assessment.id).first()
            
            summaries.append(AbilitiesAssessmentSummary(
                assessment_id=str(assessment.id),
                assessment_name=assessment.assessment_name,
                status=assessment.status,
                quiz_type=input_data.get('quiz_type', 'cognitive'),
                domain=input_data.get('domain', 'unknown'),
                normalized_score=assessment.normalized_score,
                confidence_score=assessment.confidence_score,
                created_at=assessment.created_at,
                completed_at=assessment.completed_at,
                correct_answers=result_data.get('correct_answers'),
                total_questions=result_data.get('total_questions'),
                time_spent_minutes=result_data.get('time_spent_seconds', 0) / 60
            ))
        
        return summaries
        
    except Exception as e:
        logger.error(f"Failed to get abilities assessments for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve abilities assessments"
        )


@router.get("/assessments/{assessment_id}/status", response_model=AssessmentStatus)
async def get_assessment_status(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current status of an assessment.
    
    - **assessment_id**: UUID of the assessment
    """
    try:
        abilities_service = AbilitiesService(db)
        status = await abilities_service.get_assessment_status(
            user_id=str(current_user.id),
            assessment_id=assessment_id
        )
        
        if not status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found"
            )
        
        return AssessmentStatus(**status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get assessment status {assessment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve assessment status"
        )


@router.get("/assessments/{assessment_id}/results")
async def get_assessment_results(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed results for a completed assessment.
    
    - **assessment_id**: UUID of the assessment
    """
    try:
        abilities_service = AbilitiesService(db)
        results = await abilities_service.get_assessment_results(
            user_id=str(current_user.id),
            assessment_id=assessment_id
        )
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment results not found"
            )
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get assessment results {assessment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve assessment results"
        )


@router.get("/profile", response_model=AbilitiesProfileResponse)
async def get_abilities_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive abilities profile for the current user.
    
    Aggregates data from all abilities assessments.
    """
    try:
        abilities_service = AbilitiesService(db)
        profile = await abilities_service.get_user_abilities_profile(
            user_id=str(current_user.id)
        )
        
        return AbilitiesProfileResponse(**profile)
        
    except Exception as e:
        logger.error(f"Failed to get abilities profile for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve abilities profile"
        )


@router.get("/available", response_model=AvailableAssessmentsResponse)
async def get_available_assessments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of available assessment types.
    
    Returns all available cognitive domain assessments with descriptions.
    """
    try:
        abilities_service = AbilitiesService(db)
        assessments = await abilities_service.get_available_assessments()
        
        return AvailableAssessmentsResponse(
            assessments=assessments,
            total_count=len(assessments)
        )
        
    except Exception as e:
        logger.error(f"Failed to get available assessments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available assessments"
        )


@router.get("/sessions/{session_id}", response_model=QuizSessionInfo)
async def get_quiz_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get information about an active quiz session.
    
    - **session_id**: Quiz session ID
    """
    try:
        abilities_service = AbilitiesService(db)
        
        # Find assessment associated with this session
        assessment = db.query(UserAssessment).filter(
            UserAssessment.user_id == current_user.id,
            UserAssessment.input_data['session_id'].astext == session_id
        ).first()
        
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Get session status
        status = await abilities_service.get_assessment_status(
            user_id=str(current_user.id),
            assessment_id=str(assessment.id)
        )
        
        if not status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session status not found"
            )
        
        return QuizSessionInfo(
            session_id=session_id,
            assessment_id=str(assessment.id),
            domain=status['domain'],
            current_question_number=status.get('current_question_number', 0),
            total_questions=status.get('total_questions', 0),
            progress=status.get('progress', 0.0),
            time_spent_seconds=status.get('time_spent_seconds', 0.0),
            adaptive_difficulty=status.get('adaptive_difficulty', '3'),
            is_completed=status['status'] == 'completed'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get quiz session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve quiz session"
        )


@router.post("/sessions/{session_id}/continue")
async def continue_quiz_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Continue a quiz session and get current question.
    
    - **session_id**: Quiz session ID
    """
    try:
        abilities_service = AbilitiesService(db)
        
        # Find assessment associated with this session
        assessment = db.query(UserAssessment).filter(
            UserAssessment.user_id == current_user.id,
            UserAssessment.input_data['session_id'].astext == session_id
        ).first()
        
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Get session status
        status = await abilities_service.get_assessment_status(
            user_id=str(current_user.id),
            assessment_id=str(assessment.id)
        )
        
        if not status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        if status['status'] == 'completed':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session is already completed"
            )
        
        # Get current question from session
        from src.modules.abilities.quiz_engine import QuizEngine
        quiz_engine = QuizEngine()
        session = quiz_engine.get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz session not found"
            )
        
        current_question = session.get_current_question()
        if not current_question:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No current question available"
            )
        
        return {
            "session_id": session_id,
            "assessment_id": str(assessment.id),
            "current_question": {
                'id': current_question.id,
                'type': current_question.type.value,
                'domain': current_question.domain.value,
                'difficulty': current_question.difficulty.value,
                'question_text': current_question.question_text,
                'options': current_question.options,
                'time_limit_seconds': current_question.time_limit_seconds,
                'points_possible': current_question.points_possible
            },
            "question_number": session.current_question_index + 1,
            "total_questions": len(session.questions),
            "progress": session.get_progress(),
            "time_limit_seconds": current_question.time_limit_seconds
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to continue quiz session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to continue quiz session"
        )


@router.delete("/assessments/{assessment_id}")
async def delete_assessment(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an abilities assessment.
    
    - **assessment_id**: UUID of the assessment to delete
    """
    try:
        assessment = db.query(UserAssessment).filter(
            UserAssessment.id == assessment_id,
            UserAssessment.user_id == current_user.id,
            UserAssessment.assessment_type == 'abilities'
        ).first()
        
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found"
            )
        
        # Check if assessment is in progress
        if assessment.status == 'in_progress':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete assessment in progress"
            )
        
        # Delete assessment (cascade delete should handle related records)
        db.delete(assessment)
        db.commit()
        
        logger.info(f"Deleted abilities assessment {assessment_id} for user {current_user.id}")
        return {"message": "Assessment deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete assessment {assessment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete assessment"
        )
