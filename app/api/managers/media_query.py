from typing import List
from app.api.managers.media_filter import MediaFilter
from app.api.models.media_models import MediaDbType, MediaItem, MediaItemGroup
from app.api.models.search_request import SearchRequest

class MediaQuery:
    def __init__(self, media_item_group: MediaItemGroup):
        self.media_item_group = media_item_group

    def get_items(self, search_request: SearchRequest) -> MediaItemGroup:
        # Filter items based on search request
        media_filter = MediaFilter(search_request)
        filtered_items = [item for item in self.media_item_group.items if media_filter.is_match(item)]
        return MediaItemGroup(items=filtered_items)
    
    def get_full_paths_list(self) -> List[str]:
        return [item.full_path for item in self.media_item_group.items]
    
    def get_item_in_target_group(self, source: MediaItem, target_group: MediaItemGroup) -> MediaItem:
        return next((target_item for target_item in target_group.items if target_item.get_matrix_filepath() == source.get_matrix_filepath()), None)
