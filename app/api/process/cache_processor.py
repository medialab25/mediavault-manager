import json
import os
from typing import Any, List
from app.api.managers.data_manager import DataManager
from app.api.managers.item_manager import ItemManager
from app.api.managers.matrix_manager import MatrixManager
from app.api.managers.media_manager import MediaManager
from app.api.models.media_models import ExtendedMediaInfo, MediaDbType, MediaItemGroup
from pydantic import BaseModel

class CacheManifestItem(BaseModel):
    full_file_path: str
    title_file_path: str
    extended: ExtendedMediaInfo

class CacheProcessor:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.media_manager = MediaManager(config)
        self.item_manager = ItemManager(config)
        self.data_manager = DataManager(config)
        self.matrix_manager = MatrixManager(config)
        self.media_library_info = self.matrix_manager.get_media_library_info()
        self.media_path = self.media_library_info.media_library_path
        self.cache_workflow = self.config.get("cache_workflow", {})
        
    def get_expected_cache(self, current_media: MediaItemGroup, current_cache: MediaItemGroup, dry_run: bool=False, max_cache_size_gb: int=100) -> MediaItemGroup:
        """Get the expected cache structure
        
        Args:
            current_cache (MediaItemGroup | None): Current cache state. If None, will be fetched from media manager
            cache_path (str): The path to the cache
        Returns:
            MediaItemGroup: The expected cache structure

        """

        cache_manifest = self.load_cache_manifest()

        expected_cache_items = current_cache.items

        # Remove items from expected cache, using get_matrix_filepath() as the comparison key
        remove_items = self.data_manager.get_remove_cache_items()
        
        expected_cache_items = self.item_manager.remove_items_from_list(expected_cache_items, remove_items)

        # Add items to expected cache, if they don't already exist
        add_items = self.item_manager.copy_update_items(self.data_manager.get_add_cache_items(), MediaDbType.CACHE)

        # max_cache_size in bytes
        max_cache_size = max_cache_size_gb * 1024 * 1024 * 1024

        # For each item only add if the total size of the cache is less than the max cache size
        expected_cache_size = sum(self.item_manager.get_extended_info(item).size for item in expected_cache_items)
        for item in add_items:
            ext_info = self.item_manager.get_extended_info(item)
            expected_cache_size += ext_info.size
            if expected_cache_size > max_cache_size:
                break
            expected_cache_items.append(item)

        # Add expected cache items to the cache manifest
        cache_manifest['manual_cache_items'] = []
        cache_manifest_items = []
        for item in expected_cache_items:
            ext_info = self.item_manager.get_extended_info(item)
            cache_manifest_items.append(CacheManifestItem(full_file_path=item.full_file_path, title_file_path=self.item_manager.get_title_file_path(item), extended=ext_info))

        cache_manifest['manual_cache_items'] = cache_manifest_items

        # Get the list of media items in decending created time order
        # Only run if the latest_added workflow is enabled
        if self.cache_workflow.get("latest_added", {}).get("enabled", False):
            current_media_items_desc_time = sorted(current_media.items, key=lambda x: self.item_manager.get_extended_info(x).created_at, reverse=True)
            add_expected_cache_items = []
            for media_item in current_media_items_desc_time:
            # Check if the item already exists in the expected cache items, using title_file_path as the comparison key
                if self.item_manager.get_title_file_path(media_item) not in [self.item_manager.get_title_file_path(item) for item in expected_cache_items]:
                    expected_cache_size += self.item_manager.get_extended_info(media_item).size
                    if expected_cache_size > max_cache_size:
                        break
                    add_expected_cache_items.append(media_item)

            expected_cache_items.extend(self.item_manager.copy_update_items(add_expected_cache_items, MediaDbType.CACHE))
            # Add the expected cache items to the cache manifest
            cache_manifest['latest_added_cache_items'] = [CacheManifestItem(full_file_path=item.full_file_path, title_file_path=self.item_manager.get_title_file_path(item), extended=self.item_manager.get_extended_info(item)) for item in add_expected_cache_items]

        # Save the cache manifest
        if not dry_run:
            self.save_cache_manifest(cache_manifest)

        return MediaItemGroup(items=expected_cache_items)

    def load_cache_manifest(self) -> dict[str, List[CacheManifestItem]]:
        """Load the cache manifest from the cache manifest file
        
        Returns:
            dict[str, List[CacheManifestItem]]: A dictionary of cache manifest items
        """
        cache_manifest_path = os.path.join(self.media_library_info.system_data_path, "cache_manifest.json")
        if not os.path.exists(cache_manifest_path):
            return {}
        
        try:
            with open(cache_manifest_path, "r") as f:
                data = json.load(f)
                # Convert the loaded data back into CacheManifestItem objects
                return {
                    key: [CacheManifestItem(**item) for item in items]
                    for key, items in data.items()
                }
        except json.JSONDecodeError:
            # If the file is corrupted or empty, return an empty dict
            return {}
        
    def save_cache_manifest(self, cache_manifest: dict[str, List[CacheManifestItem]]):
        """Save the cache manifest to the cache manifest file
        
        Args:
            cache_manifest (dict[str, List[CacheManifestItem]]): The cache manifest to save
        """
        cache_manifest_path = os.path.join(self.media_library_info.system_data_path, "cache_manifest.json")
        # Convert CacheManifestItem objects to dictionaries
        serializable_manifest = {
            key: [item.model_dump() for item in items] 
            for key, items in cache_manifest.items()
        }
        with open(cache_manifest_path, "w") as f:
            json.dump(serializable_manifest, f)
