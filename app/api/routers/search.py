from fastapi import APIRouter, HTTPException, Query
import logging
from typing import List

from app.core.status import Status
from app.core.settings import settings
from app.api.models.search_request import SearchRequest
from app.api.models.response import APIResponse
from app.api.managers.media_manager import MediaManager
from app.api.models.media_models import MediaDbType


logger = logging.getLogger(__name__)
router = APIRouter()
media_manager = MediaManager(settings.MEDIA_LIBRARY)

@router.get("/", status_code=200)
def search_media(
    query: str = Query(None, description="Search query string"),
    media_type: str = Query(None, description="Media type (tv,movie)"),
    quality: str = Query(None, description="Quality (hd,uhd,4k)"),
    id: str = Query(None, description="Media ID to search for"),
    season: int = Query(None, description="Season number"),
    episode: int = Query(None, description="Episode number"),
    db_type: str = Query("media", description="Comma-separated list of database types (media,cache,pending)")
):
    """Search the media library by calling the Media Library API."""
    try:
        logger.debug("Starting media search")
        
        # Parse comma-separated db_type string into list of MediaDbType
        db_types = []
        for db_type_str in db_type.split(","):
            try:
                db_types.append(MediaDbType(db_type_str.strip()))
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid database type '{db_type_str}'. Valid types are: {', '.join(t.value for t in MediaDbType)}"
                )
        
        request = SearchRequest(
            query=query or "",  # Convert None to empty string
            media_type=media_type,
            quality=quality,
            id=id,
            season=season,
            episode=episode,
            db_type=db_types
        )
        result = media_manager.search_media(request)
        logger.debug(f"Media search completed: {result}")
        return APIResponse.success(
            data=result,
            message="Media search completed successfully"
        )
    except Exception as e:
        logger.error(f"Error during media search: {str(e)}", exc_info=True)
        raise APIResponse.error(str(e)) 