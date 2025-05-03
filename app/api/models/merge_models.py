from app.api.models.media_models import MediaItem
from pydantic import BaseModel
from typing import List

class MergeResult(BaseModel):
    added_media_items: List[MediaItem]
    updated_media_items: List[MediaItem]
    deleted_media_items: List[MediaItem]
    #skipped_media_items: List[MediaItem]
    
