# class to store persisted data between sessions

from typing import Any

from app.api.models.media_models import MediaItem, MediaDbType
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
        items = []
        for item_data in (self.get_data("add_cache_items") or []):
            if item_data is not None:
                # Ensure source field is present
                if "source" not in item_data:
                    item_data["source"] = {
                        "db_type": MediaDbType.MEDIA,
                        "media_type": item_data.get("media_type", ""),
                        "media_prefix": item_data.get("media_prefix", ""),
                        "quality": item_data.get("quality", "")
                    }
                # Ensure relative_title_filepath is present
                if "relative_title_filepath" not in item_data:
                    # If we have a title and source info, construct the relative path
                    if item_data.get("title") and item_data.get("source", {}).get("media_prefix"):
                        item_data["relative_title_filepath"] = f"{item_data['title']}/{item_data.get('title', '')}"
                    else:
                        continue  # Skip items without required fields
                items.append(MediaItem(**item_data))
        return items

    def get_remove_cache_items(self) -> list[MediaItem]:
        items = []
        for item_data in (self.get_data("remove_cache_items") or []):
            if item_data is not None:
                # Ensure source field is present
                if "source" not in item_data:
                    item_data["source"] = {
                        "db_type": MediaDbType.CACHE,
                        "media_type": item_data.get("media_type", ""),
                        "media_prefix": item_data.get("media_prefix", ""),
                        "quality": item_data.get("quality", ""),
                    }
                # Ensure relative_title_filepath is present
                if "relative_title_filepath" not in item_data:
                    # If we have a title and source info, construct the relative path
                    if item_data.get("title") and item_data.get("source", {}).get("media_prefix"):
                        item_data["relative_title_filepath"] = f"{item_data['title']}/{item_data.get('title', '')}"
                    else:
                        continue  # Skip items without required fields
                items.append(MediaItem(**item_data))
        return items

    def append_remove_cache_items(self, items: list[MediaItem]):
        # Get existing items
        existing_items = [MediaItem(**item) for item in (self.get_data("remove_cache_items") or []) if item is not None]
        # Merge with new items ensuring uniqueness
        merged_list = self.item_manager.merge_unique_items(existing_items, items)
        self.set_data("remove_cache_items", [item.model_dump() for item in merged_list])
