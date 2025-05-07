from typing import Any
from app.api.managers.media_manager import MediaManager
from app.api.models.media_models import MediaDbType, MediaItem


class ItemManager:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.media_manager = MediaManager(config)
        self.media_library_info = self.media_manager.get_media_library_info()
        
    def get_unique_id(self, item: MediaItem) -> str:
        # Unique id is the title relative path
        return item.relative_title_filepath
    
    def get_unique_id_list(self, items: list[MediaItem]) -> list[str]:
        return [self.get_unique_id(item) for item in items]

    def get_file_path(self, item: MediaItem) -> str:
        # Get is_merged from metadata
        is_merged = item.metadata.get("is_merged", False)
        base_path = (self.media_library_info.media_library_path 
                    if item.db_type == MediaDbType.MEDIA 
                    else self.media_library_info.cache_library_path)
        return (self.get_full_title_filepath(base_path) 
                if is_merged 
                else self.get_full_filepath(base_path))

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

    def is_item_in_list(self, item: MediaItem, items: list[MediaItem]) -> bool:
        """Check if an item is in a list based on unique_id.
        
        Args:
            item (MediaItem): Item to check
            items (list[MediaItem]): List of items to check against
        """
        return any(self.get_unique_id(item) == self.get_unique_id(existing_item) for existing_item in items)
        
    def get_matching_items(self, item: MediaItem, items: list[MediaItem]) -> list[MediaItem]:
        """Get all items in a list that match a given item based on unique_id.
        
        Args:
            item (MediaItem): Item to check
            items (list[MediaItem]): List of items to check against
        """
        return [existing_item for existing_item in items if self.get_unique_id(item) == self.get_unique_id(existing_item)]
