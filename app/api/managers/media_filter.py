# Class to take a SearchRequest and filter the MediaItemGroup based on the request
import os
from app.api.models.media_models import MediaItem, MediaItemGroup
from app.api.models.search_request import SearchRequest

class MediaFilter:
    def __init__(self, request: SearchRequest):
        self.request = request

    def is_match(self, media_item: MediaItem) -> bool:
        # Check if the media item matches the request
        if self.request.media_type and self.request.media_type != media_item.media_type:
            return False
        if self.request.media_prefix and self.request.media_prefix != media_item.media_prefix:
            return False
        if self.request.quality and self.request.quality != media_item.quality:
            return False
        if self.request.query and self.request.query.lower() not in media_item.title.lower():
            return False
        if self.request.season and self.request.season != media_item.season:
            return False
        if self.request.episode and self.request.episode != media_item.episode:
            return False
        if self.request.db_type and media_item.db_type not in self.request.db_type and not any(db_type.value == "all" for db_type in self.request.db_type):
            return False
        if self.request.matrix_filepath and self.request.matrix_filepath != media_item.get_matrix_filepath():
            return False
        if self.request.relative_filepath and self.request.relative_filepath != media_item.get_relative_filepath():
            return False
        
        return True
