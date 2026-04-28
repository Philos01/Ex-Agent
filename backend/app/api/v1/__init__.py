"""
API v1 module
"""
from fastapi import APIRouter

from .routes import router as routes_router
from .auth import router as auth_router
from .sessions import router as sessions_router
from .skills import router as skills_router

api_router = APIRouter()

api_router.include_router(routes_router, tags=["core"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(sessions_router, prefix="/sessions", tags=["sessions"])
api_router.include_router(skills_router, prefix="/skills", tags=["skills"])
