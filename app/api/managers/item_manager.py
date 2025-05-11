from enum import Enum
import os
from pathlib import Path
from typing import Any, Callable, Optional
from app.api.managers.matrix_manager import MatrixManager
from app.api.models.media_models import ExtendedMediaInfo, MediaDbType, MediaItem

class ItemMatchKey(Enum):
    RELATIVE_TITLE_FILEPATH = "relative_title_filepath"
    FULL_PATH = "full_path"
    TITLE_PATH = "title_path"

class ItemManager:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.matrix_manager = MatrixManager(config)
        self.media_library_info = self.matrix_manager.get_media_library_info()
        
    def get_extended_info(self, item: MediaItem) -> ExtendedMediaInfo:
        if item.extended:
            return item.extended
        # Populate the extended info from file stat
        file_path = item.full_file_path
        try:
            stat_result = os.stat(file_path)
            return ExtendedMediaInfo(
                size=stat_result.st_size,
                created_at=stat_result.st_ctime,
                updated_at=stat_result.st_mtime
            )
        except FileNotFoundError:
            return None

    def get_match_key_function(self, match_key: ItemMatchKey) -> Callable[[MediaItem], str]:
        if match_key == ItemMatchKey.FULL_PATH:
            return self.get_full_file_path
        elif match_key == ItemMatchKey.TITLE_PATH:
            return self.get_title_file_path
        elif match_key == ItemMatchKey.RELATIVE_TITLE_FILEPATH:
            return self.get_relative_title_file_path

    def get_unique_id(self, item: MediaItem, match_key: ItemMatchKey=ItemMatchKey.FULL_PATH) -> str:
        # Unique id is the title relative path
        return self.get_unique_id_by_function(item, self.get_match_key_function(match_key))
    
    def get_unique_id_by_function(self, item: MediaItem, function: Callable[[MediaItem], str]) -> str:
        return function(item)

    def get_unique_id_list(self, items: list[MediaItem], match_key: ItemMatchKey=ItemMatchKey.FULL_PATH) -> list[str]:
        func = self.get_match_key_function(match_key)
        return [self.get_unique_id_by_function(item, func) for item in items]

    def copy_update_item(self, item: MediaItem, db_type: Optional[MediaDbType]=None, media_prefix: Optional[str]=None, quality: Optional[str]=None) -> MediaItem:
        new_item = item.copy()
        
        if db_type:
            new_item.db_type = db_type

        if media_prefix:
            new_item.media_prefix = media_prefix

        if quality:
            new_item.quality = quality

        # Update the source and path
        new_item.source_item = item
        new_item.full_file_path = str(self.create_full_file_path(new_item))

        return new_item

    def copy_update_items(self, items: list[MediaItem], db_type: MediaDbType, media_prefix: Optional[str]=None, quality: Optional[str]=None) -> list[MediaItem]:
        return [self.copy_update_item(item, db_type, media_prefix, quality) for item in items]

    # Matching functions
    def get_full_file_path(self, item: MediaItem) -> str:
        return item.full_file_path

    def get_title_file_path(self, item: MediaItem) -> str:
        return str(Path(item.title) / item.relative_title_filepath)

    def get_relative_title_file_path(self, item: MediaItem) -> str:
        return item.relative_title_filepath
    
    # Path generation
    def get_base_path(self, item: MediaItem) -> str:
        return (self.media_library_info.media_library_path 
                if item.db_type == MediaDbType.MEDIA 
                else self.media_library_info.cache_library_path
                if item.db_type == MediaDbType.CACHE
                else self.media_library_info.export_library_path
                if item.db_type == MediaDbType.EXPORT
                else self.media_library_info.cache_export_library_path) 
    

    def create_full_file_path(self, item: MediaItem) -> str:
        base_path = self.get_base_path(item)
        return Path(base_path) / f"{item.media_prefix}-{item.quality}" / item.title / item.relative_title_filepath

#####
    def get_file_path_link(self, item: MediaItem, media_db_type: MediaDbType) -> str:
        base_path = (self.media_library_info.media_library_path 
                    if media_db_type == MediaDbType.MEDIA 
                    else self.media_library_info.cache_library_path)
        
        if item.media_prefix and item.quality:
            return base_path / f"{item.media_prefix}-{item.quality}" / item.title / item.relative_title_filepath
        elif item.media_prefix:
            return base_path / item.media_prefix / item.relative_title_filepath
        else:
            return base_path / item.relative_title_filepath

    def get_file_path(self, item: MediaItem) -> str:
        return self.get_file_path_link(item, item.db_type)

    def get_folder_path(self, item: MediaItem) -> str:
        return self.get_file_path(item).parent

    def merge_unique_items(self, existing_items: list[MediaItem], new_items: list[MediaItem]) -> list[MediaItem]:
        """Merge two lists of MediaItems while ensuring uniqueness based on unique_id.
        
        Args:
            existing_items (list[MediaItem]): List of existing items
            new_items (list[MediaItem]): List of new items to merge
            
        Returns:
            list[MediaItem]: Combined list with duplicates removed
        """
        # Get unique IDs for existing items
        existing_ids = self.get_unique_id_list(existing_items)
        # Filter out items that already exist
        unique_new_items = [item for item in new_items if self.get_unique_id(item) not in existing_ids]
        # Return combined list
        combined_list = existing_items + unique_new_items
        return combined_list
    
    def remove_items_from_list(self, items: list[MediaItem], remove_items: list[MediaItem]) -> list[MediaItem]:
        """Remove items from a list based on unique_id.
        
        Args:
            items (list[MediaItem]): List of items to remove from
            remove_items (list[MediaItem]): List of items to remove
        """
        # Get unique IDs for remove items
        remove_ids = self.get_unique_id_list(remove_items)
        # Filter out items that are in the remove list
        remaining_items = [item for item in items if self.get_unique_id(item) not in remove_ids]
        # Return the remaining items
        return remaining_items

    def is_item_in_list(self, item: MediaItem, items: list[MediaItem], match_key: ItemMatchKey=ItemMatchKey.FULL_PATH) -> bool:
        """Check if an item is in a list based on unique_id.
        
        Args:
            item (MediaItem): Item to check
            items (list[MediaItem]): List of items to check against
        """
        func = self.get_match_key_function(match_key)
        return any(func(item) == func(existing_item) for existing_item in items)
        
    def get_matching_item(self, item: MediaItem, items: list[MediaItem], match_key: ItemMatchKey=ItemMatchKey.FULL_PATH) -> MediaItem:
        """Get the first item in a list that matches a given item based on unique_id.
        
        Args:
            item (MediaItem): Item to check
            items (list[MediaItem]): List of items to check against
        """
        func = self.get_match_key_function(match_key)
        return next((existing_item for existing_item in items if func(item) == func(existing_item)), None)

    def get_matching_items(self, item: MediaItem, items: list[MediaItem], match_key: ItemMatchKey=ItemMatchKey.FULL_PATH) -> list[MediaItem]:
        """Get all items in a list that match a given item based on unique_id.
        
        Args:
            item (MediaItem): Item to check
            items (list[MediaItem]): List of items to check against
        """
        func = self.get_match_key_function(match_key)
        return [existing_item for existing_item in items if func(item) == func(existing_item)]
