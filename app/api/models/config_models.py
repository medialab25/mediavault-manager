from typing import Dict, List
from pydantic import BaseModel, Field

class SourceMatrixEntry(BaseModel):
    quality_order: List[str] = Field(..., description="Order of quality preferences for media")
    merged_path: str = Field(..., description="Path where merged media will be stored")

class MediaLibraryConfig(BaseModel):
    default_source_path: str = Field(..., description="Default path for media sources")
    source_matrix: Dict[str, SourceMatrixEntry] = Field(
        ...,
        description="Configuration matrix for different media types (movies, tv, etc.)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "default_source_path": "/srv/storage/media",
                "source_matrix": {
                    "movies": {
                        "quality_order": ["uhd", "hd"],
                        "merged_path": "/srv/storage/media/movies-merged"
                    },
                    "tv": {
                        "quality_order": ["uhd", "hd"],
                        "merged_path": "/srv/storage/media/movies-merged"
                    }
                }
            }
        } 