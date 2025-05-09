from typing import Any, Dict, List, Optional
from app.api.managers.base_data_persistence import BaseDataPersistence
from app.api.models.media_models import MediaItem, MediaItemGroup

class ManifestManager(BaseDataPersistence):
    _instance = None

    def __new__(cls, config: dict[str, Any]):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config: dict[str, Any]):
        if not self._initialized:
            super().__init__(system_folder=config["system_data_path"], data_filename="manifest.json")
            self.config = config
            self._initialized = True

    def get_manifest_items(self) -> MediaItemGroup:
        """Get all items from the manifest"""
        data = self.get_data("manifest_items") or []
        valid_items = []
        for item in data:
            if item is None:
                continue
            try:
                valid_items.append(MediaItem(**item))
            except Exception as e:
                # Log the error and skip invalid items
                print(f"Failed to create MediaItem from manifest data: {e}")
                continue
        return MediaItemGroup(items=valid_items)

    def set_manifest_items(self, items: MediaItemGroup):
        """Set the manifest items"""
        self.set_data("manifest_items", [item.model_dump() for item in items.items])
        self.update()

    def append_manifest_items(self, items: MediaItemGroup):
        """Append items to the manifest"""
        # Get existing items
        existing_items = self.get_manifest_items()
        # Create a dictionary of existing items by id
        existing_dict = {item.id: item for item in existing_items.items}
        # Add new items, overwriting existing ones with same id
        for item in items.items:
            existing_dict[item.id] = item
        # Convert back to list and update
        self.set_manifest_items(MediaItemGroup(items=list(existing_dict.values())))

    def remove_manifest_items(self, items: MediaItemGroup):
        """Remove items from the manifest"""
        existing_items = self.get_manifest_items()
        # Create a set of ids to remove
        remove_ids = {item.id for item in items.items}
        # Filter out items with matching ids
        remaining_items = [item for item in existing_items.items if item.id not in remove_ids]
        self.set_manifest_items(MediaItemGroup(items=remaining_items))

    def clear_manifest(self):
        """Clear all items from the manifest"""
        self.set_data("manifest_items", [])
        self.update()
