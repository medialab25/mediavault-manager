# class to store persisted data between sessions

from typing import Any

from app.api.models.media_models import MediaItem
from .base_data_persistence import BaseDataPersistence
from .item_manager import ItemManager

class DataManager(BaseDataPersistence):
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.item_manager = ItemManager(config)
        super().__init__(system_folder=config["system_data_path"], data_filename="data.json")

    def set_add_cache_items(self, items: list[MediaItem]):
        self.set_data("add_cache_items", [item.model_dump() for item in items])

    def append_add_cache_items(self, items: list[MediaItem]):
        # Get existing items
        existing_items = self.get_add_cache_items()
        # Merge with new items ensuring uniqueness
        merged_list = self.item_manager.merge_unique_items(existing_items, items)
        self.set_data("add_cache_items", [item.model_dump() for item in merged_list])

    def get_add_cache_items(self) -> list[MediaItem]:
        data = self.get_data("add_cache_items") or []
        valid_items = []
        for item in data:
            if item is None:
                continue
            try:
                valid_items.append(MediaItem(**item))
            except Exception as e:
                # Log the error and skip invalid items
                print(f"Failed to create MediaItem from data: {e}")
                continue
        return [MediaItem(**item) for item in (self.get_data("add_cache_items") or []) if item is not None]

    def get_remove_cache_items(self) -> list[MediaItem]:
        data = self.get_data("remove_cache_items") or []
        valid_items = []
        for item in data:
            if item is None:
                continue
            try:
                valid_items.append(MediaItem(**item))
            except Exception as e:
                # Log the error and skip invalid items
                print(f"Failed to create MediaItem from data: {e}")
                continue
        return valid_items

    def append_remove_cache_items(self, items: list[MediaItem]):
        # Get existing items
        existing_items = [MediaItem(**item) for item in (self.get_data("remove_cache_items") or []) if item is not None]
        # Merge with new items ensuring uniqueness
        merged_list = self.item_manager.merge_unique_items(existing_items, items)
        self.set_data("remove_cache_items", [item.model_dump() for item in merged_list])

    def get_media_library_update_request(self) -> int   :
        return self.get_data("media_library_update_request") or 0   

    def set_media_library_update_request(self):
        no_requests = self.get_media_library_update_request()
        self.set_data("media_library_update_request", no_requests + 1)
        self.update()

    def clear_media_library_update_request(self) -> None:
        self.set_data("media_library_update_request", 0)
