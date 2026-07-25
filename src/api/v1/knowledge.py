"""Knowledge module API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import os
import json
from pydantic import BaseModel

from src.core.database import get_db
from src.core.auth import get_current_user
from src.core.logging import get_logger
from src.models.user import User
from src.models.assessment import UserAssessment
from src.modules.knowledge.knowledge_service import KnowledgeService
from src.schemas.knowledge import (
    CVAnalysisRequest,
    CVAnalysisResponse,
    KnowledgeAssessmentSummary,
    KnowledgeProfileResponse,
    ESCOSearchRequest,
    ESCOSearchResponse,
    SkillMappingRequest,
    SkillMappingResponse,
    OccupationSuggestionRequest,
    OccupationSuggestionResponse,
    ErrorResponse
)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])
logger = get_logger(__name__)


@router.post("/analyze-cv", response_model=CVAnalysisResponse)
async def analyze_cv(
    request: CVAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze CV text and extract knowledge insights.
    
    - **cv_text**: Raw CV text content (minimum 100 characters)
    - **cv_filename**: Optional original filename for reference
    
    Performs NLP analysis, ESCO skill mapping, and occupation suggestions.
    """
    try:
        knowledge_service = KnowledgeService(db)
        assessment = await knowledge_service.analyze_cv(
            user_id=str(current_user.id),
            cv_text=request.cv_text,
            cv_filename=request.cv_filename or "uploaded_cv"
        )
        
        # Convert to response format
        result_data = assessment.result_data or {}
        parsed_cv = result_data.get('cv_analysis', result_data.get('parsed_cv', {}))
        taxonomy_summary = result_data.get('taxonomy_summary', {})
        knowledge_scores = result_data.get('knowledge_scores', {})
        
        return CVAnalysisResponse(
            assessment_id=str(assessment.id),
            status=assessment.status,
            created_at=assessment.created_at,
            completed_at=assessment.completed_at,
            
            # Parsed CV data
            contact_info=parsed_cv.get('contact_info', {}),
            experience=parsed_cv.get('experience', []),
            education=parsed_cv.get('education', []),
            skills=parsed_cv.get('skills', []),
            projects=parsed_cv.get('projects', []),
            certifications=parsed_cv.get('certifications', []),
            languages=parsed_cv.get('languages', []),
            
            # Analysis results
            skill_matches=[{
                'user_skill': s.get('name', ''),
                'esco_skill': {'label': s.get('esco_label', s.get('name', '')), 'uri': s.get('esco_uri', '')},
                'similarity_score': min(max(s.get('esco_confidence', 0.0), 0.0), 1.0),
                'match_type': 'exact' if s.get('esco_uri') else 'partial'
            } for s in taxonomy_summary.get('skills', [])],
            occupation_matches=[{
                'occupation': {'title': o.get('onet_title', o.get('title', '')), 'code': o.get('onet_code', '')},
                'match_score': min(max(o.get('confidence', 0.0), 0.0), 1.0),
                'required_skills': [],
                'missing_skills': [],
                'skill_coverage': 0.0
            } for o in taxonomy_summary.get('occupations', [])],
            knowledge_scores=knowledge_scores,
            
            # Metrics
            total_experience_years=parsed_cv.get('metrics', {}).get('total_experience_years', len(parsed_cv.get('experience', []))),
            skill_diversity=parsed_cv.get('metrics', {}).get('skill_diversity', len(parsed_cv.get('skills', []))),
            processing_time_ms=parsed_cv.get('metadata', {}).get('processing_time_ms', 0),
            confidence_score=assessment.confidence_score or 0
        )
        
    except Exception as e:
        logger.error(f"CV analysis failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CV analysis failed"
        )


