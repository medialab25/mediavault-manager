from app.api.models.media_models import MediaItemGroup
from app.api.models.search_request import SearchRequest

class MediaQuery:
    def __init__(self, media_item_group: MediaItemGroup):
        self.media_item_group = media_item_group

    def get_items(self, search_request: SearchRequest) -> MediaItemGroup:
        return self.media_item_group
        