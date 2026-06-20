"""Skills module API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid
import json
from pathlib import Path

from pydantic import BaseModel, Field

from src.core.database import get_db
from src.core.auth import get_current_user
from src.core.config import DATA_DIR
from src.core.logging import get_logger
from src.models.user import User
from src.models.assessment import UserAssessment, SkillsAssessment
from src.modules.skills.skills_service import SkillsService
from src.modules.skills.coding_challenges import get_coding_challenges, run_coding_challenge
from src.schemas.skills import (
    GitHubAnalysisRequest,
    GitHubLinkRequest,
    GitHubLinkResponse,
    GitHubSyncRequest,
    GitHubSyncResultResponse,
    GitHubSyncLogEntryResponse,
    CodeUploadRequest,
    SkillsAssessmentSummary,
    SkillsAssessmentResults,
    SkillsProfileResponse,
    GitHubRepositoryResponse,
    RecentActivity,
    ErrorResponse,
)
from src.schemas.educational_feedback import (
    EducationalAnalysisRequest,
    LearningPathRequest,
    SkillAssessmentRequest,
)
from src.schemas.reviewer_overrides import (
    ReviewerOverrideRequest,
    ReviewerOverrideResponse,
    OverrideHistoryResponse,
    ReviewerDashboardRequest,
    ReviewerDashboardResponse,
    OverrideTemplateRequest,
    OverrideTemplate,
    OverrideValidationRequest,
    OverrideValidationResponse,
)

router = APIRouter(prefix="/skills", tags=["skills"])
logger = get_logger(__name__)


class CodingChallengeSummary(BaseModel):
    id: str
    title: str
    statement: str
    input_format: str
    output_format: str
    constraints: str
    sample_input: str
    sample_output: str
    supported_languages: List[str]
    templates: Dict[str, str]


class CodingChallengeSubmissionRequest(BaseModel):
    challenge_id: str = Field(..., min_length=1)
    language: str = Field(..., min_length=1)
    code: str = Field(..., min_length=1)


class CodingChallengeSubmissionResponse(BaseModel):
    assessment_id: str
    ok: bool
    score: float
    passed: int
    total: int
    compile_output: str
    error: Optional[str] = None
    tests: List[Dict[str, Any]]


@router.post("/analyze-github", response_model=SkillsAssessmentResults)
async def analyze_github_repository(
    request: GitHubAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze GitHub repository for technical skills assessment.
    
    - **owner**: Repository owner username
    - **repo**: Repository name
    - **github_token**: Optional GitHub access token for private repos
    
    Performs comprehensive code analysis and technical skills extraction.
    """
    try:
        skills_service = SkillsService(db)
        assessment = await skills_service.analyze_github_repository(
            user_id=str(current_user.id),
            owner=request.owner,
            repo=request.repo,
            github_token=request.github_token
        )
        
        # Convert to response format
        result_data = assessment.result_data or {}
        repository_analysis = result_data.get('repository_analysis', {})
        code_analysis = result_data.get('code_analysis', {})
        skills_assessment = result_data.get('skills_assessment', {})
        skills_scores = result_data.get('skills_scores', {})
        
        return SkillsAssessmentResults(
            assessment_id=str(assessment.id),
            source_type='github',
            source_url=repository_analysis.get('repository', {}).get('source_url'),
            project_name=repository_analysis.get('repository', {}).get('name', f"{request.owner}/{request.repo}"),
            status=assessment.status,
            created_at=assessment.created_at,
            completed_at=assessment.completed_at,
            
            # Repository info
            repository_info={
                'name': repository_analysis.get('repository', {}).get('full_name', ''),
                'description': repository_analysis.get('repository', {}).get('description'),
                'language': repository_analysis.get('repository', {}).get('language'),
                'languages': repository_analysis.get('repository', {}).get('languages', {}),
                'stars': repository_analysis.get('repository', {}).get('stars', 0),
                'forks': repository_analysis.get('repository', {}).get('forks', 0),
                'open_issues': repository_analysis.get('repository', {}).get('open_issues', 0),
                'created_at': repository_analysis.get('repository', {}).get('created_at', ''),
                'updated_at': repository_analysis.get('repository', {}).get('updated_at', ''),
                'size_kb': repository_analysis.get('repository', {}).get('size_kb', 0),
                'topics': repository_analysis.get('repository', {}).get('topics', []),
                'is_private': repository_analysis.get('repository', {}).get('is_private', False),
                'default_branch': repository_analysis.get('repository', {}).get('default_branch', 'main')
            },
            
            # Code analysis
            code_summary=code_analysis.get('summary', {}),
            technical_skills=code_analysis.get('technical_skills', []),
            patterns=code_analysis.get('patterns', []),
            quality_metrics=code_analysis.get('file_analyses', [{}])[0].get('quality_metrics', []) if code_analysis.get('file_analyses') else [],
            
            # Scores
            skills_scores=skills_scores,
            overall_scores=code_analysis.get('overall_scores', {}),
            
            # Additional details
            collaboration_indicators=repository_analysis.get('collaboration', {}),
            learning_trajectory=repository_analysis.get('learning_trajectory', [])
        )
        
    except ValueError as e:
        logger.error(f"GitHub analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"GitHub analysis failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GitHub repository analysis failed"
        )


@router.get("/coding-challenges", response_model=List[CodingChallengeSummary])
async def list_coding_challenges(
    current_user: User = Depends(get_current_user),
):
    challenges = get_coding_challenges()
    return [
        CodingChallengeSummary(
            id=c.id,
            title=c.title,
            statement=c.statement,
            input_format=c.input_format,
            output_format=c.output_format,
            constraints=c.constraints,
            sample_input=c.sample_input,
            sample_output=c.sample_output,
            supported_languages=c.supported_languages,
            templates=c.templates,
        )
        for c in challenges
    ]


