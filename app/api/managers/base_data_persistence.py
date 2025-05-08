import json
import os
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
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def _save_data(self):
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            raise e

    def get_data(self, key: str) -> dict[str, Any]:
        return self.data.get(key)

    def set_data(self, key: str, value: dict[str, Any]):
        self.data[key] = value

    def update(self) -> None:
        self._save_data() 
        