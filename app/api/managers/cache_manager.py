import os
import logging
from datetime import datetime
import shutil
from typing import List, Dict, Optional, Any
from pathlib import Path

from app.api.adapters.os_adapter import os_adapter_hard_link_file
from app.api.managers.media_manager import MediaManager
from app.api.managers.media_query import MediaQuery
from app.api.managers.update_data_manager import UpdateDataManager
from app.api.models.media_models import MediaDbType, MediaItemGroup, MediaItemGroupDict
from app.api.models.search_request import SearchRequest

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.cache_path = Path(config.get("cache_path", ""))
        self.cache_shadow_path = Path(config.get("cache_shadow_path", ""))
        self.media_manager = MediaManager(config)
        self.update_data_manager = UpdateDataManager(config)

    def list_cache(self) -> MediaItemGroupDict:
        """List all cache contents"""
        try:
            logger.debug("Listing cache contents")
            # Use the media manager to search cache
            result = self.media_manager.search_media(
                request=SearchRequest(
                    query="",
                    db_type=[MediaDbType.CACHE, MediaDbType.SHADOW, MediaDbType.MEDIA]
                )
            )

            # Use the media query to get the items
            media_query = MediaQuery(result)
            shadow_result = media_query.get_items(SearchRequest(
                db_type=[MediaDbType.SHADOW]
            ))
            cache_result = media_query.get_items(SearchRequest(
                db_type=[MediaDbType.CACHE]
            ))

            # Read update data
            update_data = self.update_data_manager.read_update_data()
            add_cache_updates = update_data.get("add_cache_updates", [])
            remove_cache_updates = update_data.get("remove_cache_updates", [])

            add_cache_result = MediaItemGroup(items=[])
            remove_cache_result = MediaItemGroup(items=[])

            # For each id in add_cache_updates, add the item to the cache
            for id in add_cache_updates:
                item = next((item for item in result.items if item.id == id), None)
                if item:
                    add_cache_result.items.append(item)

            # For each id in remove_cache_updates, remove the item from the cache   
            for id in remove_cache_updates:
                item = next((item for item in cache_result.items if item.id == id), None)
                if item:
                    remove_cache_result.items.append(item)

            # Combine the results
            return MediaItemGroupDict(
                groups={
                    "shadow": shadow_result,
                    "cache": cache_result,
                    "add_cache": add_cache_result,
                    "remove_cache": remove_cache_result
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
                id=data.get("id"),
                season=data.get("season"),
                episode=data.get("episode"),
                db_type=[MediaDbType.MEDIA]
            )

            # Use media manager to search for items
            result = self.media_manager.search_media(request)

            # If this is a dry run, just return the search results
            if dry_run:
                return result

            # Add the items to the update data manager
            self.update_data_manager.add_cache_update([item.id for item in result.items])

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
                id=data.get("id"),
                season=data.get("season"),
                episode=data.get("episode"),
                db_type=[MediaDbType.CACHE]
            )

            # Use media manager to search for items
            result = self.media_manager.search_media(request)

            # If this is a dry run, just return the search results
            if dry_run:
                return result
            
            # Only remove if items are found
            if result.items:
                # Move the items from the cache pending to the media
                self.update_data_manager.remove_cache_update([item.id for item in result.items])

            return result
        except Exception as e:
            logger.error(f"Error removing from cache: {str(e)}", exc_info=True)
            raise e

    def sync_cache(self, dry_run: bool = False) -> MediaItemGroupDict:
        """Sync the cache with the media library by moving items from pending to cache
        
        Args:
            dry_run (bool): If True, only show what would be done without making changes
            
        Returns:
            MediaItemGroupDict: The pending items that would be/are processed
        """
        add_cache_items = self.update_data_manager.get_add_cache_updates()
        remove_cache_items = self.update_data_manager.get_remove_cache_updates()

        # Get the items from the media library
        media_items = self.media_manager.search_media(SearchRequest(db_type=[MediaDbType.MEDIA, MediaDbType.CACHE, MediaDbType.SHADOW]))
        media_query = MediaQuery(media_items)

        remove_cache_items = media_query.get_items_by_ids(remove_cache_items, MediaDbType.CACHE)
        add_cache_items = media_query.get_items_by_ids(add_cache_items, MediaDbType.MEDIA)

        if dry_run:
            return MediaItemGroupDict(
                groups={
                    "remove_cache": MediaItemGroup(items=remove_cache_items),
                    "add_cache": MediaItemGroup(items=add_cache_items),
                }
            )

        # Delete the items from the cache
        for item in remove_cache_items:
            # Only if the db_type is cache
            os.remove(item.full_path)



        remove_shadow_items = media_query.get_items_by_ids(remove_cache_items, MediaDbType.SHADOW)
        add_shadow_items = media_query.get_items_by_ids(add_cache_items, MediaDbType.MEDIA)


        
        # Move the items from SHADOW to MEDIA
        for item in remove_shadow_items:
            shutil.move(item.full_path, self.media_manager.get_media_target_path(MediaDbType.MEDIA, item))

        # Move the item from MEDIA to CACHE
        for item in add_cache_items:
            shutil.move(item.full_path, self.media_manager.get_media_target_path(MediaDbType.CACHE, item))

        # Move the items from MEDIA to SHADOW
        for item in add_shadow_items:
            shutil.move(item.full_path, self.media_manager.get_media_target_path(MediaDbType.SHADOW, item))

        # Remove the items from the cache   
        self.update_data_manager.clear_cache_updates()

        return self.list_cache()

    def clean_cache(self, dry_run: bool = False) -> MediaItemGroupDict:
        """Clean the cache by removing items that are not in the media library"""

        # If there are any media items in SHADOW, move to MEDIA
        shadow_items = self.media_manager.search_media(SearchRequest(db_type=[MediaDbType.SHADOW]))
        media_query = MediaQuery(shadow_items)
        shadow_items = media_query.get_items(SearchRequest(db_type=[MediaDbType.SHADOW]))
        for item in shadow_items:
            shutil.move(item.full_path, self.media_manager.get_media_target_path(MediaDbType.MEDIA, item))
        
        # Any items in CACHE, remove
        cache_items = self.media_manager.search_media(SearchRequest(db_type=[MediaDbType.CACHE]))
        media_query = MediaQuery(cache_items)
        cache_items = media_query.get_items(SearchRequest(db_type=[MediaDbType.CACHE]))
        for item in cache_items:
            os.remove(item.full_path)

        # Clear update data
        self.update_data_manager.clear_cache_updates()

    def clean_update_data(self) -> None:
        """Clean the update data"""
        self.update_data_manager.clear_cache_updates()

    def sync_cache1(self, dry_run: bool = False) -> MediaItemGroupDict:
        """Sync the cache with the media library by moving items from pending to cache
        
        Args:
            dry_run (bool): If True, only show what would be done without making changes
            
        Returns:
            MediaItemGroupDict: The pending items that would be/are processed
        """
        try:
            logger.debug(f"Starting cache sync{' (dry run)' if dry_run else ''}")
            
            # Get the pending and cache items diff
            pending_cache_items_dict = self.get_pending_cache_items_diff()
            pending_items_not_in_cache = pending_cache_items_dict.groups["move_to_cache"]
            cache_items_not_in_pending = pending_cache_items_dict.groups["delete_from_cache"]

            # Remove all items from cache that are not in pending
            for item in cache_items_not_in_pending.items:
                os.remove(item.full_path)

            # Cleanup any empty folders in the cache
            for item in cache_items_not_in_pending.items:
                # If this is a dry run, just log the action
                if dry_run:
                    logger.info(f"Would remove {item.full_path}")
                    continue

                # Remove the folder
                if os.path.isdir(item.full_path):
                    os.rmdir(item.full_path)

            # Copy all items from pending to cache
            for item in pending_items_not_in_cache.items:
                # Get the target paths
                target_path = self.media_manager.get_media_target_path(MediaDbType.CACHE, item)

                # If this is a dry run, just log the action
                if dry_run:
                    logger.info(f"Would copy {item.full_path} to {target_path}")
                    continue

                # Copy the file. making sure the folder exists
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                shutil.copy2(item.full_path, target_path)

                # Remove the file from MEDIA
                os.remove(item.full_path)

                # Clean any folders in pending that are now empty
