from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from app.api.managers.media_server import MediaServer
from app.core.settings import settings
from app.core.status import Status
import httpx
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/serve",
    tags=["media-server"],
    responses={404: {"description": "Not found"}},
)

def get_media_server() -> MediaServer:
    """Dependency to get MediaServer instance"""
    return MediaServer()

@router.get("/recent", response_model=Dict[str, Any])
async def get_recently_viewed(
    limit: int = 20,
    media_server: MediaServer = Depends(get_media_server)
) -> Dict[str, Any]:
    """
    Get recently viewed media items.
    
    Args:
        limit: Maximum number of items to return (default: 20)
        
    Returns:
        Dict containing recently viewed items and status information
    """
    try:
        response = await media_server.get_recently_viewed(limit=limit)
        if response["status"] == Status.ERROR:
            raise HTTPException(
                status_code=500,
                detail=response["message"]
            )
        return response
    except httpx.ConnectError as e:
        logger.error(f"Connection error while getting recently viewed items: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Could not connect to Jellyfin server. Please check if the server is running and accessible."
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error from Jellyfin API: {e.response.status_code} - {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Jellyfin API error: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"Error getting recently viewed items: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recently viewed items: {str(e)}"
        )

@router.post("/refresh", response_model=Dict[str, Any])
async def refresh_media(
    media_server: MediaServer = Depends(get_media_server)
) -> Dict[str, Any]:
    """
    Refresh the media library.
    
    Returns:
        Dict containing refresh status information
    """
    try:
        response = await media_server.refresh_media()
        if response["status"] == Status.ERROR:
            raise HTTPException(
                status_code=500,
                detail=response["message"]
            )
        return response
    except httpx.ConnectError as e:
        logger.error(f"Connection error while refreshing media: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Could not connect to Jellyfin server. Please check if the server is running and accessible."
        )
    except Exception as e:
        logger.error(f"Error refreshing media: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh media: {str(e)}"
        )

@router.get("/watched", response_model=Dict[str, Any])
async def get_watched_items(
    media_server: MediaServer = Depends(get_media_server)
) -> Dict[str, Any]:
    """
    Get watched media items.
    
    Returns:
        Dict containing watched items and status information
    """
    try:
        response = await media_server.get_watched_items()
        if response["status"] == Status.ERROR:
            raise HTTPException(
                status_code=500,
                detail=response["message"]
            )
        return response
    except httpx.ConnectError as e:
        logger.error(f"Connection error while getting watched items: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Could not connect to Jellyfin server. Please check if the server is running and accessible."
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error from Jellyfin API: {e.response.status_code} - {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Jellyfin API error: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"Error getting watched items: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get watched items: {str(e)}"
        ) 