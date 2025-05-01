import os
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path

from app.api.managers.media_manager import MediaManager
from app.api.managers.media_query import MediaQuery
from app.api.models.media_models import MediaDbType, MediaItemGroup
from app.api.models.search_request import SearchRequest
from app.api.models.cache_models import CacheStatusList

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.cache_path = Path(config.get("cache_path", ""))
        self.cache_shadow_path = Path(config.get("cache_shadow_path", ""))
        self.cache_pending_path = Path(config.get("cache_pending_path", ""))
        self.media_manager = MediaManager(config)
        
    def list_cache(self) -> CacheStatusList:
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
            return CacheStatusList(
                pending=pending_result,
                cache=cache_result
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

            # TODO: Implement actual cache addition logic here
            # For now, we're just returning the search results
            return result
        except Exception as e:
            logger.error(f"Error adding to cache: {str(e)}", exc_info=True)
            raise e

