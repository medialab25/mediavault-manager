from typing import List, Dict, Any
from fastapi import APIRouter
import logging

from app.core.status import Status
from app.core.settings import settings
from app.api.common.media_manager import MediaManager

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
        folders = media_manager.get_media_group_folders()
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
