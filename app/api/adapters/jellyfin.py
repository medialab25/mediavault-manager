import httpx
from typing import Optional, Dict, Any
from app.core.status import Status
import logging

logger = logging.getLogger(__name__)

class JellyfinClient:
    def __init__(self, url: str, api_key: str):
        self.base_url = url.rstrip('/')
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "X-MediaBrowser-Token": self.api_key,
                "Content-Type": "application/json"
            }
        )

    async def get_system_info(self) -> Dict[str, Any]:
        """Get Jellyfin system information"""
        response = await self.client.get("/System/Info")
        return response.json()

    async def get_libraries(self) -> Dict[str, Any]:
        """Get all Jellyfin libraries"""
        response = await self.client.get("/Library/MediaFolders")
        return response.json()

    async def get_items(
        self,
        parent_id: Optional[str] = None,
        include_item_types: Optional[str] = None,
        recursive: bool = True
    ) -> Dict[str, Any]:
        """Get items from Jellyfin library"""
        params = {
            "recursive": recursive
        }
        if parent_id:
            params["parentId"] = parent_id
        if include_item_types:
            params["includeItemTypes"] = include_item_types

        response = await self.client.get("/Items", params=params)
        return response.json()

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    async def refresh_media(self):
        """Refresh the media library"""
        try:
            response = await self.client.post("/Library/Refresh")
            if response.status_code == 204:  # No Content
                return {
                    "status": Status.SUCCESS,
                    "message": "Library refresh initiated"
                }
            
            # If we get here, the status code wasn't 204
            error_message = response.json() if response.content else "Unknown error"
            return {
                "status": Status.ERROR,
                "message": f"Failed to refresh media library: HTTP {response.status_code}",
                "error": error_message
            }
        except httpx.HTTPError as e:
            return {
                "status": Status.ERROR,
                "message": f"Failed to refresh media library: {str(e)}",
                "error": str(e)
            }
        except Exception as e:
            return {
                "status": Status.ERROR,
                "message": "An unexpected error occurred while refreshing media library",
                "error": str(e)
            } 