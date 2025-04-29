from enum import Enum

class Status(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    NOT_REQUESTED = "not_requested" 