"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List

from src.core.database import get_db
from src.core.auth import AuthService, get_auth_service, get_current_user
from src.core.logging import get_logger, log_request_info
from src.models.user import User, UserSession
from src.schemas.auth import (
    FirebaseLoginRequest,
    LoginResponse,
    UserResponse,
    UserProfileUpdate,
    UserSessionResponse,
    LogoutResponse,
    ErrorResponse
)

router = APIRouter(prefix="/auth", tags=["authentication"])
logger = get_logger(__name__)


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    login_data: FirebaseLoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Authenticate user with Firebase ID token.
    
    - **id_token**: Firebase ID token from client
    - **device_info**: Optional device information for session tracking
    
    Returns JWT access token and user profile.
    """
    try:
        # Extract device info from request if not provided
        device_info = login_data.device_info or {
            "user_agent": request.headers.get("user-agent"),
            "ip_address": request.client.host
        }
        
        # Authenticate user and create session
        user = await auth_service.authenticate_user(login_data.id_token, device_info)
        
        # Get the most recent session
        session = auth_service.db.query(UserSession).filter(
            UserSession.user_id == user.id,
            UserSession.is_active == True
        ).order_by(UserSession.created_at.desc()).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user session"
            )
        
        # Calculate token expiration
        expires_in = int((session.expires_at - session.created_at).total_seconds())
        
        logger.info(f"User {user.email} logged in successfully")
        
        return LoginResponse(
            access_token=session.session_token,
            token_type="bearer",
            expires_in=expires_in,
            user=UserResponse.from_orm(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user profile.
    
    Returns the user's profile information including authentication status.
    """
    return UserResponse.from_orm(current_user)


@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user profile.
    
    - **first_name**: User's first name
    - **last_name**: User's last name  
    - **display_name**: Display name for the user
    - **avatar_url**: Profile picture URL
    - **profile_data**: Additional profile metadata
    """
    try:
        # Update user fields if provided
        if profile_update.first_name is not None:
            current_user.first_name = profile_update.first_name
        
        if profile_update.last_name is not None:
            current_user.last_name = profile_update.last_name
            
        if profile_update.display_name is not None:
            current_user.display_name = profile_update.display_name
            
        if profile_update.avatar_url is not None:
            current_user.avatar_url = profile_update.avatar_url
            
        if profile_update.profile_data is not None:
            if isinstance(current_user.profile_data, dict) and isinstance(profile_update.profile_data, dict):
                current_user.profile_data = {**current_user.profile_data, **profile_update.profile_data}
            else:
                current_user.profile_data = profile_update.profile_data
        
        db.commit()
        db.refresh(current_user)
        
        logger.info(f"User {current_user.email} updated profile")
        
        return UserResponse.from_orm(current_user)
        
    except Exception as e:
        logger.error(f"Profile update failed for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.get("/sessions", response_model=List[UserSessionResponse])
async def get_user_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all active sessions for the current user.
    
    Returns a list of active sessions with device information.
    """
    sessions = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_active == True
    ).order_by(UserSession.last_activity_at.desc()).all()
    
    return [UserSessionResponse.from_orm(session) for session in sessions]


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Logout current user session.
    
    Invalidates the current session token.
    """
    try:
        # Get session token from authorization header
        authorization = request.headers.get("authorization")
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header"
            )
        
        session_token = authorization.split(" ")[1]
        
        # Logout user
        success = await auth_service.logout_user(session_token)
        
        if success:
            logger.info(f"User {current_user.email} logged out successfully")
            return LogoutResponse(message="Successfully logged out", success=True)
        else:
            logger.warning(f"Failed to logout user {current_user.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to logout - session not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout failed for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.post("/logout-all", response_model=LogoutResponse)
async def logout_all_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout all sessions for the current user.
    
    Invalidates all active sessions for the user across all devices.
    """
    try:
        # Deactivate all user sessions
        sessions = db.query(UserSession).filter(
            UserSession.user_id == current_user.id,
            UserSession.is_active == True
        ).all()
        
        for session in sessions:
            session.is_active = False
        
        db.commit()
        
        logger.info(f"User {current_user.email} logged out from {len(sessions)} sessions")
        
        return LogoutResponse(
            message=f"Successfully logged out from {len(sessions)} sessions",
            success=True
        )
        
    except Exception as e:
        logger.error(f"Logout all failed for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to logout all sessions"
        )


@router.post("/dev-token")
async def dev_token(
    payload: dict,
    db: Session = Depends(get_db)
):
    """Dev-mode only: get a JWT for a given email (no Firebase required)."""
    from src.core.config import settings
    if not settings.debug:
        raise HTTPException(status_code=403, detail="Only available in debug mode")
    from jose import jwt as jose_jwt
    from datetime import datetime, timedelta

    email = payload.get("email", "dev.student@kash.local")
    is_admin_email = email == "admin@kash.local"

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            firebase_uid=f"dev-{email}",
            email=email,
            display_name="Admin KASH" if is_admin_email else email.split("@")[0],
            auth_provider="email",
            is_active=True,
            is_verified=True,
            is_admin=is_admin_email,
            last_login_at=datetime.utcnow(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    elif is_admin_email and not user.is_admin:
        user.is_admin = True
        db.commit()

    secret = settings.secret_key or "kash-secret-key-change-in-production"
    token = jose_jwt.encode(
        {"sub": str(user.id), "exp": datetime.utcnow() + timedelta(hours=24)},
        secret, algorithm="HS256"
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "display_name": user.display_name,
            "avatar_url": user.avatar_url,
            "is_admin": user.is_admin,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "auth_provider": user.auth_provider,
            "created_at": user.created_at.isoformat(),
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        }
    }


@router.delete("/sessions/{session_id}", response_model=LogoutResponse)
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a specific user session.
    
    - **session_id**: UUID of the session to delete
    """
    try:
        # Find and deactivate session
        session = db.query(UserSession).filter(
            UserSession.id == session_id,
            UserSession.user_id == current_user.id,
            UserSession.is_active == True
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        session.is_active = False
        db.commit()
        
        logger.info(f"User {current_user.email} deleted session {session_id}")
        
        return LogoutResponse(message="Session deleted successfully", success=True)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session deletion failed for user {current_user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete session"
        )
