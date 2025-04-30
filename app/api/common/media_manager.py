# Management of media using the file_manager class
from pathlib import Path
from app.core.config import Config
from typing import Any

class MediaManager:
    def __init__(self, config: dict[str, Any]):
        self.media_base_path = Path(config.get("default_source_path"))
        self.config = config

    # Get all media group folders using the source_matrix in the config
    def get_media_group_folders(self) -> list[str]:
        """Get all media group folders based on the source matrix configuration.
        
        Returns:
            list[str]: List of media group folder paths
        """
        source_matrix = self.config.get("source_matrix")
        media_groups = []
        
        for media_type, config in source_matrix.items():
            for quality in config["quality_order"]:
                group_folder = self.media_base_path / f"{media_type}-{quality}"
                if group_folder.exists():
                    media_groups.append(str(group_folder))
                    
        return media_groups

    