@router.post("/upload-cv", response_model=CVAnalysisResponse)
async def upload_cv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload and analyze CV file.
    
    - **file**: CV file (PDF, DOCX, TXT)
    
    Automatically extracts text and performs analysis.
    """
    try:
        # Validate file type
        allowed_types = ['text/plain', 'application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file.content_type}. Allowed types: {allowed_types}"
            )
        
        # Read file content
        content = await file.read()
        
        # Extract text based on file type
        if file.content_type == 'text/plain':
            cv_text = content.decode('utf-8', errors='replace')
        elif file.content_type == 'application/pdf':
            try:
                import io
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(content))
                pages = [page.extract_text() or '' for page in reader.pages]
                cv_text = '\n'.join(pages)
            except Exception:
                cv_text = content.decode('utf-8', errors='ignore')
        else:
            # DOCX
            try:
                import io
                import docx as docx_lib
                doc = docx_lib.Document(io.BytesIO(content))
                cv_text = '\n'.join(p.text for p in doc.paragraphs)
            except Exception:
                cv_text = content.decode('utf-8', errors='ignore')
        
        # Strip non-printable characters and truncate to 50k chars
        import re
        cv_text = re.sub(r'[^\x20-\x7E\n\r\t\u00C0-\u024F]', ' ', cv_text)
        cv_text = re.sub(r' {3,}', ' ', cv_text).strip()
        cv_text = cv_text[:50000]
        
        if len(cv_text.strip()) < 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Extracted text is too short for analysis. Please upload a text-based CV (not a scanned image)."
            )
        
        # Analyze the extracted text
        knowledge_service = KnowledgeService(db)
        assessment = await knowledge_service.analyze_cv(
            user_id=str(current_user.id),
            cv_text=cv_text,
            cv_filename=file.filename
        )
        
        # Convert to response (same as analyze_cv endpoint)
        result_data = assessment.result_data or {}
        parsed_cv = result_data.get('cv_analysis', result_data.get('parsed_cv', {}))
        taxonomy_summary = result_data.get('taxonomy_summary', {})
        knowledge_scores = result_data.get('knowledge_scores', {})
        
        return CVAnalysisResponse(
            assessment_id=str(assessment.id),
            status=assessment.status,
            created_at=assessment.created_at,
            completed_at=assessment.completed_at,
            
            contact_info=parsed_cv.get('contact_info', {}),
            experience=parsed_cv.get('experience', []),
            education=parsed_cv.get('education', []),
            skills=parsed_cv.get('skills', []),
            projects=parsed_cv.get('projects', []),
            certifications=parsed_cv.get('certifications', []),
            languages=parsed_cv.get('languages', []),
            
            skill_matches=[{
                'user_skill': s.get('name', ''),
                'esco_skill': {'label': s.get('esco_label', s.get('name', '')), 'uri': s.get('esco_uri', '')},
                'similarity_score': min(max(s.get('esco_confidence', 0.0), 0.0), 1.0),
                'match_type': 'exact' if s.get('esco_uri') else 'partial'
            } for s in taxonomy_summary.get('skills', [])],
            occupation_matches=[{
                'occupation': {'title': o.get('onet_title', o.get('title', '')), 'code': o.get('onet_code', '')},
                'match_score': min(max(o.get('confidence', 0.0), 0.0), 1.0),
                'required_skills': [],
                'missing_skills': [],
                'skill_coverage': 0.0
            } for o in taxonomy_summary.get('occupations', [])],
            knowledge_scores=knowledge_scores,
            
            total_experience_years=parsed_cv.get('metrics', {}).get('total_experience_years', len(parsed_cv.get('experience', []))),
            skill_diversity=parsed_cv.get('metrics', {}).get('skill_diversity', len(parsed_cv.get('skills', []))),
            processing_time_ms=parsed_cv.get('metadata', {}).get('processing_time_ms', 0),
            confidence_score=assessment.confidence_score or 0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CV upload failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CV upload and analysis failed"
        )


@router.get("/assessments", response_model=List[KnowledgeAssessmentSummary])
async def get_knowledge_assessments(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all knowledge assessments for the current user.
    
    - **limit**: Maximum number of assessments to return (default: 10)
    """
    try:
        knowledge_service = KnowledgeService(db)
        assessments = await knowledge_service.get_user_knowledge_assessments(
            user_id=str(current_user.id),
            limit=limit
        )
        
        summaries = []
        for assessment in assessments:
            result_data = assessment.result_data or {}
            cv_analysis = result_data.get('cv_analysis', result_data.get('parsed_cv', {}))
            parsed_cv = cv_analysis.get('metadata', {})
            taxonomy_summary = result_data.get('taxonomy_summary', {})
            skill_matches = taxonomy_summary.get('skills', [])
            occupation_matches = taxonomy_summary.get('occupations', [])
            
            summaries.append(KnowledgeAssessmentSummary(
                assessment_id=str(assessment.id),
                assessment_name=assessment.assessment_name,
                status=assessment.status,
                normalized_score=assessment.normalized_score,
                confidence_score=assessment.confidence_score,
                created_at=assessment.created_at,
                completed_at=assessment.completed_at,
                total_skills_found=len(skill_matches),
                occupations_suggested=len(occupation_matches),
                experience_years=parsed_cv.get('total_experience_years', 0)
            ))
        
        return summaries
        
    except Exception as e:
        logger.error(f"Failed to get knowledge assessments for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve knowledge assessments"
        )


