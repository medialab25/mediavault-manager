import json
from pathlib import Path
from typing import Any
import fcntl
import os


class UpdateDataManager:
    UPDATE_FILE_NAME = "update.json"

    # Initialize the UpdateDataManager
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.system_data_path = Path(config.get("system_data_path"))
        self.update_data_path = self.system_data_path / self.UPDATE_FILE_NAME

    # Read the update data file using the path
    def read_update_data(self) -> dict[str, Any]:
        if not self.update_data_path.exists():
            return {}
        with open(self.update_data_path, "r") as f:
            return json.load(f)
        
    # Write the update data file using the path, and use locking so only one access at a time
    def write_update_data(self, update_data: dict[str, Any]):
        # Create the update data path if it doesn't exist
        self.update_data_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.update_data_path, "w") as f:
            # Get an exclusive lock
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                json.dump(update_data, f)
            finally:
                # Release the lock
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    
    def clear_cache_updates(self):
        update_data = self.read_update_data()
        update_data["add_cache_updates"] = []
        update_data["remove_cache_updates"] = []
        self.write_update_data(update_data)

    def add_cache_update(self, update_ids: list[str]):
        update_data = self.read_update_data()
        # Get existing updates or initialize empty list
        existing_updates = update_data.get("add_cache_updates", [])
        # Combine existing and new updates, removing duplicates while preserving order
        combined_updates = existing_updates + [id for id in update_ids if id not in existing_updates]
        update_data["add_cache_updates"] = combined_updates

        # Remove any udated ones from the remove_cache_updates
        update_data["remove_cache_updates"] = [id for id in update_data["remove_cache_updates"] if id not in update_ids]

        self.write_update_data(update_data)

    def remove_cache_update(self, update_ids: list[str]):
        update_data = self.read_update_data()
        existing_updates = update_data.get("remove_cache_updates", [])
        update_data["remove_cache_updates"] = existing_updates + [id for id in update_ids if id not in existing_updates]

        # Remove any udated ones from the add_cache_updates
        update_data["add_cache_updates"] = [id for id in update_data["add_cache_updates"] if id not in update_ids]

        self.write_update_data(update_data)
        
    def get_add_cache_updates(self) -> list[str]:
        update_data = self.read_update_data()
        return update_data.get("add_cache_updates", [])
    
    def get_remove_cache_updates(self) -> list[str]:
        update_data = self.read_update_data()
        return update_data.get("remove_cache_updates", [])
    