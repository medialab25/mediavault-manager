from pathlib import Path
from typing import Any
from app.api.managers.cache_manager import CacheManager
from app.api.managers.file_transaction_manager import FileTransactionManager
from app.api.managers.media_manager import MediaManager
from app.api.models.file_transaction_models import FileTransactionList, FileTransactionSettings, ExistingFileAction, FileApplyTransactionSettings, FileTransaction, FileOperationType
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
        self.cache_manager = CacheManager(config)

    def sync(self, dry_run: bool = False) -> dict[str, Any]:
        """Sync the cache with the media library
        
        Args:
            dry_run (bool): If True, only show what would be done without making changes
            
        Returns:
            MediaItemGroupDict: The results of the sync operation
        """
        try:
            logger.debug(f"Starting sync{' (dry run)' if dry_run else ''}")

            # Get paths
            cache_path = self.config["cache_path"]
            media_export_path = self.config["media_export_path"]
            default_source_path = self.config["default_source_path"]

            # Get current state
            current_media = self.media_manager.search_media(SearchRequest(db_type=[MediaDbType.MEDIA]))
            current_cache = self.media_manager.search_media(SearchRequest(db_type=[MediaDbType.CACHE]))

            # Process cache
            expected_cache = self.cache_processor.get_expected_cache(current_cache, cache_path)

            # Get merged items group dict
            expected_merge_groups = self.media_merger.merge_libraries(current_media, expected_cache)

            expected_cache_file_transactions = self.get_cache_file_transactions(expected_cache, default_source_path, cache_path)
            for expected_merge_group in expected_merge_groups:
                # Implement cache changes
                # Get file transactions
                export_path = Path(media_export_path) / expected_merge_group.metadata["merge_name"]
                expected_merge_file_transactions = self.get_merge_file_transactions(expected_merge_group, default_source_path, export_path)

                # Get files to remove
                files_to_remove = self.get_files_to_remove(expected_merge_group, [export_path])

            cache_files_to_remove = self.get_files_to_remove(expected_cache, [cache_path])

            # Combine all transactions into a single list
            merge_file_transactions = FileTransactionList(transactions=[])
            merge_file_transactions.transactions.extend(files_to_remove.transactions)
            merge_file_transactions.transactions.extend(cache_files_to_remove.transactions)
            merge_file_transactions.transactions.extend(expected_cache_file_transactions.transactions)
            merge_file_transactions.transactions.extend(expected_merge_file_transactions.transactions)

            file_transaction_summary = self.file_transaction_manager.apply_file_transactions(merge_file_transactions, settings=None, dry_run=dry_run)

            # clear precache
            if not dry_run:
                self.cache_manager.clear_pre_cache()

            return {
                "file_transaction_summary": file_transaction_summary,
                "expected_cache": expected_cache,
                "expected_merge_group": expected_merge_group
            }

        except Exception as e:
            logger.error(f"Error in sync: {str(e)}", exc_info=True)
            raise e
           
    def get_cache_file_transactions(self, expected_cache: MediaItemGroup, media_path: str, cache_path: str) -> FileTransactionList:
        file_transactions = FileTransactionList(transactions=[])
        settings = FileTransactionSettings(existing_file_action=ExistingFileAction.SKIP_IF_SAME_SIZE)
        for item in expected_cache.items:
            source_path = str(item.get_full_filepath(media_path))
            dest_path = str(item.get_full_filepath(cache_path))
            file_transactions.transactions.append(FileTransaction(
                type=FileOperationType.COPY,
                source=source_path,
                destination=dest_path,
                settings=settings,
                metadata={}
            ))
        return file_transactions
    
    def get_merge_file_transactions(self, expected_merge_group: MediaItemGroup, media_path: str, cache_path: str) -> FileTransactionList:
        file_transactions = FileTransactionList(transactions=[])
        settings = FileTransactionSettings(existing_file_action=ExistingFileAction.SKIP_IF_SAME_SIZE)
        for item in expected_merge_group.items:
            if item.db_type == MediaDbType.CACHE:
                source_path = str(item.get_full_filepath(cache_path))
            else:
                source_path = str(item.get_full_filepath(media_path))

            dest_path = str(item.get_full_title_filepath(cache_path))
            file_transactions.transactions.append(FileTransaction(
                type=FileOperationType.LINK,
                source=source_path,
                destination=dest_path,
                settings=settings,
                metadata={}
            ))
        return file_transactions

    def get_files_to_remove(self, expected_group: MediaItemGroup, base_paths: list[str]) -> FileTransactionList:
        file_transactions = FileTransactionList(transactions=[])

        # For each file in base_path and all sub folders, check if it exists in expected_group
        for base_path in base_paths:
            for root, dirs, files in os.walk(base_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_file_path = os.path.relpath(file_path, base_path)
                    if not expected_group.title_file_path_exists(relative_file_path):
                        file_transactions.transactions.append(FileTransaction(
                            type=FileOperationType.DELETE,
                            source=str(file_path),
                            destination="",
                            metadata={}
                        ))
        return file_transactions



        
        