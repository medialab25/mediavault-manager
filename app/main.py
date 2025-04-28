from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from datetime import datetime

from app.core.config import settings
from app.routes import views, media

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(views.router)
app.include_router(media.router, prefix="/media")

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(
        "pages/home.html",
        {
            "request": request,
            "title": "Home",
            "config": settings,
            "now": datetime.now()
        }
    ) 