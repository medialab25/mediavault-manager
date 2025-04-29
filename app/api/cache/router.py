from fastapi import APIRouter, HTTPException
import logging

from app.core.status import Status
from app.core.settings import settings
from .services.cache_manager import CacheManager

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize cache manager with settings
cache_manager = CacheManager(
    hot_cache_path=settings.MEDIA_CACHE["hot_path"],
    cold_cache_path=settings.MEDIA_CACHE["cold_path"]
)

@router.get("/hot", status_code=200)
async def get_hot_cache():
    """Get the hot cache contents."""
    try:
        logger.debug("Getting hot cache contents")
        cache_contents = cache_manager.get_hot_cache()
        return {
            "status": Status.SUCCESS,
            "message": "Hot cache contents retrieved successfully",
            "data": {
                "hot_cache": cache_contents
            }
        }
    except Exception as e:
        logger.error(f"Error getting hot cache: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cold", status_code=200)
async def get_cold_cache():
    """Get the cold cache contents."""
    try:
        logger.debug("Getting cold cache contents")
        cache_contents = cache_manager.get_cold_cache()
        return {
            "status": Status.SUCCESS,
            "message": "Cold cache contents retrieved successfully",
            "data": {
                "cold_cache": cache_contents
            }
        }
    except Exception as e:
        logger.error(f"Error getting cold cache: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/all", status_code=200)
async def get_all_cache():
    """Get all cache contents (both hot and cold)."""
    try:
        logger.debug("Getting all cache contents")
        cache_contents = cache_manager.get_all_cache()
        return {
            "status": Status.SUCCESS,
            "message": "All cache contents retrieved successfully",
            "data": cache_contents
        }
    except Exception as e:
        logger.error(f"Error getting all cache: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) 