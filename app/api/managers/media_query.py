from typing import List
from app.api.models.media_models import MediaItemGroup
from app.api.models.search_request import SearchRequest

class MediaQuery:
    def __init__(self, media_item_group: MediaItemGroup):
        self.media_item_group = media_item_group

    def get_items(self, search_request: SearchRequest) -> MediaItemGroup:
        return self.media_item_group
    
    def get_full_paths_list(self) -> List[str]:
        return [item.full_path for item in self.media_item_group.items]
        