#                if os.path.isdir(item.full_path):
#                    os.rmdir(item.full_path)

            # Return the results in the expected format
            return pending_cache_items_dict
        
        except Exception as e:
            logger.error(f"Error syncing cache: {str(e)}", exc_info=True)
            raise e

    # Method to get a list of MediaItem objects in the PENDING db type but not in the CACHE db type
    def get_pending_cache_items_diff(self) -> MediaItemGroupDict:
        """Get pending items that are not in the cache"""
        try:
            # Get all pending items
            pending_items = self.media_manager.search_media(
                request=SearchRequest(
                    query="",
                    db_type=[MediaDbType.PENDING]
                )
            )
            
            # Get all cache items
            cache_items = self.media_manager.search_media(
                request=SearchRequest(
                    query="",
                    db_type=[MediaDbType.CACHE]
                )
            )   

            # Return the pending items that are not in the cache, compared via the id
            pending_items_not_in_cache = [item for item in pending_items.items if item.id not in [item.id for item in cache_items.items]]    
            cache_items_not_in_pending = [item for item in cache_items.items if item.id not in [item.id for item in pending_items.items]]
            return MediaItemGroupDict(
                groups={
                    "move_to_cache": MediaItemGroup(items=pending_items_not_in_cache),
                    "delete_from_cache": MediaItemGroup(items=cache_items_not_in_pending)
                }
            )
        
        except Exception as e:
            logger.error(f"Error getting pending items not in cache: {str(e)}", exc_info=True)
            raise e