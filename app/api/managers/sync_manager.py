from typing import Any
from app.api.managers.file_transaction_manager import FileTransactionManager
from app.api.managers.media_manager import MediaManager
from app.api.models.file_transaction_models import FileTransactionList, FileTransactionSettings, ExistingFileAction, FileApplyTransactionSettings
from app.api.models.media_models import MediaDbType, MediaItemGroupDict, MediaItemGroup
from app.api.models.search_request import SearchRequest
from app.api.process.cache_processor import CacheProcessor
from app.api.process.media_merger import MediaMerger
import logging
import os

logger = logging.getLogger(__name__)

class SyncManager:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.media_merger = MediaMerger(config)
        self.media_manager = MediaManager(config)
        self.file_transaction_manager = FileTransactionManager(config)
        self.cache_processor = CacheProcessor(config)

    def sync(self, dry_run: bool = False) -> dict[str, Any]:
        """Sync the cache with the media library
        
        Args:
            dry_run (bool): If True, only show what would be done without making changes
            
        Returns:
            MediaItemGroupDict: The results of the sync operation
        """
        try:
            logger.debug(f"Starting sync{' (dry run)' if dry_run else ''}")

            # Get current state
            current_media = self.media_manager.search_media(SearchRequest(db_type=[MediaDbType.MEDIA]))
            current_cache = self.media_manager.search_media(SearchRequest(db_type=[MediaDbType.CACHE]))

            # Process cache
            expected_cache = self.cache_processor.get_processed_cache(current_cache)

            # Get merged items group dict
            expected_merge_group = self.media_merger.merge_libraries(current_media, current_cache)

            # Implement cache changes
            # Get file transactions
            expected_cache_file_transactions = self.get_cache_file_transactions(expected_cache, dry_run=dry_run)
            expected_merge_file_transactions = self.get_merge_file_transactions(expected_merge_group, dry_run=dry_run)

            expected_cache_file_transaction_summary = self.file_transaction_manager.apply_file_transactions(expected_cache_file_transactions, settings=None, dry_run=dry_run)



            # Get file transactions
#            cache_items = self.media_manager.search_media(SearchRequest(db_type=MediaDbType.CACHE))

#            file_transactions = FileTransactionList(transactions=[])
#            settings = FileTransactionSettings(existing_file_action=ExistingFileAction.OVERWRITE)
#            for key, group in merged_items_group_dict.groups.items():
#                merged_path = group.metadata["merged_path"]
#                cache_path = group.metadata["cache_path"]
#                # Set cache_data based on whether cache_merge_folder exists
#                cache_data = "cache_merge_folder" in group.metadata
#                cache_merge_folder = group.metadata.get("cache_merge_folder")
                
#                if cache_data:
#                    cache_base_path = os.path.join(cache_path, cache_merge_folder)

#                    for item in group.items:
#                        # Is this item matching to matrix_file_path in the cache items
#                        matching_item = next((cache_item for cache_item in cache_items.items if cache_item.get_matrix_file_path() == item.get_matrix_filepath()), None)
#                        if matching_item:
#                            source = matching_item.full_path
#                            destination = os.path.join(cache_base_path, item.get_relative_filepath())
#                        else:
#                            source = item.full_path 
#                            destination = os.path.join(merged_path, item.get_relative_filepath())
#                else:
#                    for item in group.items:
#                        source = item.full_path
#                        destination = os.path.join(merged_path, item.get_relative_filepath())

                # Create metadata dictionary with necessary information
#                file_transactions.copy(source, destination, settings=settings)

            # Remove unreferenced files
#            file_transactions = self.file_transaction_manager.get_file_transactions_remove_unreferenced_files(merged_path, file_transactions)

            # Apply file transactions
#            file_transaction_summary = self.file_transaction_manager.apply_file_transactions(file_transactions, settings=None, dry_run=dry_run)

            return {
                "merged_items_group_dict": merged_items_group_dict,
                "file_transaction_summary": file_transaction_summary,
                "cache_file_transaction_summary": cache_file_transaction_summary
            }

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
    
    def get_cache_file_transactions(self, expected_cache: MediaItemGroup, dry_run: bool = False) -> FileTransactionList:
        file_transactions = FileTransactionList(transactions=[])
        settings = FileTransactionSettings(existing_file_action=ExistingFileAction.SKIP_IF_SAME_SIZE)
        for item in expected_cache.items:
            file_transactions.copy(item.full_path, item.get_matrix_filepath(), settings=settings)

        file_transaction_summary = self.file_transaction_manager.apply_file_transactions(file_transactions, settings=None, dry_run=dry_run)
        return file_transaction_summary
    
    def get_merge_file_transactions(self, expected_merge_group: MediaItemGroup, dry_run: bool = False) -> FileTransactionList:
        file_transactions = FileTransactionList(transactions=[])
        settings = FileTransactionSettings(existing_file_action=ExistingFileAction.SKIP_IF_SAME_SIZE)
        for item in expected_merge_group.items:
            file_transactions.link(item.full_path, item.get_matrix_filepath(), settings=settings)
        return file_transactions
