from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel

# enum for the db types, MEDIA, CACHE, SHADOW
class MediaDbType(Enum):
    MEDIA = "media"
    CACHE = "cache"
    SHADOW = "shadow"

class ExtendedMediaInfo(BaseModel):
    size: int
    created_at: float
    updated_at: float
    metadata: Optional[dict] = None

class MediaFileItem(BaseModel):
    path: str
    season: Optional[int] = None
    episode: Optional[int] = None
    extended: Optional[ExtendedMediaInfo] = None

class MediaItemFolder(BaseModel):
    title: str
    media_type: str
    path: str
    items: List[MediaFileItem] = []

class MediaGroupFolder(BaseModel):
    media_type: str
    media_prefix: str
    quality: str
    cache_export: bool
    path: str
    media_folder_items: List[MediaItemFolder] = []

class MediaGroupFolderList(BaseModel):
    groups: List[MediaGroupFolder]

class MediaItem(BaseModel):
    id: str
    db_type: MediaDbType
    full_path: str
    media_type: str
    media_prefix: str
    quality: str
    title: str
    season: Optional[int] = None
    episode: Optional[int] = None
    extended: Optional[ExtendedMediaInfo] = None

class MediaItemGroup(BaseModel):
    items: List[MediaItem]

class MediaItemGroupList(BaseModel):
    groups: List[MediaItemGroup]

class MediaItemGroupDict(BaseModel):
    groups: Dict[str, MediaItemGroup]
