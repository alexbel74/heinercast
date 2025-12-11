"""
HeinerCast Application Configuration
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    app_name: str = Field(default="HeinerCast", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_debug: bool = Field(default=False, alias="APP_DEBUG")
    app_url: str = Field(default="http://localhost:8000", alias="APP_URL")
    secret_key: str = Field(default="change-this-secret-key", alias="SECRET_KEY")
    
    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://heinercast:password@localhost:5432/heinercast",
        alias="DATABASE_URL"
    )
    
    # JWT
    jwt_secret_key: str = Field(default="change-this-jwt-secret", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_hours: int = Field(default=24, alias="ACCESS_TOKEN_EXPIRE_HOURS")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # Storage
    storage_type: str = Field(default="local", alias="STORAGE_TYPE")  # "local" or "google_drive"
    storage_path: str = Field(default="./storage", alias="STORAGE_PATH")
    
    # Google Drive (optional)
    google_drive_credentials_path: Optional[str] = Field(default=None, alias="GOOGLE_DRIVE_CREDENTIALS_PATH")
    
    # Default API keys (optional, can be overridden by user settings)
    default_openrouter_api_key: Optional[str] = Field(default=None, alias="DEFAULT_OPENROUTER_API_KEY")
    default_elevenlabs_api_key: Optional[str] = Field(default=None, alias="DEFAULT_ELEVENLABS_API_KEY")
    default_kieai_api_key: Optional[str] = Field(default=None, alias="DEFAULT_KIEAI_API_KEY")
    
    # Encryption key for user API keys (must be 32 chars)
    encryption_key: str = Field(default="change-this-encryption-key-32ch", alias="ENCRYPTION_KEY")
    
    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_path: str = Field(default="./logs", alias="LOG_PATH")
    
    # Rate limiting
    rate_limit_login: str = Field(default="5/minute", alias="RATE_LIMIT_LOGIN")
    rate_limit_generation: str = Field(default="10/hour", alias="RATE_LIMIT_GENERATION")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# LLM Provider configurations
LLM_PROVIDERS = {
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "models": [
            # OpenAI
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "openai/gpt-4-turbo",
            "openai/gpt-4",
            "openai/gpt-3.5-turbo",
            # Anthropic
            "anthropic/claude-sonnet-4",
            "anthropic/claude-3-opus",
            "anthropic/claude-3-sonnet",
            "anthropic/claude-3-haiku",
            # Google
            "google/gemini-pro",
            "google/gemini-1.5-pro",
            "google/gemini-1.5-flash",
            # xAI
            "x-ai/grok-2",
            "x-ai/grok-2-mini"
        ]
    },
    "polza": {
        "base_url": "https://api.polza.ai/v1",
        "models": [
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "openai/gpt-4-turbo",
            "anthropic/claude-sonnet-4",
            "anthropic/claude-3-opus",
            "anthropic/claude-3-sonnet",
        ]
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "models": [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo"
        ]
    }
}

# ElevenLabs API endpoints
ELEVENLABS_BASE_URL = "https://api.elevenlabs.io"
ELEVENLABS_ENDPOINTS = {
    "text_to_dialogue": "/v1/text-to-dialogue/with-timestamps",
    "sound_generation": "/v1/sound-generation",
    "music_plan": "/v1/music/plan",
    "music": "/v1/music",
    "voices": "/v1/voices"
}

# kie.ai API endpoints
KIEAI_BASE_URL = "https://kieai.erweima.ai"
KIEAI_ENDPOINTS = {
    "create_task": "/api/v1/jobs/createTask",
    "record_info": "/api/v1/jobs/recordInfo"
}

# Audio settings
AUDIO_SETTINGS = {
    "max_chars_per_request": 4800,
    "chars_per_minute": 850,
    "max_parts": 3,
    "output_format": "mp3",
    "output_quality": 2  # FFmpeg quality (2 is high quality)
}

# Supported languages
SUPPORTED_LANGUAGES = ["ru", "en", "de"]

# Default AI writer prompt (Russian)
DEFAULT_AI_WRITER_PROMPT = """ТЫ — ЛУЧШИЙ В МИРЕ ПИСАТЕЛЬ-ФУТУРОЛОГ, специализирующийся на создании захватывающих аудиокниг.

Твоя задача — создать сценарий для аудиокниги на основе предоставленной информации.

ТРЕБОВАНИЯ К СЦЕНАРИЮ:
1. Диалоги должны быть живыми и естественными
2. Каждая реплика должна быть помечена именем персонажа и эмоциональным тоном в квадратных скобках [emotion]
3. Включай описания звуковых эффектов там, где это уместно
4. Поддерживай напряжение и интерес на протяжении всего эпизода
5. Учитывай желаемую продолжительность эпизода

ФОРМАТ ВЫВОДА:
Верни JSON объект со следующей структурой:
{
  "story_title": "Название истории",
  "genre_tone": "Жанр и тон",
  "approx_duration_minutes": число,
  "lines": [
    {
      "speaker": "Имя персонажа",
      "voice_id": "ID голоса",
      "text": "[emotion] Текст реплики",
      "sound_effect": "описание звука или null"
    }
  ]
}"""

# Default cover prompt template
DEFAULT_COVER_PROMPT_TEMPLATE = """Create a cinematic audiobook cover for:
Title: {title}
Genre: {genre_tone}
Description: {description}

Style: Dark, atmospheric, professional audiobook cover art
Mood: Dramatic, cinematic
Format: Square, suitable for podcast/audiobook platforms"""


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
