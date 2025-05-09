from fastapi import APIRouter, HTTPException
import logging

from app.api.managers.media_server import MediaServer
from app.api.managers.media_manager import MediaManager
from app.core.status import Status
from app.core.settings import settings
from app.api.models.response import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter()
media_server = MediaServer()
media_manager = MediaManager(settings.MEDIA_LIBRARY)

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

@router.post("/update", status_code=200)
async def update_media():
    """Update the media library by scanning for changes and updating metadata."""
    try:
        logger.debug("Starting media update")

        media_manager.request_media_library_update()

        result = {"status": "success", "message": "Media update completed"}
        logger.debug(f"Media update completed: {result}")
        return APIResponse.success(
            data=result,
            message="Media update completed successfully"
        )
    except Exception as e:
        logger.error(f"Error during media update: {str(e)}", exc_info=True)
        raise APIResponse.error(str(e))
  