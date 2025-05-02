# Management of media using the file_manager class
from pathlib import Path
from app.api.managers.media_filter import MediaFilter
from app.api.models.media_models import (
    ExtendedMediaInfo, MediaDbType, MediaGroupFolder, MediaGroupFolderList,
    MediaFileItem, MediaItemFolder, MediaItem, MediaItemGroup
)
from app.api.models.search_request import SearchCacheExportFilter, SearchRequest
from app.core.config import Config
from typing import Any, List, Optional, Tuple
import re
import hashlib
import os

class MediaManager:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        # Initialize paths from config
        self.media_base_path = Path(config.get("default_source_path"))
        self.media_full_base_path = Path(config.get("default_full_source_path"))
        self.cache_base_path = Path(config.get("cache_path"))
        self.system_data_path = Path(config.get("system_data_path"))

    def _generate_media_id(self, relative_path: str, media_type: str, media_prefix: str, title: str, season: Optional[int] = None, episode: Optional[int] = None) -> str:
        """Generate a unique ID for the media item based on its properties."""
        # Create a string combining the unique properties
        id_string = f"{relative_path}:{media_type}:{media_prefix}:{title}"
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

    def get_db_path(self, db_type: MediaDbType) -> Path:
        if db_type == MediaDbType.MEDIA:
            return self.media_base_path
        elif db_type == MediaDbType.CACHE:
            return self.cache_base_path
        elif db_type == MediaDbType.SHADOW:
            return self.cache_shadow_path
        else:
            return self.media_base_path  # Default to media base path for UNDEFINED

    #def get_db_path_with_base_path(self, db_type: MediaDbType, base_path: str) -> Path:

    # Get all media group folders using the source_matrix in the config
    def get_media_group_folders(self, base_path: Path=None) -> MediaGroupFolderList:
        """Get all media group folders based on the source matrix configuration.
        
        Returns:
            MediaGroupFolderList: List of media group folder paths
        """

        media_groups = []
        source_matrix = self.config.get("source_matrix")
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
                        media_folder_items=[],
                        cache_export=config.get("cache_export", False)
                    ))

        # De-duplicate media_groups based on prefix and quality properties
        unique_media_groups = {}
        for media_group in media_groups:
            key = (media_group.media_prefix, media_group.quality)
            if key not in unique_media_groups:
                unique_media_groups[key] = media_group

        return MediaGroupFolderList(groups=list(unique_media_groups.values()))

    def search_media(self, request: SearchRequest, base_path: str=None) -> MediaItemGroup:
        """Search media in cache by title and optional parameters"""

        # For each db_type get the base path and add to list
        all_items = []
        if base_path:
            base_path_conv = Path(base_path)
            result = self._search_media_db(request, base_path_conv, MediaDbType.UNDEFINED)
            if result and result.items:
                all_items.extend(result.items)
        else:
            for db_type in request.db_type:
                result = self._search_media_db(request, self.get_db_path(db_type), db_type)
                if result and result.items:
                    all_items.extend(result.items)

        # Return combined results
        return MediaItemGroup(items=all_items)

    def get_media_target_path(self, db_type: MediaDbType, media_item: MediaItem) -> Path:
        """Get the target path for the media item based on the media type and quality"""
        media_prefix = media_item.media_prefix
        quality = media_item.quality
        file_name = media_item.full_path.split("/")[-1]
        return self.get_db_path(db_type) / f"{media_prefix}-{quality}" / media_item.title / file_name

    def get_media_relative_path_from_media_item(self, media_item: MediaItem) -> str:
        """Get the relative path for the media item based on the media type and quality"""
        media_prefix = media_item.media_prefix
        quality = media_item.quality
        file_name = media_item.full_path.split("/")[-1]
        return os.path.join(f"{media_prefix}-{quality}", media_item.title, file_name)

    def get_media_relative_path(self, media_prefix: str, quality: str, title: str, file_name: str) -> str:
        """Get the relative path for the media item based on the media type and quality"""
        return os.path.join(f"{media_prefix}-{quality}", title, file_name)

    def get_relative_path_to_title(self, title_path: str, file_path: str) -> str:
        """Get the subpath of the file relative to its title folder by removing title_path"""
        # Convert both paths to Path objects
        full_path = Path(file_path)
        title_path_obj = Path(title_path)
        
        try:
            # Get the relative path by removing the title_path
            return str(full_path.relative_to(title_path_obj))
        except ValueError:
            # If paths are not related, return empty string
            return ""

    def _search_media_db(self, request: SearchRequest, base_path: Path, db_type: MediaDbType) -> MediaItemGroup:
        """Search media in cache by title and optional parameters"""

        # Create a media filter
        media_filter = MediaFilter(request)

        # Get all media group folders
        media_groups = self.get_media_group_folders(base_path)

        # Filter groups based on request
        filtered_media_groups = []
        for media_group in media_groups.groups:

            if request.cache_export_filter == SearchCacheExportFilter.APPLY and not media_group.cache_export:
                continue

            if request.cache_export_filter == SearchCacheExportFilter.EXCLUDE and media_group.cache_export:
                continue

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
                                db_type=db_type,
                                add_season_episode=add_season_episode,
                                add_extended_info=request.add_extended_info
                            )
                            
                            # Check if the media item matches the request
                            if media_filter.is_match(media_item):
                                media_items.append(media_item)

        # Return the filtered results
        return MediaItemGroup(items=media_items)

    def _create_media_item_from_file(self, file: Path, media_group: MediaGroupFolder, title: str, db_type: MediaDbType, add_season_episode: bool = False, add_extended_info: bool = False) -> MediaItem:
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
                relative_path=self.get_media_relative_path(
                    media_prefix=media_group.media_prefix,
                    quality=media_group.quality,
                    title=title,
                    file_name=file.name
                ),
                media_type=media_group.media_type,
                media_prefix=media_group.media_prefix,
                title=title,
                season=season,
                episode=episode
            ),
            db_type=db_type,
            full_path=file.as_posix(),
            relative_title_path=self.get_relative_path_to_title(
                title_path=media_group.path,
                file_path=file.as_posix()
            ), 
            media_type=media_group.media_type,
            media_prefix=media_group.media_prefix,
            quality=media_group.quality,
            title=title,
            season=season,
            episode=episode,
            extended=extended
        )
