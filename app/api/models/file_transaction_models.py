from enum import Enum
from typing import Any, List
from pydantic import BaseModel

class FileOperationType(Enum):
    DELETE = (0, "delete")
    LINK = (1, "link")
    COPY = (2, "copy")
    MOVE = (3, "move")

    def __init__(self, order: int, value: str):
        self.order = order
        self._value_ = value

    def __lt__(self, other):
        return self.order < other.order

class ExistingFileAction(Enum):
    OVERWRITE = (0, "overwrite")
    SKIP = (1, "skip")
    SKIP_IF_SAME_SIZE = (2, "skip_if_same_size")

    def __init__(self, order: int, value: str):
        self.order = order
        self._value_ = value

class FileTransactionSettings(BaseModel):
    existing_file_action: ExistingFileAction

    def get_default_settings(self) -> "FileTransactionSettings":
        return FileTransactionSettings(existing_file_action=ExistingFileAction.OVERWRITE)

class FileApplyTransactionSettings(BaseModel):
    apply_delete_first: bool = False
    write_file_metadata: bool = False
    clear_existing_file_path: str = None

class FileTransaction(BaseModel):
    type: FileOperationType
    settings: FileTransactionSettings = None
    source: str
    destination: str
    metadata: dict[str, Any] = None

class FileTransactionSummary(BaseModel):
    added_transactions: List[FileTransaction]
    updated_transactions: List[FileTransaction]
    skipped_transactions: List[FileTransaction]
    deleted_transactions: List[FileTransaction]
    linked_transactions: List[FileTransaction]

class FileTransactionList(BaseModel):
    transactions: List[FileTransaction]

    def copy(self, source: str, destination: str, settings: FileTransactionSettings = None, metadata: dict[str, Any] = None) -> None:
        self.transactions.append(FileTransaction(type=FileOperationType.COPY, source=source, destination=destination, settings=settings, metadata=metadata))

    def move(self, source: str, destination: str, settings: FileTransactionSettings = None, metadata: dict[str, Any] = None) -> None:
        self.transactions.append(FileTransaction(type=FileOperationType.MOVE, source=source, destination=destination, settings=settings, metadata=metadata))

    def delete(self, path: str, settings: FileTransactionSettings = None, metadata: dict[str, Any] = None) -> None:
        self.transactions.append(FileTransaction(type=FileOperationType.DELETE, source=path, destination="", settings=settings, metadata=metadata))

    def link(self, source: str, destination: str, settings: FileTransactionSettings = None, metadata: dict[str, Any] = None) -> None:
        self.transactions.append(FileTransaction(type=FileOperationType.LINK, source=source, destination=destination, settings=settings, metadata=metadata))
