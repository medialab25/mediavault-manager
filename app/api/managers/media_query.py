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
    
    def get_item(self, item_id: str) -> MediaItem:
        return next((item for item in self.media_item_group.items if item.id == item_id), None)

    def get_items_by_ids(self, item_ids: List[str], db_type: MediaDbType = None) -> List[MediaItem]:
        if db_type:
            return [item for item in self.media_item_group.items if item.id in item_ids and item.db_type == db_type]
        else:
            return [item for item in self.media_item_group.items if item.id in item_ids]
