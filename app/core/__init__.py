"""
HeinerCast Core Module
"""
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_access_token,
    verify_refresh_token,
    generate_api_key,
    hash_api_key,
    verify_api_key,
    encrypt_api_key,
    decrypt_api_key
)

from app.core.exceptions import (
    HeinerCastException,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    AlreadyExistsError,
    ValidationError,
    ExternalAPIError,
    ElevenLabsError,
    LLMProviderError,
    KieAIError,
    ProcessingError,
    AudioProcessingError,
    ScriptGenerationError,
    RateLimitExceededError,
    ConfigurationError,
    MissingAPIKeyError,
    BusinessLogicError,
    EpisodeDeletionError,
    InvalidStatusTransitionError,
    MaxCharactersExceededError
)

from app.core.dependencies import (
    get_current_user,
    get_current_user_optional,
    get_user_language,
    verify_project_ownership,
    verify_episode_ownership,
    verify_voice_ownership
)

from app.core.middleware import (
    SecurityHeadersMiddleware,
    RequestLoggingMiddleware,
    RateLimitMiddleware
)

__all__ = [
    # Security
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "verify_access_token",
    "verify_refresh_token",
    "generate_api_key",
    "hash_api_key",
    "verify_api_key",
    "encrypt_api_key",
    "decrypt_api_key",
    
    # Exceptions
    "HeinerCastException",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "AlreadyExistsError",
    "ValidationError",
    "ExternalAPIError",
    "ElevenLabsError",
    "LLMProviderError",
    "KieAIError",
    "ProcessingError",
    "AudioProcessingError",
    "ScriptGenerationError",
    "RateLimitExceededError",
    "ConfigurationError",
    "MissingAPIKeyError",
    "BusinessLogicError",
    "EpisodeDeletionError",
    "InvalidStatusTransitionError",
    "MaxCharactersExceededError",
    
    # Dependencies
    "get_current_user",
    "get_current_user_optional",
    "get_user_language",
    "verify_project_ownership",
    "verify_episode_ownership",
    "verify_voice_ownership",
    
    # Middleware
    "SecurityHeadersMiddleware",
    "RequestLoggingMiddleware",
    "RateLimitMiddleware"
]
