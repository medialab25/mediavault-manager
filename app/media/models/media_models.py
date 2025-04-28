from datetime import datetime
from typing import Optional
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