import os
import logging
from datetime import datetime
import shutil
from typing import List, Dict, Optional, Any
from pathlib import Path

from app.api.adapters.os_adapter import os_adapter_hard_link_file
from app.api.managers.media_manager import MediaManager
from app.api.managers.media_query import MediaQuery
from app.api.models.media_models import MediaDbType, MediaItemGroup, MediaItemGroupDict
from app.api.models.search_request import SearchRequest

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.cache_path = Path(config.get("cache_path", ""))
        self.cache_shadow_path = Path(config.get("cache_shadow_path", ""))
        self.cache_pending_path = Path(config.get("cache_pending_path", ""))
        self.media_manager = MediaManager(config)
        
    def list_cache(self) -> MediaItemGroupDict:
        """List all cache contents"""
        try:
            logger.debug("Listing cache contents")
            # Use the media manager to search cache
            result = self.media_manager.search_media(
                request=SearchRequest(
                    query="",
                    db_type=[MediaDbType.PENDING, MediaDbType.CACHE]
                )
            )

            # Use the media query to get the items
            media_query = MediaQuery(result)
            pending_result = media_query.get_items(SearchRequest(
                db_type=[MediaDbType.PENDING]
            ))
            cache_result = media_query.get_items(SearchRequest(
                db_type=[MediaDbType.CACHE]
            ))

            # Combine the results
            return MediaItemGroupDict(
                groups={
                    "pending": pending_result,
                    "cache": cache_result
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

            # All items in result, use os_adapter to hard link to cache pending path
            # Extract file paths from result items
            for item in result.items:
                target_path = self.media_manager.get_media_target_path(MediaDbType.PENDING, item)
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                # If already exists, remove it
                if os.path.exists(target_path):
                    os.remove(target_path)
                # Link the file
                os.link(item.full_path, target_path)

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
                db_type=[MediaDbType.PENDING]
            )

            # Use media manager to search for items
            result = self.media_manager.search_media(request)

            # If this is a dry run, just return the search results
            if dry_run:
                return result

            # Move the items from the cache pending to the media
            for item in result.items:
                media_path = self.media_manager.get_media_target_path(MediaDbType.MEDIA, item)
                os.makedirs(os.path.dirname(media_path), exist_ok=True)
                # If already exists in media, delete the PENDING file
                if os.path.exists(media_path):
                    os.remove(item.full_path)
                else:
                    # Move the file
                    os.rename(item.full_path, media_path)

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

                # Copy the file
                shutil.copy2(item.full_path, target_path)

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
                    "move_to_cache": pending_items_not_in_cache,
                    "delete_from_cache": cache_items_not_in_pending
                }
            )
        
        except Exception as e:
            logger.error(f"Error getting pending items not in cache: {str(e)}", exc_info=True)
            raise e