from typing import Optional, List
from pydantic import BaseModel

from app.api.models.media_models import MediaDbType

class SearchRequest(BaseModel):
    """
    Model for handling search API requests.
    """
    query: Optional[str] = ""       # The search query string
    quality: Optional[str] = None   # hd, uhd, 4k, etc.
    media_type: Optional[str] = None # tv, movie, etc.
    add_extended_info: bool = False # Whether to add extended info to the response
    id: Optional[str] = None        # Optional media ID to search for
    season: Optional[int] = None    # Optional season number to search for
    episode: Optional[int] = None   # Optional episode number to search for
    media_prefix: Optional[str] = None # Optional media prefix to search for
    db_type: Optional[List[MediaDbType]] = [MediaDbType.MEDIA]  # List of database types to search in
