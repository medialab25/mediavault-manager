# Management of media using the file_manager class
from pathlib import Path
from app.api.common.models.media_models import MediaGroupFolder, MediaGroupFolderList
from app.core.config import Config
from typing import Any, Optional

class MediaManager:
    def __init__(self, config: dict[str, Any]):
        self.media_base_path = Path(config.get("default_source_path"))
        self.config = config

    # Get all media group folders using the source_matrix in the config
    def get_media_group_folders_slim(self) -> list[str]:
        """Get all media group folders based on the source matrix configuration.
        
        Returns:
            list[str]: List of media group folder paths
        """
        return [group.path for group in self.get_media_group_folders().groups]

# Get all media group folders using the source_matrix in the config
    def get_media_group_folders(self) -> MediaGroupFolderList:
        """Get all media group folders based on the source matrix configuration.
        
        Returns:
            MediaGroupFolderList: List of media group folder paths
        """
        source_matrix = self.config.get("source_matrix")
        media_groups = []
        
        for media_type_element, config in source_matrix.items():
            for quality in config["quality_order"]:
                media_type = config["media_type"] if config["media_type"] else media_type_element
                media_prefix = config["prefix"] if config["prefix"] else media_type_element
                group_folder = self.media_base_path / f"{media_prefix}-{quality}"
                if group_folder.exists():
                    media_groups.append(MediaGroupFolder(
                        media_type=media_type,
                        media_prefix=media_prefix,
                        quality=quality,
                        path=str(group_folder)
                    ))
                    
        return MediaGroupFolderList(groups=media_groups)

    def find_media(self, title: str, season: Optional[int] = None, episode: Optional[int] = None, group: Optional[str] = None, media_type: Optional[str] = None, search_cache: bool = False) -> list[str]:
        """Find media in cache by title and optional parameters"""

        # Get all media group folders
        media_groups = self.get_media_group_folders()

        # Search for the media in the cache
        for media_group in media_groups:
            # Use the media_type from the MediaGroupFolder object
            if media_type and media_type != media_group.media_type:
                continue

            #for file in Path(media_group.path).glob("**/*"):
            #    if file.is_file():
            #        if title in file.name:
            #            return [str(file)]