"""
HeinerCast Pydantic Schemas
"""
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserLogin,
    UserUpdate,
    UserResponse,
    UserSettingsLLM,
    UserSettingsElevenLabs,
    UserSettingsKieAI,
    UserSettingsStorage,
    UserSettingsPrompts,
    UserSettingsResponse,
    TokenResponse,
    TokenRefresh,
    PasswordChange
)

from app.schemas.voice import (
    VoiceBase,
    VoiceCreate,
    VoiceUpdate,
    VoiceResponse,
    VoiceTestRequest,
    VoiceTestResponse
)

from app.schemas.project import (
    ProjectBase,
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectDetailResponse,
    ProjectListResponse,
    ProjectCharacterBase,
    ProjectCharacterCreate,
    ProjectCharacterUpdate,
    ProjectCharacterResponse
)

from app.schemas.episode import (
    EpisodeBase,
    EpisodeCreate,
    EpisodeUpdate,
    EpisodeResponse,
    EpisodeDetailResponse,
    EpisodeListResponse,
    EpisodeScriptUpdate,
    EpisodeContinuationCreate,
    ScriptLine,
    ScriptContent,
    SoundEffect,
    CoverVariant
)

from app.schemas.generation import (
    GenerateScriptRequest,
    GenerateScriptResponse,
    GenerateVoiceoverRequest,
    GenerateVoiceoverResponse,
    GenerateSoundsRequest,
    GenerateSoundsResponse,
    GenerateMusicRequest,
    GenerateMusicResponse,
    MergeAudioRequest,
    MergeAudioResponse,
    GenerateCoverRequest,
    GenerateCoverResponse,
    SelectCoverRequest,
    GenerateFullRequest,
    GenerateFullResponse,
    GenerationStatusResponse
)

from app.schemas.api_key import (
    APIKeyBase,
    APIKeyCreate,
    APIKeyResponse,
    APIKeyCreateResponse,
    APIKeyListResponse
)

__all__ = [
    # User schemas
    "UserBase",
    "UserCreate",
    "UserLogin",
    "UserUpdate",
    "UserResponse",
    "UserSettingsLLM",
    "UserSettingsElevenLabs",
    "UserSettingsKieAI",
    "UserSettingsStorage",
    "UserSettingsPrompts",
    "UserSettingsResponse",
    "TokenResponse",
    "TokenRefresh",
    "PasswordChange",
    
    # Voice schemas
    "VoiceBase",
    "VoiceCreate",
    "VoiceUpdate",
    "VoiceResponse",
    "VoiceTestRequest",
    "VoiceTestResponse",
    
    # Project schemas
    "ProjectBase",
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "ProjectDetailResponse",
    "ProjectListResponse",
    "ProjectCharacterBase",
    "ProjectCharacterCreate",
    "ProjectCharacterUpdate",
    "ProjectCharacterResponse",
    
    # Episode schemas
    "EpisodeBase",
    "EpisodeCreate",
    "EpisodeUpdate",
    "EpisodeResponse",
    "EpisodeDetailResponse",
    "EpisodeListResponse",
    "EpisodeScriptUpdate",
    "EpisodeContinuationCreate",
    "ScriptLine",
    "ScriptContent",
    "SoundEffect",
    "CoverVariant",
    
    # Generation schemas
    "GenerateScriptRequest",
    "GenerateScriptResponse",
    "GenerateVoiceoverRequest",
    "GenerateVoiceoverResponse",
    "GenerateSoundsRequest",
    "GenerateSoundsResponse",
    "GenerateMusicRequest",
    "GenerateMusicResponse",
    "MergeAudioRequest",
    "MergeAudioResponse",
    "GenerateCoverRequest",
    "GenerateCoverResponse",
    "SelectCoverRequest",
    "GenerateFullRequest",
    "GenerateFullResponse",
    "GenerationStatusResponse",
    
    # API Key schemas
    "APIKeyBase",
    "APIKeyCreate",
    "APIKeyResponse",
    "APIKeyCreateResponse",
    "APIKeyListResponse",
]
