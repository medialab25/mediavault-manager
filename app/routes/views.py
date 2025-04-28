from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from pathlib import Path
from datetime import datetime

from app.core.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard")
async def dashboard(request: Request):
    return templates.TemplateResponse(
        "pages/dashboard.html",
        {
            "request": request,
            "title": "Dashboard",
            "config": settings,
            "now": datetime.now()
        }
    )

@router.get("/profile")
async def profile(request: Request):
    return templates.TemplateResponse(
        "pages/profile.html",
        {
            "request": request,
            "title": "Profile",
            "config": settings,
            "now": datetime.now()
        }
    ) 