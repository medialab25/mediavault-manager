from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

# enum for the db types, MEDIA, CACHE, SHADOW
class MediaDbType(str,Enum):
    MEDIA = "media"
    CACHE = "cache"
    EXPORT = "export"

class ExtendedMediaInfo(BaseModel):
    size: int
    created_at: float
    updated_at: float
    metadata: Optional[dict] = None

class MediaFileItem(BaseModel):
    path: str
    season: Optional[int] = None
    episode: Optional[int] = None
    extended: Optional[ExtendedMediaInfo] = None

class MediaItemFolder(BaseModel):
    title: str
    media_type: str
    path: str
    items: List[MediaFileItem] = []

class MediaGroupFolder(BaseModel):
    media_type: str
    media_prefix: str
    quality: str
    cache_export: bool
    path: str
    media_folder_items: List[MediaItemFolder] = []

class MediaGroupFolderList(BaseModel):
    groups: List[MediaGroupFolder]

class MediaItem(BaseModel):
    db_type: MediaDbType    # = Field(alias="db_type")
    relative_title_filepath: str   # The filepath relative to the top-level title
    media_type: str
    media_prefix: str
    quality: str
    title: str
    season: Optional[int] = None
    episode: Optional[int] = None
    extended: Optional[ExtendedMediaInfo] = None
    source_item: Optional["MediaItem"] = None
    full_file_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def copy(self) -> "MediaItem":
        return MediaItem(
            db_type=self.db_type,
            media_type=self.media_type,
            media_prefix=self.media_prefix,
            quality=self.quality,
            title=self.title,
            season=self.season,
            episode=self.episode,
            relative_title_filepath=self.relative_title_filepath,
            extended=self.extended,
            source_item=self.source_item,
            full_file_path=self.full_file_path,
            metadata=self.metadata.copy() if self.metadata else {}
        )
    
    # Path with all folders execpt the base_path
    def get_unique_path(self) -> str:
        return f"{self.media_prefix}-{self.quality}/{self.title}/{self.relative_title_filepath}"
    


#####
    def clone_with_update(self, db_type: MediaDbType) -> "MediaItem":
        result = self.clone()
        result.db_type = db_type
        return result
    
    def get_path(self, media_path: str, cache_path: str, is_merged: bool=False) -> str:
        if self.db_type == MediaDbType.MEDIA:
            if is_merged:
                return self.get_full_title_filepath(media_path)
            else:
                return self.get_full_filepath(media_path)
        elif self.db_type == MediaDbType.CACHE:
            if is_merged:
                return self.get_full_title_filepath(cache_path)
            else:
                return self.get_full_filepath(cache_path)

    def get_full_filepath(self, base_path: str) -> str:
        return Path(base_path) / f"{self.media_prefix}-{self.quality}/{self.title}/{self.relative_title_filepath}"

    def equals(self, other: "MediaItem") -> bool:
        return self.get_relative_matrix_filepath() == other.get_relative_matrix_filepath()

    def exists_in(self, other: "MediaItemGroup") -> bool:
        return any(item.equals(self) for item in other.items)
    
    
    def get_full_matrix_filepath(self, base_path: str) -> str:
        return Path(base_path) / self.get_relative_matrix_filepath()

    def get_full_title_filepath(self, base_path: str) -> str:
        return Path(base_path) / self.title / self.relative_title_filepath

    def get_relative_matrix_filepath(self) -> str:
        return f"{self.media_prefix}-{self.quality}/{self.relative_title_filepath}"

    def get_relative_title_folderpath(self) -> str:
        return str(Path(self.relative_title_filepath).parent)
    

class MediaItemGroup(BaseModel):
    items: List[MediaItem]
    metadata: Optional[Dict[str, Any]] = None
   
    def copy(self) -> "MediaItemGroup":
        return MediaItemGroup(items=[item.copy() for item in self.items])

#####

    def title_file_path_exists(self, title_file_path: str) -> bool:
        return any(item.relative_title_filepath == title_file_path for item in self.items)

    def does_item_path_exist(self, media_path: str, cache_path: str, is_merged: bool, item_path: str) -> bool:
        lst = [item.get_path(media_path, cache_path, is_merged) for item in self.items]
        return item_path in lst

#class MediaItemGroupList(BaseModel):
#    groups: List[MediaItemGroup]

class MediaItemGroupDict(BaseModel):
    groups: Dict[str, MediaItemGroup]

class MediaMatrixInfo(BaseModel):
    media_type: str 
    media_prefix: str
    quality_order: List[str]
    merge_prefix: str
    merge_quality: str
    use_cache: bool
    
class MediaLibraryInfo(BaseModel):
    media_matrix_info: Dict[str, MediaMatrixInfo]
    media_library_path: str
    cache_library_path: str
    export_library_path: str
    system_data_path: str
