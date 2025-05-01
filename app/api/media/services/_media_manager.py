import os
import re
from datetime import datetime
from typing import List, Optional, Dict
from pathlib import Path

from app.api.managers.models.media_models import MediaGroupFolderList, MediaFileItem, MediaItemFolder, MediaGroupFolder, ExtendedMediaInfo

class MediaDataManager:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)

    def _get_file_info(self, file_path: Path) -> ExtendedMediaInfo:
        """Get extended information about a file."""
        stat = file_path.stat()
        return ExtendedMediaInfo(
            size=stat.st_size,
            created_at=datetime.fromtimestamp(stat.st_ctime),
            updated_at=datetime.fromtimestamp(stat.st_mtime),
            metadata={}  # TODO: Implement metadata extraction
        )

    def _parse_filename(self, filename: str) -> Dict[str, Optional[int]]:
        """Parse season and episode numbers from filename.
        
        Expected format: "title with optional year - S00E00 - Additional data"
        Example: "Show Name (2023) - S01E02 - Episode Title"
        """
        # Remove file extension
        filename = os.path.splitext(filename)[0]
        
        # Pattern to match S00E00 format
        pattern = r'.*?[-\s]+S(\d{1,2})E(\d{1,2})[-\s]+.*'
        match = re.match(pattern, filename, re.IGNORECASE)
        
        if match:
            season = int(match.group(1))
            episode = int(match.group(2))
            return {"season": season, "episode": episode}
        
        return {"season": None, "episode": None}

    def read_media_item(self, file_path: str) -> MediaFileItem:
        """Read a single media item from a file path."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Media file not found: {file_path}")

        filename = path.name
        file_info = self._parse_filename(filename)
        extended_info = self._get_file_info(path)

        return MediaFileItem(
            filename=filename,
            season=file_info["season"],
            episode=file_info["episode"],
            extended=extended_info
        )

    def read_media_folder(self, folder_path: str) -> MediaItemFolder:
        """Read all media items in a folder."""
        path = Path(folder_path)
        if not path.exists():
            raise FileNotFoundError(f"Media folder not found: {folder_path}")

        title = path.name
        items: List[MediaFileItem] = []

        for file in path.glob("*"):
            if file.is_file():
                try:
                    media_item = self.read_media_item(str(file))
                    items.append(media_item)
                except Exception as e:
                    print(f"Error reading file {file}: {e}")

        return MediaItemFolder(title=title, items=items)

    def read_media_group(self, group_path: str) -> MediaGroupFolder:
        """Read a media group folder (e.g., movies-4k, tv-hd)."""
        path = Path(group_path)
        if not path.exists():
            raise FileNotFoundError(f"Media group not found: {group_path}")

        # Parse media type and quality from path
        parts = path.name.split("-")
        if len(parts) != 2:
            raise ValueError(f"Invalid media group format: {path.name}")

        media_type, quality = parts

        return MediaGroupFolder(
            media_type=media_type,
            quality=quality,
            path=str(path)
        )

    def list_media_groups(self) -> List[MediaGroupFolder]:
        """List all media groups in the base path."""
        groups: List[MediaGroupFolder] = []
        
        for item in self.base_path.iterdir():
            if item.is_dir():
                try:
                    group = self.read_media_group(str(item))
                    groups.append(group)
                except Exception as e:
                    print(f"Error reading group {item}: {e}")

        return groups

    def get_media_group_folder_list(self, path: str) -> MediaGroupFolderList:
        """Get the media group folder list for a given path."""
        groups = self.list_media_groups(path)
        return MediaGroupFolderList(groups=groups)
