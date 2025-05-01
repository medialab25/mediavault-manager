from fastapi import HTTPException
from typing import Dict, Any

def validate_media_library_config(media_library_config: Dict[str, Any]) -> None:
    """Validate the media library configuration.
    
    Args:
        media_library_config: The media library configuration dictionary
        
    Raises:
        HTTPException: If the configuration is invalid
    """
    # Validate required fields
    if not all(field in media_library_config for field in ["default_source_path", "source_matrix"]):
        raise HTTPException(
            status_code=500,
            detail="Missing required media library configuration fields"
        )

    source_matrix = media_library_config["source_matrix"]
    if not isinstance(source_matrix, dict):
        raise HTTPException(status_code=500, detail="source_matrix must be a dictionary")

    # Validate each media type configuration
    for media_type, config in source_matrix.items():
        if not isinstance(config, dict) or not all(field in config for field in ["quality_order", "merged_path"]):
            raise HTTPException(
                status_code=500,
                detail=f"Invalid configuration for media type {media_type}"
            )

        if not isinstance(config["quality_order"], list) or not config["quality_order"] or not config["merged_path"]:
            raise HTTPException(
                status_code=500,
                detail=f"Invalid quality_order or merged_path for {media_type}"
            )

def validate_media_merge_settings(media_library_config: Dict[str, Any], media_merge_settings: Dict[str, Any]) -> None:
    """Validate media library and merge settings.
    
    Args:
        media_library_config: The media library configuration dictionary
        media_merge_settings: The media merge settings dictionary
        
    Raises:
        HTTPException: If the configuration is invalid
    """
    if not media_library_config:
        raise HTTPException(status_code=500, detail="Media library configuration not found")
        
    if "user" not in media_merge_settings or "group" not in media_merge_settings:
        raise HTTPException(status_code=500, detail="Media merge user/group configuration not found")
        
    try:
        int(media_merge_settings["user"])
        int(media_merge_settings["group"])
    except ValueError:
        raise HTTPException(status_code=500, detail="Invalid user or group ID in media merge settings")
        
    validate_media_library_config(media_library_config) 