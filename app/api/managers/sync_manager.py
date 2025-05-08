from pathlib import Path
from typing import Any
from app.api.managers.cache_manager import CacheManager
from app.api.managers.file_transaction_manager import FileTransactionManager
from app.api.managers.item_manager import ItemManager
from app.api.managers.media_manager import MediaManager
from app.api.managers.media_query import MediaQuery
from app.api.models.file_transaction_models import FileTransactionList, FileTransactionSettings, ExistingFileAction, FileOperationType
from app.api.models.media_models import MediaDbType, MediaItemGroup
from app.api.models.search_request import SearchRequest
from app.api.process.cache_processor import CacheProcessor
from app.api.process.media_merger import MediaMerger
import logging

logger = logging.getLogger(__name__)

class SyncManager:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.media_merger = MediaMerger(config)
        self.media_manager = MediaManager(config)
        self.file_transaction_manager = FileTransactionManager(config)
        self.cache_processor = CacheProcessor(config)
        self.cache_manager = CacheManager(config)
        self.item_manager = ItemManager(config)

    def sync(self, dry_run: bool = False, details: bool = False) -> dict[str, Any]:
        """Sync the cache with the media library
        
        Args:
            dry_run (bool): If True, only show what would be done without making changes
            details (bool): If True, show details of the sync operation
        Returns:
            MediaItemGroupDict: The results of the sync operation
        """
        try:
            logger.debug(f"Starting sync{' (dry run)' if dry_run else ''}")

            # Get current state
            actual_media_model = self.media_manager.search_media(SearchRequest(db_type=[MediaDbType.MEDIA, MediaDbType.CACHE]))
            query = MediaQuery(actual_media_model)

            actual_media_group = query.get_items(SearchRequest(db_type=[MediaDbType.MEDIA]))
            actual_cache_group = query.get_items(SearchRequest(db_type=[MediaDbType.CACHE]))

            self._link_cache_items_to_media_items(actual_cache_group, actual_media_group)

            # Process cache
            expected_cache_group = self.cache_processor.get_expected_cache(actual_cache_group)

            # Get merged items
            expected_merge_group = self.media_merger.merge_libraries(actual_media_group, expected_cache_group)

            file_transactions = FileTransactionList(transactions=[])

            # Get file transactions for cache
            self._add_file_transactions(file_transactions, expected_cache_group, FileOperationType.COPY)

            # Get file transactions for merge group
            self._add_file_transactions(file_transactions, expected_merge_group, FileOperationType.LINK)

            file_transaction_summary = self.file_transaction_manager.apply_file_transactions(file_transactions, settings=None, dry_run=dry_run)

            # clear precache
            if not dry_run:
                self.cache_manager.clear_pre_cache()

            if details:
                return {
                    "file_transaction_summary": file_transaction_summary,
                    "expected_cache_group": expected_cache_group,
                    "expected_merge_group": expected_merge_group
                }
            else:
                return {
                    "file_transaction_summary": file_transaction_summary,
                }

        except Exception as e:
            logger.error(f"Error in sync: {str(e)}", exc_info=True)
            raise e

    def _link_cache_items_to_media_items(self, cache_group: MediaItemGroup, media_group: MediaItemGroup) -> None:
        """Link cache items to their corresponding media items.
        
        Args:
            cache_group (MediaItemGroup): Group containing cache items
            media_group (MediaItemGroup): Group containing media items
        """
        for item in cache_group.items:
            if item.source_item:
                continue

            # Find matching media item
            matching_media_item = self.item_manager.get_matching_item(item, media_group.items)
            if not matching_media_item:
                continue

            # Link cache item to media item
            item.source_item = matching_media_item
            
    def _get_file_transactions(self, expected_group: MediaItemGroup, operation_type: FileOperationType) -> FileTransactionList:
        file_transactions = FileTransactionList(transactions=[])
        self._add_file_transactions(file_transactions, expected_group, operation_type)
        return file_transactions

    def _add_file_transactions(self, file_transactions: FileTransactionList, expected_group: MediaItemGroup, operation_type: FileOperationType) -> None:
        for item in expected_group.items:
            if not item.source_item:
                continue

            file_transactions.add(
                source=str(item.source_item.full_file_path),
                destination=str(item.full_file_path),
                type=operation_type,
                settings=FileTransactionSettings(existing_file_action=ExistingFileAction.SKIP_IF_SAME_SIZE),
                metadata={})



        
        