@router.get("/assessments/{assessment_id}", response_model=CVAnalysisResponse)
async def get_knowledge_assessment(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get specific knowledge assessment by ID.
    
    - **assessment_id**: UUID of the assessment
    """
    try:
        knowledge_service = KnowledgeService(db)
        assessment = await knowledge_service.get_knowledge_assessment(
            assessment_id=assessment_id,
            user_id=str(current_user.id)
        )
        
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge assessment not found"
            )
        
        # Convert to response format
        result_data = assessment.result_data or {}
        parsed_cv = result_data.get('parsed_cv', {})
        skill_matches = result_data.get('skill_matches', [])
        occupation_matches = result_data.get('occupation_matches', [])
        knowledge_scores = result_data.get('knowledge_scores', {})
        
        return CVAnalysisResponse(
            assessment_id=str(assessment.id),
            status=assessment.status,
            created_at=assessment.created_at,
            completed_at=assessment.completed_at,
            
            contact_info=parsed_cv.get('contact_info', {}),
            experience=parsed_cv.get('experience', []),
            education=parsed_cv.get('education', []),
            skills=parsed_cv.get('skills', []),
            projects=parsed_cv.get('projects', []),
            certifications=parsed_cv.get('certifications', []),
            languages=parsed_cv.get('languages', {}),
            
            skill_matches=[{
                'user_skill': match['user_skill'],
                'esco_skill': match['esco_skill'],
                'similarity_score': match['similarity_score'],
                'match_type': match['match_type']
            } for match in skill_matches],
            occupation_matches=[{
                'occupation': match['occupation'],
                'match_score': match['match_score'],
                'required_skills': match['required_skills'],
                'missing_skills': match['missing_skills'],
                'skill_coverage': match['skill_coverage']
            } for match in occupation_matches],
            knowledge_scores=knowledge_scores,
            
            total_experience_years=parsed_cv.get('metrics', {}).get('total_experience_years', 0),
            skill_diversity=parsed_cv.get('metrics', {}).get('skill_diversity', 0),
            processing_time_ms=parsed_cv.get('metrics', {}).get('processing_time_ms', 0),
            confidence_score=assessment.confidence_score or 0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get knowledge assessment {assessment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve knowledge assessment"
        )


@router.delete("/assessments/{assessment_id}")
async def delete_knowledge_assessment(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a knowledge assessment.
    
    - **assessment_id**: UUID of the assessment to delete
    """
    try:
        knowledge_service = KnowledgeService(db)
        success = await knowledge_service.delete_knowledge_assessment(
            assessment_id=assessment_id,
            user_id=str(current_user.id)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge assessment not found"
            )
        
        return {"message": "Knowledge assessment deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete knowledge assessment {assessment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete knowledge assessment"
        )


@router.get("/profile", response_model=KnowledgeProfileResponse)
async def get_knowledge_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get complete knowledge profile for the current user.
    
    Aggregates data from all knowledge assessments.
    """
    try:
        knowledge_service = KnowledgeService(db)
        assessments = await knowledge_service.get_user_knowledge_assessments(
            user_id=str(current_user.id),
            limit=50
        )
        
        if not assessments:
            return KnowledgeProfileResponse(
                user_id=str(current_user.id),
                total_assessments=0,
                latest_assessment=None,
                average_knowledge_score=None,
                skill_categories={},
                top_skills=[],
                career_suggestions=[],
                skill_gaps=[],
                learning_recommendations=[]
            )
        
        # Calculate aggregated metrics
        scores = [a.normalized_score for a in assessments if a.normalized_score is not None]
        average_score = sum(scores) / len(scores) if scores else None
        
        # Get latest assessment
        latest_assessment = assessments[0]
        result_data = latest_assessment.result_data or {}
        parsed_cv = result_data.get('cv_analysis', result_data.get('parsed_cv', {}))
        taxonomy_summary = result_data.get('taxonomy_summary', {})
        skill_matches = taxonomy_summary.get('skills', [])
        occupation_matches = taxonomy_summary.get('occupations', [])
        
        # Extract skill categories
        skill_categories = {}
        for skill in parsed_cv.get('skills', []):
            category = skill.get('category', 'other')
            skill_categories[category] = skill_categories.get(category, 0) + 1
        
        # Top skills
        top_skills = [skill['name'] for skill in parsed_cv.get('skills', [])[:10]]
        
        # Career suggestions
        career_suggestions = [
            match['occupation']['preferred_label'] 
            for match in occupation_matches[:5]
        ]
        
        # Skill gaps from latest assessment
        skill_gaps = []
        knowledge_assessment = result_data.get('knowledge_assessment', {})
        gaps_data = knowledge_assessment.get('skill_gaps', [])
        
        for gap in gaps_data:
            skill_gaps.append({
                'occupation': gap['occupation'],
                'missing_skills': gap['missing_skills'],
                'skill_coverage': gap['skill_coverage'],
                'priority': gap['priority']
            })
        
        # Learning recommendations (simplified)
        learning_recommendations = [
            f"Focus on developing {skill}" 
            for gap in skill_gaps[:3] 
            for skill in gap['missing_skills'][:2]
        ]
        
        return KnowledgeProfileResponse(
            user_id=str(current_user.id),
            total_assessments=len(assessments),
            latest_assessment=KnowledgeAssessmentSummary(
                assessment_id=str(latest_assessment.id),
                assessment_name=latest_assessment.assessment_name,
                status=latest_assessment.status,
                normalized_score=latest_assessment.normalized_score,
                confidence_score=latest_assessment.confidence_score,
                created_at=latest_assessment.created_at,
                completed_at=latest_assessment.completed_at,
                total_skills_found=len(skill_matches),
                occupations_suggested=len(occupation_matches),
                experience_years=parsed_cv.get('metrics', {}).get('total_experience_years', 0)
            ),
            average_knowledge_score=average_score,
            skill_categories=skill_categories,
            top_skills=top_skills,
            career_suggestions=career_suggestions,
            skill_gaps=skill_gaps,
            learning_recommendations=learning_recommendations
        )
        
    except Exception as e:
        logger.error(f"Failed to get knowledge profile for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve knowledge profile"
        )


@router.post("/search-esco", response_model=ESCOSearchResponse)
async def search_esco(
    request: ESCOSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search ESCO database for skills or occupations.
    
    - **query**: Search term
    - **type**: Search type (skill or occupation)
    - **limit**: Maximum results (default: 10)
    """
    try:
        from src.integration.esco_client import ESCOClient
        
        esco_client = ESCOClient()
        
        if request.type == 'skill':
            results = await esco_client.search_skills(request.query, request.limit)
            formatted_results = [
                {
                    'uri': skill.uri,
                    'preferred_label': skill.preferred_label,
                    'description': skill.description,
                    'skill_type': skill.skill_type,
                    'concept_uri': skill.concept_uri
                }
                for skill in results
            ]
        else:  # occupation
            results = await esco_client.search_occupations(request.query, request.limit)
            formatted_results = [
                {
                    'uri': occupation.uri,
                    'preferred_label': occupation.preferred_label,
                    'description': occupation.description,
                    'concept_uri': occupation.concept_uri,
                    'isco_code': occupation.isco_code
                }
                for occupation in results
            ]
        
        return ESCOSearchResponse(
            query=request.query,
            type=request.type,
            total_found=len(formatted_results),
            results=formatted_results
        )
        
    except Exception as e:
        logger.error(f"ESCO search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ESCO search failed"
        )


@router.post("/map-skills", response_model=SkillMappingResponse)
async def map_skills(
    request: SkillMappingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Map user skills to ESCO skills database.
    
    - **skills**: List of user skills to map
    """
    try:
        from src.integration.esco_client import ESCOClient
        
        esco_client = ESCOClient()
        matches = await esco_client.match_user_skills_to_esco(request.skills)
        
        formatted_matches = [
            {
                'user_skill': match.user_skill,
                'esco_skill': {
                    'uri': match.esco_skill.uri,
                    'preferred_label': match.esco_skill.preferred_label,
                    'description': match.esco_skill.description,
                    'skill_type': match.esco_skill.skill_type
                },
                'similarity_score': match.similarity_score,
                'match_type': match.match_type
            }
            for match in matches
        ]
        
        match_rate = len(formatted_matches) / len(request.skills) if request.skills else 0
        
        return SkillMappingResponse(
            user_skills=request.skills,
            matches=formatted_matches,
            total_matched=len(formatted_matches),
            match_rate=match_rate
        )
        
    except Exception as e:
        logger.error(f"Skill mapping failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Skill mapping failed"
        )


# =============================================================================
# KASH Knowledge ML Model endpoints
# Pipeline: Data Cleaning -> NLTK Tokenization -> Stemming -> TF-IDF -> KNN
# =============================================================================

def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Guard: only admin users can access ML model management endpoints."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required. This endpoint is restricted to administrators."
        )
    return current_user


@router.get("/model-status")
async def get_model_status(current_user: User = Depends(_require_admin)):
    """Check if the KASH Knowledge ML model is trained and ready. Admin only."""
    from src.modules.knowledge.ml.knowledge_model import get_knowledge_model
    model = get_knowledge_model()
    return {
        "is_trained": model.is_trained,
        "classes": model.classes_ if model.is_trained else [],
        "n_features": len(model.feature_names) if model.is_trained else 0,
        "training_report": model.training_report if model.is_trained else None,
    }


@router.post("/train-model")
async def train_model(current_user: User = Depends(_require_admin)):
    """
    Train the KASH Knowledge ML model on the ENSEM CV corpus. Admin only.

    Pipeline: Data Cleaning -> Tokenization -> Stemming -> TF-IDF -> Classifier comparison -> Save.
    The trained model is persisted to disk and automatically used by the platform.
    """
    from src.modules.knowledge.ml.knowledge_model import get_knowledge_model, RESULTS_PATH

    model = get_knowledge_model()

    cv_results = []
    if os.path.exists(RESULTS_PATH):
        with open(RESULTS_PATH, 'r', encoding='utf-8') as f:
            cv_results = json.load(f)

    if not cv_results:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No training data found at {RESULTS_PATH}. Upload CVs first via the test webapp."
        )

    report = model.train(cv_results)

    if 'error' in report:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=report['error']
        )

    return report


class PredictFiliereRequest(BaseModel):
    cv_text: str


@router.post("/predict-filiere")
async def predict_filiere(
    request: PredictFiliereRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Predict the filiere (field) of a CV using the trained KASH Knowledge model.

    Body: {"cv_text": "..."}
    Returns predicted filiere, probabilities, cluster, and TF-IDF/KNN similarity scores.
    """
    from src.modules.knowledge.ml.knowledge_model import get_knowledge_model
    model = get_knowledge_model()

    if not model.is_trained:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le modele KASH Knowledge n'est pas encore entraine. Utilisez /api/v1/knowledge/train-model d'abord."
        )

    cv_text = request.cv_text

    if len(cv_text.strip()) < 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Texte trop court (min 50 caracteres)"
        )

    result = model.predict(cv_text)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Prediction echouee"
        )

    return result


