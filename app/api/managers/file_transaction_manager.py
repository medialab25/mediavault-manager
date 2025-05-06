import logging
import os
import shutil
import json
from typing import Any

from app.api.models.file_transaction_models import ExistingFileAction, FileApplyTransactionSettings, FileOperationType, FileTransaction, FileTransactionList, FileTransactionSettings, FileTransactionSummary

class FileTransactionManager:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.file_transaction_settings = FileTransactionSettings(existing_file_action=ExistingFileAction.OVERWRITE)

    def _write_metadata_file(self, file_path: str, metadata: dict[str, Any]) -> None:
        """Write metadata to a .meta file alongside the target file
        
        Args:
            file_path (str): Path to the target file
            metadata (dict[str, Any]): Metadata to write
        """
        meta_path = f"{file_path}.meta"
        if os.path.exists(meta_path):
            os.remove(meta_path)
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)

    def _should_skip_file(self, source_path: str, dest_path: str, settings: FileTransactionSettings) -> bool:
        """Check if we should skip copying/moving a file based on the settings
        
        Args:
            source_path (str): Path to the source file
            dest_path (str): Path to the destination file
            settings (FileTransactionSettings): Settings to check against
            
        Returns:
            bool: True if the file should be skipped, False otherwise
        """
        if not os.path.exists(dest_path):
            return False
            
        if settings.existing_file_action == ExistingFileAction.OVERWRITE:
            return False
            
        if settings.existing_file_action == ExistingFileAction.SKIP:
            return True
            
        if settings.existing_file_action == ExistingFileAction.SKIP_IF_SAME_SIZE:
            return os.path.getsize(source_path) == os.path.getsize(dest_path)
            
        return False

    def apply_file_transactions(self, file_transactions: FileTransactionList, settings: FileApplyTransactionSettings = None, dry_run: bool = False) -> FileTransactionSummary:
        """Apply the file transactions to the file system
        
        Args:
            file_transactions (FileTransactionList): The file transactions to apply
            settings (FileApplyTransactionSettings): Settings for applying transactions
            dry_run (bool): If True, simulate the operations without actually performing them
            
        Returns:
            FileTransactionSummary: Summary of the applied transactions
        """
        settings = settings or FileApplyTransactionSettings()

        try:
            summary = FileTransactionSummary(
                added_transactions=[],
                skipped_transactions=[],
                deleted_transactions=[],
                linked_transactions=[],
                updated_transactions=[]
            )
            
            # Apply list in this order: DELETE, LINK, COPY, MOVE, if apply_delete_first set
            transactions = file_transactions.transactions 
            if settings.apply_delete_first:
               # Make a copy of the transactions list
               transactions = FileTransactionList(transactions=[transactions])
               transactions.sort(key=lambda x: x.type.order)

            for transaction in transactions:
                transaction_settings = transaction.settings or self.file_transaction_settings
                if transaction.type == FileOperationType.COPY:
                    if os.path.exists(transaction.destination):
                        if self._should_skip_file(transaction.source, transaction.destination, transaction_settings):
                            summary.skipped_transactions.append(transaction)
                            continue
                        if not dry_run:
                            os.remove(transaction.destination)
                        summary.updated_transactions.append(transaction)
                    else:
                        summary.added_transactions.append(transaction)
                    if not dry_run:
                        shutil.copy(transaction.source, transaction.destination)
                        if settings.write_file_metadata and transaction.metadata:
                            self._write_metadata_file(transaction.destination, transaction.metadata)
                elif transaction.type == FileOperationType.MOVE:
                    if os.path.exists(transaction.destination):
                        if self._should_skip_file(transaction.source, transaction.destination, transaction_settings):
                            summary.skipped_transactions.append(transaction)
                            continue
                        if not dry_run:
                            os.remove(transaction.destination)
                        summary.updated_transactions.append(transaction)
                    else:
                        summary.added_transactions.append(transaction)
                    if not dry_run:
                        shutil.move(transaction.source, transaction.destination)
                        if settings.write_file_metadata and transaction.metadata:
                            self._write_metadata_file(transaction.destination, transaction.metadata)
                elif transaction.type == FileOperationType.DELETE:
                    if os.path.exists(transaction.source):
                        if not dry_run:
                            os.remove(transaction.source)
                            # Also remove metadata file if it exists
                            meta_path = f"{transaction.source}.meta"
                            if os.path.exists(meta_path):
                                os.remove(meta_path)
                        summary.deleted_transactions.append(transaction)
                elif transaction.type == FileOperationType.LINK:
                    if os.path.exists(transaction.destination):
                        if not dry_run:
                            os.remove(transaction.destination)
                        summary.updated_transactions.append(transaction)
                    else:
                        summary.linked_transactions.append(transaction)
                    if not dry_run:
                        os.link(transaction.source, transaction.destination)
                        if settings.write_file_metadata and transaction.metadata:
                            self._write_metadata_file(transaction.destination, transaction.metadata)
                else:
                    raise ValueError(f"Invalid file operation type: {transaction.type}")
            
            return summary
            
        except Exception as e:
            logging.error(f"Error applying file transactions: {str(e)}", exc_info=True)
            raise e

    def get_file_transactions_remove_unreferenced_files(self, base_path: str, file_transactions: FileTransactionList) -> FileTransactionList:
        # Recursively get all files in base_path, and if this does not exist in the file transactions for COPY, UPDATE then add to a delete trasnaction list
        delete_transactions = []
        for root, dirs, files in os.walk(base_path):
            for file in files:
                file_path = os.path.join(root, file)
                if not any(transaction.destination == file_path and transaction.type in [FileOperationType.COPY, FileOperationType.UPDATE] for transaction in file_transactions.transactions):
                    delete_transactions.append(FileTransaction(
                        type=FileOperationType.DELETE,
                        source=file_path,
                        destination="",
                        metadata={}
                    ))

        # Merge the file_transactions with the delete_transactions as a new file_transactions object and return it
        return FileTransactionList(transactions=file_transactions.transactions + delete_transactions)
