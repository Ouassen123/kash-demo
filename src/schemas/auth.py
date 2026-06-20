"""Authentication schemas for API requests/responses."""

from pydantic import BaseModel, EmailStr, validator, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class FirebaseLoginRequest(BaseModel):
    """Request schema for Firebase authentication."""
    id_token: str
    device_info: Optional[Dict[str, Any]] = None
    
    @validator('id_token')
    def validate_id_token(cls, v):
        if not v or len(v) < 100:
            raise ValueError('Invalid Firebase ID token')
        return v


class LoginResponse(BaseModel):
    """Response schema for successful authentication."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until expiration
    user: "UserResponse"
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "token_type": "bearer",
                "expires_in": 86400,
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "user@example.com",
                    "display_name": "John Doe",
                    "avatar_url": "https://example.com/avatar.jpg",
                    "auth_provider": "google",
                    "is_verified": True,
                    "created_at": "2024-01-01T00:00:00Z"
                }
            }
        }


class UserResponse(BaseModel):
    """User profile response schema."""
    id: str
    email: str
    display_name: Optional[str]
    avatar_url: Optional[str]
    auth_provider: str
    is_active: bool
    is_verified: bool
    is_admin: bool = False
    created_at: datetime
    last_login_at: Optional[datetime]

    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v
    
    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    """User profile update request schema."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    profile_data: Optional[Dict[str, Any]] = None
    
    @validator('first_name', 'last_name', 'display_name')
    def validate_names(cls, v):
        if v is not None and len(v.strip()) == 0:
            raise ValueError('Name cannot be empty')
        return v.strip() if v else v


class UserSessionResponse(BaseModel):
    """User session response schema."""
    id: str
    device_info: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    created_at: datetime
    expires_at: datetime
    last_activity_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


class LogoutResponse(BaseModel):
    """Logout response schema."""
    message: str = "Successfully logged out"
    success: bool = True


class RefreshTokenRequest(BaseModel):
    """Token refresh request schema."""
    refresh_token: str


class ErrorResponse(BaseModel):
    """Standard error response schema."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "error": "authentication_failed",
                "message": "Invalid Firebase ID token",
                "details": {
                    "code": "INVALID_TOKEN",
                    "provider": "firebase"
                }
            }
        }


# Forward reference resolution
LoginResponse.model_rebuild()
