"""Admin API endpoints — candidate management and analytics."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from src.core.database import get_db
from src.core.auth import get_current_user
from src.core.logging import get_logger
from src.models.user import User
from src.models.assessment import UserAssessment
from pydantic import BaseModel

router = APIRouter(prefix="/admin", tags=["admin"])
logger = get_logger(__name__)


# ── Schemas ──────────────────────────────────────────────────────────────────

class CandidateProfile(BaseModel):
    id: str
    email: str
    display_name: Optional[str]
    is_active: bool
    is_admin: bool
    created_at: str
    last_login_at: Optional[str]
    total_assessments: int
    kash_score: float
    knowledge_score: float
    abilities_score: float
    skills_score: float
    last_assessment_at: Optional[str]

class CandidateUpdate(BaseModel):
    display_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None

class CandidateCreate(BaseModel):
    email: str
    display_name: Optional[str] = None
    is_active: bool = True

class AdminStats(BaseModel):
    total_candidates: int
    active_candidates: int
    assessments_today: int
    assessments_this_week: int
    avg_kash_score: float
    top_career_stage: str

class ActivityPoint(BaseModel):
    date: str
    count: int


# ── Guard ─────────────────────────────────────────────────────────────────────

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_candidate(user: User, db: Session) -> dict:
    assessments = db.query(UserAssessment).filter(
        UserAssessment.user_id == user.id,
        UserAssessment.status == 'completed'
    ).all()

    total = len(assessments)
    last_at = None
    kash = abilities = knowledge = skills = 0.0

    for a in assessments:
        if a.assessment_type == 'knowledge':
            knowledge = max(knowledge, float(a.normalized_score or 0))
        elif a.assessment_type == 'abilities':
            abilities = max(abilities, float(a.normalized_score or 0))
        elif a.assessment_type == 'skills':
            skills = max(skills, float(a.normalized_score or 0))

    if assessments:
        latest = max(assessments, key=lambda x: x.created_at)
        last_at = latest.created_at.isoformat()
        kash = round((knowledge * 0.3 + abilities * 0.4 + skills * 0.3), 1)

    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name or user.email.split("@")[0],
        "is_active": user.is_active,
        "is_admin": user.is_admin,
        "created_at": user.created_at.isoformat(),
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "total_assessments": total,
        "kash_score": kash,
        "knowledge_score": round(knowledge, 1),
        "abilities_score": round(abilities, 1),
        "skills_score": round(skills, 1),
        "last_assessment_at": last_at,
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/stats", response_model=AdminStats)
async def get_admin_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Global platform statistics."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)

    total_candidates = db.query(User).filter(User.is_admin == False).count()
    active_candidates = db.query(User).filter(User.is_admin == False, User.is_active == True).count()

    assessments_today = db.query(UserAssessment).filter(
        UserAssessment.created_at >= today_start
    ).count()

    assessments_week = db.query(UserAssessment).filter(
        UserAssessment.created_at >= week_start
    ).count()

    avg_score_row = db.query(func.avg(UserAssessment.normalized_score)).filter(
        UserAssessment.status == 'completed',
        UserAssessment.normalized_score.isnot(None)
    ).scalar()
    avg_score = round(float(avg_score_row or 0), 1)

    return AdminStats(
        total_candidates=total_candidates,
        active_candidates=active_candidates,
        assessments_today=assessments_today,
        assessments_this_week=assessments_week,
        avg_kash_score=avg_score,
        top_career_stage="explorer"
    )


@router.get("/candidates", response_model=List[CandidateProfile])
async def list_candidates(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """List all candidates with their KASH scores."""
    query = db.query(User).filter(User.is_admin == False)
    if search:
        query = query.filter(User.email.ilike(f"%{search}%"))
    users = query.order_by(desc(User.created_at)).offset(skip).limit(limit).all()
    return [_build_candidate(u, db) for u in users]


@router.post("/candidates", response_model=CandidateProfile)
async def create_candidate(
    payload: CandidateCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    email = (payload.email or "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email")

    user = db.query(User).filter(User.email == email).first()
    if user:
        if user.is_admin:
            raise HTTPException(status_code=400, detail="Cannot create candidate with admin email")
        if payload.display_name is not None:
            user.display_name = payload.display_name
        user.is_active = payload.is_active
        db.commit()
        db.refresh(user)
        return _build_candidate(user, db)

    user = User(
        firebase_uid=f"admin-created-{uuid.uuid4()}",
        email=email,
        display_name=payload.display_name,
        auth_provider="email",
        is_active=payload.is_active,
        is_verified=False,
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _build_candidate(user, db)


@router.get("/candidates/{candidate_id}", response_model=CandidateProfile)
async def get_candidate(
    candidate_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Get a single candidate profile."""
    user = db.query(User).filter(User.id == candidate_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return _build_candidate(user, db)


@router.patch("/candidates/{candidate_id}")
async def update_candidate(
    candidate_id: str,
    payload: CandidateUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Update candidate — name, active status, admin role."""
    user = db.query(User).filter(User.id == candidate_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if payload.display_name is not None:
        user.display_name = payload.display_name
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.is_admin is not None:
        user.is_admin = payload.is_admin
    db.commit()
    db.refresh(user)
    return {"ok": True, "candidate": _build_candidate(user, db)}


@router.delete("/candidates/{candidate_id}")
async def deactivate_candidate(
    candidate_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Soft-delete (deactivate) a candidate."""
    user = db.query(User).filter(User.id == candidate_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Candidate not found")
    user.is_active = False
    db.commit()
    return {"ok": True, "message": f"Candidate {user.email} deactivated"}


@router.get("/activity")
async def get_activity(
    days: int = 14,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Assessment activity per day for the last N days."""
    since = datetime.utcnow() - timedelta(days=days)
    rows = db.query(
        func.date_trunc('day', UserAssessment.created_at).label('day'),
        func.count(UserAssessment.id).label('count')
    ).filter(UserAssessment.created_at >= since).group_by('day').order_by('day').all()
    return [{"date": str(r.day)[:10], "count": r.count} for r in rows]


@router.get("/candidates/{candidate_id}/assessments")
async def get_candidate_assessments(
    candidate_id: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """All assessments for a specific candidate."""
    assessments = db.query(UserAssessment).filter(
        UserAssessment.user_id == candidate_id
    ).order_by(desc(UserAssessment.created_at)).all()
    return [
        {
            "id": str(a.id),
            "type": a.assessment_type,
            "name": a.assessment_name,
            "status": a.status,
            "score": float(a.normalized_score or 0),
            "created_at": a.created_at.isoformat(),
        }
        for a in assessments
    ]
