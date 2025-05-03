import os
from app.api.managers.media_manager import MediaManager
from app.api.models.media_models import MediaItem


def get_intersect_based_on_rel_path(source_items: list[MediaItem], target_items: list[MediaItem]) -> list[MediaItem]:
    # Get the intersect of the source and target items based on the relative path in the target 
    return [item for item in target_items if item.relative_path in [item.relative_path for item in source_items]]

def get_missing_items(source_items: list[MediaItem], target_items: list[MediaItem], compare_fn=lambda x, y: x.relative_path == y.relative_path) -> list[MediaItem]:
    # Get the items that are in the target but not in the source based on the compare function
    return [item for item in target_items if not any(compare_fn(item, source_item) for source_item in source_items)]

def get_added_items(source_items: list[MediaItem], target_items: list[MediaItem], compare_fn=lambda x, y: x.relative_path == y.relative_path) -> list[MediaItem]:
    # Get the items that are in the source but not in the target based on the relative path
    return [item for item in source_items if not any(compare_fn(item, target_item) for target_item in target_items)]

# function to show how to use get_missing_items to compare quality, pass in compare fn for quality
def show_missing_items():
    source_items = [MediaItem(relative_path="path/to/item1", quality="1080p")]
    target_items = [MediaItem(relative_path="path/to/item1", quality="1080p"), MediaItem(relative_path="path/to/item2", quality="1080p")]
    missing_items = get_missing_items(source_items, target_items, compare_fn=lambda x, y: x.quality == y.quality)
    print(missing_items)

def media_item_and_file_same(media_item: MediaItem, file_path: str) -> bool:
    """Compare a MediaItem with a file path to determine if they represent the same file.
    
    Args:
        media_item: The MediaItem to compare
        file_path: The file path to compare against
        media_manager: The MediaManager instance to use for populating extended info
        
    Returns:
        bool: True if the files are the same, False otherwise
    """
    # Check if both files exist
    if not os.path.exists(media_item.full_path) or not os.path.exists(file_path):
        return False
        
    # Compare file names
    if os.path.basename(media_item.full_path) != os.path.basename(file_path):
        return False
        
    # Compare file sizes
    source_size = os.path.getsize(media_item.full_path)
    target_size = os.path.getsize(file_path)
    if source_size != target_size:
        return False
        
    return True
