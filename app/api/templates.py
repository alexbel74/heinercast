from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID

from app.database import get_db
from app.models.project_template import ProjectTemplate
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/templates", tags=["templates"])

class TemplateCreate(BaseModel):
    name: str
    genre_tone: Optional[str] = None
    musical_atmosphere: Optional[str] = None
    include_sound_effects: bool = True
    include_background_music: bool = True
    target_duration_minutes: int = 10
    cover_style: Optional[str] = None
    characters_json: Optional[List[dict]] = None

class TemplateResponse(BaseModel):
    id: UUID
    name: str
    genre_tone: Optional[str]
    musical_atmosphere: Optional[str]
    include_sound_effects: bool
    include_background_music: bool
    target_duration_minutes: int
    cover_style: Optional[str]
    characters_json: Optional[List[dict]] = None
    
    class Config:
        from_attributes = True

@router.get("", response_model=List[TemplateResponse])
async def list_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(ProjectTemplate).where(ProjectTemplate.user_id == current_user.id)
    )
    return result.scalars().all()

@router.post("", response_model=TemplateResponse)
async def create_template(
    data: TemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    template = ProjectTemplate(
        user_id=current_user.id,
        name=data.name,
        genre_tone=data.genre_tone,
        musical_atmosphere=data.musical_atmosphere,
        include_sound_effects=data.include_sound_effects,
        include_background_music=data.include_background_music,
        target_duration_minutes=data.target_duration_minutes,
        cover_style=data.cover_style,
        characters_json=data.characters_json
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template

@router.delete("/{template_id}")
async def delete_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(ProjectTemplate).where(
            ProjectTemplate.id == template_id,
            ProjectTemplate.user_id == current_user.id
        )
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    await db.delete(template)
    await db.commit()
    return {"message": "Template deleted"}
