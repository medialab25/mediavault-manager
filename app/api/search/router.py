from fastapi import APIRouter, HTTPException, Query
import logging

from app.core.status import Status
from app.core.settings import settings
from app.api.models.search_request import SearchRequest
from app.api.managers.media_manager import MediaManager


logger = logging.getLogger(__name__)
router = APIRouter()
media_manager = MediaManager(settings.MEDIA_LIBRARY)

@router.get("/", status_code=200)
async def search_media(
    query: str = Query(..., description="Search query string"),
    media_type: str = Query(None, description="Media type (tv,movie)"),
    quality: str = Query(None, description="Quality (hd,uhd,4k)")
):
    """Search the media library by calling the Media Library API."""
    try:
        logger.debug("Starting media search")
        request = SearchRequest(
            query=query,
            media_type=media_type,
            quality=quality
        )
        result = await media_manager.search_media(request)
        logger.debug(f"Media search completed: {result}")
        return {
            "status": Status.SUCCESS,
            "message": "Media search completed successfully",
            "data": result
        }
    except Exception as e:
        logger.error(f"Error during media search: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
