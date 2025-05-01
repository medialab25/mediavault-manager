from pydantic import BaseModel
from app.api.models.media_models import MediaItemGroup


class CacheStatusList(BaseModel):
    pending: MediaItemGroup
    cache: MediaItemGroup