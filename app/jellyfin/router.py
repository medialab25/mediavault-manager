from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, AsyncGenerator
from app.jellyfin.client import JellyfinClient

router = APIRouter(prefix="/jellyfin", tags=["jellyfin"])

async def get_jellyfin_client() -> AsyncGenerator[JellyfinClient, None]:
    client = JellyfinClient()
    try:
        yield client
    finally:
        await client.close()

@router.get("/system")
async def get_system_info(client: JellyfinClient = Depends(get_jellyfin_client)) -> Dict[str, Any]:
    """Get Jellyfin system information"""
    try:
        return await client.get_system_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get Jellyfin system info: {str(e)}")

@router.get("/libraries")
async def get_libraries(client: JellyfinClient = Depends(get_jellyfin_client)) -> Dict[str, Any]:
    """Get all Jellyfin libraries"""
    try:
        return await client.get_libraries()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get Jellyfin libraries: {str(e)}")

@router.get("/items")
async def get_items(
    parent_id: str = None,
    include_item_types: str = None,
    recursive: bool = True,
    client: JellyfinClient = Depends(get_jellyfin_client)
) -> Dict[str, Any]:
    """Get items from Jellyfin library"""
    try:
        return await client.get_items(
            parent_id=parent_id,
            include_item_types=include_item_types,
            recursive=recursive
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get Jellyfin items: {str(e)}") 