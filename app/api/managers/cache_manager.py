import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path

from app.api.managers.data_manager import DataManager
from app.api.managers.item_manager import ItemManager
from app.api.managers.media_manager import MediaManager
from app.api.managers.media_query import MediaQuery
from app.api.models.media_models import MediaDbType, MediaItemGroup, MediaItemGroupDict, MediaItem
from app.api.models.search_request import SearchRequest

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.cache_path = Path(config.get("cache_path", ""))
        self.media_manager = MediaManager(config)
        self.data_manager = DataManager(config)
        self.item_manager = ItemManager(config)

    def list_cache(self) -> MediaItemGroupDict:
        """List all cache contents"""
        try:
            logger.debug("Listing cache contents")
            add_cache_items = self.data_manager.get_data("add_cache_items") or []
            remove_cache_items = self.data_manager.get_data("remove_cache_items") or []
            
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
                    "add_cache": MediaItemGroup(items=add_cache_items),
                    "remove_cache": MediaItemGroup(items=remove_cache_items)
                }
            )
        except Exception as e:
            logger.error(f"Error listing cache: {str(e)}", exc_info=True)
            raise e

    def add_to_cache(self, data: dict, dry_run: bool = False) -> Dict:
        """Add items to cache based on search criteria"""
        try:
            
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

            # Add items to add cache items list
            self.data_manager.append_add_cache_items(result.items)

            # Update the data manager
            self.data_manager.update()

            return result
        except Exception as e:
            logger.error(f"Error adding to cache: {str(e)}", exc_info=True)
            raise e

    def remove_from_cache(self, data: dict, dry_run: bool = False) -> Dict:
        """Remove items from cache based on search criteria"""
        try:
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

            # If this is a dry run, just return the search results
            if dry_run:
                return cache_result

            # Add items to remove list if in the cache result
            self.data_manager.append_remove_cache_items(cache_result.items)

            # Remove any from the existing list if the unique id matches any in the remove list
            existing_items = self.data_manager.get_add_cache_items()
            remaining_add_items = self.item_manager.remove_items_from_list(existing_items, result.items)
            # Add the remaining items to the add cache items list
            self.data_manager.set_add_cache_items(remaining_add_items)

            # Update the data manager
            self.data_manager.update()

            return cache_result
        except Exception as e:
            logger.error(f"Error removing from cache: {str(e)}", exc_info=True)
            raise e

    def clear_pre_cache(self):
        """Clear the pre cache"""
        # Clear both add and remove cache lists
        self.data_manager.set_data("add_cache_items", [])
        self.data_manager.set_data("remove_cache_items", [])

        # Update the data manager
        self.data_manager.update()
        