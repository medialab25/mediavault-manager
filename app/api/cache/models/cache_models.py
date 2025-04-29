from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class CacheItem(BaseModel):
    """Represents a single item in the cache."""
    id: str
    name: str
    type: str
    size: int
    last_accessed: datetime
    created_at: datetime
    metadata: Optional[dict] = None

    class Config:
        from_attributes = True

class CacheGroup(BaseModel):
    """Represents a group of cache items."""
    name: str
    items: List[CacheItem]
    total_size: int
    item_count: int

    class Config:
        from_attributes = True

class CacheContents(BaseModel):
    """Represents the contents of a cache (hot or cold)."""
    groups: List[CacheGroup]
    total_size: int
    total_items: int

    class Config:
        from_attributes = True

class CacheResponse(BaseModel):
    """Response model for cache API endpoints."""
    hot_cache: Optional[CacheContents] = None
    cold_cache: Optional[CacheContents] = None

    class Config:
        from_attributes = True 