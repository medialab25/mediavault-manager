from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

from app.core.settings import settings
from app.api.routers import views, system
from app.api.routers.media import router as media_router
from app.api.routers.search import router as search_router
from app.api.routers.cache import router as cache_router
from app.scheduler import start_scheduler, stop_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    start_scheduler()
    yield
    stop_scheduler()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
#app.include_router(views.router)
#app.include_router(tasks.router)
app.include_router(system.router, prefix="/system")
app.include_router(media_router, prefix="/api/media", tags=["media"])
app.include_router(search_router, prefix="/api/search", tags=["search"])
app.include_router(cache_router, prefix="/api/cache", tags=["cache"])

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