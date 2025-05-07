from pathlib import Path
from typing import Any
from app.api.managers.cache_manager import CacheManager
from app.api.managers.file_transaction_manager import FileTransactionManager
from app.api.managers.item_manager import ItemManager
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
        self.item_manager = ItemManager(config)

    def sync(self, dry_run: bool = False) -> FileTransactionList:
        """Sync the cache with the media library"""
        # Get current media and cache states
        current_media = self.media_manager.search_media(SearchRequest(db_type=[MediaDbType.MEDIA]))
        current_cache = self.media_manager.search_media(SearchRequest(db_type=[MediaDbType.CACHE]))

        # Process cache
        expected_cache = self.cache_processor.get_expected_cache(current_cache)

        # Merge items
        expected_merge_groups = self.media_merger.merge_libraries(current_media, expected_cache)

        # Create file transactions
        file_transactions = []
        for item in expected_merge_groups.items:
            # Get source and destination paths
            src_path = item.get_file_path_link(self.media_base_path, item.source.db_type)
            dest_path = item.get_file_path_link(self.media_base_path, item.source.db_type)

            # Create file transaction
            file_transaction = FileTransaction(
                source_path=src_path,
                destination_path=dest_path,
                operation_type=FileOperationType.COPY,
                existing_file_action=ExistingFileAction.SKIP
            )
            file_transactions.append(file_transaction)

        # Create file transaction list
        file_transaction_list = FileTransactionList(
            transactions=file_transactions,
            settings=FileTransactionSettings(
                dry_run=dry_run,
                apply_settings=FileApplyTransactionSettings(
                    create_directories=True,
                    preserve_permissions=True
                )
            )
        )

        # Apply transactions if not dry run
        if not dry_run:
            self.file_transaction_manager.apply_transactions(file_transaction_list)

        return file_transaction_list

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


        
        