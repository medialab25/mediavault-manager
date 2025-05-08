from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager
import logging
import sys

from app.core.settings import settings
from app.api.routers import views
from app.api.routers.media import router as media_router
from app.api.routers.search import router as search_router
from app.api.routers.cache import router as cache_router
from app.api.routers.sync import router as sync_router
from app.api.routers.system import router as system_router
from app.scheduler import start_scheduler, stop_scheduler

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/mediavault-manager.log')
    ]
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    tasks = settings.TASKS
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
app.include_router(system_router, prefix="/api/system", tags=["system"])
app.include_router(media_router, prefix="/api/media", tags=["media"])
app.include_router(search_router, prefix="/api/search", tags=["search"])
app.include_router(cache_router, prefix="/api/cache", tags=["cache"])
app.include_router(sync_router, prefix="/api/sync", tags=["sync"])

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