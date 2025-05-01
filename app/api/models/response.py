from typing import TypeVar, Generic, Optional, Any
from pydantic import BaseModel
from fastapi import HTTPException
from app.core.status import Status

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    status: Status
    message: str
    data: Optional[T] = None

    @classmethod
    def success(cls, data: Any = None, message: str = "Operation completed successfully") -> "APIResponse":
        return cls(
            status=Status.SUCCESS,
            message=message,
            data=data
        )

    @classmethod
    def error(cls, message: str, status_code: int = 500) -> HTTPException:
        return HTTPException(
            status_code=status_code,
            detail={
                "status": Status.ERROR,
                "message": message
            }
        )

    @classmethod
    def not_found(cls, message: str = "Resource not found") -> HTTPException:
        return cls.error(message=message, status_code=404)

    @classmethod
    def bad_request(cls, message: str = "Invalid request") -> HTTPException:
        return cls.error(message=message, status_code=400)

    @classmethod
    def unauthorized(cls, message: str = "Unauthorized access") -> HTTPException:
        return cls.error(message=message, status_code=401)

    @classmethod
    def forbidden(cls, message: str = "Forbidden access") -> HTTPException:
        return cls.error(message=message, status_code=403) 