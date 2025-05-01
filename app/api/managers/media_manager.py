# Management of media using the file_manager class
from pathlib import Path
from app.api.managers.media_filter import MediaFilter
from app.api.models.media_models import (
    ExtendedMediaInfo, MediaDbType, MediaGroupFolder, MediaGroupFolderList,
    MediaFileItem, MediaItemFolder, MediaItem, MediaItemGroup
)
from app.api.models.search_request import SearchRequest
from app.core.config import Config
from typing import Any, List, Optional, Tuple
import re
import hashlib

class MediaManager:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        # Initialize paths from config
        self.media_base_path = Path(config.get("default_source_path"))
        self.cache_base_path = Path(config.get("cache_path"))
        self.cache_shadow_path = Path(config.get("cache_shadow_path"))
        self.cache_pending_path = Path(config.get("cache_pending_path"))

    def _generate_media_id(self, full_path: str, media_type: str, title: str, season: Optional[int] = None, episode: Optional[int] = None) -> str:
        """Generate a unique ID for the media item based on its properties."""
        # Create a string combining the unique properties
        id_string = f"{full_path}:{media_type}:{title}"
        if season is not None:
            id_string += f":s{season}"
        if episode is not None:
            id_string += f":e{episode}"
        # Generate SHA-256 hash and take first 16 characters for a shorter ID
        return hashlib.sha256(id_string.encode()).hexdigest()[:16]

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
        return [group.path for group in self.get_media_group_folders(self.media_base_path).groups]

    # Get all media group folders using the source_matrix in the config
    def get_media_group_folders(self, base_path: Path) -> MediaGroupFolderList:
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
                group_folder = base_path / f"{media_prefix}-{quality}"
                if group_folder.exists():
                    media_groups.append(MediaGroupFolder(
                        media_type=media_type,
                        media_prefix=media_prefix,
                        quality=quality,
                        path=str(group_folder),
                        media_folder_items=[]
                    ))
                    
        return MediaGroupFolderList(groups=media_groups)

    def search_media(self, request: SearchRequest) -> MediaItemGroup:
        """Search media in cache by title and optional parameters"""

        # For each db_type get the base path and add to list
        base_paths = []
        for db_type in request.db_type:
            if db_type == MediaDbType.MEDIA:
                base_paths.append(self.media_base_path)
            elif db_type == MediaDbType.CACHE:
                base_paths.append(self.cache_base_path)
            elif db_type == MediaDbType.PENDING:
                base_paths.append(self.cache_pending_path)

        # Search each base path for the media
        for base_path in base_paths:
            result = self.search_media_db(request, base_path)
            if result:
                return result

        return None

    def search_media_db(self, request: SearchRequest, base_path: Path) -> MediaItemGroup:
        """Search media in cache by title and optional parameters"""

        # Create a media filter
        media_filter = MediaFilter(request)

        # Get all media group folders
        media_groups = self.get_media_group_folders(base_path)

        # Filter groups based on request
        filtered_media_groups = []
        for media_group in media_groups.groups:
            if request.media_type and request.media_type != media_group.media_type:
                continue
            
            if request.quality and request.quality != media_group.quality:
                continue

            # Get the media items
            filtered_media_groups.append(media_group)   

        # Initialize empty list for media items
        media_items = []

        # Search through each media group
        for media_group in filtered_media_groups:
            path = Path(media_group.path)
            
            # Search through each folder in the media group
            for folder in path.glob("*"):
                if folder.is_dir():
                    # Get all files in the folder
                    for file in folder.glob("**/*"):
                        if file.is_file():
                            add_season_episode = media_group.media_type == "tv"
                            media_item = self._create_media_item_from_file(
                                file=file,
                                media_group=media_group,
                                title=folder.name,
                                add_season_episode=add_season_episode,
                                add_extended_info=request.add_extended_info
                            )
                            
                            # Check if the media item matches the request
                            if media_filter.is_match(media_item):
                                media_items.append(media_item)

        # Return the filtered results
        return MediaItemGroup(items=media_items)

    def _create_media_item_from_file(self, file: Path, media_group: MediaGroupFolder, title: str, add_season_episode: bool = False, add_extended_info: bool = False) -> MediaItem:
        season = None
        episode = None
        
        if add_season_episode:
            season, episode = self._parse_episode_info(file.name)
        
        extended = None
        if add_extended_info:
            extended = ExtendedMediaInfo(
                size=file.stat().st_size,
                created_at=file.stat().st_ctime,
                updated_at=file.stat().st_mtime,
                metadata=None)
            
        return MediaItem(
            id=self._generate_media_id(
                full_path=file.as_posix(),
                media_type=media_group.media_type,
                title=title,
                season=season,
                episode=episode
            ),
            db_type=MediaDbType.MEDIA,
            full_path=file.as_posix(),
            media_type=media_group.media_type,
            quality=media_group.quality,
            title=title,
            season=season,
            episode=episode,
            extended=extended
        )
