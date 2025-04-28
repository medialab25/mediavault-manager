from fastapi import APIRouter, HTTPException
from typing import List
import logging
from .models.media_models import Media
from .services.media_service import MediaService
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()
media_service = MediaService()

@router.post("/refresh", status_code=200)
async def refresh_media():
    """Refresh the media library by calling the Media Library API."""
    try:
        logger.debug("Starting media refresh")
        result = await media_service.refresh_media()
        logger.debug(f"Media refresh completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Error during media refresh: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    
# @router.get("/", response_model=List[Media])
# async def list_media():
#     """List all media items in the library."""
#     try:
#         media_items = media_service.scan_directory(settings.MEDIA_ROOT)
#         return media_items
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))