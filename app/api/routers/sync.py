import logging

from fastapi import APIRouter, Body
from typing import Dict

from app.core.settings import settings
from app.api.models.response import APIResponse 
from app.api.managers.sync_manager import SyncManager
logger = logging.getLogger(__name__)
router = APIRouter()
sync_manager = SyncManager(settings.MEDIA_LIBRARY)

@router.post("/", status_code=200)
async def sync_cache(data: Dict = Body(...)):
    """Sync the cache with the media library"""
    try:
        logger.debug("Syncing cache with media library")
        result = sync_manager.sync()
        return APIResponse.success(
            data=result,
            message="Cache synced successfully"
        )
    except Exception as e:
        logger.error(f"Error syncing cache: {str(e)}", exc_info=True)
        raise APIResponse.error(str(e))
