from typing import Any
from app.api.models.media_models import MediaItemGroupList


class SyncManager:
    def __init__(self, config: dict[str, Any]):
        self.config = config

    def sync(self) -> MediaItemGroupList:
        """Sync the cache with the media library"""
        return self.cache_manager.sync_cache()