from pathlib import Path
from typing import Any
from app.api.managers.cache_manager import CacheManager
from app.api.managers.file_transaction_manager import FileTransactionManager
from app.api.managers.item_manager import ItemManager
from app.api.managers.media_manager import MediaManager
from app.api.managers.media_query import MediaQuery
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
        self.item_manager = ItemManager(config)

    def sync(self, dry_run: bool = False) -> dict[str, Any]:
        """Sync the cache with the media library
        
        Args:
            dry_run (bool): If True, only show what would be done without making changes
            
        Returns:
            MediaItemGroupDict: The results of the sync operation
        """
        try:
            logger.debug(f"Starting sync{' (dry run)' if dry_run else ''}")

            media_library_info = self.media_manager.get_media_library_info()

            # Get paths
            cache_path = media_library_info.cache_library_path
            media_export_path = media_library_info.export_library_path
            default_source_path = media_library_info.media_library_path

            # Get current state
            
            actual_media_model = self.media_manager.search_media(SearchRequest(db_type=[MediaDbType.MEDIA, MediaDbType.CACHE]))
            query = MediaQuery(actual_media_model)

            actual_media_group = query.get_items(SearchRequest(db_type=[MediaDbType.MEDIA]))
            actual_cache_group = query.get_items(SearchRequest(db_type=[MediaDbType.CACHE]))

            # Process cache
            expected_cache_group = self.cache_processor.get_expected_cache(actual_cache_group)

            # Get merged items
            #expected_merge_group = self.media_merger.merge_libraries(current_media, expected_cache)

            # Get file transactions for cache
            #expected_cache_file_transactions = self.get_source_file_transactions(expected_cache, FileOperationType.COPY)

            # Get file transactions for merge group
            #expected_merge_file_transactions = self.get_source_file_transactions(expected_merge_group, FileOperationType.LINK)

            return expected_cache, expected_merge_group




            expected_cache_file_transactions = self.get_cache_file_transactions(expected_cache, default_source_path, cache_path)
            export_path_list = []
            for expected_merge_group in expected_merge_groups:
                # Implement cache changes
                # Get file transactions
                export_path = Path(media_export_path) / expected_merge_group.metadata["merge_name"]
                export_path_list.append(export_path)
                expected_merge_file_transactions = self.get_merge_file_transactions(expected_merge_group, default_source_path, export_path)

                # Get files to remove
            # Flatten all expected_merge_groups into a single list
            expected_merge_groups_list = []
            for merge_group in expected_merge_groups:
                expected_merge_groups_list.extend(merge_group.items)

            files_to_remove = self.get_files_to_remove(export_path_list, expected_merge_file_transactions)
            cache_files_to_remove = self.get_files_to_remove([cache_path], expected_cache_file_transactions)

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
           
    def get_source_file_transactions(self, expected_group: MediaItemGroup, operation_type: FileOperationType) -> FileTransactionList:
        file_transactions = FileTransactionList(transactions=[])
        settings = FileTransactionSettings(existing_file_action=ExistingFileAction.SKIP_IF_SAME_SIZE)
        for item in expected_group.items:
            if "src_file_path" not in item.metadata:
                continue

            source_path = item.metadata["src_file_path"]
            dest_path = self.item_manager.get_full_filepath(item)

            file_transactions.transactions.append(FileTransaction(
                type=operation_type,
                source=source_path,
                destination=dest_path,
                settings=settings,
                metadata={}
            ))
        return file_transactions

    def get_file_linked_transactions(self, expected_group: MediaItemGroup, source_db_type: MediaDbType) -> FileTransactionList:
        file_transactions = FileTransactionList(transactions=[])
        settings = FileTransactionSettings(existing_file_action=ExistingFileAction.SKIP_IF_SAME_SIZE)
        for item in expected_group.items:
            dest_path = item.get_file_path_link(self.media_base_path, item.db_type)

            file_transactions.transactions.append(FileTransaction(
                type=FileOperationType.LINK,
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

    def get_files_to_remove2(self, expected_group: MediaItemGroup, base_paths: list[str], media_path: str, cache_path: str, is_merged: bool) -> FileTransactionList:
        file_transactions = FileTransactionList(transactions=[])

        # For each file in base_path and all sub folders, check if it exists in expected_group
        for base_path in base_paths:
            for root, dirs, files in os.walk(base_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if not expected_group.does_item_path_exist(media_path, cache_path, is_merged, file_path):
                        file_transactions.transactions.append(FileTransaction(
                            type=FileOperationType.DELETE,
                            source=str(file_path),
                            destination="",
                            metadata={}
                        ))
        return file_transactions


    def get_files_to_remove(self, base_paths: list[str], source_file_transactions: FileTransactionList) -> FileTransactionList:
        file_transactions = FileTransactionList(transactions=[])

        # For each file in base_path and all sub folders, check if it exists in expected_group
        for base_path in base_paths:
            for root, dirs, files in os.walk(base_path):
                for file in files:
                    file_path = os.path.join(root, file)

                    # Check if the file exists in the source_file_transactions for COPY, LINK, or SYMLINK
                    for transaction in source_file_transactions.transactions:
                        if transaction.type in [FileOperationType.COPY, FileOperationType.LINK] and transaction.destination == file_path:
                            break
                    else:
                        file_transactions.transactions.append(FileTransaction(
                            type=FileOperationType.DELETE,
                            source=str(file_path),
                            destination="",
                            metadata={}
                        ))

        return file_transactions


        
        