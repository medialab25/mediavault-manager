import os
from typing import Any
from app.api.managers.data_manager import DataManager
from app.api.managers.item_manager import ItemManager
from app.api.managers.media_manager import MediaManager
from app.api.models.media_models import MediaDbType, MediaItemGroup, MediaItemTarget
from app.api.models.search_request import SearchRequest

class CacheProcessor:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.media_manager = MediaManager(config)
        self.item_manager = ItemManager(config)
        self.data_manager = DataManager(config)
        self.media_path = self.media_manager.get_media_library_info().media_library_path
        
    def get_expected_cache(self, current_cache: MediaItemGroup) -> MediaItemGroup:
        """Get the expected cache structure
        
        Args:
            current_cache (MediaItemGroup | None): Current cache state. If None, will be fetched from media manager
            cache_path (str): The path to the cache
        Returns:
            MediaItemGroup: The expected cache structure

        """
        expected_cache_items = current_cache.items

        # Remove items from expected cache, using get_matrix_filepath() as the comparison key
        remove_items = self.data_manager.get_remove_cache_items()
        
        expected_cache_items = self.item_manager.remove_items_from_list(expected_cache_items, remove_items)

        # Add items to expected cache, if they don't already exist
        add_items = [item.clone() for item in self.data_manager.get_add_cache_items()]
        for item in add_items:
            item.destination = MediaItemTarget(
                db_type=MediaDbType.CACHE,
                media_prefix=item.source.media_prefix,
                quality=item.source.quality
            )

        expected_cache_items.extend(add_items)

        return MediaItemGroup(items=expected_cache_items)