@router.post("/upload-training-cv")
async def upload_training_cv(
    file: UploadFile = File(...),
    filiere: str = Form(...),
    current_user: User = Depends(_require_admin),
):
    """
    Upload a new CV PDF to add to the training corpus. Admin only.

    The CV is saved to the CV_DATA_DIR and registered in test_knowledge_results.json
    with the specified filiere. After uploading, re-train the model to include the new CV.
    """
    from src.modules.knowledge.ml.knowledge_model import RESULTS_PATH

    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted."
        )

    cv_data_dir = os.path.join(os.path.dirname(RESULTS_PATH), "cv_uploads")
    os.makedirs(cv_data_dir, exist_ok=True)

    safe_name = file.filename.replace(" ", "_")
    save_path = os.path.join(cv_data_dir, safe_name)

    content = await file.read()
    with open(save_path, 'wb') as f:
        f.write(content)

    # Extract text from PDF to get skills/education
    try:
        from pypdf import PdfReader
        import io as _io
        reader = PdfReader(_io.BytesIO(content))
        pages = [page.extract_text() or '' for page in reader.pages]
        cv_text = '\n'.join(pages)
    except Exception:
        cv_text = ''

    # Simple skill extraction from text
    skill_keywords = [
        'python', 'java', 'javascript', 'react', 'node', 'typescript', 'c++', 'c#',
        'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'docker', 'kubernetes',
        'aws', 'azure', 'gcp', 'tensorflow', 'pytorch', 'scikit', 'pandas', 'numpy',
        'matlab', 'simulink', 'scada', 'plc', 'autocad', 'solidworks', 'catia',
        'ansys', 'abaqus', 'latex', 'excel', 'vba', 'tableau', 'powerbi',
        'project', 'management', 'agile', 'scrum', 'kanban', 'lean', 'six sigma',
        'iso', 'quality', 'maintenance', 'supply', 'logistics', 'erp', 'sap',
        'arduino', 'raspberry', 'vhdl', 'verilog', 'fpga', 'embedded', 'pcb',
        'machine learning', 'deep learning', 'nlp', 'data science', 'big data',
        'html', 'css', 'flask', 'django', 'fastapi', 'spring', 'angular', 'vue',
    ]
    cv_lower = cv_text.lower()
    extracted_skills = [kw for kw in skill_keywords if kw in cv_lower]

    # Load existing results
    cv_results = []
    if os.path.exists(RESULTS_PATH):
        with open(RESULTS_PATH, 'r', encoding='utf-8') as f:
            cv_results = json.load(f)

    # Check if CV already exists (by filename)
    existing_idx = None
    for i, r in enumerate(cv_results):
        if r.get('filename') == safe_name:
            existing_idx = i
            break

    new_entry = {
        'filename': safe_name,
        'filiere': filiere,
        'normalized_score': 0.0,
        'confidence': 0.0,
        'skills': extracted_skills,
        'skills_count': len(extracted_skills),
        'education': [],
        'experience_years': 0,
        'text_length': len(cv_text),
        'top_matches': [],
        'knn_raw': 0.0,
        'path': save_path,
    }

    if existing_idx is not None:
        cv_results[existing_idx] = new_entry
        action = 'updated'
    else:
        cv_results.append(new_entry)
        action = 'added'

    with open(RESULTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(cv_results, f, ensure_ascii=False, indent=2)

    return {
        'status': 'success',
        'action': action,
        'filename': safe_name,
        'filiere': filiere,
        'skills_extracted': extracted_skills,
        'n_skills': len(extracted_skills),
        'total_cvs': len(cv_results),
        'message': f'CV "{safe_name}" {action} to training corpus with filiere "{filiere}". Re-train the model to include this CV.'
    }


@router.get("/training-cvs")
async def list_training_cvs(current_user: User = Depends(_require_admin)):
    """List all CVs in the training corpus. Admin only."""
    from src.modules.knowledge.ml.knowledge_model import RESULTS_PATH

    if not os.path.exists(RESULTS_PATH):
        return {'cvs': [], 'total': 0}

    with open(RESULTS_PATH, 'r', encoding='utf-8') as f:
        cv_results = json.load(f)

    cvs = [
        {
            'filename': r.get('filename', ''),
            'filiere': r.get('filiere', ''),
            'skills_count': r.get('skills_count', 0),
            'text_length': r.get('text_length', 0),
        }
        for r in cv_results
    ]
    return {'cvs': cvs, 'total': len(cvs)}


@router.get("/training-history")
async def get_training_history(current_user: User = Depends(_require_admin)):
    """Return the training history used by the admin dashboard charts. Admin only."""
    from src.modules.knowledge.ml.knowledge_model import TRAINING_HISTORY_PATH

    if not os.path.exists(TRAINING_HISTORY_PATH):
        return {'history': [], 'total': 0}

    with open(TRAINING_HISTORY_PATH, 'r', encoding='utf-8') as f:
        history = json.load(f)

    return {'history': history, 'total': len(history)}


@router.post("/predict-filiere-pdf")
async def predict_filiere_pdf(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Predict a filiere directly from a PDF CV upload."""
    from src.modules.knowledge.ml.knowledge_model import get_knowledge_model
    from pypdf import PdfReader
    import io as _io

    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted."
        )

    model = get_knowledge_model()
    if not model.is_trained:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le modele KASH Knowledge n'est pas encore entraine. Utilisez /api/v1/knowledge/train-model d'abord."
        )

    content = await file.read()
    try:
        reader = PdfReader(_io.BytesIO(content))
        cv_text = '\n'.join(page.extract_text() or '' for page in reader.pages)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Impossible d'extraire le texte du PDF: {e}"
        )

    if len(cv_text.strip()) < 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Texte du PDF trop court (min 50 caracteres)"
        )

    result = model.predict(cv_text)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Prediction echouee"
        )

    result['source'] = 'pdf'
    result['filename'] = file.filename
    result['extracted_text_length'] = len(cv_text)
    return result
