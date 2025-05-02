import logging
import os
import shutil
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict

from app.api.managers.media_manager import MediaManager
from app.api.managers.media_query import MediaQuery
from app.api.models.media_models import MediaDbType, MediaItem, MediaItemGroup, MediaItemGroupDict
from app.api.models.search_request import SearchHasFilter, SearchRequest

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
    added_folders: list[str]
    updated_folders: list[str]
    deleted_folders: list[str]
    skipped_folders: list[str]
    status: FolderOperationStatus

class MediaMerger:
    def __init__(self, config: dict):
        self.config = config

        self.user = int(config.get("user", 1000))
        self.group = int(config.get("group", 1000))
        self.media_manager = MediaManager(config)

    def merge_libraries(self, dry_run: bool = False) -> MediaItemGroupDict:
        added_media_items = []
        skipped_media_items = []
        updated_media_items = []
        deleted_media_items_path = []

        media_items = self.media_manager.search_media(
            SearchRequest(
                db_type=[MediaDbType.MEDIA],
                has_merged_path=SearchHasFilter.YES
            )
        )

        # For the source_matrix in config, get the dict of child items and the entries
        source_matrix = self.config.get("source_matrix", {})
        for source_key, source_value in source_matrix.items():
            merged_path = source_value.get("merged_path", None)
            quality_order = source_value.get("quality_order", [])
            merged_path = source_value.get("merged_path", None)
            if merged_path is None:
                continue

            target_folder = merged_path

            # Get list of folders of the merged path, if it exists and build a dict of quality flags
            merged_folders = os.listdir(target_folder) if os.path.exists(target_folder) else []
            merged_folders_dict = {}
            
            for folder in merged_folders:
                merged_folders_dict[folder] = self.get_folder_quality_flags(os.path.join(target_folder, folder), quality_order)

            for src_item in media_items.items:
                src_title = src_item.title

                # Does the title exist in the target_folders?
                if src_title in merged_folders_dict:
                    # Check if the quality flag is the same
                    if merged_folders_dict[src_title] == src_item.quality:
                        logging.info(f"Title {src_title} already merged with {src_item.quality}, skipping")
                        skipped_media_items.append(src_item)
                    else:
                        # Ensure both qualities exist in quality_order before comparing
                        if src_item.quality not in quality_order:
                            logging.warning(f"Quality not found in quality_order for {src_title}: src={src_item.quality}")
                            skipped_media_items.append(src_item)
                        elif merged_folders_dict[src_title] not in quality_order:
                            logging.warning(f"Quality not found in quality_order for {src_title}: merged={merged_folders_dict[src_title]}")
                            added_media_items.append(src_item)
                        # Is quality of src better than the quality of the target?
                        elif quality_order.index(src_item.quality) < quality_order.index(merged_folders_dict[src_title]):
                            logging.info(f"Title {src_title} already merged with {src_item.quality}, updating")
                            updated_media_items.append(src_item)
                            merged_folders_dict[src_title] = src_item.quality
                        else:
                            logging.info(f"Title {src_title} already merged with {src_item.quality}, skipping")
                            skipped_media_items.append(src_item)
                else:
                    added_media_items.append(src_item)
                    merged_folders_dict[src_title] = src_item.quality

            # Update the quality of the target folder
            for folder in merged_folders_dict.keys():
                target_path = os.path.join(target_folder, folder)
                # Remove the quality file if it exists, any starting with a .
                for file in os.listdir(target_path):
                    if file.startswith("."):
                        if not dry_run:
                            os.remove(os.path.join(target_path, file))
                # Create the quality file
                if not dry_run:
                    with open(os.path.join(target_path, ".quality"), "w") as f:
                        f.write(merged_folders_dict[folder])

            # Cleanup folders in merged_path that are not in merged_folders
            src_folders = list({item.title: None for item in media_items.items}.keys())

            # for each folder in target_folder, if it is not in src_folders, delete it
            for folder in merged_folders_dict.keys():
                if folder not in src_folders:
                    delete_folder_path = os.path.join(target_folder, folder)
                    deleted_media_items_path.append(delete_folder_path)

        result = MediaItemGroupDict(
            groups={
                "added": MediaItemGroup(items=added_media_items),
                "updated": MediaItemGroup(items=updated_media_items),
                "skipped": MediaItemGroup(items=skipped_media_items),
                "deleted": MediaItemGroup(items=[MediaItem(
                    full_path=path,
                    title=os.path.basename(path),
                    id=path,
                    db_type=MediaDbType.MEDIA,
                    media_type="unknown",
                    media_prefix="unknown",
                    quality="unknown"
                ) for path in deleted_media_items_path])
            }
        )

        if dry_run:
            return result

        # For all added_media_items, create any folders needed and hard-link the files removing any pre-existing ones
        for item in added_media_items + updated_media_items:
            target_path = os.path.join(target_folder, item.title)
            if not os.path.exists(target_path):
                os.makedirs(target_path, mode=0o755)
                os.chown(target_path, self.user, self.group)

            # Hard-link the file removing any pre-existing ones
            src = item.full_path
            dst = os.path.join(target_path, item.title)
            if os.path.exists(dst):
                os.unlink(dst)
                os.link(src, dst)

        # for all deleted_media_items_path, delete the folder
        for path in deleted_media_items_path:
            shutil.rmtree(path)

        return result


    # def merge_libraries(self, media_type: str, source_paths: list[str], quality_list: list[str], merged_path: str, dry_run: bool = False) -> MergeLibrariesResult:
    #     success = True
    #     self.merged_folders = {}  # Reset merged folders
    #     self.added_folders = {}  # Reset added folders
    #     self.updated_folders = {}  # Reset updated folders
    #     self.deleted_folders = {}  # Reset deleted folders
    #     self.skipped_folders = {}  # Reset skipped folders

    #     for source_path in source_paths:
    #         for quality in quality_list:
    #             media_folder = f"{media_type}-{quality}"
    #             media_path = f"{source_path}/{media_folder}"

    #             if os.path.exists(media_path):
    #                 folders = os.listdir(media_path)

    #                 for folder in folders:
    #                     self.merge_folder(media_path, folder, merged_path, quality, quality_list, dry_run)

    #     # Cleanup folders in merged_path that are not in merged_folders
    #     if os.path.exists(merged_path):
    #         for folder in os.listdir(merged_path):
    #             if folder not in self.merged_folders:
    #                 print(f"Removing folder {folder} from {merged_path} because it is not in merged_folders")
    #                 quality = self.get_folder_quality_flags(os.path.join(merged_path, folder), quality_list)
    #                 if not dry_run:
    #                     shutil.rmtree(os.path.join(merged_path, folder))
    #                 self.deleted_folders[folder] = quality if quality else "unknown"

    #     return MergeLibrariesResult(
    #         added_folders=self.added_folders,
    #         updated_folders=self.updated_folders,
    #         deleted_folders=self.deleted_folders,
    #         skipped_folders=self.skipped_folders,
    #         status=FolderOperationStatus.SUCCESS if success else FolderOperationStatus.FAILED
    #     )

    def get_folder_flags(self, media_path: str) -> list[str]:
        folder_flags = []
        if os.path.exists(media_path):
            for file in os.listdir(media_path):
                if file.startswith('.'):
                    folder_flags.append(file[1:])
        return folder_flags

    def get_folder_quality_flags(self, folder: str, quality_list: list[str]) -> str:
        folder_flags = self.get_folder_flags(folder)
        for flag in folder_flags:
            if flag in quality_list:
                return flag
        return None

    # def merge_folder(self, media_path: str, folder: str, merged_path: str, quality: str, quality_list: list[str], dry_run: bool = False) -> bool:
    #     success = True

    #     source_path = f"{media_path}/{folder}"
    #     target_path = f"{merged_path}/{folder}"
    #     if not os.path.exists(target_path):
    #         try:
    #             if not dry_run:
    #                 os.makedirs(target_path, mode=0o755)
    #                 os.chown(target_path, self.user_id, self.group_id)
    #         except PermissionError as e:
    #             return False

    #     if folder in self.merged_folders:
    #         existing_quality = self.merged_folders[folder]
    #         if quality_list.index(existing_quality) <= quality_list.index(quality):
    #             print(f"Folder {folder} already merged with {existing_quality} (better or equal to {quality}), skipping")
    #             self.skipped_folders[folder] = existing_quality
    #             return True
    #         else:
    #             print(f"Folder {folder} already merged with {existing_quality} (worse than {quality}), updating")
    #             self.updated_folders[folder] = quality
    #     else:
    #         current_quality = self.get_folder_quality_flags(target_path, quality_list)
    #         print(f"Current quality of {folder}: {current_quality}")
    #         if current_quality is not None:
    #             if quality_list.index(current_quality) == quality_list.index(quality):
    #                 print(f"Folder {folder} already merged with {current_quality} (equal to {quality}), skipping")
    #                 self.merged_folders[folder] = quality
    #                 self.skipped_folders[folder] = current_quality
    #                 return True
    #             else:
    #                 print(f"Folder {folder} already merged with {current_quality} (worse than {quality}), updating")
    #                 self.updated_folders[folder] = quality
    #         else:
    #             print(f"Folder {folder} is not merged, adding")
    #             self.added_folders[folder] = quality

    #     self.merged_folders[folder] = quality
        
    #     if dry_run:
    #         return True

    #     if os.path.exists(target_path):
    #         for root, dirs, files in os.walk(target_path, topdown=False):
    #             for name in files:
    #                 os.remove(os.path.join(root, name))
    #                 print(f"Removing all files in {target_path}")
    #             for name in dirs:
    #                 os.rmdir(os.path.join(root, name))

    #     flag_file = f"{target_path}/.{quality}"
    #     with open(flag_file, 'w') as f:
    #         f.write(f"{quality}")

    #     for root, dirs, files in os.walk(source_path):
    #         for file in files:
    #             rel_path = os.path.relpath(root, source_path)
    #             src = os.path.join(root, file)
    #             dst_dir = os.path.join(target_path, rel_path)
    #             dst = os.path.join(dst_dir, file)

    #             os.makedirs(dst_dir, mode=0o755, exist_ok=True)
    #             os.chown(dst_dir, self.user_id, self.group_id)

    #             try:
    #                 print(f"Linking {src} to {dst}")
    #                 os.link(src, dst)
    #             except FileExistsError:
    #                 print(f"Skipping existing file: {dst}")
    #                 pass
    #             except OSError as e:
    #                 print(f"Failed to link {src} to {dst}: {e}")
    #                 success = False

    #     return success