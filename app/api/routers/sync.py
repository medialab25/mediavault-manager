import logging

from fastapi import APIRouter, Body
from typing import Dict

from app.api.models.media_models import SyncDetailRequest
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
        dry_run = data.get("dry_run", False)    
        details = data.get("details", SyncDetailRequest.NONE)
        force = data.get("force", False)
        logger.debug(f"Syncing cache with media library{' (dry run)' if dry_run else ''}")
        result = await sync_manager.sync(dry_run=dry_run, details=details, force=force)
        return APIResponse.success(
            data=result,
            message="Cache would be synced successfully" if dry_run else "Cache synced successfully"
        )
    except Exception as e:
        logger.error(f"Error syncing cache: {str(e)}", exc_info=True)
        raise APIResponse.error(str(e))
