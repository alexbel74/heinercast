"""
HeinerCast - Main Application Entry Point
Automated Audiobook Production Platform
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import os

from app.config import get_settings
from app.database import init_db, close_db
from app.core.exceptions import HeinerCastException
from app.core.middleware import SecurityHeadersMiddleware

# Import API routers
from app.api.auth import router as auth_router
from app.api.cover_styles import router as cover_styles_router
from app.api.users import router as users_router
from app.api.projects import router as projects_router
from app.api.episodes import router as episodes_router
from app.api.voices import router as voices_router
from app.api.generation import router as generation_router
from app.api.files import router as files_router
from app.api.settings import router as settings_router
from app.api.pages import router as pages_router

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info(f"Starting {settings.app_name}...")
    
    # Create storage directories
    storage_dirs = ["audio", "covers", "temp"]
    for dir_name in storage_dirs:
        dir_path = os.path.join(settings.storage_path, dir_name)
        os.makedirs(dir_path, exist_ok=True)
    
    # Create logs directory
    os.makedirs(settings.log_path, exist_ok=True)
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.app_name}...")
    await close_db()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Automated Audiobook Production Platform with AI-generated scripts, voiceover, sound effects, background music, and cover art.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.app_debug else None,
    redoc_url="/api/redoc" if settings.app_debug else None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.app_url] if settings.app_env == "production" else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Mount static files
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

# Mount storage for serving files
if os.path.exists(settings.storage_path):
    app.mount("/storage", StaticFiles(directory=settings.storage_path), name="storage")

# Templates
templates_path = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_path) if os.path.exists(templates_path) else None


# Exception handlers
@app.exception_handler(HeinerCastException)
async def heinercast_exception_handler(request: Request, exc: HeinerCastException):
    """Handle custom application exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    # Log full error with traceback
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    
    # Get error message
    error_message = str(exc)
    
    # Parse common error patterns for user-friendly messages
    if "401" in error_message or "Unauthorized" in error_message:
        user_message = "Authentication failed. Please check your API key."
    elif "403" in error_message or "Forbidden" in error_message:
        user_message = "Access denied. Check your permissions."
    elif "404" in error_message:
        user_message = "Resource not found."
    elif "429" in error_message or "rate limit" in error_message.lower():
        user_message = "Rate limit exceeded. Please wait and try again."
    elif "timeout" in error_message.lower():
        user_message = "Request timed out. Please try again."
    elif "api key" in error_message.lower() or "api_key" in error_message.lower():
        user_message = "Invalid or missing API key. Please check your settings."
    else:
        user_message = "An unexpected error occurred" if not settings.app_debug else error_message
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": user_message,
            "details": error_message if settings.app_debug else None
        }
    )


# API routes
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/api/users", tags=["Users"])
app.include_router(projects_router, prefix="/api/projects", tags=["Projects"])
app.include_router(episodes_router, prefix="/api/episodes", tags=["Episodes"])
app.include_router(voices_router, prefix="/api/voices", tags=["Voices"])
app.include_router(cover_styles_router)
app.include_router(generation_router, prefix="/api/generation", tags=["Generation"])
app.include_router(files_router, prefix="/api/files", tags=["Files"])
app.include_router(settings_router, prefix="/api/settings", tags=["Settings"])

# Web pages
app.include_router(pages_router, tags=["Pages"])


# Health check endpoint
@app.get("/api/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.app_debug
    )
