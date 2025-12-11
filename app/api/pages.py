"""
Web Pages Router - HTML pages
"""
import os
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.models.user import User
from app.core.dependencies import get_current_user_optional

router = APIRouter()

# Templates directory
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir) if os.path.exists(templates_dir) else None


def get_template_response(
    request: Request,
    template_name: str,
    context: dict = None
) -> HTMLResponse:
    """Helper to render templates with common context"""
    if templates is None:
        return HTMLResponse(content="<h1>Templates not configured</h1>", status_code=500)
    
    ctx = {"request": request}
    if context:
        ctx.update(context)
    
    return templates.TemplateResponse(template_name, ctx)


@router.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Home page"""
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    
    return get_template_response(request, "index.html", {"user": user})


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Login page"""
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    
    return get_template_response(request, "login.html")


@router.get("/register", response_class=HTMLResponse)
async def register_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Registration page"""
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    
    return get_template_response(request, "register.html")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """User dashboard"""
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    return get_template_response(request, "dashboard.html", {"user": user})


@router.get("/projects/{project_id}", response_class=HTMLResponse)
async def project_page(
    request: Request,
    project_id: str,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Project detail page"""
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    return get_template_response(
        request, 
        "project.html", 
        {"user": user, "project_id": project_id}
    )


@router.get("/episodes/{episode_id}", response_class=HTMLResponse)
async def episode_page(
    request: Request,
    episode_id: str,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Episode detail page"""
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    return get_template_response(
        request, 
        "episode.html", 
        {"user": user, "episode_id": episode_id}
    )


@router.get("/voices", response_class=HTMLResponse)
async def voices_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Voice library page"""
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    return get_template_response(request, "voices.html", {"user": user})


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """User settings page"""
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    return get_template_response(request, "settings.html", {"user": user})
