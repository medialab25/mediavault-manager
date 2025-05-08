from fastapi import APIRouter, status
from datetime import datetime
import logging

from app.api.models.response import APIResponse
from app.api.managers.data_manager import DataManager
from app.core.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()
data_manager = DataManager(settings.MEDIA_LIBRARY)

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint to verify the system is running
    """
    try:
        logger.debug("Performing health check")
        return APIResponse.success(
            data={
                "timestamp": datetime.now().isoformat(),
                "media_library_update_request_count": data_manager.get_media_library_update_request()
            },
            message="System is healthy"
        )
    except Exception as e:
        logger.error(f"Error during health check: {str(e)}", exc_info=True)
        raise APIResponse.error(str(e)) 