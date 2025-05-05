from typing import Any
from app.api.managers.file_transaction_manager import FileTransactionManager
from app.api.models.media_models import MediaItemGroup
from app.api.managers.cache_manager import _add_cache_items, _remove_cache_items
from app.api.models.file_transaction_models import FileTransactionList, FileTransactionSummary

class CacheProcessor:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.file_transaction_manager = FileTransactionManager(config)

    def sync_cache(self, dry_run: bool = False) -> FileTransactionSummary:
        """Process the cache
        
        Args:
            dry_run (bool): If True, only show what would be done without making changes
            
        Returns:
            FileTransactionSummary: The summary of the file transactions
        """

        # Create file transaction list to delete all items in _remove_cache_items
        file_transactions = FileTransactionList(transactions=[])
        for item in _remove_cache_items:
            file_transactions.delete(item.full_path)

        # Create file transaction list to add all items in _add_cache_items
        file_transactions = FileTransactionList(transactions=[])
        for item in _add_cache_items:
            file_transactions.add(item.full_path)

        # Apply file transactions
        file_transaction_summary = self.file_transaction_manager.apply_file_transactions(file_transactions, settings=None, dry_run=dry_run)

        # Process cache
        return file_transaction_summary

