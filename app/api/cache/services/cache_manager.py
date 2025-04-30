import os
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

from app.api.cache.models.cache_models import CacheItem, CacheGroup, CacheContents

class CacheManager:
    def __init__(self, cache_path: str, storage_paths: List[str]):
        """
        Initialize CacheManager with cache path and storage paths.
        
        Args:
            cache_path (str): Path to the cache directory
            storage_paths (List[str]): List of storage paths to monitor
        """
        self.cache_path = Path(cache_path)
        self.storage_paths = [Path(path) for path in storage_paths]

    def _get_file_info(self, file_path: Path) -> Dict:
        """Get information about a file."""
        stat = file_path.stat()
        return {
            "size": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_ctime),
            "last_accessed": datetime.fromtimestamp(stat.st_atime)
        }

    def _scan_cache_directory(self, cache_path: Path) -> List[CacheGroup]:
        """Scan a cache directory and return its contents."""
        groups: List[CacheGroup] = []
        
        if not cache_path.exists():
            return groups

        for item in cache_path.iterdir():
            if item.is_dir():
                group_items: List[CacheItem] = []
                total_size = 0
                
                for file in item.glob("**/*"):
                    if file.is_file():
                        file_info = self._get_file_info(file)
                        cache_item = CacheItem(
                            id=str(file.relative_to(cache_path)),
                            name=file.name,
                            type=file.suffix[1:] if file.suffix else "unknown",
                            size=file_info["size"],
                            last_accessed=file_info["last_accessed"],
                            created_at=file_info["created_at"]
                        )
                        group_items.append(cache_item)
                        total_size += file_info["size"]

                if group_items:
                    groups.append(CacheGroup(
                        name=item.name,
                        items=group_items,
                        total_size=total_size,
                        item_count=len(group_items)
                    ))

        return groups

    def get_hot_cache(self) -> CacheContents:
        """Get the contents of the hot cache."""
        groups = self._scan_cache_directory(self.cache_path)
        total_size = sum(group.total_size for group in groups)
        total_items = sum(group.item_count for group in groups)
        
        return CacheContents(
            groups=groups,
            total_size=total_size,
            total_items=total_items
        )

    def get_cold_cache(self) -> CacheContents:
        """Get the contents of the cold cache."""
        # For now, return empty cache contents since we're using a single cache
        return CacheContents(
            groups=[],
            total_size=0,
            total_items=0
        )

    def get_all_cache(self) -> Dict[str, CacheContents]:
        """Get the contents of both hot and cold caches."""
        return {
            "hot_cache": self.get_hot_cache(),
            "cold_cache": self.get_cold_cache()
        } 