from pathlib import Path
from typing import Any
from app.api.managers.cache_manager import CacheManager
from app.api.managers.data_manager import DataManager
from app.api.managers.file_transaction_manager import FileTransactionManager
from app.api.managers.item_manager import ItemManager, ItemMatchKey
from app.api.managers.matrix_manager import MatrixManager
from app.api.managers.media_manager import MediaManager
from app.api.managers.media_query import MediaQuery
from app.api.managers.media_server import MediaServer
from app.api.models.file_transaction_models import FileSequenceTransaction, FileSequenceTransactionOperation, FileTransactionList, FileTransactionSettings, ExistingFileAction, FileOperationType
from app.api.models.media_models import MediaDbType, MediaItemGroup, SyncDetailRequest
from app.api.models.search_request import SearchRequest
from app.api.process.cache_processor import CacheProcessor
from app.api.process.media_merger import MediaMerger
from app.api.managers.manifest_manager import ManifestManager
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
        self.data_manager = DataManager(config)
        self.matrix_manager = MatrixManager(config)
        self.media_library_info = self.matrix_manager.get_media_library_info()
        self.manifest_manager = ManifestManager(config)
        self.media_server = MediaServer()
        
    async def sync(self, dry_run: bool = False, details: SyncDetailRequest = SyncDetailRequest.NONE, force: bool = False) -> dict[str, Any]:
        """Sync the cache with the media library
        
        Args:
            dry_run (bool): If True, only show what would be done without making changes
            details (SyncDetailRequest): If True, show details of the sync operation
        Returns:
            MediaItemGroupDict: The results of the sync operation
        """
        try:
            # Only sync if the media_library_update_request_count is greater than 0 or a force flag is passed
            if self.data_manager.get_media_library_update_request() == 0 and not force:
                logger.debug("No media library update request count, skipping sync")
                return {
                    "message": "No media library update request count, skipping sync"
                }
            
            logger.debug(f"Starting sync{' (dry run)' if dry_run else ''}")

            # Get current state
            actual_media_model = self.media_manager.search_media(SearchRequest(db_type=[MediaDbType.MEDIA, MediaDbType.CACHE]))
            query = MediaQuery(actual_media_model)

            actual_media_group = query.get_items(SearchRequest(db_type=[MediaDbType.MEDIA]))
            actual_cache_group = query.get_items(SearchRequest(db_type=[MediaDbType.CACHE]))

            self._link_cache_items_to_media_items(actual_cache_group, actual_media_group)

            # Process cache
            # Get the max cache size
            max_cache_size_gb = self.config.get("max_cache_size_gb", 100)
            expected_cache_group = self.cache_processor.get_expected_cache(actual_media_group, actual_cache_group, dry_run=dry_run, max_cache_size_gb=max_cache_size_gb)

            # Get merged items
            expected_merge_group = self.media_merger.merge_libraries(actual_media_group, expected_cache_group)

            file_transactions = FileTransactionList(transactions=[])

            # Get file transactions for delete group
            group_list = [expected_cache_group, expected_merge_group]
            path_list = [self.media_library_info.cache_library_path, self.media_library_info.export_library_path]
            self._add_file_delete_transactions(file_transactions, group_list, path_list)

            # Get file transactions for cache
            self._add_file_transactions(file_transactions, expected_cache_group, FileOperationType.COPY)

            # Get file transactions for merge group
            self._add_file_transactions(file_transactions, expected_merge_group, FileOperationType.LINK)

            file_transaction_summary = self.file_transaction_manager.apply_file_transactions(file_transactions, settings=None, dry_run=dry_run)

            # Delete empty folders
            self._delete_empty_folders([self.media_library_info.cache_library_path, self.media_library_info.export_library_path], file_transaction_summary.sequence_transactions, dry_run=dry_run)

            # clear precache
            if not dry_run:
                self.cache_manager.clear_pre_cache()

                # clear media library update request count
                self.data_manager.clear_media_library_update_request()
                self.data_manager.update()

                # Refresh media server
                await self.media_server.refresh_media()

            if details == SyncDetailRequest.DETAILS:
                return {
                    "file_transaction_summary": file_transaction_summary,
                    "expected_cache_group": expected_cache_group,
                    "expected_merge_group": expected_merge_group,
                    "file_transactions": file_transactions
                }
            elif details == SyncDetailRequest.SUMMARY:
                return {
                    "file_transaction_summary": file_transaction_summary
                }
            elif details == SyncDetailRequest.TRANSACTIONS:
                resultSummary = {
                    "transactions": file_transaction_summary.sequence_transactions
                }
                return resultSummary
            else:
                return {}

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
            matching_media_item = self.item_manager.get_matching_item(item, media_group.items, ItemMatchKey.TITLE_PATH)
            if not matching_media_item:
                continue

            # Link cache item to media item
            item.source_item = matching_media_item
            
    def _get_file_transactions(self, expected_group: MediaItemGroup, operation_type: FileOperationType) -> FileTransactionList:
        file_transactions = FileTransactionList(transactions=[])
        self._add_file_transactions(file_transactions, expected_group, operation_type)
        return file_transactions

    def _recurse_delete_empty_folders(self, folder: Path, sequence_transactions: list[FileSequenceTransaction], dry_run: bool = False) -> None:
        for child in folder.iterdir():
            if child.is_dir():
                self._recurse_delete_empty_folders(child, sequence_transactions, dry_run)
        
        if folder.is_dir() and not any(folder.iterdir()):
            if not dry_run:
                folder.rmdir()
                sequence_transactions.append(FileSequenceTransaction(operation=FileSequenceTransactionOperation.DELETE_FOLDER, source=str(folder), destination=str(folder)))

    def _delete_empty_folders(self, base_paths: list[str], sequence_transactions: list[FileSequenceTransaction], dry_run: bool = False) -> None:
        for base_path in base_paths:
            if not Path(base_path).exists():
                continue

            # Get list of folders in base_path, only top level
            folders = [f for f in Path(base_path).iterdir() if f.is_dir()]
            for folder in folders:
                child_folders = [f for f in folder.iterdir() if f.is_dir()]
                for child_folder in child_folders:
                    self._recurse_delete_empty_folders(child_folder, sequence_transactions, dry_run)

    def _add_file_delete_transactions(self, file_transactions: FileTransactionList, group_list: list[MediaItemGroup], base_paths: list[str]) -> None:
        # Get list of all allowed files from the group list
        allowed_files = []
        for group in group_list:
            for item in group.items:
                if item.full_file_path:
                    allowed_files.append(Path(item.full_file_path))

        # Get list of all files in the base paths
        files = []
        for base_path in base_paths:
            files.extend([f for f in Path(base_path).glob("**/*") if f.is_file()])

        # Get list of all files in the base paths that are not in the allowed files list
        files_to_delete = [file for file in files if file not in allowed_files]

        for file in files_to_delete:
            file_transactions.delete(
                path=str(file),
                settings=FileTransactionSettings(existing_file_action=ExistingFileAction.SKIP_IF_SAME_SIZE),
                metadata={}
            )

    def _add_file_transactions(self, file_transactions: FileTransactionList, expected_group: MediaItemGroup, operation_type: FileOperationType) -> None:
        for item in expected_group.items:
            if not item.source_item:
                file_transactions.delete(
                    path=str(item.full_file_path),
                    settings=FileTransactionSettings(existing_file_action=ExistingFileAction.SKIP_IF_SAME_SIZE),
                    metadata={}
                )
                continue

            file_transactions.add(
                source=str(item.source_item.full_file_path),
                destination=str(item.full_file_path),
                type=operation_type,
                settings=FileTransactionSettings(existing_file_action=ExistingFileAction.SKIP_IF_SAME_SIZE),
                metadata={})

    #def update_manifest(self, manifest_group: ManifestItemGroup, media_items: list[MediaItem]) -> None:
    #    items = [ManifestItem(full_file_path=item.full_file_path) for item in media_items]
    #
    #    # At present replace all items in the manifest
    #    self.manifest_manager.set_manifest_group(ManifestItemGroup(manifest_type=manifest_group.manifest_type, items=items))