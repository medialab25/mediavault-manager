from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

# enum for the db types, MEDIA, CACHE, SHADOW
class MediaDbType(Enum):
    MEDIA = "media"
    CACHE = "cache"
    SHADOW = "shadow"
    UNDEFINED = "undefined"
    ALL = "all"

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
    db_type: MediaDbType
    relative_title_filepath: str   # The filepath relative to the top-level title
    media_type: str
    media_prefix: str
    quality: str
    title: str
    season: Optional[int] = None
    episode: Optional[int] = None
    extended: Optional[ExtendedMediaInfo] = None

    def clone(self) -> "MediaItem":
        return MediaItem(
            db_type=self.db_type,
            media_type=self.media_type,
            media_prefix=self.media_prefix,
            quality=self.quality,
            title=self.title,
            season=self.season,
            episode=self.episode,
            relative_title_filepath=self.relative_title_filepath
        )
    
    def clone_with_update(self, db_type: MediaDbType) -> "MediaItem":
        result = self.clone()
        result.db_type = db_type
        return result

    def get_full_filepath(self, base_path: str) -> str:
        return Path(base_path) / self.relative_title_filepath
    
    def get_full_matrix_filepath(self, base_path: str) -> str:
        return Path(base_path) / self.get_matrix_filepath()
    
    def get_relative_matrix_filepath(self) -> str:
        return f"{self.media_prefix}-{self.quality}/{self.relative_title_filepath}"

class MediaItemGroup(BaseModel):
    items: List[MediaItem]
    metadata: Optional[Dict[str, Any]] = None

class MediaItemGroupList(BaseModel):
    groups: List[MediaItemGroup]

class MediaItemGroupDict(BaseModel):
    groups: Dict[str, MediaItemGroup]
