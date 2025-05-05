import os
from pathlib import Path
import shutil
from enum import Enum
from dataclasses import dataclass
from typing import Any, List, Dict

from app.api.managers.media_filter import MediaFilter
from app.api.managers.media_manager import MediaManager
from app.api.models.media_models import MediaDbType, MediaItem, MediaItemGroup, MediaItemGroupDict
from app.api.models.search_request import SearchRequest

class FolderOperationStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

class MediaMerger:
    def __init__(self, config: dict[str, Any]):
        self.config = config

        self.media_manager = MediaManager(config)
        self.media_filter = MediaFilter(config)

    def merge_libraries(self) -> MediaItemGroupDict:
        """Merge the libraries into a single media item group dict

        Returns:
            MediaItemGroupDict: The merged media item group dict
        """
        merged_items_group_dict: MediaItemGroupDict = MediaItemGroupDict(groups={})
        cache_path = self.config["cache_path"]

        for media_type, config in self.config["source_matrix"].items():
            if not config.get("merged_path"):
                continue

            if not config.get("quality_order"):
                continue

            # Get quality and prefix from config
            quality_order = config["quality_order"]
            prefix = config["prefix"]
            merged_path = config["merged_path"]

            # Get all from this quality and prefix
            merged_items_dict: Dict[str, List[MediaItem]] = {}

            merged_quality_index: Dict[str, int] = {}
            for quality in quality_order:
                # get index for this quality
                quality_index = quality_order.index(quality)
                media_quality_items = self.media_manager.search_media(
                    SearchRequest(
                        quality=quality, 
                        media_prefix=prefix,
                        db_type=[MediaDbType.MEDIA]
                    )
                )  

                for item in media_quality_items.items:
                    # get title/relative_path
                    key_path = f"{item.media_prefix}-{item.get_relative_folderpath()}"
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
                key = f"{item.media_prefix}-{item.quality}"
                if key not in merged_items_group_dict.groups:
                    metadata = {
                        "merged_path": merged_path,
                        "prefix": item.media_prefix,
                        "quality": item.quality,
                        "cache_path": cache_path,
                        "cache_data": config.get("cache_data", False)
                    }
                    merged_items_group_dict.groups[key] = MediaItemGroup(
                        items=[item],
                        metadata=metadata
                    )
                else:
                    merged_items_group_dict.groups[key].items.append(item)

        return merged_items_group_dict
