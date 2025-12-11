"""
HeinerCast API Routes
"""
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.projects import router as projects_router
from app.api.episodes import router as episodes_router
from app.api.voices import router as voices_router
from app.api.generation import router as generation_router
from app.api.files import router as files_router
from app.api.settings import router as settings_router
from app.api.pages import router as pages_router

__all__ = [
    "auth_router",
    "users_router",
    "projects_router",
    "episodes_router",
    "voices_router",
    "generation_router",
    "files_router",
    "settings_router",
    "pages_router"
]
