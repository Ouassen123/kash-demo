"""API v1 package."""

from fastapi import APIRouter
from .auth import router as auth_router
from .knowledge import router as knowledge_router
from .abilities import router as abilities_router
from .skills import router as skills_router
from .intelligence import router as intelligence_router
from .admin import router as admin_router

# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Include sub-routers
api_router.include_router(auth_router, tags=["authentication"])
api_router.include_router(knowledge_router, tags=["knowledge"])
api_router.include_router(abilities_router, tags=["abilities"])
api_router.include_router(skills_router, tags=["skills"])
api_router.include_router(intelligence_router, tags=["intelligence"])
api_router.include_router(admin_router, tags=["admin"])

# Export for easy importing
__all__ = ["api_router"]
