"""Intelligence module API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from src.core.database import get_db
from src.core.auth import get_current_user
from src.core.logging import get_logger
from src.models.user import User
from src.models.assessment import UserAssessment
from src.modules.intelligence.intelligence_service import IntelligenceService
from src.schemas.intelligence import (
    IntelligenceAssessmentRequest,
    IntelligenceAssessmentResults,
    IntelligenceAssessmentSummary,
    IntelligenceProfileResponse,
    CareerPathRequest,
    CareerPathResponse,
    SkillGapRequest,
    SkillGapResponse,
    ErrorResponse
)

router = APIRouter(prefix="/intelligence", tags=["intelligence"])
logger = get_logger(__name__)


@router.post("/assess", response_model=IntelligenceAssessmentResults)
async def generate_intelligence_assessment(
    request: IntelligenceAssessmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate comprehensive intelligence assessment with KASH scoring and explainability.
    
    - **industry**: Target industry for weight adjustment
    - **career_goals**: List of career goals
    - **custom_weights**: Optional custom KASH weight overrides
    
    Performs comprehensive analysis including KASH scoring, SHAP explanations,
    career path analysis, and skill gap identification.
    """
    try:
        intelligence_service = IntelligenceService(db)
        assessment = await intelligence_service.generate_comprehensive_intelligence(
            user_id=str(current_user.id),
            industry=request.industry,
            career_goals=request.career_goals,
            custom_weights=request.custom_weights
        )
        
        # Convert to response format
        result_data = assessment.result_data or {}
        kash_score = result_data.get('kash_score', {})
        
        return IntelligenceAssessmentResults(
            assessment_id=str(assessment.id),
            assessment_name=assessment.assessment_name,
            status=assessment.status,
            created_at=assessment.created_at,
            completed_at=assessment.completed_at,
            
            # KASH scoring
            kash_score={
                'overall_score': kash_score.get('overall_score', 0),
                'knowledge_score': kash_score.get('knowledge_score', 0),
                'abilities_score': kash_score.get('abilities_score', 0),
                'skills_score': kash_score.get('skills_score', 0),
                'experience_score': kash_score.get('experience_score', 0),
                'confidence': kash_score.get('confidence', 0),
                'career_stage': kash_score.get('career_stage', 'explorer'),
                'strengths': kash_score.get('strengths', []),
                'improvement_areas': kash_score.get('improvement_areas', []),
                'recommendations': kash_score.get('recommendations', [])
            },
            
            # SHAP explanations
            feature_importance=[
                {
                    'feature_name': fi.get('feature_name', ''),
                    'feature_value': fi.get('feature_value', 0),
                    'shap_value': fi.get('shap_value', 0),
                    'contribution_percentage': fi.get('contribution_percentage', 0),
                    'direction': fi.get('direction', 'neutral'),
                    'explanation': fi.get('explanation', '')
                }
                for fi in result_data.get('feature_importance', [])
            ],
            
            career_explanations=[
                {
                    'career_path': ce.get('career', ''),
                    'match_score': ce.get('match_score', 0),
                    'key_factors': ce.get('key_factors', []),
                    'skill_gaps': ce.get('skill_gaps', []),
                    'alignment_reasons': ce.get('alignment_reasons', []),
                    'development_needs': ce.get('development_needs', [])
                }
                for ce in result_data.get('career_explanations', [])
            ],
            
            skill_gap_analysis=result_data.get('skill_gap_analysis', []),
            
            assessment_impacts=[
                {
                    'assessment_type': ai.get('assessment_type', ''),
                    'assessment_name': ai.get('assessment_name', ''),
                    'score_contribution': ai.get('score_contribution', 0),
                    'confidence_impact': ai.get('confidence_impact', 0),
                    'improvement_potential': ai.get('improvement_potential', 0)
                }
                for ai in result_data.get('assessment_impacts', [])
            ],
            
            recommendation_explanations={
                key: {
                    'recommendation': value.get('recommendation', ''),
                    'type': value.get('type', ''),
                    'explanation': value.get('explanation', ''),
                    'priority': value.get('priority', 'medium'),
                    'expected_impact': value.get('expected_impact', {})
                }
                for key, value in result_data.get('recommendation_explanations', {}).items()
            },
            
            # Input parameters
            industry=request.industry,
            career_goals=request.career_goals,
            custom_weights=request.custom_weights
        )
        
    except ValueError as e:
        logger.error(f"Intelligence assessment failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        import traceback
        logger.error(f"Intelligence assessment failed for user {current_user.id}: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Intelligence assessment generation failed"
        )


@router.get("/assessments", response_model=List[IntelligenceAssessmentSummary])
async def get_intelligence_assessments(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all intelligence assessments for the current user.
    
    - **limit**: Maximum number of assessments to return (default: 10)
    """
    try:
        intelligence_service = IntelligenceService(db)
        assessments = await intelligence_service.get_user_intelligence_assessments(
            user_id=str(current_user.id),
            limit=limit
        )
        
        summaries = []
        for assessment in assessments:
            result_data = assessment.result_data or {}
            kash_score = result_data.get('kash_score', {})
            input_data = assessment.input_data or {}
            
            summaries.append(IntelligenceAssessmentSummary(
                assessment_id=str(assessment.id),
                assessment_name=assessment.assessment_name,
                status=assessment.status,
                created_at=assessment.created_at,
                completed_at=assessment.completed_at,
                
                # Quick KASH scores
                overall_score=kash_score.get('overall_score'),
                confidence=kash_score.get('confidence'),
                career_stage=kash_score.get('career_stage'),
                
                # Quick stats
                industry=input_data.get('industry'),
                career_goals_count=len(input_data.get('career_goals', [])),
                strengths_count=len(kash_score.get('strengths', [])),
                recommendations_count=len(kash_score.get('recommendations', []))
            ))
        
        return summaries
        
    except Exception as e:
        logger.error(f"Failed to get intelligence assessments for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve intelligence assessments"
        )


@router.get("/assessments/{assessment_id}", response_model=IntelligenceAssessmentResults)
async def get_intelligence_assessment(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed results for an intelligence assessment.
    
    - **assessment_id**: UUID of the assessment
    """
    try:
        intelligence_service = IntelligenceService(db)
        assessment = await intelligence_service.get_intelligence_assessment(
            assessment_id=assessment_id,
            user_id=str(current_user.id)
        )
        
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Intelligence assessment not found"
            )
        
        # Convert to response format
        result_data = assessment.result_data or {}
        kash_score = result_data.get('kash_score', {})
        input_data = assessment.input_data or {}
        
        return IntelligenceAssessmentResults(
            assessment_id=str(assessment.id),
            assessment_name=assessment.assessment_name,
            status=assessment.status,
            created_at=assessment.created_at,
            completed_at=assessment.completed_at,
            
            # KASH scoring
            kash_score={
                'overall_score': kash_score.get('overall_score', 0),
                'knowledge_score': kash_score.get('knowledge_score', 0),
                'abilities_score': kash_score.get('abilities_score', 0),
                'skills_score': kash_score.get('skills_score', 0),
                'experience_score': kash_score.get('experience_score', 0),
                'confidence': kash_score.get('confidence', 0),
                'career_stage': kash_score.get('career_stage', 'explorer'),
                'strengths': kash_score.get('strengths', []),
                'improvement_areas': kash_score.get('improvement_areas', []),
                'recommendations': kash_score.get('recommendations', [])
            },
            
            # SHAP explanations
            feature_importance=[
                {
                    'feature_name': fi.get('feature_name', ''),
                    'feature_value': fi.get('feature_value', 0),
                    'shap_value': fi.get('shap_value', 0),
                    'contribution_percentage': fi.get('contribution_percentage', 0),
                    'direction': fi.get('direction', 'neutral'),
                    'explanation': fi.get('explanation', '')
                }
                for fi in result_data.get('feature_importance', [])
            ],
            
            career_explanations=[
                {
                    'career_path': ce.get('career', ''),
                    'match_score': ce.get('match_score', 0),
                    'key_factors': ce.get('key_factors', []),
                    'skill_gaps': ce.get('skill_gaps', []),
                    'alignment_reasons': ce.get('alignment_reasons', []),
                    'development_needs': ce.get('development_needs', [])
                }
                for ce in result_data.get('career_explanations', [])
            ],
            
            skill_gap_analysis=result_data.get('skill_gap_analysis', []),
            
            assessment_impacts=[
                {
                    'assessment_type': ai.get('assessment_type', ''),
                    'assessment_name': ai.get('assessment_name', ''),
                    'score_contribution': ai.get('score_contribution', 0),
                    'confidence_impact': ai.get('confidence_impact', 0),
                    'improvement_potential': ai.get('improvement_potential', 0)
                }
                for ai in result_data.get('assessment_impacts', [])
            ],
            
            recommendation_explanations={
                key: {
                    'recommendation': value.get('recommendation', ''),
                    'type': value.get('type', ''),
                    'explanation': value.get('explanation', ''),
                    'priority': value.get('priority', 'medium'),
                    'expected_impact': value.get('expected_impact', {})
                }
                for key, value in result_data.get('recommendation_explanations', {}).items()
            },
            
            # Input parameters
            industry=input_data.get('industry'),
            career_goals=input_data.get('career_goals'),
            custom_weights=input_data.get('custom_weights')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get intelligence assessment {assessment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve intelligence assessment"
        )


@router.delete("/assessments/{assessment_id}")
async def delete_intelligence_assessment(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an intelligence assessment.
    
    - **assessment_id**: UUID of the assessment to delete
    """
    try:
        assessment = db.query(UserAssessment).filter(
            UserAssessment.id == assessment_id,
            UserAssessment.user_id == current_user.id,
            UserAssessment.assessment_type == 'intelligence'
        ).first()
        
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Intelligence assessment not found"
            )
        
        # Delete assessment (cascade delete should handle related records)
        db.delete(assessment)
        db.commit()
        
        logger.info(f"Deleted intelligence assessment {assessment_id} for user {current_user.id}")
        return {"message": "Intelligence assessment deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete intelligence assessment {assessment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete intelligence assessment"
        )


@router.get("/profile", response_model=IntelligenceProfileResponse)
async def get_intelligence_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive intelligence profile for the current user.
    
    Aggregates data from all intelligence assessments with trends and insights.
    """
    try:
        intelligence_service = IntelligenceService(db)
        profile = await intelligence_service.get_user_intelligence_profile(
            user_id=str(current_user.id)
        )
        
        return IntelligenceProfileResponse(**profile)
        
    except Exception as e:
        logger.error(f"Failed to get intelligence profile for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve intelligence profile"
        )


@router.post("/career-path", response_model=CareerPathResponse)
async def explain_career_path(
    request: CareerPathRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed career path explanation.
    
    - **target_career**: Target career path
    
    Provides detailed analysis of career match, key factors, skill gaps,
    and development needs for the specified career path.
    """
    try:
        intelligence_service = IntelligenceService(db)
        career_explanation = await intelligence_service.explain_career_path(
            user_id=str(current_user.id),
            target_career=request.target_career
        )
        
        return CareerPathResponse(**career_explanation)
        
    except ValueError as e:
        logger.error(f"Career path explanation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Career path explanation failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Career path explanation failed"
        )


@router.post("/skill-gaps", response_model=SkillGapResponse)
async def analyze_skill_gaps(
    request: SkillGapRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze skill gaps for target role.
    
    - **target_role**: Target role name
    - **experience_level**: Required experience level
    
    Provides detailed skill gap analysis with development timelines
    and priority recommendations.
    """
    try:
        intelligence_service = IntelligenceService(db)
        skill_gap_analysis = await intelligence_service.analyze_skill_gaps(
            user_id=str(current_user.id),
            target_role=request.target_role,
            experience_level=request.experience_level.value
        )
        
        return SkillGapResponse(**skill_gap_analysis)
        
    except ValueError as e:
        logger.error(f"Skill gap analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Skill gap analysis failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Skill gap analysis failed"
        )


@router.get("/kash-scores")
async def get_kash_scores(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get KASH scores history and current status.
    
    Returns historical KASH scores with trends and current status.
    """
    try:
        intelligence_service = IntelligenceService(db)
        profile = await intelligence_service.get_user_intelligence_profile(
            user_id=str(current_user.id)
        )
        
        return {
            'current_scores': profile.get('current_kash_score', {}),
            'trend': profile.get('kash_trend', []),
            'career_stage': profile.get('career_stage'),
            'confidence': profile.get('confidence'),
            'last_updated': profile.get('last_assessment')
        }
        
    except Exception as e:
        logger.error(f"Failed to get KASH scores for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve KASH scores"
        )


@router.get("/feature-importance")
async def get_feature_importance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get feature importance analysis.
    
    Returns SHAP-based feature importance with explanations.
    """
    try:
        intelligence_service = IntelligenceService(db)
        profile = await intelligence_service.get_user_intelligence_profile(
            user_id=str(current_user.id)
        )
        
        feature_trends = profile.get('feature_importance_trends', {})
        
        return {
            'current_importance': feature_trends.get('current_importance', []),
            'top_features': feature_trends.get('top_features', []),
            'explanations': [
                {
                    'feature': feature['feature_name'],
                    'importance': feature['contribution_percentage'],
                    'explanation': feature['explanation'],
                    'direction': feature['direction']
                }
                for feature in feature_trends.get('current_importance', [])
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get feature importance for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve feature importance"
        )


@router.get("/recommendations")
async def get_intelligence_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get intelligence-based recommendations.
    
    Returns personalized recommendations with explanations and priorities.
    """
    try:
        intelligence_service = IntelligenceService(db)
        profile = await intelligence_service.get_user_intelligence_profile(
            user_id=str(current_user.id)
        )
        
        recommendation_history = profile.get('recommendation_history', [])
        current_recommendations = recommendation_history[0]['recommendations'] if recommendation_history else []
        
        return {
            'current_recommendations': current_recommendations,
            'recommendation_history': recommendation_history,
            'total_recommendations': len(current_recommendations),
            'based_on': {
                'career_stage': profile.get('career_stage'),
                'kash_scores': profile.get('current_kash_score', {}),
                'skill_gaps': profile.get('skill_development_progress', {})
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get intelligence recommendations for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve intelligence recommendations"
        )


@router.get("/career-insights")
async def get_career_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get career insights and analysis.
    
    Returns career stage analysis, strengths, improvement areas,
    and career path recommendations.
    """
    try:
        intelligence_service = IntelligenceService(db)
        profile = await intelligence_service.get_user_intelligence_profile(
            user_id=str(current_user.id)
        )
        
        career_insights = profile.get('career_insights', {})
        
        return {
            'career_stage': career_insights.get('career_stage', 'unknown'),
            'strengths': career_insights.get('strengths', []),
            'improvement_areas': career_insights.get('improvement_areas', []),
            'career_explanations': career_insights.get('career_explanations', []),
            'skill_development_progress': profile.get('skill_development_progress', {}),
            'recommendations': career_insights.get('strengths', [])  # Use strengths as recommendations
        }
        
    except Exception as e:
        logger.error(f"Failed to get career insights for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve career insights"
        )
