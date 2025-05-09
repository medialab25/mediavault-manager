from typing import Any
from app.api.models.media_models import MediaLibraryInfo, MediaMatrixInfo


class MatrixManager:
    def __init__(self, config: dict[str, Any]):
        self.config = config

    def get_media_matrix_info(self) -> dict[str, MediaMatrixInfo]:
        """Get the media matrix info"""
        source_matrix = self.config.get("source_matrix")
        media_matrix_info = {}
        for media_key, config in source_matrix.items():
            media_type = config["media_type"] if config["media_type"] else media_key
            media_prefix = config["prefix"] if config["prefix"] else media_key
            media_matrix_info[media_key] = MediaMatrixInfo(
                media_type=media_type,
                media_prefix=media_prefix,
                quality_order=config["quality_order"],
                merge_prefix=config.get("merge_prefix", media_prefix),
                merge_quality=config.get("merge_quality", "merged"),
                use_cache=config["use_cache"]
            )
        return media_matrix_info

    def get_media_library_info(self) -> MediaLibraryInfo:
        """Get the media library info"""
        media_matrix_info = self.get_media_matrix_info()
        return MediaLibraryInfo(
            media_matrix_info=media_matrix_info,
            media_library_path=self.config.get("default_source_path"),
            cache_library_path=self.config.get("cache_path"),
            export_library_path=self.config.get("media_export_path"),
            cache_export_library_path=self.config.get("cache_export_path"),
            system_data_path=self.config.get("system_data_path")
        )
