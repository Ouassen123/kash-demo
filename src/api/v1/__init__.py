"""API v1 package."""

from fastapi import APIRouter
from .auth import router as auth_router
from .knowledge import router as knowledge_router
from .abilities import router as abilities_router
from .habits import router as habits_router
from .skills import router as skills_router
from .intelligence import router as intelligence_router
from .admin import router as admin_router
from .attitude import router as attitude_router
from .psychometric import router as psychometric_router
from .practical import router as practical_router

# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Include sub-routers
api_router.include_router(auth_router, tags=["authentication"])
api_router.include_router(knowledge_router, tags=["knowledge"])
api_router.include_router(abilities_router, tags=["attitude", "abilities"])
api_router.include_router(habits_router, tags=["habits"])
api_router.include_router(skills_router, tags=["skills"])
api_router.include_router(intelligence_router, tags=["intelligence"])
api_router.include_router(admin_router, tags=["admin"])
api_router.include_router(attitude_router, tags=["attitude"])
api_router.include_router(psychometric_router, tags=["psychometric"])
api_router.include_router(practical_router, tags=["practical"])

# Export for easy importing
__all__ = ["api_router"]
