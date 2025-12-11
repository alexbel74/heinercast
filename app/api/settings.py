"""
Application Settings API Endpoints
"""
from fastapi import APIRouter, Depends

from app.models.user import User
from app.core.dependencies import get_current_user
from app.config import get_settings, LLM_PROVIDERS, SUPPORTED_LANGUAGES

settings = get_settings()
router = APIRouter()


@router.get("/providers")
async def get_providers():
    """Get available LLM providers and their models"""
    return {
        "providers": [
            {
                "id": provider_id,
                "name": provider_id.title(),
                "base_url": provider_data["base_url"],
                "models": provider_data["models"]
            }
            for provider_id, provider_data in LLM_PROVIDERS.items()
        ]
    }


@router.get("/languages")
async def get_languages():
    """Get supported UI languages"""
    language_names = {
        "ru": {"native": "Русский", "english": "Russian"},
        "en": {"native": "English", "english": "English"},
        "de": {"native": "Deutsch", "english": "German"}
    }
    
    return {
        "languages": [
            {
                "code": lang,
                "native_name": language_names.get(lang, {}).get("native", lang),
                "english_name": language_names.get(lang, {}).get("english", lang)
            }
            for lang in SUPPORTED_LANGUAGES
        ]
    }


@router.get("/app-info")
async def get_app_info():
    """Get application information"""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "environment": settings.app_env,
        "features": {
            "llm_providers": list(LLM_PROVIDERS.keys()),
            "storage_types": ["local", "google_drive"],
            "max_characters_per_project": 5,
            "max_cover_variants": 4,
            "supported_languages": SUPPORTED_LANGUAGES
        }
    }


@router.get("/storage-stats")
async def get_storage_stats(
    current_user: User = Depends(get_current_user)
):
    """Get storage usage statistics for current user"""
    from app.services.storage_service import StorageService
    
    storage_service = StorageService(
        current_user.storage_type,
        current_user.google_drive_credentials
    )
    
    return storage_service.get_storage_stats()


@router.post("/cleanup-temp")
async def cleanup_temp_files(
    max_age_hours: int = 24,
    current_user: User = Depends(get_current_user)
):
    """Clean up old temporary files"""
    from app.services.storage_service import StorageService
    
    storage_service = StorageService(
        current_user.storage_type,
        current_user.google_drive_credentials
    )
    
    await storage_service.cleanup_temp(max_age_hours)
    
    return {"message": f"Cleaned up temp files older than {max_age_hours} hours"}


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": "1.0.0"
    }


@router.get("/default-prompts")
async def get_default_prompts():
    """Get default AI prompts"""
    from app.config import DEFAULT_AI_WRITER_PROMPT, DEFAULT_COVER_PROMPT_TEMPLATE
    
    return {
        "ai_writer_prompt": DEFAULT_AI_WRITER_PROMPT,
        "cover_prompt_template": DEFAULT_COVER_PROMPT_TEMPLATE
    }
