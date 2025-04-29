from fastapi import APIRouter, HTTPException
import logging

from app.api.media.services.media_server import MediaServer
from .models.media_models import MediaItem, MediaItemFolder, MediaGroupFolder
from .models.status import Status
from .services.media_merger import MediaMerger
from .api.validators import validate_media_library_config, validate_media_merge_settings
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()
media_server = MediaServer(
    jellyfin_url=settings.JELLYFIN["url"],
    jellyfin_api_key=settings.JELLYFIN["api_key"]
)

@router.post("/refresh", status_code=200)
async def refresh_media():
    """Refresh the media library by calling the Media Library API."""
    try:
        logger.debug("Starting media refresh")
        result = await media_server.refresh_media()
        logger.debug(f"Media refresh completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Error during media refresh: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/merge", status_code=200)
async def merge_media(refresh: bool = False) -> dict:
    """Merge the media library by calling the Media Merge API.
    
    Args:
        refresh (bool): If True, refresh the media library after merging. Defaults to False.
    """
    try:
        logger.debug("Starting media merge")
        
        # Validate settings
        validate_media_merge_settings(settings.MEDIA_LIBRARY, settings.MEDIA_MERGE)
        
        # Get user and group IDs
        user_id = int(settings.MEDIA_MERGE["user"])
        group_id = int(settings.MEDIA_MERGE["group"])
        
        # Create MediaMerger instance
        media_merger = MediaMerger(user_id=user_id, group_id=group_id)
        
        # Call merge_libraries for each media type
        results = {}
        for media_type, config in settings.MEDIA_LIBRARY["source_matrix"].items():
            result = media_merger.merge_libraries(
                media_type=media_type,
                source_paths=[settings.MEDIA_LIBRARY["default_source_path"]],
                quality_list=config["quality_order"],
                merged_path=config["merged_path"]
            )
            results[media_type] = result
        
        logger.debug(f"Media merge completed: {results}")
        
        # Refresh media if requested
        refresh_result = None
        if refresh:
            refresh_result = await media_server.refresh_media()
            logger.debug(f"Media refresh completed: {refresh_result}")
            
        return {
            "status": Status.SUCCESS,
            "message": "Media merge completed successfully",
            "data": {
                "merge": results,
                "refresh": refresh_result if refresh else None
            }
        }
    except Exception as e:
        logger.error(f"Error during media merge: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    


# @router.get("/cache/list", status_code=200)
# async def get_cache_list():
#     """Get the cache list by calling the Media Cache API."""
#     try:
#         logger.debug("Starting cache list")
#         result = await media_service.get_cache_list()
#         logger.debug(f"Cache list completed: {result}")
#         return result
#     except Exception as e:
#         logger.error(f"Error during cache list: {str(e)}", exc_info=True)
#         raise HTTPException(status_code=500, detail=str(e))

# @router.get("/", response_model=List[Media])
# async def list_media():
#     """List all media items in the library."""
#     try:
#         media_items = media_service.scan_directory(settings.MEDIA_ROOT)
#         return media_items
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e)) 