
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

