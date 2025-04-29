from fastapi import APIRouter, HTTPException
from typing import List
import logging

from app.api.media.services.media_server import MediaServer
from .models.media_models import MediaItem, MediaItemFolder, MediaGroupFolder
from .services.media_service import MediaService
from .services.media_merger import merge_libraries
from .api.validators import validate_media_library_config
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
async def merge_media(refresh: bool = False):
    """Merge the media library by calling the Media Merge API.
    
    Args:
        refresh (bool): If True, refresh the media library after merging. Defaults to False.
    """
    try:
        logger.debug("Starting media merge")
        
        # Get media library config from settings
        media_library_config = settings.MEDIA_LIBRARY
        if not media_library_config:
            raise HTTPException(status_code=500, detail="Media library configuration not found")
            
        # Get user and group IDs from media merge settings
        if "user" not in settings.MEDIA_MERGE or "group" not in settings.MEDIA_MERGE:
            raise HTTPException(status_code=500, detail="Media merge user/group configuration not found")
        user_id = int(settings.MEDIA_MERGE["user"])
        group_id = int(settings.MEDIA_MERGE["group"])
        
        # Validate media library configuration
        validate_media_library_config(media_library_config)
        
        # Call merge_libraries for each media type
        results = {}
        for media_type, config in media_library_config["source_matrix"].items():
            result = await merge_libraries(
                media_type=media_type,
                source_paths=[media_library_config["default_source_path"]],
                quality_list=config["quality_order"],
                merged_path=config["merged_path"],
                user_id=user_id,
                group_id=group_id
            )
            results[media_type] = result
        
        logger.debug(f"Media merge completed: {results}")
        
        # Refresh media if requested
        if refresh:
            await media_server.refresh_media()
            
        return results
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