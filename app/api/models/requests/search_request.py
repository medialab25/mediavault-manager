from typing import Optional
from pydantic import BaseModel

class SearchRequest(BaseModel):
    """
    Model for handling search API requests.
    """
    quality: Optional[str] = None       # hd, uhd, 4k, etc.
    media_type: Optional[str] = None    # tv, movie, etc.


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
