# Cache group router

from fastapi import APIRouter, HTTPException, Body
import logging
from typing import Optional, Dict

from app.api.managers.cache_manager import CacheManager
from app.api.managers.media_query import MediaQuery
from app.core.status import Status
from app.core.settings import settings
from app.api.models.response import APIResponse
from app.api.managers.media_manager import MediaManager
from app.api.models.media_models import MediaDbType, MediaItemGroupList
from app.api.models.search_request import SearchRequest

logger = logging.getLogger(__name__)
router = APIRouter()
media_manager = MediaManager(settings.MEDIA_LIBRARY)
cache_manager = CacheManager(settings.MEDIA_LIBRARY)

@router.get("/list", status_code=200)
async def list_cache():
    """List all cache contents"""
    try:
        logger.debug("Listing cache contents")
        result = cache_manager.list_cache()
        return APIResponse.success(
            data=result,
            message="Cache contents retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error listing cache: {str(e)}", exc_info=True)
        raise APIResponse.error(str(e))

@router.post("/add", status_code=200)
async def add_to_cache(data: Dict = Body(...)):
    """Add items to cache based on search criteria"""
    try:
        dry_run = data.pop("dry_run", False)
        logger.debug(f"Adding items to cache with data: {data} (dry_run: {dry_run})")
        
        # Use the media manager to search and add to cache
        result = cache_manager.add_to_cache(data, dry_run=dry_run)
            
        return APIResponse.success(
            data=result,
            message="Items would be added to cache successfully" if dry_run else "Items added to cache successfully"
        )
    except Exception as e:
        logger.error(f"Error adding to cache: {str(e)}", exc_info=True)
        raise APIResponse.error(str(e))
