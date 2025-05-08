import json
import os
import fcntl
from typing import Any, Dict

from app.api.models.media_models import MediaItem, MediaItemGroup


class BaseDataPersistence:
    def __init__(self, system_folder: str, data_filename: str):
        self.system_folder = system_folder
        self.data_file = os.path.join(self.system_folder, data_filename)
        self.data: Dict[str, Any] = {}
        
        # Create system folder if it doesn't exist
        os.makedirs(self.system_folder, exist_ok=True)
        
        # Load existing data if available
        self.data = self._load_data()

    def _load_data(self) -> Dict[str, Any]:
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    # Get a shared lock for reading
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                    try:
                        return json.load(f)
                    finally:
                        # Release the lock
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            except json.JSONDecodeError:
                return {}
        return {}

    def _save_data(self):
        try:
            with open(self.data_file, 'w') as f:
                # Get an exclusive lock for writing
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    json.dump(self.data, f, indent=4)
                finally:
                    # Release the lock
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except Exception as e:
            raise e

    def get_data(self, key: str) -> dict[str, Any]:
        return self.data.get(key)

    def set_data(self, key: str, value: dict[str, Any]):
        self.data[key] = value

    def update(self) -> None:
        self._save_data() 
        