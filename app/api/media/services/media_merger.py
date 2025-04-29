import os
import shutil

# Merge library type
# Inputs:
# - media_type: string. e.g. 'tv', 'movies'
# - quality_list: array of strings. e.g. ['4k', 'uhd', 'hd', 'sd']
# - source_paths: array of folder base paths
# - merged_path: folder base path for merged media
# Outputs:
# - bool: True if merge was successful, False otherwise

def merge_libraries(media_type: str, source_paths: list[str], quality_list: list[str], merged_path: str, user_id: int, group_id: int) -> bool:
    success = True
    merged_folders = {}  # Dictionary to track merged folders and their quality
    updated_folders = {}  # Dictionary to track updated folders and their quality
    for source_path in source_paths:
        for quality in quality_list:
            media_folder = f"{media_type}-{quality}"

            media_path = f"{source_path}/{media_folder}"
            #print(f"Media path: {media_path}")
            #print(f"Merging {media_type} from {media_path} to {merged_path}")

            # Get all folders in media_path if it exists
            if os.path.exists(media_path):
                folders = os.listdir(media_path)
                #print(f"Folders: {folders}")

                # For each folder, call merge_folder
                for folder in folders:
                    merge_folder(media_path, folder, merged_path, quality, quality_list, user_id, group_id, merged_folders, updated_folders)

    # Cleanup folders in merged_path that are not in merged_folders
    for folder in os.listdir(merged_path):
        if folder not in merged_folders:
            print(f"Removing folder {folder} from {merged_path} because it is not in merged_folders")
            shutil.rmtree(os.path.join(merged_path, folder))

    # Print merged folders sorted by key with value in a list
    print(f"Merged folders:")
    for key, value in sorted(merged_folders.items()):
        print(f"{key}: {value}")

    print(f"Updated folders:")
    for key, value in sorted(updated_folders.items()):
        print(f"{key}: {value}")

    return success

# Get folder flag
# A folder flag is a file starting with '.' with rest of name being the flag name
# Outputs:
# - array of strings representing the flag names
def get_folder_flags(media_path: str) -> list[str]:
    folder_flags = []
    for file in os.listdir(media_path):
        if file.startswith('.'):
            folder_flags.append(file[1:])
    return folder_flags

# Get folder quality flags
# Inputs:
# - folder: string. e.g. 'tv-4k'
# Outputs:
# - the quality type, so the found flag files need to match with quality array
def get_folder_quality_flags(folder: str, quality_list: list[str]) -> str:
    # get folder flags and see if any of them match with quality_list
    folder_flags = get_folder_flags(folder)
    for flag in folder_flags:
        if flag in quality_list:
            return flag
    return None

def merge_folder(media_path: str, folder: str, merged_path: str, quality: str, quality_list: list[str], user_id: int, group_id: int, merged_folders: dict[str, str], updated_folders: dict[str, str]) -> bool:
    success = True

    # See if folder exists in merged_path, and create it if it doesn't
    source_path = f"{media_path}/{folder}"
    target_path = f"{merged_path}/{folder}"
    if not os.path.exists(target_path):
        #print(f"Folder {folder} does not exist in {merged_path}, creating it")
        try:
            # Create directory with proper permissions
            os.makedirs(target_path, mode=0o755)
            os.chown(target_path, user_id, group_id)
        except PermissionError as e:
            #print(f"Error creating directory {target_path}: {str(e)}")
            return False

    # call get_folder_flags on the folder
    folder_quality_flag = get_folder_quality_flags(target_path, quality_list)
    #print(f"Folder quality flag: {folder_quality_flag}")

    # Check if folder is already merged with a better quality
    if folder in merged_folders:
        existing_quality = merged_folders[folder]
        if quality_list.index(existing_quality) <= quality_list.index(quality):
            print(f"Folder {folder} already merged with {existing_quality} (better or equal to {quality}), skipping")
            return True
        else:
            print(f"Folder {folder} already merged with {existing_quality} (worse than {quality}), updating")
    else:
        # What is the current quality of the folder?
        current_quality = get_folder_quality_flags(target_path, quality_list)
        print(f"Current quality of {folder}: {current_quality}")
        if current_quality is not None:
            if quality_list.index(current_quality) == quality_list.index(quality):
                print(f"Folder {folder} already merged with {current_quality} (equal to {quality}), skipping")
                merged_folders[folder] = quality
                return True
            else:
                print(f"Folder {folder} already merged with {current_quality} (worse than {quality}), updating")

    # Add folder to merged_folders
    merged_folders[folder] = quality
    updated_folders[folder] = quality

    # If files exist in target_path, recursively remove them all
    if os.path.exists(target_path):
        for root, dirs, files in os.walk(target_path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
                print(f"Removing all files in {target_path}")
            for name in dirs:
                os.rmdir(os.path.join(root, name))

    # Merge folder
    # Create a flag file with current quality
    flag_file = f"{target_path}/.{quality}"
    with open(flag_file, 'w') as f:
        f.write(f"{quality}")
        #print(f"Created flag file {flag_file}")

    # Recursively hard link all files in source_path to target_path keeping the same relative path
    for root, dirs, files in os.walk(source_path):
        for file in files:
            rel_path = os.path.relpath(root, source_path)
            src = os.path.join(root, file)
            dst_dir = os.path.join(target_path, rel_path)
            dst = os.path.join(dst_dir, file)

            os.makedirs(dst_dir, mode=0o755, exist_ok=True)
            os.chown(dst_dir, user_id, group_id)

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