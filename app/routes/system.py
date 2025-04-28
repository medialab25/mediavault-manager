from fastapi import APIRouter, status
from datetime import datetime

router = APIRouter(tags=["system"])

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint to verify the system is running
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    } 