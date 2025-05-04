from typing import Any
from app.api.managers.file_transaction_manager import FileTransactionManager
from app.api.models.file_transaction_models import FileTransactionList, FileTransactionSettings, ExistingFileAction
from app.api.models.media_models import MediaItemGroupDict, MediaItemGroup
from app.api.managers.cache_manager import CacheManager
from app.api.process.media_merger import MediaMerger
import logging
import os

logger = logging.getLogger(__name__)

class SyncManager:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.cache_manager = CacheManager(config)
        self.media_merger = MediaMerger(config)
        self.file_transaction_manager = FileTransactionManager(config)
        
    def sync(self, dry_run: bool = False) -> MediaItemGroupDict:
        """Sync the cache with the media library
        
        Args:
            dry_run (bool): If True, only show what would be done without making changes
            
        Returns:
            MediaItemGroupDict: The results of the sync operation
        """
        try:
            logger.debug(f"Starting sync{' (dry run)' if dry_run else ''}")

            # Get merged items group dict
            merged_items_group_dict = self.media_merger.merge_libraries()

            # Get file transactions
            file_transactions = FileTransactionList(transactions=[])
            settings = FileTransactionSettings(existing_file_action=ExistingFileAction.OVERWRITE)
            for key, group in merged_items_group_dict.groups.items():
                merged_path = group.metadata["merged_path"]
                for item in group.items:
                    # Construct destination path by joining merged_path with the relative path
                    relative_path = item.get_relative_filepath()
                    destination = os.path.join(merged_path, relative_path)
                    # Create metadata dictionary with necessary information
                    metadata = {
                        "source_path": item.full_path,
                        "destination_path": destination,
                        "media_type": item.media_type,
                        "media_prefix": item.media_prefix,
                        "quality": item.quality,
                        "title": item.title
                    }
                    file_transactions.copy(item.full_path, destination, settings=settings, metadata=metadata)

            # Apply file transactions
            file_transaction_summary = self.file_transaction_manager.apply_file_transactions(file_transactions, dry_run=dry_run)

            # Flatten the merged items group dict
            #flattened_items_group = self.flatten_merged_items_group_dict(merged_items_group_dict)

            #cache_sync_result = self.cache_manager.sync_cache(dry_run=dry_run)

            #return cache_sync_result

            return merged_items_group_dict

        except Exception as e:
            logger.error(f"Error in sync: {str(e)}", exc_info=True)
            raise e
        
    def flatten_merged_items_group_dict(self, merged_items_group_dict: MediaItemGroupDict) -> MediaItemGroup:
        """Flatten the merged items group dict
        
        Args:
            merged_items_group_dict (MediaItemGroupDict): The merged items group dict
        """
        flattened_items_group = MediaItemGroup(items=[])
        for key, group in merged_items_group_dict.groups.items():
            flattened_items_group.items.extend(group.items)
        return flattened_items_group