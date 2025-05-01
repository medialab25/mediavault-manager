from app.api.adapters.jellyfin import JellyfinClient
from app.core.status import Status
import logging

logger = logging.getLogger(__name__)

class MediaServer:
    def __init__(self, jellyfin_url: str, jellyfin_api_key: str):
        """
        Initialize MediaServer with Jellyfin configuration.
        
        Args:
            jellyfin_url (str): Jellyfin server URL
            jellyfin_api_key (str): Jellyfin API key
        """
        self.jellyfin_client = JellyfinClient(
            url=jellyfin_url,
            api_key=jellyfin_api_key
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