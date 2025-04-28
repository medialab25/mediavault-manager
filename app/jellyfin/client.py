import httpx
from typing import Optional, Dict, Any
from app.core.config import settings

class JellyfinClient:
    def __init__(self):
        self.base_url = settings.JELLYFIN_URL
        self.api_key = settings.JELLYFIN_API_KEY
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