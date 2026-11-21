from enum import Enum
from typing import Any
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class ErrorCode(str, Enum):
    INVALID_INN_CHECKSUM = "INVALID_INN_CHECKSUM"
    INVALID_SNILS_CHECKSUM = "INVALID_SNILS_CHECKSUM"
    INVALID_STATUS_TRANSITION = "INVALID_STATUS_TRANSITION"
    ENTITY_NOT_FOUND = "ENTITY_NOT_FOUND"
    DUPLICATE_IDEMPOTENCY_KEY = "DUPLICATE_IDEMPOTENCY_KEY"


class BusinessException(Exception):
    def __init__(
        self,
        message: str,
        error_code: ErrorCode | str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Any = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code.value if isinstance(error_code, ErrorCode) else error_code
        self.status_code = status_code
        self.details = details


class InvalidINNChecksumException(BusinessException):
    def __init__(self, message: str = "Invalid legal entity INN checksum", details: Any = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.INVALID_INN_CHECKSUM,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class InvalidSNILSChecksumException(BusinessException):
    def __init__(self, message: str = "Invalid SNILS checksum", details: Any = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.INVALID_SNILS_CHECKSUM,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class InvalidStatusTransitionException(BusinessException):
    def __init__(
        self,
        current_status: str,
        target_status: str,
        message: str | None = None,
        details: Any = None,
    ):
        msg = message or f"Transition from '{current_status}' to '{target_status}' is not allowed"
        super().__init__(
            message=msg,
            error_code=ErrorCode.INVALID_STATUS_TRANSITION,
            status_code=status.HTTP_409_CONFLICT,
            details=details or {"current_status": current_status, "target_status": target_status},
        )


class EntityNotFoundException(BusinessException):
    def __init__(self, entity_name: str, entity_id: Any):
        super().__init__(
            message=f"{entity_name} with identifier '{entity_id}' not found",
            error_code=ErrorCode.ENTITY_NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND,
            details={"entity_name": entity_name, "identifier": str(entity_id)},
        )


class DuplicateIdempotencyKeyException(BusinessException):
    def __init__(self, key: str):
        super().__init__(
            message=f"Request with idempotency key '{key}' already exists",
            error_code=ErrorCode.DUPLICATE_IDEMPOTENCY_KEY,
            status_code=status.HTTP_409_CONFLICT,
            details={"idempotency_key": key},
        )


async def business_exception_handler(request: Request, exc: BusinessException) -> JSONResponse:
    content: dict[str, Any] = {
        "error": {
            "code": exc.error_code,
            "message": exc.message,
        }
    }
    if exc.details is not None:
        content["error"]["details"] = exc.details

    return JSONResponse(status_code=exc.status_code, content=content)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(BusinessException, business_exception_handler)
