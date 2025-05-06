import os
from pathlib import Path
import shutil
from enum import Enum
from dataclasses import dataclass
from typing import Any, List, Dict

from app.api.managers.media_filter import MediaFilter
from app.api.managers.media_manager import MediaManager
from app.api.managers.media_query import MediaQuery
from app.api.models.media_models import MediaDbType, MediaItem, MediaItemGroup, MediaItemGroupDict
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

    def merge_libraries(self, current_media: MediaItemGroup, current_cache: MediaItemGroup) -> MediaItemGroup:
        """Merge the libraries into a single media item group

        Returns:
            MediaItemGroupDict: The merged media item group dict
        """
        # Initialize result group
        result_item_group = MediaItemGroup(items=[])

        for media_type, config in self.config["source_matrix"].items():
            merge_name = config.get("merge_name", None)
            if not merge_name:
                continue

            if not config.get("quality_order"):
                continue

            # Get quality and prefix from config
            quality_order = config["quality_order"]
            prefix = config["prefix"]
            use_cache = config.get("use_cache", False)

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
                    key_path = f"{item.media_prefix}-{item.get_relative_title_folderpath()}"
                    # create list if key_path not exists
                    if key_path not in merged_quality_index:
                        merged_items_dict[key_path] = [item]
                        merged_quality_index[key_path] = quality_index
                    else:
                        if quality_index == merged_quality_index[key_path]:
                            merged_items_dict[key_path].append(item)

            # Flatten the lists of items
            all_merged_items = [item for items in merged_items_dict.values() for item in items]

            # Add to item group by prefix-quality
            for item in all_merged_items:
                current_item = item

                # Does current item exist in cache, using get_matrix_filepath as comparison key
                cache_items = current_cache.get_equal_items(current_cache)
                if cache_items and len(cache_items) > 0:
                    for cache_item in cache_items:
                        if use_cache:
                            current_item = cache_item.clone_with_update(MediaDbType.CACHE)
                        else:
                            current_item = item

                result_item_group.items.append(current_item)

        return result_item_group
