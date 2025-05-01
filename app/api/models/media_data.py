from typing import List
from pydantic import BaseModel

class MediaItem(BaseModel):
    id: str
    full_path: str
    media_type: str
    quality: str


class MediaItemGroup(BaseModel):
    items: List[MediaItem]
