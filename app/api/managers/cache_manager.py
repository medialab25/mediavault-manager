import os
import logging
from datetime import datetime
import shutil
from typing import List, Dict, Optional, Any
from pathlib import Path

from app.api.managers.media_manager import MediaManager
from app.api.managers.media_query import MediaQuery
from app.api.managers.update_data_manager import UpdateDataManager
from app.api.models.media_models import MediaDbType, MediaItemGroup, MediaItemGroupDict, MediaItem
from app.api.models.search_request import SearchRequest

logger = logging.getLogger(__name__)

# Cache for persisting calls
_add_cache_items: List[MediaItem] = []
_remove_cache_items: List[MediaItem] = []

class CacheManager:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.cache_path = Path(config.get("cache_path", ""))
        self.media_manager = MediaManager(config)
        self.update_data_manager = UpdateDataManager(config)

    def list_cache(self) -> MediaItemGroupDict:
        """List all cache contents"""
        try:
            logger.debug("Listing cache contents")
            global _add_cache_items
            global _remove_cache_items
            
            # Use the media manager to search cache
            cache_result = self.media_manager.search_media(
                request=SearchRequest(
                    query="",
                    db_type=[MediaDbType.CACHE]
                )
            )

            # Combine the results
            return MediaItemGroupDict(
                groups={
                    "cache": cache_result,
                    "add_cache": MediaItemGroup(items=_add_cache_items),
                    "remove_cache": MediaItemGroup(items=_remove_cache_items)
                }
            )
        except Exception as e:
            logger.error(f"Error listing cache: {str(e)}", exc_info=True)
            raise e

    def add_to_cache(self, data: dict, dry_run: bool = False) -> Dict:
        """Add items to cache based on search criteria"""
        try:
            global _add_cache_items
            
            # Create a search request from the data
            request = SearchRequest(
                query=data.get("query", ""),
                media_type=data.get("media_type"),
                quality=data.get("quality"),
                season=data.get("season"),
                episode=data.get("episode"),
                matrix_filepath=data.get("matrix_filepath"),
                relative_filepath=data.get("relative_filepath"),
                db_type=[MediaDbType.MEDIA]
            )

            # Use media manager to search for items
            result = self.media_manager.search_media(request)

            # If this is a dry run, just return the search results
            if dry_run:
                return result

            # Get existing matrix filepaths to avoid duplicates
            existing_paths = {item.get_relative_matrix_filepath() for item in _add_cache_items}
            # Only add items whose matrix filepath is not already in the list
            _add_cache_items.extend([item for item in result.items if item.get_relative_matrix_filepath() not in existing_paths])
            return result
        except Exception as e:
            logger.error(f"Error adding to cache: {str(e)}", exc_info=True)
            raise e

    def remove_from_cache(self, data: dict, dry_run: bool = False) -> Dict:
        """Remove items from cache based on search criteria"""
        try:
            global _add_cache_items
            global _remove_cache_items
            
            # Create a search request from the data
            request = SearchRequest(
                query=data.get("query", ""),
                media_type=data.get("media_type"),
                quality=data.get("quality"),
                matrix_filepath=data.get("matrix_filepath"),
                relative_filepath=data.get("relative_filepath"),
                season=data.get("season"),
                episode=data.get("episode"),
                db_type=[MediaDbType.CACHE, MediaDbType.MEDIA]
            )

            # Use media manager to search for items
            result = self.media_manager.search_media(request)
            query = MediaQuery(result)
            cache_result = query.get_items(SearchRequest(db_type=[MediaDbType.CACHE]))
            media_result = query.get_items(SearchRequest(db_type=[MediaDbType.MEDIA]))

            # If this is a dry run, just return the search results
            if dry_run:
                return cache_result

            # Add to the remove list if the item already exists in the result using get_matrix_filepath as key
            existing_paths = {item.get_relative_matrix_filepath() for item in cache_result.items}
            _remove_cache_items.extend([item for item in cache_result.items if item.get_relative_matrix_filepath() in existing_paths])

            # Remove any from _add_cache_items that have same matrix filepath as result
            media_paths = {item.get_relative_matrix_filepath() for item in media_result.items}
            _add_cache_items = [item for item in _add_cache_items if item.get_relative_matrix_filepath() not in media_paths]

            return cache_result
        except Exception as e:
            logger.error(f"Error removing from cache: {str(e)}", exc_info=True)
            raise e

    def clear_pre_cache(self):
        """Clear the pre cache"""
        global _add_cache_items
        global _remove_cache_items
        _add_cache_items = []
        _remove_cache_items = []
        