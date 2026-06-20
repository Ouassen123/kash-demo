"""Authentication service with Firebase integration."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json
import jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

try:
    import firebase_admin
    from firebase_admin import credentials, auth
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

from src.core.config import settings
from src.core.database import get_db
from src.core.logging import get_logger
from src.models.user import User, UserSession

logger = get_logger(__name__)
security = HTTPBearer(auto_error=False)

# Initialize Firebase Admin SDK
firebase_app = None
if FIREBASE_AVAILABLE and all([
    settings.firebase_project_id,
    settings.firebase_private_key,
    settings.firebase_client_email
]):
    try:
        firebase_credentials = credentials.Certificate({
            "type": "service_account",
            "project_id": settings.firebase_project_id,
            "private_key_id": settings.firebase_private_key_id,
            "private_key": settings.firebase_private_key,
            "client_email": settings.firebase_client_email,
            "client_id": settings.firebase_client_id,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        })
        firebase_app = firebase_admin.initialize_app(firebase_credentials)
        logger.info("Firebase Admin SDK initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        firebase_app = None
else:
    logger.warning("Firebase credentials not configured - authentication will be limited")


class AuthService:
    """Authentication service for user management."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def verify_firebase_token(self, id_token: str) -> Dict[str, Any]:
        """Verify Firebase ID token and return user info."""
        if not firebase_app:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Firebase authentication not configured"
            )
        
        try:
            # Verify the ID token
            decoded_token = auth.verify_id_token(id_token)
            return decoded_token
        except auth.ExpiredIdTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except auth.InvalidIdTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except Exception as e:
            logger.error(f"Firebase token verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token verification failed"
            )
    
    async def authenticate_user(self, id_token: str, device_info: Optional[Dict] = None) -> User:
        """Authenticate user with Firebase token and create/update user record."""
        # Verify Firebase token
        firebase_data = await self.verify_firebase_token(id_token)
        
        # Extract user information
        firebase_uid = firebase_data["uid"]
        email = firebase_data.get("email")
        name = firebase_data.get("name", "")
        picture = firebase_data.get("picture")
        
        # Determine auth provider
        provider = "email"
        if "firebase" in firebase_data.get("sign_in_provider", ""):
            if "google.com" in firebase_data["sign_in_provider"]:
                provider = "google"
            elif "linkedin.com" in firebase_data["sign_in_provider"]:
                provider = "linkedin"
        
        # Find or create user
        user = self.db.query(User).filter(User.firebase_uid == firebase_uid).first()
        
        if not user:
            # Create new user
            user = User(
                firebase_uid=firebase_uid,
                email=email,
                display_name=name,
                avatar_url=picture,
                auth_provider=provider,
                is_verified=True,  # Firebase users are verified
                last_login_at=datetime.utcnow()
            )
            self.db.add(user)
            logger.info(f"Created new user: {email}")
        else:
            # Update existing user
            user.last_login_at = datetime.utcnow()
            if name and not user.display_name:
                user.display_name = name
            if picture and not user.avatar_url:
                user.avatar_url = picture
            logger.info(f"Updated existing user: {email}")
        
        self.db.commit()
        self.db.refresh(user)
        
        # Create user session
        await self.create_user_session(user, device_info)
        
        return user
    
    async def create_user_session(self, user: User, device_info: Optional[Dict] = None) -> UserSession:
        """Create a new user session."""
        # Generate session token
        session_token = self.generate_session_token(user)
        
        # Create session record
        session = UserSession(
            user_id=user.id,
            session_token=session_token,
            device_info=device_info or {},
            expires_at=datetime.utcnow() + timedelta(hours=24),
            last_activity_at=datetime.utcnow()
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        logger.info(f"Created session for user {user.id}")
        return session
    
    def generate_session_token(self, user: User) -> str:
        """Generate JWT session token for user."""
        payload = {
            "user_id": str(user.id),
            "firebase_uid": user.firebase_uid,
            "email": user.email,
            "exp": datetime.utcnow() + timedelta(hours=24),
            "iat": datetime.utcnow(),
            "type": "session"
        }
        return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
        """Get current user from JWT token."""
        if credentials is None:
            if settings.debug:
                return self._get_or_create_dev_user()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        try:
            # Decode JWT token
            payload = jwt.decode(
                credentials.credentials,
                settings.secret_key,
                algorithms=[settings.algorithm]
            )
            
            # Check token type (skip for dev tokens that use 'sub')
            token_type = payload.get("type")
            if token_type is not None and token_type != "session":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            # Get user from database — support both 'user_id' and 'sub'
            user_id = payload.get("user_id") or payload.get("sub")
            user = self.db.query(User).filter(User.id == user_id).first()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account is inactive"
                )
            
            return user
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except Exception:
            if settings.debug:
                return self._get_or_create_dev_user()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    def _get_or_create_dev_user(self) -> User:
        """Return a stable local development user when auth providers are unavailable."""
        dev_email = "dev.student@kash.local"
        user = self.db.query(User).filter(User.email == dev_email).first()

        if user:
            return user

        user = User(
            firebase_uid="dev-local-user",
            email=dev_email,
            display_name="Dev Student",
            auth_provider="email",
            is_active=True,
            is_verified=True,
            last_login_at=datetime.utcnow(),
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    async def logout_user(self, session_token: str) -> bool:
        """Logout user by invalidating session."""
        session = self.db.query(UserSession).filter(
            UserSession.session_token == session_token,
            UserSession.is_active == True
        ).first()
        
        if session:
            session.is_active = False
            self.db.commit()
            logger.info(f"Logged out session {session.id}")
            return True
        
        return False


# Dependency function for FastAPI
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """FastAPI dependency to get current authenticated user."""
    auth_service = AuthService(db)
    return await auth_service.get_current_user(credentials)


async def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Get authentication service instance."""
    return AuthService(db)
