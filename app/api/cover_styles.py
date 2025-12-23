from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID

from app.database import get_db
from app.models.cover_style import CoverStyle
from app.api.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/cover-styles", tags=["cover-styles"])


class CoverStyleSchema(BaseModel):
    id: Optional[UUID] = None
    key: str
    name: str
    emoji: str = '🎨'
    instructions: str
    mood: str
    is_active: bool = True
    sort_order: int = 0

    class Config:
        from_attributes = True


class CoverStyleCreate(BaseModel):
    key: str
    name: str
    emoji: str = '🎨'
    instructions: str
    mood: str
    sort_order: int = 0


class CoverStyleUpdate(BaseModel):
    name: Optional[str] = None
    emoji: Optional[str] = None
    instructions: Optional[str] = None
    mood: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


@router.get("", response_model=List[CoverStyleSchema])
async def get_cover_styles(
    active_only: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """Get all cover styles"""
    query = select(CoverStyle)
    if active_only:
        query = query.where(CoverStyle.is_active == True)
    query = query.order_by(CoverStyle.sort_order)
    
    result = await db.execute(query)
    styles = result.scalars().all()
    return styles


@router.post("", response_model=CoverStyleSchema)
async def create_cover_style(
    style: CoverStyleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new cover style"""
    # Check if key exists
    existing = await db.execute(
        select(CoverStyle).where(CoverStyle.key == style.key)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Style key already exists")
    
    new_style = CoverStyle(**style.model_dump())
    db.add(new_style)
    await db.commit()
    await db.refresh(new_style)
    return new_style


@router.put("/{style_id}", response_model=CoverStyleSchema)
async def update_cover_style(
    style_id: UUID,
    style_update: CoverStyleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a cover style"""
    result = await db.execute(
        select(CoverStyle).where(CoverStyle.id == style_id)
    )
    style = result.scalar_one_or_none()
    if not style:
        raise HTTPException(status_code=404, detail="Style not found")
    
    update_data = style_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(style, key, value)
    
    await db.commit()
    await db.refresh(style)
    return style


@router.delete("/{style_id}")
async def delete_cover_style(
    style_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a cover style"""
    result = await db.execute(
        select(CoverStyle).where(CoverStyle.id == style_id)
    )
    style = result.scalar_one_or_none()
    if not style:
        raise HTTPException(status_code=404, detail="Style not found")
    
    if style.key == 'auto':
        raise HTTPException(status_code=400, detail="Cannot delete 'auto' style")
    
    await db.delete(style)
    await db.commit()
    return {"status": "deleted"}
