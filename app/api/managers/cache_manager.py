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
                os_adapter_hard_link_file(item.full_path, target_path)

            return result
        except Exception as e:
            logger.error(f"Error adding to cache: {str(e)}", exc_info=True)
            raise e

    def sync_cache(self, dry_run: bool = False) -> MediaItemGroup:
        """Sync the cache with the media library by moving items from pending to cache
        
        Args:
            dry_run (bool): If True, only show what would be done without making changes
            
        Returns:
            MediaItemGroupDict: The pending items that would be/are processed
        """
        try:
            logger.debug(f"Starting cache sync{' (dry run)' if dry_run else ''}")
            
            # Get all pending items
            pending_items = self.media_manager.search_media(
                request=SearchRequest(
                    query="",
                    db_type=[MediaDbType.PENDING]
                )
            )

            # Process each pending item
            for item in pending_items.items:
                # Get the target paths
                target_path = self.media_manager.get_media_target_path(MediaDbType.CACHE, item)
                shadow_path = self.media_manager.get_media_target_path(MediaDbType.SHADOW, item)
                
                if dry_run:
                    logger.info(f"Would copy {item.full_path} to {target_path}")
                    logger.info(f"Would move {item.full_path} to {shadow_path}")
                    continue
                
                # Create the target directory if it doesn't exist
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                
                # Copy the file making sure it doesn't already exist
                if not os.path.exists(target_path):
                    shutil.copy2(item.full_path, target_path)

                    # Move the pending into the shadow path ensuring the target folder exists 
                    os.makedirs(os.path.dirname(shadow_path), exist_ok=True)
                    os.rename(item.full_path, shadow_path)  
                
                # Update the item to the cache db type
                item.db_type = MediaDbType.CACHE

            # Return the results in the expected format
            return pending_items
        
        except Exception as e:
            logger.error(f"Error syncing cache: {str(e)}", exc_info=True)
            raise e

