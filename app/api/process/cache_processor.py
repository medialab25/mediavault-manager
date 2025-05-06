from typing import Any
from app.api.managers.media_manager import MediaManager
from app.api.models.media_models import MediaDbType, MediaItemGroup
from app.api.managers.cache_manager import _add_cache_items, _remove_cache_items
from app.api.models.search_request import SearchRequest

class CacheProcessor:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.media_manager = MediaManager(config)
        
    def get_processed_cache(self, current_cache: MediaItemGroup, cache_path: str) -> MediaItemGroup:
        """Get the expected cache structure
        
        Args:
            current_cache (MediaItemGroup | None): Current cache state. If None, will be fetched from media manager
            
        Returns:
            MediaItemGroup: The expected cache structure

        """
        expected_cache = MediaItemGroup(items=[])

        # Get list of all matrix_filepath in current cache
        current_cache_matrix_filepaths = [item.get_matrix_filepath() for item in current_cache.items]
        
        # Make clone of current state
        for item in current_cache.items:
            expected_cache.items.append(item.clone())

        # Remove items from expected cache, using get_matrix_filepath() as the comparison key
        for item in _remove_cache_items:
            # Find items with matching matrix_filepath
            matching_items = [i for i in expected_cache.items if i.get_matrix_filepath() == item.get_matrix_filepath()]
            for matching_item in matching_items:
                expected_cache.items.remove(matching_item)

        # Add items to expected cache, if they don't already exist
        for item in _add_cache_items:
            if item.get_matrix_filepath() not in current_cache_matrix_filepaths:
                updated_item = item.clone()
                updated_item.db_type = MediaDbType.CACHE
                updated_item
                expected_cache.items.append(item.clone())

        return expected_cache
