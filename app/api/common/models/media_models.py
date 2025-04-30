from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from enum import Enum

class ExtendedMediaInfo(BaseModel):
    size: int
    created_at: datetime
    updated_at: datetime
    metadata: Optional[dict] = None

class MediaItem(BaseModel):
    path: str
    season: Optional[int] = None
    episode: Optional[int] = None
    extended: Optional[ExtendedMediaInfo] = None
    
    class Config:
        from_attributes = True
   
# Movie/TVShow/Anime/Documentary/Music
class MediaItemFolder(BaseModel):
    title: str
    media_type: str
    path: str
    items: List[MediaItem]

    class Config:
        from_attributes = True

# tv-hd, movies-uhd, anime-4k, documentaries-4k
class MediaGroupFolder(BaseModel):
    media_type: str     # movies, tv
    media_prefix: str  # movies, tv
    quality: str        # 4k, uhd, hd, sd
    path: str           # /media/movies/4k, /media/tv/4k
    media_folder_items: List[MediaItemFolder]
    
    class Config:
        from_attributes = True

class MediaGroupFolderList(BaseModel):
    groups: List[MediaGroupFolder]

    class Config:
        from_attributes = True

class MediaCacheList(BaseModel):
    hot_groups: List[MediaGroupFolderList]
    cold_groups: List[MediaGroupFolderList]

    class Config:
        from_attributes = True