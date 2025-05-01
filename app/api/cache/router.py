from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query
import logging

from app.core.status import Status
from app.core.settings import settings
from app.api.managers.media_manager import MediaManager

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize cache manager with settings
    
@router.get("/list", status_code=200)
async def list_cache() -> Dict[str, Any]:
    """List all cache contents using MediaManager.
    
    Returns:
        Dict[str, Any]: Response containing status, message and data
    """
    try:
        media_manager = MediaManager(settings.MEDIA_LIBRARY)
        folders = media_manager.get_media_group_folders_slim()
        return {
            "status": Status.SUCCESS,
            "message": "Cache contents retrieved successfully",
            "data": folders if folders else []
        }
    except Exception as e:
        logger.error(f"Error listing cache: {str(e)}")
        return {
            "status": Status.ERROR,
            "message": f"Error retrieving cache contents: {str(e)}",
            "data": []
        }

@router.get("/find", status_code=200)
async def find_media(
    title: str = Query(..., description="Title to search for"),
    season: Optional[int] = Query(None, description="Season number"),
    episode: Optional[int] = Query(None, description="Episode number"),
    group: Optional[str] = Query(None, description="Release group"),
    media_type: Optional[str] = Query(None, description="Media type (tv,movie)"),
    search_cache: bool = Query(False, description="Search in cache")
) -> Dict[str, Any]:
    """Find media in cache by title and optional parameters"""
    try:
        media_manager = MediaManager(settings.MEDIA_LIBRARY)
        results = media_manager.find_media(title, season, episode, group, media_type, search_cache)
        return {
            "status": Status.SUCCESS,
            "message": "Media found successfully",
            "data": results if results else []
        }
    except Exception as e:
        logger.error(f"Error finding media: {str(e)}")
        return {
            "status": Status.ERROR,
            "message": f"Error finding media: {str(e)}",
            "data": []
        }