@router.post("/coding-challenges/submit", response_model=CodingChallengeSubmissionResponse)
async def submit_coding_challenge(
    payload: CodingChallengeSubmissionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        result = run_coding_challenge(
            challenge_id=payload.challenge_id,
            language=payload.language,
            code=payload.code,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Coding challenge failed for user {current_user.id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Coding challenge failed")

    score = float(result.get("score") or 0)
    passed = int(result.get("passed") or 0)
    total = int(result.get("total") or 0)
    ok = bool(result.get("ok"))
    compile_output = str(result.get("compile_output") or "")
    error = result.get("error")
    tests = result.get("tests") or []

    assessment = UserAssessment(
        id=uuid.uuid4(),
        user_id=str(current_user.id),
        assessment_type='skills',
        assessment_name=f"Coding Challenge - {payload.challenge_id}",
        assessment_version='1.0',
        status='completed',
        raw_score=score,
        normalized_score=score,
        confidence_score=min(1.0, 0.5 + (score / 200.0)),
        input_data={
            'source_type': 'coding_game',
            'challenge_id': payload.challenge_id,
            'language': payload.language,
        },
        result_data={
            'coding_game': {
                'ok': ok,
                'passed': passed,
                'total': total,
                'score': score,
                'compile_output': compile_output,
                'error': error,
                'tests': tests,
            },
            'skills_scores': {
                'raw_score': score,
                'normalized_score': score,
                'confidence_score': min(1.0, 0.5 + (score / 200.0)),
                'component_scores': {
                    'correctness': score,
                },
            },
        },
    )

    db.add(assessment)
    db.flush()

    skills_assessment = SkillsAssessment(
        id=uuid.uuid4(),
        assessment_id=assessment.id,
        source_type='text',
        source_url=None,
        source_metadata={
            'source_type': 'coding_game',
            'challenge_id': payload.challenge_id,
            'language': payload.language,
            'passed': passed,
            'total': total,
        },
        programming_languages={payload.language: 1.0},
        code_quality_metrics=None,
        technical_skills=['problem_solving', 'algorithms'],
        project_complexity=None,
        collaboration_indicators={},
        learning_trajectory=[],
        analyzer_version='1.0',
        analysis_date=None,
    )

    db.add(skills_assessment)
    db.commit()

    return CodingChallengeSubmissionResponse(
        assessment_id=str(assessment.id),
        ok=ok,
        score=score,
        passed=passed,
        total=total,
        compile_output=compile_output,
        error=error,
        tests=tests,
    )


@router.post("/github/links", response_model=GitHubLinkResponse)
async def register_github_link(
    request: GitHubLinkRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Register or update the learner's GitHub repository link."""

    try:
        skills_service = SkillsService(db)
        link = skills_service.register_github_link(
            learner_id=str(current_user.id),
            repository_full_name=request.repository_full_name,
            project_id=request.project_id,
            github_handle=request.github_handle,
            metadata=request.metadata,
        )
        return link
    except Exception as e:
        logger.error(f"Failed to register GitHub link for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register GitHub link",
        )


@router.get("/github/links", response_model=List[GitHubLinkResponse])
async def list_github_links(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List learner GitHub links used for submission syncing."""

    try:
        skills_service = SkillsService(db)
        return skills_service.get_github_links(str(current_user.id))
    except Exception as e:
        logger.error(f"Failed to list GitHub links for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve GitHub links",
        )


@router.post("/github/sync", response_model=GitHubSyncResultResponse)
async def sync_github_submission(
    request: GitHubSyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Trigger a GitHub sync for a learner submission and record audit logs."""

    try:
        skills_service = SkillsService(db)
        result = await skills_service.sync_github_submission(
            learner_id=str(current_user.id),
            submission_id=request.submission_id,
            template_id=request.template_id,
            project_id=request.project_id,
            metadata=request.metadata,
        )
        return result
    except Exception as e:
        logger.error(f"Failed to sync GitHub submission for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GitHub sync failed",
        )


@router.get("/github/sync/{submission_id}", response_model=GitHubSyncLogEntryResponse)
async def get_latest_github_sync(
    submission_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch the latest GitHub sync log for a submission."""

    try:
        skills_service = SkillsService(db)
        entry = skills_service.get_latest_github_sync(submission_id)
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sync log not found",
            )
        return entry
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve GitHub sync for submission {submission_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve GitHub sync log",
        )


@router.get("/github/sync-history", response_model=List[GitHubSyncLogEntryResponse])
async def list_github_sync_history(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List recent GitHub sync logs for the learner."""

    try:
        skills_service = SkillsService(db)
        return skills_service.list_github_sync_history(str(current_user.id), max(limit, 0))
    except Exception as e:
        logger.error(f"Failed to list GitHub sync history for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve GitHub sync history",
        )


@router.post("/analyze-upload", response_model=SkillsAssessmentResults)
async def analyze_code_upload(
    project_name: str = Form(...),
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze uploaded code files for technical skills assessment.
    
    - **project_name**: Name for the project
    - **files**: Code files to analyze (max 50 files)
    
    Performs comprehensive code analysis and technical skills extraction.
    """
    try:
        # Read and validate files
        code_files = []
        for file in files:
            if file.size > 1024 * 1024:  # 1MB limit per file
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File {file.filename} is too large (max 1MB)"
                )
            
            content = await file.read()
            try:
                content_str = content.decode('utf-8')
            except UnicodeDecodeError:
                content_str = content.decode('utf-8', errors='ignore')
            
            code_files.append({
                'path': file.filename or 'unknown',
                'content': content_str
            })
        
        if len(code_files) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid files provided"
            )
        
        # Analyze code
        skills_service = SkillsService(db)
        assessment = await skills_service.analyze_code_upload(
            user_id=str(current_user.id),
            files=code_files,
            project_name=project_name
        )
        
        # Convert to response format
        result_data = assessment.result_data or {}
        code_analysis = result_data.get('code_analysis', {})
        skills_assessment = result_data.get('skills_assessment', {})
        skills_scores = result_data.get('skills_scores', {})
        
        return SkillsAssessmentResults(
            assessment_id=str(assessment.id),
            source_type='upload',
            source_url=None,
            project_name=project_name,
            status=assessment.status,
            created_at=assessment.created_at,
            completed_at=assessment.completed_at,
            
            # Repository info (not applicable for uploads)
            repository_info=None,
            
            # Code analysis
            code_summary=code_analysis.get('summary', {}),
            technical_skills=code_analysis.get('technical_skills', []),
            patterns=code_analysis.get('patterns', []),
            quality_metrics=code_analysis.get('file_analyses', [{}])[0].get('quality_metrics', []) if code_analysis.get('file_analyses') else [],
            
            # Scores
            skills_scores=skills_scores,
            overall_scores=code_analysis.get('overall_scores', {}),
            
            # Additional details
            collaboration_indicators={},
            learning_trajectory=[]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Code upload analysis failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Code upload analysis failed"
        )


@router.get("/assessments", response_model=List[SkillsAssessmentSummary])
async def get_skills_assessments(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all skills assessments for the current user.
    
    - **limit**: Maximum number of assessments to return (default: 10)
    """
    try:
        skills_service = SkillsService(db)
        assessments = await skills_service.get_user_skills_assessments(
            user_id=str(current_user.id),
            limit=limit
        )
        
        summaries = []
        for assessment in assessments:
            input_data = assessment.input_data or {}
            result_data = assessment.result_data or {}
            skills_assessment = result_data.get('skills_assessment', {})
            
            summaries.append(SkillsAssessmentSummary(
                assessment_id=str(assessment.id),
                assessment_name=assessment.assessment_name,
                status=assessment.status,
                source_type=input_data.get('source_type', 'unknown'),
                source_url=skills_assessment.get('source_url'),
                normalized_score=assessment.normalized_score,
                confidence_score=assessment.confidence_score,
                created_at=assessment.created_at,
                completed_at=assessment.completed_at,
                project_name=input_data.get('project_name', 'Unknown'),
                languages_detected=list(skills_assessment.get('programming_languages', {}).keys()),
                technical_skills_count=len(skills_assessment.get('technical_skills', [])),
                project_complexity=skills_assessment.get('project_complexity')
            ))
        
        return summaries
        
    except Exception as e:
        logger.error(f"Failed to get skills assessments for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve skills assessments"
        )


@router.get("/assessments/{assessment_id}", response_model=SkillsAssessmentResults)
async def get_skills_assessment(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed results for a skills assessment.
    
    - **assessment_id**: UUID of the assessment
    """
    try:
        skills_service = SkillsService(db)
        assessment = await skills_service.get_skills_assessment(
            assessment_id=assessment_id,
            user_id=str(current_user.id)
        )
        
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Skills assessment not found"
            )
        
        # Convert to response format
        result_data = assessment.result_data or {}
        repository_analysis = result_data.get('repository_analysis', {})
        code_analysis = result_data.get('code_analysis', {})
        skills_assessment = result_data.get('skills_assessment', {})
        skills_scores = result_data.get('skills_scores', {})
        
        return SkillsAssessmentResults(
            assessment_id=str(assessment.id),
            source_type=assessment.input_data.get('source_type', 'unknown'),
            source_url=skills_assessment.get('source_url'),
            project_name=assessment.input_data.get('project_name', 'Unknown'),
            status=assessment.status,
            created_at=assessment.created_at,
            completed_at=assessment.completed_at,
            
            repository_info={
                'name': repository_analysis.get('repository', {}).get('full_name', ''),
                'description': repository_analysis.get('repository', {}).get('description'),
                'language': repository_analysis.get('repository', {}).get('language'),
                'languages': repository_analysis.get('repository', {}).get('languages', {}),
                'stars': repository_analysis.get('repository', {}).get('stars', 0),
                'forks': repository_analysis.get('repository', {}).get('forks', 0),
                'open_issues': repository_analysis.get('repository', {}).get('open_issues', 0),
                'created_at': repository_analysis.get('repository', {}).get('created_at', ''),
                'updated_at': repository_analysis.get('repository', {}).get('updated_at', ''),
                'size_kb': repository_analysis.get('repository', {}).get('size_kb', 0),
                'topics': repository_analysis.get('repository', {}).get('topics', []),
                'is_private': repository_analysis.get('repository', {}).get('is_private', False),
                'default_branch': repository_analysis.get('repository', {}).get('default_branch', 'main')
            } if repository_analysis else None,
            
            code_summary=code_analysis.get('summary', {}),
            technical_skills=code_analysis.get('technical_skills', []),
            patterns=code_analysis.get('patterns', []),
            quality_metrics=code_analysis.get('file_analyses', [{}])[0].get('quality_metrics', []) if code_analysis.get('file_analyses') else [],
            
            skills_scores=skills_scores,
            overall_scores=code_analysis.get('overall_scores', {}),
            
            collaboration_indicators=repository_analysis.get('collaboration', {}),
            learning_trajectory=repository_analysis.get('learning_trajectory', [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get skills assessment {assessment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve skills assessment"
        )


@router.delete("/assessments/{assessment_id}")
async def delete_skills_assessment(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a skills assessment.
    
    - **assessment_id**: UUID of the assessment to delete
    """
    try:
        assessment = db.query(UserAssessment).filter(
            UserAssessment.id == assessment_id,
            UserAssessment.user_id == current_user.id,
            UserAssessment.assessment_type == 'skills'
        ).first()
        
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Skills assessment not found"
            )
        
        # Delete assessment (cascade delete should handle related records)
        db.delete(assessment)
        db.commit()
        
        logger.info(f"Deleted skills assessment {assessment_id} for user {current_user.id}")
        return {"message": "Skills assessment deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete skills assessment {assessment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete skills assessment"
        )


@router.get("/profile", response_model=SkillsProfileResponse)
async def get_skills_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive skills profile for the current user.
    
    Aggregates data from all skills assessments.
    """
    try:
        skills_service = SkillsService(db)
        profile = await skills_service.get_user_skills_profile(
            user_id=str(current_user.id)
        )
        
        return SkillsProfileResponse(**profile)
        
    except Exception as e:
        logger.error(f"Failed to get skills profile for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve skills profile"
        )


@router.get("/github/{owner}/{repo}", response_model=GitHubRepositoryResponse)
async def get_github_repository_info(
    owner: str,
    repo: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get basic GitHub repository information.
    
    - **owner**: Repository owner username
    - **repo**: Repository name
    
    Returns repository metadata without full analysis.
    """
    try:
        skills_service = SkillsService(db)
        repo_info = await skills_service.get_github_repository_info(owner, repo)
        
        if not repo_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="GitHub repository not found or inaccessible"
            )
        
        return GitHubRepositoryResponse(**repo_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get GitHub repository info {owner}/{repo}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve GitHub repository information"
        )


@router.get("/languages")
async def get_programming_languages(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get programming languages distribution across all user assessments.
    
    Returns aggregated language statistics.
    """
    try:
        skills_service = SkillsService(db)
        profile = await skills_service.get_user_skills_profile(
            user_id=str(current_user.id)
        )
        
        return {
            'languages': profile.get('programming_languages', {}),
            'total_languages': len(profile.get('programming_languages', {})),
            'most_used_language': max(profile.get('programming_languages', {}).items(), key=lambda x: x[1])[0] if profile.get('programming_languages') else None
        }
        
    except Exception as e:
        logger.error(f"Failed to get programming languages for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve programming languages"
        )


@router.get("/technical-skills")
async def get_technical_skills_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get technical skills summary across all assessments.
    
    Returns aggregated technical skills with confidence levels.
    """
    try:
        skills_service = SkillsService(db)
        profile = await skills_service.get_user_skills_profile(
            user_id=str(current_user.id)
        )
        
        technical_skills = profile.get('technical_skills', {})
        
        return {
            'skills_by_category': technical_skills.get('skills_by_category', {}),
            'proficiency_distribution': technical_skills.get('proficiency_distribution', {}),
            'total_unique_skills': technical_skills.get('total_unique_skills', 0),
            'top_skills': technical_skills.get('top_skills', [])[:10],
            'skill_categories': list(technical_skills.get('skills_by_category', {}).keys())
        }
        
    except Exception as e:
        logger.error(f"Failed to get technical skills for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve technical skills"
        )


@router.get("/recommendations")
async def get_skills_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized skills development recommendations.
    
    Returns recommendations based on current skills and performance.
    """
    try:
        skills_service = SkillsService(db)
        profile = await skills_service.get_user_skills_profile(
            user_id=str(current_user.id)
        )
        
        return {
            'recommendations': profile.get('recommendations', []),
            'total_recommendations': len(profile.get('recommendations', [])),
            'based_on': {
                'total_assessments': profile.get('total_assessments', 0),
                'average_score': profile.get('overall_performance', {}).get('average_score', 0),
                'skill_diversity': profile.get('overall_performance', {}).get('skill_diversity', 0)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get skills recommendations for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve skills recommendations"
        )


@router.get("/activity")
async def get_recent_activity(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get recent skills assessment activity.
    
    - **limit**: Maximum number of activities to return (default: 10)
    """
    try:
        skills_service = SkillsService(db)
        profile = await skills_service.get_user_skills_profile(
            user_id=str(current_user.id)
        )
        
        recent_activity = profile.get('recent_activity', [])
        
        return {
            'activities': recent_activity[:limit],
            'total_activities': len(recent_activity),
            'last_activity': recent_activity[0]['completed_at'] if recent_activity else None
        }
        
    except Exception as e:
        logger.error(f"Failed to get recent activity for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recent activity"
        )


@router.get("/submissions/{submission_id}/analysis")
async def get_submission_analysis(
    submission_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get code analysis results for a specific submission.
    
    - **submission_id**: The UUID of the submission to get analysis for
    
    Returns detailed analysis results including scores, findings, and overrides.
    """
    try:
        # Phase 3: Expose analysis API endpoint using SkillsService
        skills_service = SkillsService(db)
        analysis_data = await skills_service.get_analysis_artifacts(submission_id)
        
        if not analysis_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No analysis found for submission {submission_id}"
            )
        
        # Verify user has access to this submission
        if analysis_data.get("learner_id") != str(current_user.id):
            # Check if user is an instructor or admin with access rights
            # For now, we'll deny access - implement role-based access as needed
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this submission"
            )
        
        return {
            "submission_id": analysis_data["submission_id"],
            "analysis_profile": analysis_data["analysis_profile"],
            "analyzed_at": analysis_data["analyzed_at"],
            "commit_sha": analysis_data["commit_sha"],
            "repository": analysis_data["repository"],
            "scores": {
                "automated_score": analysis_data["automated_score"],
                "adjusted_score": analysis_data["adjusted_score"],
                "grade": analysis_data["grade"],
                "confidence": analysis_data["confidence"],
            },
            "severity_summary": analysis_data["severity_buckets"],
            "findings": analysis_data["findings"],
            "overrides": analysis_data["overrides"],
            "summary": analysis_data["summary"],
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analysis for submission {submission_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve analysis: {str(e)}"
        )


# Educational Feedback and Scoring Endpoints

@router.post("/submissions/{submission_id}/educational-analysis", response_model=Dict[str, Any])
async def run_educational_analysis(
    submission_id: str,
    request: EducationalAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Run educational analysis with quality metrics and feedback on a submission.
    
    - **submission_id**: The UUID of the submission to analyze
    - **request**: Educational analysis configuration
    
    Returns comprehensive educational feedback including quality scores,
    learning recommendations, and personalized feedback.
    """
    try:
        skills_service = SkillsService(db)
        
        # Get existing submission data
        submission_data = await skills_service.get_submission_data(submission_id)
        if not submission_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Submission {submission_id} not found"
            )
        
        # Verify user access
        if submission_data.get("learner_id") != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this submission"
            )
        
        # Run educational analysis
        from src.modules.skills.code_analysis import CodeAnalysisEngine
        from src.modules.skills.code_analysis.context import RepositoryInput
        
        engine = CodeAnalysisEngine()
        
        # Create repository input from submission data
        repo_input = RepositoryInput(
            submission_id=submission_id,
            learner_id=str(current_user.id),
            template_id=submission_data.get("template_id", ""),
            root_path=Path(submission_data.get("repository_path", "")),
            files=[Path(f) for f in submission_data.get("files", [])],
            analysis_profile=request.analysis_profile,
        )
        
        # Run analysis
        result = await engine.analyze(repo_input)
        
        # Prepare response
        response = {
            "submission_id": result.submission_id,
            "learner_id": result.learner_id,
            "analysis_profile": result.analysis_profile,
            "overall_score": result.overall_score,
            "confidence": result.confidence,
            "summary": result.summary,
            "analyzed_at": result.analyzed_at.isoformat(),
            "analyzer_reports": [
                {
                    "analyzer_name": report.analyzer_name,
                    "analyzer_version": report.analyzer_version,
                    "execution_time_ms": report.execution_time_ms,
                    "findings_count": len(report.findings),
                    "findings": [
                        {
                            "rule_id": finding.rule_id,
                            "message": finding.message,
                            "file_path": str(finding.file_path),
                            "line_number": finding.line_number,
                            "severity": finding.severity.value,
                            "category": finding.category,
                            "score_impact": finding.score_impact,
                            "metadata": finding.metadata,
                        }
                        for finding in report.findings
                    ]
                }
                for report in result.analyzer_reports
            ]
        }
        
        # Add quality score if available
        if hasattr(result, 'quality_score') and result.quality_score:
            qs = result.quality_score
            response["quality_score"] = {
                "overall_score": qs.overall_score,
                "confidence": qs.confidence,
                "grade": qs.grade,
                "strengths": qs.strengths,
                "weaknesses": qs.weaknesses,
                "recommendations": qs.recommendations,
                "metrics": [
                    {
                        "name": metric.name,
                        "category": metric.category.value,
                        "score": metric.score,
                        "weight": metric.weight,
                        "description": metric.description,
                        "findings_count": metric.findings_count,
                        "severity_distribution": metric.severity_distribution,
                        "details": metric.details,
                    }
                    for metric in qs.metrics
                ]
            }
        
        # Add educational feedback if available
        if hasattr(result, 'educational_feedback') and result.educational_feedback:
            ef = result.educational_feedback
            response["educational_feedback"] = {
                "overall_summary": ef.overall_summary,
                "grade": ef.grade,
                "strengths": ef.strengths,
                "improvement_areas": ef.improvement_areas,
                "learning_path": ef.learning_path.value,
                "motivational_message": ef.motivational_message,
                "feedback_items": [
                    {
                        "type": item.type.value,
                        "title": item.title,
                        "message": item.message,
                        "priority": item.priority,
                        "actionable": item.actionable,
                        "estimated_effort": item.estimated_effort,
                        "related_findings": item.related_findings,
                        "learning_resources": item.learning_resources,
                        "next_steps": item.next_steps,
                    }
                    for item in ef.feedback_items
                ],
                "recommendations": [
                    {
                        "skill_area": rec.skill_area,
                        "current_level": rec.current_level,
                        "target_level": rec.target_level,
                        "description": rec.description,
                        "resources": [
                            {"title": r["title"], "url": r["url"]} 
                            for r in rec.resources
                        ],
                        "practice_exercises": rec.practice_exercises,
                        "estimated_time": rec.estimated_time,
                        "prerequisites": rec.prerequisites,
                    }
                    for rec in ef.recommendations
                ],
                "progress_indicators": ef.progress_indicators,
            }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to run educational analysis for submission {submission_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run educational analysis: {str(e)}"
        )


@router.get("/submissions/{submission_id}/quality-score", response_model=Dict[str, Any])
async def get_quality_score(
    submission_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get quality score breakdown for a specific submission.
    
    - **submission_id**: The UUID of the submission
    
    Returns detailed quality metrics across different categories.
    """
    try:
        skills_service = SkillsService(db)
        
        # Check if educational analysis exists
        analysis_data = await skills_service.get_analysis_artifacts(submission_id)
        if not analysis_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No analysis found for submission {submission_id}"
            )
        
        # Verify user access
        if analysis_data.get("learner_id") != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this submission"
            )
        
        # Run educational analysis with quality metrics
        from src.modules.skills.code_analysis import CodeAnalysisEngine
        from src.modules.skills.code_analysis.context import RepositoryInput
        
        engine = CodeAnalysisEngine()
        
        # Create repository input
        repo_input = RepositoryInput(
            submission_id=submission_id,
            learner_id=str(current_user.id),
            template_id=analysis_data.get("template_id", ""),
            root_path=Path(analysis_data.get("repository_path", "")),
            files=[Path(f) for f in analysis_data.get("files", [])],
            analysis_profile="educational",
        )
        
        # Run analysis
        result = await engine.analyze(repo_input)
        
        if not hasattr(result, 'quality_score') or not result.quality_score:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quality score not available for this submission"
            )
        
        qs = result.quality_score
        
        return {
            "submission_id": submission_id,
            "overall_score": qs.overall_score,
            "confidence": qs.confidence,
            "grade": qs.grade,
            "strengths": qs.strengths,
            "weaknesses": qs.weaknesses,
            "recommendations": qs.recommendations,
            "metrics": [
                {
                    "name": metric.name,
                    "category": metric.category.value,
                    "score": metric.score,
                    "weight": metric.weight,
                    "description": metric.description,
                    "findings_count": metric.findings_count,
                    "severity_distribution": metric.severity_distribution,
                    "details": metric.details,
                }
                for metric in qs.metrics
            ],
            "calculated_at": result.analyzed_at.isoformat(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get quality score for submission {submission_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quality score: {str(e)}"
        )


@router.get("/submissions/{submission_id}/educational-feedback", response_model=Dict[str, Any])
async def get_educational_feedback(
    submission_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get educational feedback for a specific submission.
    
    - **submission_id**: The UUID of the submission
    
    Returns personalized learning feedback and recommendations.
    """
    try:
        skills_service = SkillsService(db)
        
        # Check if educational analysis exists
        analysis_data = await skills_service.get_analysis_artifacts(submission_id)
        if not analysis_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No analysis found for submission {submission_id}"
            )
        
        # Verify user access
        if analysis_data.get("learner_id") != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this submission"
            )
        
        # Run educational analysis with feedback
        from src.modules.skills.code_analysis import CodeAnalysisEngine
        from src.modules.skills.code_analysis.context import RepositoryInput
        
        engine = CodeAnalysisEngine()
        
        # Create repository input
        repo_input = RepositoryInput(
            submission_id=submission_id,
            learner_id=str(current_user.id),
            template_id=analysis_data.get("template_id", ""),
            root_path=Path(analysis_data.get("repository_path", "")),
            files=[Path(f) for f in analysis_data.get("files", [])],
            analysis_profile="educational",
        )
        
        # Run analysis
        result = await engine.analyze(repo_input)
        
        if not hasattr(result, 'educational_feedback') or not result.educational_feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Educational feedback not available for this submission"
            )
        
        ef = result.educational_feedback
        
        return {
            "submission_id": submission_id,
            "overall_summary": ef.overall_summary,
            "grade": ef.grade,
            "strengths": ef.strengths,
            "improvement_areas": ef.improvement_areas,
            "learning_path": ef.learning_path.value,
            "motivational_message": ef.motivational_message,
            "feedback_items": [
                {
                    "type": item.type.value,
                    "title": item.title,
                    "message": item.message,
                    "priority": item.priority,
                    "actionable": item.actionable,
                    "estimated_effort": item.estimated_effort,
                    "related_findings": item.related_findings,
                    "learning_resources": item.learning_resources,
                    "next_steps": item.next_steps,
                }
                for item in ef.feedback_items
            ],
            "recommendations": [
                {
                    "skill_area": rec.skill_area,
                    "current_level": rec.current_level,
                    "target_level": rec.target_level,
                    "description": rec.description,
                    "resources": [
                        {"title": r["title"], "url": r["url"]} 
                        for r in rec.resources
                    ],
                    "practice_exercises": rec.practice_exercises,
                    "estimated_time": rec.estimated_time,
                    "prerequisites": rec.prerequisites,
                }
                for rec in ef.recommendations
            ],
            "progress_indicators": ef.progress_indicators,
            "generated_at": result.analyzed_at.isoformat(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get educational feedback for submission {submission_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get educational feedback: {str(e)}"
        )


@router.post("/learning-path", response_model=Dict[str, Any])
async def generate_learning_path(
    request: LearningPathRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate personalized learning path based on current and target skills.
    
    - **request**: Learning path configuration
    
    Returns a structured learning path with resources and milestones.
    """
    try:
        from src.modules.skills.code_analysis.metrics.feedback_generator import EducationalFeedbackGenerator
        
        feedback_generator = EducationalFeedbackGenerator()
        
        # Create a mock quality score for learning path generation
        # In a real implementation, this would be based on actual assessment data
        mock_findings = []  # Would be populated from user's assessment history
        
        # Generate learning recommendations
        recommendations = []
        for skill, target_level in request.target_skills.items():
            current_level = request.current_skills.get(skill, "beginner")
            
            # Create learning recommendation
            recommendation = {
                "skill_area": skill,
                "current_level": current_level,
                "target_level": target_level,
                "description": f"Improve {skill} skills from {current_level} to {target_level} level",
                "resources": feedback_generator._get_metric_resources(
                    feedback_generator.MetricCategory.MAINTAINABILITY, 
                    skill  # Using skill as language hint
                ),
                "practice_exercises": [
                    f"Practice {skill} with small exercises",
                    f"Build a {skill} project",
                    f"Study {skill} best practices",
                ],
                "estimated_time": "2-4 weeks",
                "prerequisites": [f"Basic {skill} knowledge"],
            }
            recommendations.append(recommendation)
        
        # Create learning path steps
        steps = []
        step_number = 1
        
        for skill in request.target_skills.keys():
            step = {
                "step_number": step_number,
                "title": f"Master {skill.title()}",
                "description": f"Develop your {skill} skills from {request.current_skills.get(skill, 'beginner')} to {request.target_skills[skill]}",
                "skill_area": skill,
                "resources": [
                    {"title": f"{skill.title()} Documentation", "url": f"https://docs.{skill}.org"},
                    {"title": f"{skill.title()} Tutorial", "url": f"https://tutorial.{skill}.org"},
                ],
                "practice_exercises": [
                    f"Complete {skill} exercises",
                    f"Build a {skill} project",
                ],
                "estimated_time": "1-2 weeks",
                "prerequisites": [f"Basic programming knowledge"],
                "completion_criteria": f"Demonstrate {request.target_skills[skill]} level proficiency in {skill}",
            }
            steps.append(step)
            step_number += 1
        
        return {
            "path_id": str(uuid.uuid4()),
            "learner_id": str(current_user.id),
            "current_level": "intermediate",  # Would be calculated from assessments
            "target_level": "advanced",  # Would be calculated from targets
            "estimated_duration": f"{len(steps) * 2} weeks",
            "steps": steps,
            "progress_indicators": {
                "total_steps": len(steps),
                "current_step": 1,
                "completion_percentage": 0,
            },
            "milestones": [
                f"Complete {skill} fundamentals" for skill in request.target_skills.keys()
            ] + [
                f"Master {skill} advanced concepts" for skill in request.target_skills.keys()
            ],
            "recommendations": recommendations,
            "created_at": datetime.utcnow().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Failed to generate learning path: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate learning path: {str(e)}"
        )


@router.post("/skill-assessment", response_model=Dict[str, Any])
async def assess_skills(
    request: SkillAssessmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Assess skills from provided code samples.
    
    - **request**: Skill assessment configuration with code samples
    
    Returns detailed skill assessment with scores and recommendations.
    """
    try:
        from src.modules.skills.code_analysis import CodeAnalysisEngine
        from src.modules.skills.code_analysis.context import RepositoryInput
        import tempfile
        import os
        
        # Create temporary directory for code samples
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            file_paths = []
            
            # Write code samples to temporary files
            for i, sample in enumerate(request.code_samples):
                language = sample.get("language", "python")
                code = sample.get("code", "")
                filename = sample.get("filename", f"sample_{i}.{language}")
                
                file_path = temp_path / filename
                file_path.write_text(code)
                file_paths.append(file_path)
            
            # Run analysis
            engine = CodeAnalysisEngine()
            
            repo_input = RepositoryInput(
                submission_id=str(uuid.uuid4()),
                learner_id=str(current_user.id),
                template_id="skill_assessment",
                root_path=temp_path,
                files=file_paths,
                analysis_profile="educational",
            )
            
            result = await engine.analyze(repo_input)
            
            # Prepare assessment response
            response = {
                "assessment_id": str(uuid.uuid4()),
                "learner_id": str(current_user.id),
                "overall_score": result.overall_score,
                "confidence": result.confidence,
                "skill_breakdown": {},
                "strengths": [],
                "improvement_areas": [],
                "recommendations": [],
                "assessed_at": result.analyzed_at.isoformat(),
                "code_samples_analyzed": len(request.code_samples),
                "depth_level": request.depth_level,
            }
            
            # Add quality score details if available
            if hasattr(result, 'quality_score') and result.quality_score:
                qs = result.quality_score
                response["strengths"] = qs.strengths
                response["improvement_areas"] = qs.weaknesses
                response["recommendations"] = qs.recommendations
                
                # Create skill breakdown from metrics
                for metric in qs.metrics:
                    response["skill_breakdown"][metric.category.value] = metric.score
            
            # Add educational feedback if available
            if hasattr(result, 'educational_feedback') and result.educational_feedback:
                ef = result.educational_feedback
                response["learning_path"] = ef.learning_path.value
                response["motivational_message"] = ef.motivational_message
                response["next_steps"] = [
                    item.next_steps[0] if item.next_steps else "Continue practicing"
                    for item in ef.feedback_items[:3]
                ]
            
            return response
        
    except Exception as e:
        logger.error(f"Failed to assess skills: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assess skills: {str(e)}"
        )


# Reviewer Override Endpoints

@router.post("/submissions/{submission_id}/reviewer-override", response_model=Dict[str, Any])
async def create_reviewer_override(
    submission_id: str,
    request: ReviewerOverrideRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a reviewer override for analysis results.
    
    - **submission_id**: The UUID of the submission to override
    - **request**: Override details and reasoning
    
    Allows reviewers to manually adjust analysis results based on educational context,
    false positives, or other valid reasons.
    """
    try:
        # Get original analysis
        skills_service = SkillsService(db)
        analysis_data = await skills_service.get_analysis_artifacts(submission_id)
        if not analysis_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No analysis found for submission {submission_id}"
            )
        
        # Check user permissions (simplified - in real app, check reviewer role)
        if not current_user.is_instructor:  # Assuming User model has this attribute
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only instructors can create overrides"
            )
        
        # Create reviewer service and apply override
        from src.modules.skills.code_analysis.reviewer_service import ReviewerOverrideService
        from src.modules.skills.code_analysis import CodeAnalysisEngine
        
        reviewer_service = ReviewerOverrideService()
        
        # Reconstruct original analysis result
        # In a real implementation, this would be stored properly
        original_result = await _reconstruct_analysis_result(analysis_data)
        
        # Create override
        override_response = reviewer_service.create_override(request, original_result)
        
        return {
            "override_id": override_response.override_id,
            "submission_id": override_response.submission_id,
            "status": override_response.status.value,
            "changes_summary": override_response.changes_summary,
            "created_at": override_response.created_at.isoformat(),
            "message": "Reviewer override created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create reviewer override for submission {submission_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create reviewer override: {str(e)}"
        )


@router.get("/submissions/{submission_id}/override-history", response_model=Dict[str, Any])
async def get_override_history(
    submission_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get override history for a specific submission.
    
    - **submission_id**: The UUID of the submission
    
    Returns all manual overrides that have been applied to this submission.
    """
    try:
        # Check user permissions
        if not current_user.is_instructor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only instructors can view override history"
            )
        
        from src.modules.skills.code_analysis.reviewer_service import ReviewerOverrideService
        
        reviewer_service = ReviewerOverrideService()
        history = reviewer_service.get_override_history(submission_id)
        
        return {
            "submission_id": history.submission_id,
            "total_overrides": history.total_overrides,
            "overrides": [
                {
                    "override_id": override.override_id,
                    "reviewer_id": override.reviewer_id,
                    "changes_made": override.changes_made,
                    "reason": override.reason.value,
                    "comment": override.comment,
                    "created_at": override.created_at.isoformat(),
                    "status": override.status.value
                }
                for override in history.overrides
            ],
            "current_analysis": history.current_analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get override history for submission {submission_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get override history: {str(e)}"
        )


@router.get("/reviewer-dashboard", response_model=Dict[str, Any])
async def get_reviewer_dashboard(
    status_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get reviewer dashboard with pending submissions and statistics.
    
    Returns dashboard data for reviewers including pending submissions,
    recent overrides, and performance statistics.
    """
    try:
        # Check user permissions
        if not current_user.is_instructor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only instructors can access reviewer dashboard"
            )
        
        from src.modules.skills.code_analysis.reviewer_service import ReviewerOverrideService
        from src.schemas.reviewer_overrides import OverrideStatusEnum
        
        reviewer_service = ReviewerOverrideService()
        
        # Parse status filter
        status_filter_list = None
        if status_filter:
            try:
                status_filter_list = [OverrideStatusEnum(status_filter)]
            except ValueError:
                pass  # Invalid filter, ignore
        
        dashboard_request = ReviewerDashboardRequest(
            reviewer_id=str(current_user.id),
            status_filter=status_filter_list,
            limit=limit,
            offset=offset
        )
        
        dashboard = reviewer_service.get_reviewer_dashboard(dashboard_request)
        
        return {
            "reviewer_stats": {
                "reviewer_id": dashboard.reviewer_stats.reviewer_id,
                "reviewer_name": dashboard.reviewer_stats.reviewer_name,
                "total_reviews": dashboard.reviewer_stats.total_reviews,
                "pending_reviews": dashboard.reviewer_stats.pending_reviews,
                "approved_overrides": dashboard.reviewer_stats.approved_overrides,
                "rejected_overrides": dashboard.reviewer_stats.rejected_overrides,
                "average_score_adjustment": dashboard.reviewer_stats.average_score_adjustment,
                "most_common_reasons": dashboard.reviewer_stats.most_common_reasons
            } if dashboard.reviewer_stats else None,
            "pending_submissions": dashboard.pending_submissions,
            "recent_overrides": [
                {
                    "override_id": override.override_id,
                    "reviewer_id": override.reviewer_id,
                    "changes_made": override.changes_made,
                    "reason": override.reason.value,
                    "comment": override.comment,
                    "created_at": override.created_at.isoformat(),
                    "status": override.status.value
                }
                for override in dashboard.recent_overrides
            ],
            "summary_stats": dashboard.summary_stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get reviewer dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get reviewer dashboard: {str(e)}"
        )


@router.post("/override-templates", response_model=Dict[str, Any])
async def create_override_template(
    request: OverrideTemplateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new override template for common scenarios.
    
    - **request**: Template configuration
    
    Creates reusable templates for common override scenarios to improve
    reviewer efficiency and consistency.
    """
    try:
        # Check user permissions
        if not current_user.is_instructor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only instructors can create override templates"
            )
        
        from src.modules.skills.code_analysis.reviewer_service import ReviewerOverrideService
        
        reviewer_service = ReviewerOverrideService()
        template = reviewer_service.create_template(request, str(current_user.id))
        
        return {
            "template_id": template.template_id,
            "name": template.name,
            "description": template.description,
            "reason": template.reason.value,
            "created_at": template.created_at.isoformat(),
            "message": "Override template created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create override template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create override template: {str(e)}"
        )


@router.get("/override-templates", response_model=Dict[str, Any])
async def get_override_templates(
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get available override templates.
    
    - **reason**: Optional filter by override reason
    
    Returns all available override templates, optionally filtered by reason.
    """
    try:
        # Check user permissions
        if not current_user.is_instructor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only instructors can view override templates"
            )
        
        from src.modules.skills.code_analysis.reviewer_service import ReviewerOverrideService
        from src.schemas.reviewer_overrides import OverrideReasonEnum
        
        reviewer_service = ReviewerOverrideService()
        
        # Parse reason filter
        reason_filter = None
        if reason:
            try:
                reason_filter = OverrideReasonEnum(reason)
            except ValueError:
                pass  # Invalid filter, ignore
        
        templates = reviewer_service.get_templates(reason_filter)
        
        return {
            "templates": [
                {
                    "template_id": template.template_id,
                    "name": template.name,
                    "description": template.description,
                    "reason": template.reason.value,
                    "comment_template": template.comment_template,
                    "common_findings": template.common_findings,
                    "score_adjustment": template.score_adjustment,
                    "is_active": template.is_active,
                    "created_by": template.created_by,
                    "created_at": template.created_at.isoformat()
                }
                for template in templates
            ],
            "total_templates": len(templates)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get override templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get override templates: {str(e)}"
        )


@router.post("/validate-override", response_model=Dict[str, Any])
async def validate_override(
    request: OverrideValidationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Validate a proposed override before applying it.
    
    - **request**: Override validation request
    
    Validates proposed overrides for consistency, rules compliance,
    and provides recommendations before actual application.
    """
    try:
        # Check user permissions
        if not current_user.is_instructor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only instructors can validate overrides"
            )
        
        # Get original analysis
        skills_service = SkillsService(db)
        analysis_data = await skills_service.get_analysis_artifacts(request.submission_id)
        if not analysis_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No analysis found for submission {request.submission_id}"
            )
        
        from src.modules.skills.code_analysis.reviewer_service import ReviewerOverrideService
        
        reviewer_service = ReviewerOverrideService()
        
        # Reconstruct original analysis result
        original_result = await _reconstruct_analysis_result(analysis_data)
        
        # Validate override
        validation = reviewer_service.validate_override(request, original_result)
        
        return {
            "is_valid": validation.is_valid,
            "validation_errors": validation.validation_errors,
            "validation_warnings": validation.validation_warnings,
            "estimated_impact": validation.estimated_impact,
            "recommendations": validation.recommendations
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate override: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate override: {str(e)}"
        )


# Helper function to reconstruct analysis result
async def _reconstruct_analysis_result(analysis_data: Dict[str, Any]):
    """Helper function to reconstruct AnalysisResult from stored data."""
    # This is a simplified reconstruction - in a real implementation,
    # the AnalysisResult would be stored properly or reconstructed from database
    
    from src.modules.skills.code_analysis.models import AnalysisResult, AnalyzerReport, AnalyzerFinding
    from datetime import datetime
    
    # Create mock findings (in real implementation, these would be stored)
    mock_findings = []
    for i in range(5):  # Mock 5 findings
        finding = AnalyzerFinding(
            rule_id=f"RULE{i:03d}",
            message=f"Sample finding {i}",
            file_path=Path("sample.py"),
            line_number=i + 1,
            severity=SeverityLevel.MEDIUM,
            category="style",
            score_impact=-2.0,
            metadata={}
        )
        mock_findings.append(finding)
    
    # Create mock report
    mock_report = AnalyzerReport(
        analyzer_name="heuristics",
        analyzer_version="1.0.0",
        execution_time_ms=100,
        findings=mock_findings
    )
    
    # Create analysis result
    result = AnalysisResult(
        submission_id=analysis_data.get("submission_id", "unknown"),
        learner_id=analysis_data.get("learner_id", "unknown"),
        template_id=analysis_data.get("template_id", "unknown"),
        analysis_profile=analysis_data.get("analysis_profile", "educational"),
        overall_score=analysis_data.get("automated_score", 75.0),
        confidence=0.8,
        analyzer_reports=[mock_report],
        summary=analysis_data.get("summary", "Sample analysis"),
        analyzed_at=datetime.utcnow()
    )
    
    return result
