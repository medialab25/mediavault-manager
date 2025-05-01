from typing import List, Optional
from pydantic import BaseModel

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
    path: str
    media_folder_items: List[MediaItemFolder] = []

class MediaGroupFolderList(BaseModel):
    groups: List[MediaGroupFolder]

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
