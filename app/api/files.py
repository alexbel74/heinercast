"""
Files API Endpoints
"""
import os
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.episode import Episode
from app.models.project import Project
from app.core.dependencies import get_current_user, verify_episode_ownership
from app.core.exceptions import NotFoundError
from app.services.storage_service import StorageService
from app.config import get_settings

settings = get_settings()
router = APIRouter()


@router.get("/audio/{episode_id}")
async def get_audio(
    episode: Episode = Depends(verify_episode_ownership),
    format: str = "final"  # "final", "voice", "music"
):
    """Get episode audio file"""
    if format == "final":
        url = episode.final_audio_url or episode.voice_audio_url
    elif format == "voice":
        url = episode.voice_audio_url
    elif format == "music":
        url = episode.music_url
    else:
        raise HTTPException(status_code=400, detail="Invalid format")
    
    if not url:
        raise NotFoundError("Audio file")
    
    # Convert to absolute path
    if url.startswith("/storage/"):
        file_path = os.path.join(settings.storage_path, url[9:])
    else:
        raise NotFoundError("Audio file")
    
    if not os.path.exists(file_path):
        raise NotFoundError("Audio file")
    
    filename = f"episode_{episode.episode_number}_{format}.mp3"
    
    return FileResponse(
        path=file_path,
        media_type="audio/mpeg",
        filename=filename,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/cover/{episode_id}")
async def get_cover(
    episode: Episode = Depends(verify_episode_ownership),
    variant: Optional[int] = None
):
    """Get episode cover image"""
    url = episode.cover_url
    
    # If variant specified and variants exist
    if variant is not None and episode.cover_variants_json:
        variants = episode.cover_variants_json
        if 0 <= variant < len(variants):
            url = variants[variant].get("url")
    
    if not url:
        raise NotFoundError("Cover image")
    
    # Convert to absolute path
    if url.startswith("/storage/"):
        file_path = os.path.join(settings.storage_path, url[9:])
    else:
        raise NotFoundError("Cover image")
    
    if not os.path.exists(file_path):
        raise NotFoundError("Cover image")
    
    # Determine media type from extension
    ext = os.path.splitext(file_path)[1].lower()
    media_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp"
    }
    media_type = media_types.get(ext, "image/png")
    
    filename = f"cover_episode_{episode.episode_number}{ext}"
    
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename
    )


@router.post("/upload/reference")
async def upload_reference_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload a reference image for cover generation"""
    # Validate file type
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )
    
    # Validate file size (max 10MB)
    max_size = 10 * 1024 * 1024
    contents = await file.read()
    if len(contents) > max_size:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 10MB"
        )
    
    # Save file
    storage_service = StorageService(
        current_user.storage_type,
        current_user.google_drive_credentials
    )
    
    # Get extension from content type
    ext_map = {
        "image/png": "png",
        "image/jpeg": "jpg",
        "image/jpg": "jpg",
        "image/webp": "webp"
    }
    extension = ext_map.get(file.content_type, "jpg")
    
    url = await storage_service.save_file(
        contents,
        subfolder="references",
        extension=extension
    )
    
    return {
        "url": url,
        "filename": file.filename,
        "size": len(contents)
    }


@router.get("/stream/{episode_id}")
async def stream_audio(
    episode: Episode = Depends(verify_episode_ownership)
):
    """Stream episode audio"""
    url = episode.final_audio_url or episode.voice_audio_url
    
    if not url:
        raise NotFoundError("Audio file")
    
    # Convert to absolute path
    if url.startswith("/storage/"):
        file_path = os.path.join(settings.storage_path, url[9:])
    else:
        raise NotFoundError("Audio file")
    
    if not os.path.exists(file_path):
        raise NotFoundError("Audio file")
    
    file_size = os.path.getsize(file_path)
    
    def iterfile():
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                yield chunk
    
    return StreamingResponse(
        iterfile(),
        media_type="audio/mpeg",
        headers={
            "Content-Length": str(file_size),
            "Accept-Ranges": "bytes"
        }
    )


@router.get("/project/{project_id}/cover")
async def get_project_cover(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get project cover image"""
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id
        )
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise NotFoundError("Project", str(project_id))
    
    if not project.cover_url:
        raise NotFoundError("Cover image")
    
    # Convert to absolute path
    if project.cover_url.startswith("/storage/"):
        file_path = os.path.join(settings.storage_path, project.cover_url[9:])
    else:
        raise NotFoundError("Cover image")
    
    if not os.path.exists(file_path):
        raise NotFoundError("Cover image")
    
    ext = os.path.splitext(file_path)[1].lower()
    media_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg"
    }
    media_type = media_types.get(ext, "image/png")
    
    return FileResponse(
        path=file_path,
        media_type=media_type
    )


@router.delete("/audio/{episode_id}")
async def delete_audio(
    episode: Episode = Depends(verify_episode_ownership),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete episode audio files"""
    storage_service = StorageService(
        current_user.storage_type,
        current_user.google_drive_credentials
    )
    
    deleted = []
    
    # Delete voice audio
    if episode.voice_audio_url:
        await storage_service.delete_file(episode.voice_audio_url)
        deleted.append("voice_audio")
        episode.voice_audio_url = None
        episode.voice_audio_duration_seconds = None
        episode.voice_timestamps_json = None
    
    # Delete sounds
    if episode.sounds_json:
        for sound in episode.sounds_json:
            if sound.get("url"):
                await storage_service.delete_file(sound["url"])
        deleted.append("sounds")
        episode.sounds_json = None
    
    # Delete music
    if episode.music_url:
        await storage_service.delete_file(episode.music_url)
        deleted.append("music")
        episode.music_url = None
        episode.music_composition_plan = None
    
    # Delete final audio
    if episode.final_audio_url:
        await storage_service.delete_file(episode.final_audio_url)
        deleted.append("final_audio")
        episode.final_audio_url = None
        episode.final_audio_duration_seconds = None
    
    return {"message": "Audio files deleted", "deleted": deleted}
