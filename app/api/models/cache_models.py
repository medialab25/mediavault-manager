from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class CacheItem(BaseModel):
    """Represents a single item in the cache"""
    id: str
    name: str
    type: str
    size: int
    last_accessed: datetime
    created_at: datetime

class CacheGroup(BaseModel):
    """Represents a group of cache items"""
    name: str
    items: List[CacheItem]
    total_size: int
    item_count: int

class CacheContents(BaseModel):
    """Represents the entire cache contents"""
    groups: List[CacheGroup] 