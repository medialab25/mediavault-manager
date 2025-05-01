from typing import List, Optional
from pydantic import BaseModel

from app.api.managers.models.media_models import ExtendedMediaInfo

class MediaItem(BaseModel):
    id: str
    full_path: str
    media_type: str
    quality: str
    title: str
    season: Optional[int] = None
    episode: Optional[int] = None
    extended: Optional[ExtendedMediaInfo] = None

class MediaItemGroup(BaseModel):
    items: List[MediaItem]
