from fastapi import APIRouter, status
from datetime import datetime
from app.api.models.response import APIResponse

router = APIRouter(tags=["system"])

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint to verify the system is running
    """
    return APIResponse.success(
        data={
            "timestamp": datetime.now().isoformat()
        },
        message="System is healthy"
    ) 