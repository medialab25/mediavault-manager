from fastapi import APIRouter, HTTPException
import logging

from app.api.managers.media_server import MediaServer
from app.core.status import Status
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
  