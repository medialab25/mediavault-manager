from app.api.adapters.jellyfin import JellyfinClient
from app.core.status import Status
from app.core.settings import settings
import logging

logger = logging.getLogger(__name__)

class MediaServer:
    def __init__(self):
        """
        Initialize MediaServer with Jellyfin configuration from settings.
        """
        self.jellyfin_client = JellyfinClient(
            url=settings.JELLYFIN["url"],
            api_key=settings.JELLYFIN["api_key"]
        )
        
    async def refresh_media(self):
        """Refresh the media library by calling the Media Library API."""
        try:
            logger.debug("Calling Jellyfin refresh_media")
            response = await self.jellyfin_client.refresh_media()
            logger.debug(f"Jellyfin refresh response: {response}")
            return response
        except Exception as e:
            logger.error(f"Error refreshing media library: {str(e)}")
            return {
                "status": Status.ERROR,
                "message": f"Failed to refresh media library: {str(e)}",
                "error": str(e)
            } 
        
