"""Practical challenges API endpoints — domain-adaptive Skills (S) assessment."""

from __future__ import annotations

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from src.core.logging import get_logger
from src.modules.skills.practical_challenges import (
    get_challenges_by_domain,
    get_all_practical_challenges,
    get_challenge_by_id,
    score_practical_challenge,
    PracticalChallenge,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/skills/practical", tags=["skills-practical"])

# Mapping from Knowledge model tech_domains to practical challenge domains
_TECH_DOMAIN_TO_CHALLENGE_DOMAIN = {
    "electrical": "electrical",
    "mechanical": "mechanical",
    "quality": "quality",
    "logistics": "logistics",
    "management": "management",
    "software": "management",  # software devs often get management challenges too
}


class PracticalSubmitRequest(BaseModel):
    challenge_id: str
    answers: Dict[str, str]  # {test_case_name: answer_text}


class CVRecommendRequest(BaseModel):
    cv_text: str
    top_n: int = 3


@router.get("/challenges")
async def list_practical_challenges(domain: str = ""):
    """List practical challenges, optionally filtered by domain.

    Domains: electrical, mechanical, quality, logistics, management
    """
    if domain:
        challenges = get_challenges_by_domain(domain)
    else:
        challenges = get_all_practical_challenges()

    return [
        {
            "id": c.id,
            "title": c.title,
            "domain": c.domain,
            "difficulty": c.difficulty,
            "estimated_time_minutes": c.estimated_time_minutes,
            "statement": c.statement,
            "is_coding": c.is_coding,
            "test_cases": [
                {"name": tc.name, "question": tc.question}
                for tc in c.test_cases
            ],
        }
        for c in challenges
    ]


@router.get("/challenges/{challenge_id}")
async def get_practical_challenge(challenge_id: str):
    """Get a specific practical challenge with full details."""
    challenge = get_challenge_by_id(challenge_id)
    if not challenge:
        raise HTTPException(status_code=404, detail=f"Challenge {challenge_id} not found")

    return {
        "id": challenge.id,
        "title": challenge.title,
        "domain": challenge.domain,
        "difficulty": challenge.difficulty,
        "estimated_time_minutes": challenge.estimated_time_minutes,
        "statement": challenge.statement,
        "is_coding": challenge.is_coding,
        "test_cases": [
            {
                "name": tc.name,
                "question": tc.question,
                "min_score": tc.min_score,
            }
            for tc in challenge.test_cases
        ],
    }


@router.post("/submit")
async def submit_practical_challenge(request: PracticalSubmitRequest):
    """Submit answers for a practical challenge and get scoring results."""
    challenge = get_challenge_by_id(request.challenge_id)
    if not challenge:
        raise HTTPException(status_code=404, detail=f"Challenge {request.challenge_id} not found")

    result = score_practical_challenge(challenge, request.answers)
    return result


@router.post("/recommend")
async def recommend_challenges_from_cv(request: CVRecommendRequest):
    """Analyze CV text and recommend domain-adaptive practical challenges.

    Uses the Knowledge model's tech domain detection to match the student's
    field (e.g., Génie Électrique) to relevant practical challenges.

    Returns:
        detected_domains: list of detected tech domains with hit counts
        recommended_challenges: challenges matching the top domain
        all_domains: all available challenge domains for manual selection
    """
    cv_text = request.cv_text.strip()
    if len(cv_text) < 50:
        raise HTTPException(status_code=400, detail="CV text too short (min 50 characters)")

    # Use the Knowledge model's tech keyword extraction
    try:
        from src.modules.knowledge.ml.knowledge_model import get_knowledge_model
        model = get_knowledge_model()
        tech_domains = model._extract_tech_keywords(cv_text)
    except Exception as e:
        logger.warning(f"Knowledge model not available, using fallback keyword matching: {e}")
        # Fallback: simple keyword matching
        from src.modules.knowledge.ml.knowledge_model import _TECH_KEYWORDS
        cv_lower = cv_text.lower()
        tech_domains = {}
        for domain, keywords in _TECH_KEYWORDS.items():
            hits = sum(1 for kw in keywords if kw in cv_lower)
            if hits > 0:
                tech_domains[domain] = hits

    # Sort domains by hit count (most relevant first)
    sorted_domains = sorted(tech_domains.items(), key=lambda x: x[1], reverse=True)

    # Map tech domains to challenge domains and get challenges
    recommended = []
    detected_challenge_domains = set()

    for tech_domain, hits in sorted_domains:
        challenge_domain = _TECH_DOMAIN_TO_CHALLENGE_DOMAIN.get(tech_domain, tech_domain)
        if challenge_domain in detected_challenge_domains:
            continue
        detected_challenge_domains.add(challenge_domain)
        challenges = get_challenges_by_domain(challenge_domain)
        for c in challenges:
            recommended.append({
                "id": c.id,
                "title": c.title,
                "domain": c.domain,
                "difficulty": c.difficulty,
                "estimated_time_minutes": c.estimated_time_minutes,
                "statement": c.statement,
                "is_coding": c.is_coding,
                "test_cases": [
                    {"name": tc.name, "question": tc.question}
                    for tc in c.test_cases
                ],
                "match_score": hits,
                "source_tech_domain": tech_domain,
            })

    # If no domain detected, return all challenges
    if not recommended:
        for c in get_all_practical_challenges():
            recommended.append({
                "id": c.id,
                "title": c.title,
                "domain": c.domain,
                "difficulty": c.difficulty,
                "estimated_time_minutes": c.estimated_time_minutes,
                "statement": c.statement,
                "is_coding": c.is_coding,
                "test_cases": [
                    {"name": tc.name, "question": tc.question}
                    for tc in c.test_cases
                ],
                "match_score": 0,
                "source_tech_domain": "unknown",
            })

    # Limit to top_n
    recommended = recommended[:request.top_n]

    return {
        "detected_tech_domains": dict(sorted_domains),
        "detected_challenge_domains": list(detected_challenge_domains),
        "recommended_challenges": recommended,
        "all_challenge_domains": ["electrical", "mechanical", "quality", "logistics", "management"],
        "total_available": len(get_all_practical_challenges()),
    }


@router.post("/recommend-pdf")
async def recommend_challenges_from_pdf(file: UploadFile = File(...), top_n: int = 3):
    """Upload a CV file (PDF, DOCX, TXT) and get recommended practical challenges.

    Extracts text from the file, detects tech domains using the Knowledge model,
    and returns challenges adapted to the student's field.
    """
    allowed = ['text/plain', 'application/pdf',
               'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    if file.content_type not in allowed:
        raise HTTPException(status_code=400,
                            detail=f"Unsupported file type: {file.content_type}. Allowed: PDF, DOCX, TXT")

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

    import re
    cv_text = re.sub(r'[^\x20-\x7E\n\r\t\u00C0-\u024F]', ' ', cv_text)
    cv_text = re.sub(r' {3,}', ' ', cv_text).strip()
    cv_text = cv_text[:50000]

    if len(cv_text.strip()) < 50:
        raise HTTPException(status_code=400,
                            detail="Extracted text too short (min 50 chars). Upload a text-based CV, not a scanned image.")

    # Use the same logic as the text endpoint
    try:
        from src.modules.knowledge.ml.knowledge_model import get_knowledge_model, _TECH_KEYWORDS
        model = get_knowledge_model()
        tech_domains = model._extract_tech_keywords(cv_text)
    except Exception:
        from src.modules.knowledge.ml.knowledge_model import _TECH_KEYWORDS
        cv_lower = cv_text.lower()
        tech_domains = {}
        for domain, keywords in _TECH_KEYWORDS.items():
            hits = sum(1 for kw in keywords if kw in cv_lower)
            if hits > 0:
                tech_domains[domain] = hits

    sorted_domains = sorted(tech_domains.items(), key=lambda x: x[1], reverse=True)

    recommended = []
    detected_challenge_domains = set()

    for tech_domain, hits in sorted_domains:
        challenge_domain = _TECH_DOMAIN_TO_CHALLENGE_DOMAIN.get(tech_domain, tech_domain)
        if challenge_domain in detected_challenge_domains:
            continue
        detected_challenge_domains.add(challenge_domain)
        challenges = get_challenges_by_domain(challenge_domain)
        for c in challenges:
            recommended.append({
                "id": c.id,
                "title": c.title,
                "domain": c.domain,
                "difficulty": c.difficulty,
                "estimated_time_minutes": c.estimated_time_minutes,
                "statement": c.statement,
                "is_coding": c.is_coding,
                "test_cases": [
                    {"name": tc.name, "question": tc.question}
                    for tc in c.test_cases
                ],
                "match_score": hits,
                "source_tech_domain": tech_domain,
            })

    if not recommended:
        for c in get_all_practical_challenges():
            recommended.append({
                "id": c.id,
                "title": c.title,
                "domain": c.domain,
                "difficulty": c.difficulty,
                "estimated_time_minutes": c.estimated_time_minutes,
                "statement": c.statement,
                "is_coding": c.is_coding,
                "test_cases": [
                    {"name": tc.name, "question": tc.question}
                    for tc in c.test_cases
                ],
                "match_score": 0,
                "source_tech_domain": "unknown",
            })

    recommended = recommended[:top_n]

    # Also detect skills from the CV
    cv_lower = cv_text.lower()
    detected_skills = []
    from src.modules.knowledge.ml.knowledge_model import _TECH_KEYWORDS
    for domain_k, keywords in _TECH_KEYWORDS.items():
        for kw in keywords:
            if kw in cv_lower and kw not in detected_skills:
                detected_skills.append(kw)

    # Map to filiere name
    domain_to_filiere = {
        'electrical': 'Génie Électrique',
        'mechanical': 'Génie Mécanique',
        'quality': 'Qualité & Maintenance',
        'logistics': 'Logistique',
        'management': 'Génie Industriel',
        'software': 'Informatique',
    }
    predicted_filiere = domain_to_filiere.get(sorted_domains[0][0], 'Unknown') if sorted_domains else 'Unknown'

    return {
        "filename": file.filename,
        "extracted_text_length": len(cv_text),
        "predicted_filiere": predicted_filiere,
        "detected_tech_domains": dict(sorted_domains),
        "detected_challenge_domains": list(detected_challenge_domains),
        "detected_skills": detected_skills[:20],
        "recommended_challenges": recommended,
        "all_challenge_domains": ["electrical", "mechanical", "quality", "logistics", "management"],
        "total_available": len(get_all_practical_challenges()),
    }
