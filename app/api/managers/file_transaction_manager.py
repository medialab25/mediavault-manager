import logging
import os
import shutil
from typing import Any

from app.api.models.file_transaction_models import ExistingFileAction, FileOperationType, FileTransactionList, FileTransactionSettings, FileTransactionSummary

class FileTransactionManager:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.file_transaction_settings = FileTransactionSettings(existing_file_action=ExistingFileAction.OVERWRITE)

    def apply_file_transactions(self, file_transactions: FileTransactionList, dry_run: bool = False) -> FileTransactionSummary:
        """Apply the file transactions to the file system
        
        Args:
            file_transactions (FileTransactionList): The file transactions to apply
            dry_run (bool): If True, simulate the operations without actually performing them
            
        Returns:
            FileTransactionSummary: Summary of the applied transactions
        """
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
                elif transaction.type == FileOperationType.MOVE:
                    if os.path.exists(transaction.destination):
                        if not dry_run:
                            os.remove(transaction.destination)
                        summary.updated_transactions.append(transaction)
                    else:
                        summary.added_transactions.append(transaction)
                    if not dry_run:
                        shutil.move(transaction.source, transaction.destination)
                elif transaction.type == FileOperationType.DELETE:
                    if os.path.exists(transaction.path):
                        if not dry_run:
                            os.remove(transaction.path)
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
                else:
                    raise ValueError(f"Invalid file operation type: {transaction.type}")
            
            return summary
            
        except Exception as e:
            logging.error(f"Error applying file transactions: {str(e)}", exc_info=True)
            raise e
