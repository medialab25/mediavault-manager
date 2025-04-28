from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class Media(BaseModel):
    id: str
    title: str
    type: str  # movie, tv_show, music, etc.
    path: str
    size: int
    created_at: datetime
    updated_at: datetime
    metadata: Optional[dict] = None

    class Config:
        from_attributes = True

class Episode(BaseModel):
    id: str
    title: str
    episode_number: int
    path: str
    size: int
    duration: Optional[int] = None  # Duration in seconds
    metadata: Optional[dict] = None

    class Config:
        from_attributes = True

class Season(BaseModel):
    id: str
    season_number: int
    episodes: List[Episode]
    metadata: Optional[dict] = None

    class Config:
        from_attributes = True

class Movie(Media):
    duration: Optional[int] = None  # Duration in seconds
    release_year: Optional[int] = None
    director: Optional[str] = None
    cast: Optional[List[str]] = None

    class Config:
        from_attributes = True

class TVShow(Media):
    seasons: List[Season]
    total_seasons: int
    total_episodes: int
    network: Optional[str] = None
    status: Optional[str] = None  # ongoing, ended, etc.

    class Config:
        from_attributes = True 