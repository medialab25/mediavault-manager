import os
from pathlib import Path
import shutil
from enum import Enum
from dataclasses import dataclass
from typing import Any, List, Dict

from app.api.managers.item_manager import ItemManager
from app.api.managers.media_filter import MediaFilter
from app.api.managers.media_manager import MediaManager
from app.api.managers.media_query import MediaQuery
from app.api.models.media_models import MediaDbType, MediaItem, MediaItemGroup, MediaItemGroupDict, MediaItemGroupList
from app.api.models.search_request import SearchRequest

class FolderOperationStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

class MediaMerger:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.media_filter = MediaFilter(config)
        self.cache_path = config["cache_path"]
        self.media_manager = MediaManager(config)
        self.media_library_info = self.media_manager.get_media_library_info()   
        self.item_manager = ItemManager(config)

    def merge_libraries(self, current_media: MediaItemGroup, current_cache: MediaItemGroup) -> MediaItemGroup:
        """Merge the libraries into a single media item group

        Returns:
            MediaItemGroup: The merged media item group
        """
        result_items = []
        for media_key, media_matrix_info in self.media_library_info.media_matrix_info.items():
            # Initialize result group
            result_item_group = MediaItemGroup(items=[])
    
            merge_name = media_matrix_info.merge_name
            if not merge_name:
                continue

            if not media_matrix_info.quality_order:
                continue

            # Get quality and prefix from config
            quality_order = media_matrix_info.quality_order
            prefix = media_matrix_info.media_prefix
            use_cache = media_matrix_info.use_cache

            result_item_group.metadata = {
                "media_key": media_key
            }

            # Get all from this quality and prefix
            merged_items_dict: Dict[str, List[MediaItem]] = {}

            merged_quality_index: Dict[str, int] = {}
            for quality in quality_order:
                # get index for this quality
                quality_index = quality_order.index(quality)
                media_query = MediaQuery(current_media)
                media_quality_items = media_query.get_items(SearchRequest(quality=quality, media_prefix=prefix))

                for item in media_quality_items.items:
                    # get title/relative_path
                    key_path = f"{item.media_prefix}-{item.title}-{item.get_relative_title_folderpath()}"
                    # create list if key_path not exists
                    if key_path not in merged_quality_index:
                        merged_items_dict[key_path] = [item]
                        merged_quality_index[key_path] = quality_index
                    else:
                        if quality_index == merged_quality_index[key_path]:
                            merged_items_dict[key_path].append(item)

            # Flatten the lists of items
            all_merged_items = [item for items in merged_items_dict.values() for item in items]

            for item in all_merged_items:
                current_item = item

                # Does current item exist in cache, using get_matrix_filepath as comparison key
                cache_items = self.item_manager.get_matching_items(current_item, current_cache.items)

                if cache_items and len(cache_items) > 0:
                    for cache_item in cache_items:
                        if use_cache:
                            current_item = cache_item.clone_with_update(MediaDbType.CACHE)
                        else:
                            current_item = item

                result_items.append(current_item)
                
        return MediaItemGroup(items=result_items)
