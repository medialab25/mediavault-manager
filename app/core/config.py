import json
from pathlib import Path
from typing import Dict, Any
from app.api.media.api.media_library import MediaLibraryConfig

class Config:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from JSON file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            config_data = json.load(f)

        # Initialize MediaLibraryConfig
        self.media_library = MediaLibraryConfig(**config_data["MEDIA_LIBRARY"])

    def get_media_library_config(self) -> MediaLibraryConfig:
        """Get the media library configuration."""
        return self.media_library

    def get_source_matrix(self) -> Dict[str, Any]:
        """Get the source matrix configuration."""
        return self.media_library.source_matrix

    def get_default_source_path(self) -> str:
        """Get the default source path."""
        return self.media_library.default_source_path 