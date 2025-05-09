from enum import Enum
from typing import List
from pydantic import BaseModel

class ManifestType(Enum):
    MANUAL = "manual"
    EPISODE = "episode"
    LATEST = "latest"

class ManifestItem(BaseModel):
    full_file_path: str

class ManifestItemGroup(BaseModel):
    manifest_type: ManifestType
    items: List[ManifestItem]

