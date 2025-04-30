import os
import shutil
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict

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
    def __init__(self, user_id: int, group_id: int):
        self.user_id = user_id
        self.group_id = group_id
        self.merged_folders = {}  # Dictionary to track merged folders and their quality
        self.added_folders = {}  # Dictionary to track added folders and their quality
        self.updated_folders = {}  # Dictionary to track updated folders and their quality
        self.deleted_folders = {}  # Dictionary to track deleted folders and their quality
        self.skipped_folders = {}  # Dictionary to track skipped folders and their quality

    def merge_libraries(self, media_type: str, source_paths: list[str], quality_list: list[str], merged_path: str) -> MergeLibrariesResult:
        success = True
        self.merged_folders = {}  # Reset merged folders
        self.added_folders = {}  # Reset added folders
        self.updated_folders = {}  # Reset updated folders
        self.deleted_folders = {}  # Reset deleted folders
        self.skipped_folders = {}  # Reset skipped folders

        for source_path in source_paths:
            for quality in quality_list:
                media_folder = f"{media_type}-{quality}"
                media_path = f"{source_path}/{media_folder}"

                if os.path.exists(media_path):
                    folders = os.listdir(media_path)

                    for folder in folders:
                        self.merge_folder(media_path, folder, merged_path, quality, quality_list)

        # Cleanup folders in merged_path that are not in merged_folders
        for folder in os.listdir(merged_path):
            if folder not in self.merged_folders:
                print(f"Removing folder {folder} from {merged_path} because it is not in merged_folders")
                quality = self.get_folder_quality_flags(os.path.join(merged_path, folder), quality_list)
                shutil.rmtree(os.path.join(merged_path, folder))
                self.deleted_folders[folder] = quality if quality else "unknown"

        return MergeLibrariesResult(
            added_folders=self.added_folders,
            updated_folders=self.updated_folders,
            deleted_folders=self.deleted_folders,
            skipped_folders=self.skipped_folders,
            status=FolderOperationStatus.SUCCESS if success else FolderOperationStatus.FAILED
        )

    def get_folder_flags(self, media_path: str) -> list[str]:
        folder_flags = []
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

    def merge_folder(self, media_path: str, folder: str, merged_path: str, quality: str, quality_list: list[str]) -> bool:
        success = True

        source_path = f"{media_path}/{folder}"
        target_path = f"{merged_path}/{folder}"
        if not os.path.exists(target_path):
            try:
                os.makedirs(target_path, mode=0o755)
                os.chown(target_path, self.user_id, self.group_id)
            except PermissionError as e:
                return False

        if folder in self.merged_folders:
            existing_quality = self.merged_folders[folder]
            if quality_list.index(existing_quality) <= quality_list.index(quality):
                print(f"Folder {folder} already merged with {existing_quality} (better or equal to {quality}), skipping")
                self.skipped_folders[folder] = existing_quality
                return True
            else:
                print(f"Folder {folder} already merged with {existing_quality} (worse than {quality}), updating")
                self.updated_folders[folder] = quality
        else:
            current_quality = self.get_folder_quality_flags(target_path, quality_list)
            print(f"Current quality of {folder}: {current_quality}")
            if current_quality is not None:
                if quality_list.index(current_quality) == quality_list.index(quality):
                    print(f"Folder {folder} already merged with {current_quality} (equal to {quality}), skipping")
                    self.merged_folders[folder] = quality
                    self.skipped_folders[folder] = current_quality
                    return True
                else:
                    print(f"Folder {folder} already merged with {current_quality} (worse than {quality}), updating")
                    self.updated_folders[folder] = quality
            else:
                print(f"Folder {folder} is not merged, adding")
                self.added_folders[folder] = quality

        self.merged_folders[folder] = quality
        
        if os.path.exists(target_path):
            for root, dirs, files in os.walk(target_path, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                    print(f"Removing all files in {target_path}")
                for name in dirs:
                    os.rmdir(os.path.join(root, name))

        flag_file = f"{target_path}/.{quality}"
        with open(flag_file, 'w') as f:
            f.write(f"{quality}")

        for root, dirs, files in os.walk(source_path):
            for file in files:
                rel_path = os.path.relpath(root, source_path)
                src = os.path.join(root, file)
                dst_dir = os.path.join(target_path, rel_path)
                dst = os.path.join(dst_dir, file)

                os.makedirs(dst_dir, mode=0o755, exist_ok=True)
                os.chown(dst_dir, self.user_id, self.group_id)

                try:
                    print(f"Linking {src} to {dst}")
                    os.link(src, dst)
                except FileExistsError:
                    print(f"Skipping existing file: {dst}")
                    pass
                except OSError as e:
                    print(f"Failed to link {src} to {dst}: {e}")
                    success = False

        return success