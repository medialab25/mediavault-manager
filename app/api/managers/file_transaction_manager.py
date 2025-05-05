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
            
            # Apply list in this order: DELETE, LINK, COPY, MOVE
            transactions = file_transactions.transactions 
            transactions.sort(key=lambda x: x.type.order)
            for transaction in transactions:
                if transaction.type == FileOperationType.COPY:
                    if os.path.exists(transaction.destination):
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
                    if os.path.exists(transaction.path):
                        if not dry_run:
                            os.remove(transaction.path)
                            # Also remove metadata file if it exists
                            meta_path = f"{transaction.path}.meta"
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

    def get_file_transactions_remove_unreferenced_files(self, base_path: str, file_transactions: FileTransactionList) -> FileTransactionSummary:
        # Recursively get all files in base_path, and if this does not exist in the file transactions for COPY, UPDATE then add to a delete trasnaction list
        delete_transactions = []
        for root, dirs, files in os.walk(base_path):
            for file in files:
                file_path = os.path.join(root, file)
                if not any(transaction.destination == file_path and transaction.type in [FileOperationType.COPY, FileOperationType.UPDATE] for transaction in file_transactions.transactions):
                    delete_transactions.append(FileTransaction(type=FileOperationType.DELETE, path=file_path))

        # Merge the file_transactions with the delete_transactions as a new file_transactions object and return it
        return FileTransactionList(transactions=file_transactions.transactions + delete_transactions)
