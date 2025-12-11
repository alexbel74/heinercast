"""
HeinerCast Custom Exceptions
"""
from typing import Optional, Any


class HeinerCastException(Exception):
    """Base exception for HeinerCast application"""
    
    def __init__(
        self,
        message: str,
        error_code: str = "error",
        status_code: int = 400,
        details: Optional[Any] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


# Authentication exceptions
class AuthenticationError(HeinerCastException):
    """Authentication failed"""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Any] = None):
        super().__init__(
            message=message,
            error_code="authentication_error",
            status_code=401,
            details=details
        )


class InvalidCredentialsError(AuthenticationError):
    """Invalid username or password"""
    
    def __init__(self):
        super().__init__(message="Invalid username or password")


class TokenExpiredError(AuthenticationError):
    """Token has expired"""
    
    def __init__(self):
        super().__init__(message="Token has expired")


class InvalidTokenError(AuthenticationError):
    """Invalid token"""
    
    def __init__(self):
        super().__init__(message="Invalid token")


# Authorization exceptions
class AuthorizationError(HeinerCastException):
    """Authorization failed"""
    
    def __init__(self, message: str = "Access denied", details: Optional[Any] = None):
        super().__init__(
            message=message,
            error_code="authorization_error",
            status_code=403,
            details=details
        )


class InsufficientPermissionsError(AuthorizationError):
    """User doesn't have required permissions"""
    
    def __init__(self, resource: str = "resource"):
        super().__init__(message=f"You don't have permission to access this {resource}")


# Resource exceptions
class NotFoundError(HeinerCastException):
    """Resource not found"""
    
    def __init__(self, resource: str = "Resource", resource_id: Optional[str] = None):
        message = f"{resource} not found"
        if resource_id:
            message = f"{resource} with id '{resource_id}' not found"
        super().__init__(
            message=message,
            error_code="not_found",
            status_code=404
        )


class AlreadyExistsError(HeinerCastException):
    """Resource already exists"""
    
    def __init__(self, resource: str = "Resource", field: str = ""):
        message = f"{resource} already exists"
        if field:
            message = f"{resource} with this {field} already exists"
        super().__init__(
            message=message,
            error_code="already_exists",
            status_code=409
        )


# Validation exceptions
class ValidationError(HeinerCastException):
    """Validation failed"""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            error_code="validation_error",
            status_code=422,
            details=details
        )


# External API exceptions
class ExternalAPIError(HeinerCastException):
    """External API call failed"""
    
    def __init__(self, service: str, message: str, details: Optional[Any] = None):
        super().__init__(
            message=f"{service} API error: {message}",
            error_code="external_api_error",
            status_code=502,
            details=details
        )


class ElevenLabsError(ExternalAPIError):
    """ElevenLabs API error"""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(service="ElevenLabs", message=message, details=details)


class LLMProviderError(ExternalAPIError):
    """LLM Provider API error"""
    
    def __init__(self, provider: str, message: str, details: Optional[Any] = None):
        super().__init__(service=f"LLM ({provider})", message=message, details=details)


class KieAIError(ExternalAPIError):
    """kie.ai API error"""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(service="kie.ai", message=message, details=details)


# Processing exceptions
class ProcessingError(HeinerCastException):
    """Processing failed"""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            error_code="processing_error",
            status_code=500,
            details=details
        )


class AudioProcessingError(ProcessingError):
    """Audio processing (FFmpeg) failed"""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message=f"Audio processing error: {message}", details=details)


class ScriptGenerationError(ProcessingError):
    """Script generation failed"""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message=f"Script generation error: {message}", details=details)


# Rate limiting
class RateLimitExceededError(HeinerCastException):
    """Rate limit exceeded"""
    
    def __init__(self, message: str = "Rate limit exceeded. Please try again later."):
        super().__init__(
            message=message,
            error_code="rate_limit_exceeded",
            status_code=429
        )


# Configuration exceptions
class ConfigurationError(HeinerCastException):
    """Configuration error"""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            error_code="configuration_error",
            status_code=500,
            details=details
        )


class MissingAPIKeyError(ConfigurationError):
    """Required API key is not configured"""
    
    def __init__(self, service: str):
        super().__init__(message=f"{service} API key is not configured. Please add it in Settings.")


# Business logic exceptions
class BusinessLogicError(HeinerCastException):
    """Business logic violation"""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(
            message=message,
            error_code="business_logic_error",
            status_code=400,
            details=details
        )


class EpisodeDeletionError(BusinessLogicError):
    """Cannot delete episode"""
    
    def __init__(self, reason: str = "Only the last episode can be deleted"):
        super().__init__(message=f"Cannot delete episode: {reason}")


class InvalidStatusTransitionError(BusinessLogicError):
    """Invalid status transition"""
    
    def __init__(self, current_status: str, target_status: str):
        super().__init__(
            message=f"Cannot transition from '{current_status}' to '{target_status}'"
        )


class MaxCharactersExceededError(BusinessLogicError):
    """Maximum characters per project exceeded"""
    
    def __init__(self, max_count: int = 5):
        super().__init__(message=f"Maximum number of characters ({max_count}) exceeded")
