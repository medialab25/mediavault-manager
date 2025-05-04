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
    id: str
    db_type: MediaDbType
    full_path: str
    title_path: str
    media_type: str
    media_prefix: str
    quality: str
    title: str
    season: Optional[int] = None
    episode: Optional[int] = None
    extended: Optional[ExtendedMediaInfo] = None

    def get_relative_filepath(self) -> str:
        """Get the subpath of the file relative to its title folder by removing title_path"""
        # Convert both paths to Path objects
        full_path = Path(self.full_path)
        title_path_obj = Path(self.title_path)
        
        try:
            # Get the relative path by removing the title_path
            return str(full_path.relative_to(title_path_obj))
        except ValueError:
            # If paths are not related, return empty string
            return ""

    def get_relative_folderpath(self) -> str:
        """Get the subpath of the file relative to its title folder by removing title_path"""
        # Convert both paths to Path objects
        full_path = Path(self.full_path)
        title_path_obj = Path(self.title_path)
        
        try:
            # Get the relative path by removing the title_path and return parent folder
            return str(full_path.relative_to(title_path_obj).parent)
        except ValueError:
            # If paths are not related, return empty string
            return ""

class MediaItemGroup(BaseModel):
    items: List[MediaItem]
    metadata: Optional[Dict[str, Any]] = None

class MediaItemGroupList(BaseModel):
    groups: List[MediaItemGroup]

class MediaItemGroupDict(BaseModel):
    groups: Dict[str, MediaItemGroup]
