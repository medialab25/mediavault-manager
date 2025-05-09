from typing import Any, List, Optional
from app.api.managers.base_data_persistence import BaseDataPersistence
from app.api.models.manifest_models import ManifestItem, ManifestItemGroup, ManifestType
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

    def get_manifest_groups(self) -> List[ManifestItemGroup]:
        """Get all items from the manifest"""
        manifest_groups = []
        for manifest_type in ManifestType:
            data = self.get_data(manifest_type) or []
            manifest_groups.append(ManifestItemGroup(manifest_type=manifest_type, items=data))
        return manifest_groups

    def get_manifest_group(self, manifest_type: ManifestType) -> ManifestItemGroup:
        """Get the manifest items for a given manifest type"""
        data = self.get_data(manifest_type) or []
        return ManifestItemGroup(manifest_type=manifest_type, items=data)

    def set_manifest_group(self, group: ManifestItemGroup):
        """Set the manifest items"""
        self.set_data(group.manifest_type, [item.model_dump() for item in group.items])

    def append_manifest_items(self, items: ManifestItemGroup):
        """Append items to the manifest"""
        # Get existing items
        existing_items = self.get_manifest_group(items.manifest_type)
        # Create a dictionary of existing items by id
        existing_dict = {item.id: item for item in existing_items.items}
        # Add new items, overwriting existing ones with same id
        for item in items.items:
            existing_dict[item.id] = item
        # Convert back to list and update
        self.set_manifest_group(ManifestItemGroup(manifest_type=items.manifest_type, items=list(existing_dict.values())))

    def remove_manifest_items(self, items: ManifestItemGroup):
        """Remove items from the manifest"""
        existing_items = self.get_manifest_group(items.manifest_type)
        # Create a set of ids to remove
        remove_ids = {item.id for item in items.items}
        # Filter out items with matching ids
        remaining_items = [item for item in existing_items.items if item.id not in remove_ids]
        self.set_manifest_group(ManifestItemGroup(manifest_type=items.manifest_type, items=remaining_items))

    def clear_manifest(self):
        """Clear all items from the manifest"""
        for manifest_type in ManifestType:
            self.set_data(manifest_type, [])

    def update(self):
        """Update the manifest"""
        self.update()
