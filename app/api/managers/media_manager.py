# Management of media using the file_manager class
from pathlib import Path
from app.api.managers.models.media_models import ExtendedMediaInfo, MediaGroupFolder, MediaGroupFolderList, MediaFileItem, MediaItemFolder
from app.api.models.media_data import MediaItem, MediaItemGroup
from app.api.models.search_request import SearchRequest
from app.core.config import Config
from typing import Any, Optional, Tuple
import re

class MediaManager:
    def __init__(self, config: dict[str, Any]):
        self.media_base_path = Path(config.get("default_source_path"))
        self.config = config

    def _parse_episode_info(self, filename: str) -> Tuple[Optional[int], Optional[int]]:
        """Parse season and episode numbers from filename.
        
        Expected format: "{Series Title} - S{season:00}E{episode:00} - {Episode Title} {Quality Full}"
        Example: "Breaking Bad - S01E02 - Cat's in the Bag... 2160p"
        
        Returns:
            Tuple[Optional[int], Optional[int]]: Season and episode numbers, or None if not found
        """
        pattern = r'.*?S(\d{2})E(\d{2}).*'
        match = re.match(pattern, filename, re.IGNORECASE)
        
        if match:
            season = int(match.group(1))
            episode = int(match.group(2))
            return season, episode
        
        return None, None

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
                        path=str(group_folder),
                        media_folder_items=[]
                    ))
                    
        return MediaGroupFolderList(groups=media_groups)


    def get_media_group_folders_with_items(self, add_extended_info: bool = False) -> MediaGroupFolderList:
        """Get all media group folders with items based on the source matrix configuration.
        
        Returns:
            MediaGroupFolderList: List of media group folder paths with items
        """
        media_groups = self.get_media_group_folders()
        self.populate_media_group_folders_with_items(media_groups, add_extended_info)
        return media_groups
    
    def populate_media_group_folders_with_items(self, media_group_folders: MediaGroupFolderList, add_extended_info: bool = False) -> None:
        """Get all media group folders with items based on the source matrix configuration.
        
        Returns:
            MediaGroupFolderList: List of media group folder paths with items
        """
        for media_group in media_group_folders.groups:
            path = media_group.path
            
            # Get the media items from the folder
            media_folder_items = []
            for folder in Path(path).glob("*"):
                if folder.is_dir():
                    media_folder_item = MediaItemFolder(
                        title=folder.name,
                        media_type=media_group.media_type,
                        path=str(folder),
                        items=[]
                    )
                    media_folder_items.append(media_folder_item)

                    # Get all files in folder
                    for file in folder.glob("**/*"):
                        extended = None
                        if add_extended_info:
                            extended = ExtendedMediaInfo(
                                size=file.stat().st_size,
                                created_at=file.stat().st_ctime,
                                updated_at=file.stat().st_mtime,
                                metadata=None)

                        season, episode = self._parse_episode_info(file.name)
                        media_folder_item.items.append(MediaFileItem(
                            path=str(file),
                            season=season,
                            episode=episode,
                            extended=extended))
                            
            media_group.media_folder_items = media_folder_items
    

    def find_media(self, title: str, season: Optional[int] = None, episode: Optional[int] = None, media_prefix: Optional[str] = None, quality: Optional[str] = None, media_type: Optional[str] = None, search_cache: bool = False) -> list[str]:
        """Find media in cache by title and optional parameters"""

        # Get all media group folders
        media_groups = self.get_media_group_folders()

        filtered_media_groups = []
        # Search for the media in the cache
        for media_group in media_groups.groups:
            # Use the media_type from the MediaGroupFolder object
            if media_type and media_type != media_group.media_type:
                continue

            # Check if the media_prefix matches
            if media_prefix and media_prefix != media_group.media_prefix:
                continue

            # Check if the quality matches
            if quality and quality != media_group.quality:
                continue

            # Get the media items
            filtered_media_groups.append(media_group)

        # return the media group names
        return [media_group.media_prefix for media_group in filtered_media_groups]

    async def search_media(self, request: SearchRequest) -> MediaItemGroup:
        """Search media in cache by title and optional parameters"""
        # Return dummy data for now
        return MediaItemGroup(
            items=[
                MediaItem(
                    id="dummy-1",
                    full_path="/dummy/path/1",
                    media_type="movie",
                    quality="4k"
                ),
                MediaItem(
                    id="dummy-2", 
                    full_path="/dummy/path/2",
                    media_type="tv",
                    quality="hd"
                )
            ]
        )
