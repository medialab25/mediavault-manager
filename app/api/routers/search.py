from fastapi import APIRouter, HTTPException, Query
import logging

from app.core.status import Status
from app.core.settings import settings
from app.api.models.search_request import SearchRequest
from app.api.models.response import APIResponse
from app.api.managers.media_manager import MediaManager


logger = logging.getLogger(__name__)
router = APIRouter()
media_manager = MediaManager(settings.MEDIA_LIBRARY)

@router.get("/", status_code=200)
async def search_media(
    query: str = Query(None, description="Search query string"),
    media_type: str = Query(None, description="Media type (tv,movie)"),
    quality: str = Query(None, description="Quality (hd,uhd,4k)"),
    id: str = Query(None, description="Media ID to search for")
):
    """Search the media library by calling the Media Library API."""
    try:
        logger.debug("Starting media search")
        request = SearchRequest(
            query=query or "",  # Convert None to empty string
            media_type=media_type,
            quality=quality,
            id=id
        )
        result = await media_manager.search_media(request)
        logger.debug(f"Media search completed: {result}")
        return APIResponse.success(
            data=result,
            message="Media search completed successfully"
        )
    except Exception as e:
        logger.error(f"Error during media search: {str(e)}", exc_info=True)
        raise APIResponse.error(str(e)) 