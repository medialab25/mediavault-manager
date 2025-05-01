from typing import Any
from app.api.models.media_models import MediaItemGroupDict, MediaItemGroup
from app.api.managers.cache_manager import CacheManager
import logging

logger = logging.getLogger(__name__)

class SyncManager:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.cache_manager = CacheManager(config)

    def sync(self, dry_run: bool = False) -> MediaItemGroupDict:
        """Sync the cache with the media library
        
        Args:
            dry_run (bool): If True, only show what would be done without making changes
            
        Returns:
            MediaItemGroupDict: The results of the sync operation
        """
        try:
            logger.debug(f"Starting sync{' (dry run)' if dry_run else ''}")
            cache_sync_result = self.cache_manager.sync_cache(dry_run=dry_run)

            return MediaItemGroupDict(
                groups={
                    "pending": cache_sync_result,
                    "cache": MediaItemGroup(items=[])
                }
            )
        except Exception as e:
            logger.error(f"Error in sync: {str(e)}", exc_info=True)
            raise e