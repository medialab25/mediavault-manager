import os
from pathlib import Path
import shutil
from enum import Enum
from dataclasses import dataclass
from typing import Any, List, Dict

from app.api.managers.media_filter import MediaFilter
from app.api.managers.media_manager import MediaManager
from app.api.managers.media_ops import media_item_and_file_same
from app.api.managers.media_query import MediaQuery
from app.api.models.media_models import MediaDbType, MediaItem, MediaItemGroupDict
from app.api.models.merge_models import MergeResult
from app.api.models.search_request import SearchRequest, SearchRequestAll
# Merge library type
# Inputs:
# - media_type: string. e.g. 'tv', 'movies'
# - quality_list: array of strings. e.g. ['4k', 'uhd', 'hd', 'sd']
# - source_paths: array of folder base paths
# - merged_path: folder base path for merged media
# Outputs:
# - bool: True if merge was successful, False otherwise

class FolderOperationStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class MergeLibrariesResult:
    added_folders: Dict[str, str]  # folder_name -> quality
    updated_folders: Dict[str, str]  # folder_name -> quality
    deleted_folders: Dict[str, str]  # folder_name -> quality
    skipped_folders: Dict[str, str]  # folder_name -> quality
    status: FolderOperationStatus

class MediaMerger:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.user_id = int(config["user"])
        self.group_id = int(config["group"])
        self.media_manager = MediaManager(config)
        self.media_filter = MediaFilter(config)

    def merge_libraries(self, dry_run: bool = False) -> MergeResult:
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
            compare_items_dict: Dict[str, List[MediaItem]] = {}

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

            compare_items = self.media_manager.search_media(
                SearchRequestAll(), merged_path
            )

            for item in compare_items.items:
                key_path = f"{item.media_prefix}-{item.get_relative_folderpath()}"
                if key_path not in compare_items_dict:
                    compare_items_dict[key_path] = []
                compare_items_dict[key_path].append(item)

            # Flatten the lists of items
            all_merged_items = [item for items in merged_items_dict.values() for item in items]
            all_compare_items = [item for items in compare_items_dict.values() for item in items]

            # added_media_items = the items in merged_items_dict that are not in compare_items_dict     
            added_media_items = [
                item 
                for item in all_merged_items
                if not any(
                    item.get_relative_filepath() == target_item.get_relative_filepath() 
                    for target_item in all_compare_items
                )
            ]

            # updated_media_items = the items in merged_items_dict that are in compare_items_dict, that are not the same quality
            updated_media_items = [
                item for item in all_merged_items
                if any(
                    item.get_relative_filepath() == target_item.get_relative_filepath() and item.quality != target_item.quality 
                    for target_item in all_compare_items
                )
            ]

            # deleted_media_items = the items in compare_items_dict that are not in merged_items_dict
            deleted_media_items = [
                item 
                for item in all_compare_items
                if not any(
                    item.get_relative_filepath() == target_item.get_relative_filepath() 
                    for target_item in all_merged_items
                )
            ]

            # skipped_media_items = the items in compare_items_dict that are in merged_items_dict but are the same quality as the target item
            #skipped_media_items = [
            #    item 
            #    for item in all_compare_items
            #    if any(
            #        item.get_relative_filepath() == target_item.get_relative_filepath() and item.quality == target_item.quality 
            #        for target_item in all_merged_items
            #    )
            #]
        self.create_linked_media('/tmp/merged', dry_run=dry_run)
        if dry_run:
            return MergeResult(
                added_media_items=added_media_items,
                updated_media_items=updated_media_items,
                deleted_media_items=deleted_media_items
                #skipped_media_items=skipped_media_items
            )

        # Delete items  
        for item in deleted_media_items:
            os.remove(item.full_path)

        # Update folders
        for updated_item in updated_media_items + added_media_items:
            # Create target path if not exists
            target_file_path = os.path.join(merged_path, f"{updated_item.media_prefix}-{updated_item.quality}", updated_item.get_relative_filepath())
            if not os.path.exists(os.path.dirname(target_file_path)):
                os.makedirs(os.path.dirname(target_file_path), mode=0o755)
                os.chown(os.path.dirname(target_file_path), self.user_id, self.group_id)

            # Hard link the item to the merged path, removing the old item if it exists
            if os.path.exists(target_file_path):
                os.remove(target_file_path)
            os.link(updated_item.full_path, target_file_path)

        return MergeResult(
            added_media_items=added_media_items,
            updated_media_items=updated_media_items,
            deleted_media_items=deleted_media_items
            #skipped_media_items=skipped_media_items
        )

    def create_linked_media(self, target_path: str, dry_run: bool = False) -> list[str]:
        linked_files = []
        for media_type, config in self.config["source_matrix"].items():
            if not config.get("merged_path"):
                continue

            if not config.get("quality_order"):
                continue

            # Get quality and prefix from config
            merged_path = config["merged_path"]

            source_media_items = self.media_manager.search_media(
                SearchRequest(
                    db_type=[MediaDbType.ALL]
                ), merged_path
            )

            for item in source_media_items.items:
                # For each items full path, create a hard link to the target path recursively and create folders as required.
                target_file_path = os.path.join(target_path, item.get_relative_filepath())
                linked_files.append(target_file_path)

                # See if file exists and is the same as the media item
                if os.path.exists(target_file_path):
                    if media_item_and_file_same(item, target_file_path):
                        continue

                if dry_run:
                    continue

                if not os.path.exists(os.path.dirname(target_file_path)):
                    os.makedirs(os.path.dirname(target_file_path), mode=0o755)
                    os.chown(os.path.dirname(target_file_path), self.user_id, self.group_id)
                
                if not os.path.exists(target_file_path):
                    os.link(item.full_path, target_file_path)

        # Remove any files and empty folders in target_path that are not in the linked_files list
        if not dry_run and os.path.exists(target_path):
            for root, dirs, files in os.walk(target_path, topdown=False):
                # Remove files not in linked_files
                for file in files:
                    full_path = os.path.join(root, file)
                    if full_path not in linked_files:
                        os.remove(full_path)
                
                # Remove empty directories
                for dir in dirs:
                    dir_path = os.path.join(root, dir)
                    if not os.listdir(dir_path):
                        os.rmdir(dir_path)
        
        return linked_files
