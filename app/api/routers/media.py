from fastapi import APIRouter, HTTPException
import logging

from app.api.managers.media_server import MediaServer
from app.api.models.media_models import MediaFileItem, MediaItemFolder, MediaGroupFolder
from app.api.models.merge_models import MergeResult
from app.core.status import Status
from app.api.managers.media_merger import MediaMerger
from app.api.validators.validators import validate_media_merge_settings
from app.core.settings import settings
from app.api.models.response import APIResponse

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
        return APIResponse.success(
            data=result,
            message="Media refresh completed successfully"
        )
    except Exception as e:
        logger.error(f"Error during media refresh: {str(e)}", exc_info=True)
        raise APIResponse.error(str(e))
    
@router.post("/merge", status_code=200)
async def merge_media(refresh: bool = False, dry_run: bool = False) -> APIResponse:
    """Merge the media library by calling the Media Merge API.
    
    Args:
        refresh (bool): If True, refresh the media library after merging. Defaults to False.
        dry_run (bool): If True, only show what would be done without making changes. Defaults to False.
    """
    try:
        logger.debug("Starting media merge")
        logger.debug(f"Media library config: {settings.MEDIA_LIBRARY}")
        logger.debug(f"Media merge settings: {settings.MEDIA_MERGE}")
        
        # Validate settings
        try:
            validate_media_merge_settings(settings.MEDIA_LIBRARY, settings.MEDIA_MERGE)
        except HTTPException as e:
            logger.error(f"Validation error during media merge: {str(e.detail)}")
            raise APIResponse.error(str(e.detail))
        
        # Create MediaMerger instance
        media_merger = MediaMerger(settings.MEDIA_LIBRARY)
        results = media_merger.merge_libraries(dry_run=dry_run)
        
        # Refresh media if requested
        refresh_result = None
        if refresh:
            refresh_result = await media_server.refresh_media()
            logger.debug(f"Media refresh completed: {refresh_result}")

        return APIResponse.success(
            data={
                "merge": results.model_dump(),
                "refresh": refresh_result if refresh else None
            },
            message="Media merge completed successfully"
        )
    except Exception as e:
        logger.error(f"Error during media merge: {str(e)}", exc_info=True)
        raise APIResponse.error(str(e)) 