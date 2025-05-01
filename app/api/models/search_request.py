from typing import Optional
from pydantic import BaseModel

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
    
#    title: Optional[str] = None # 
#    title: str
#    season: Optional[int] = None
#    episode: Optional[int] = None
#    media_prefix: Optional[str] = None
#    quality: Optional[str] = None
#    media_type: Optional[str] = None
    # class Config:
    #     json_schema_extra = {
    #         "example": {
    #             "title": "The Big Bang Theory", 
    #             "season": 1,
    #             "episode": 1,
    #             "media_prefix": "",
    #             "quality": "1080p",
    #             "media_type": "tv"
    #         }
    #     }
