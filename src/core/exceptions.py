from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from src.core.logger import get_logger, request_id_ctx

logger = get_logger(__name__)


class BaseDomainException(Exception):
    """Base exception for all domain errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class ResourceNotFoundException(BaseDomainException):
    def __init__(
        self,
        message: str = "Resource not found",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message,
            code="RESOURCE_NOT_FOUND",
            status_code=404,
            details=details,
        )


class ValidationException(BaseDomainException):
    def __init__(
        self,
        message: str = "Validation failed",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message,
            code="VALIDATION_ERROR",
            status_code=422,
            details=details,
        )


class BusinessLogicException(BaseDomainException):
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message,
            code="BUSINESS_LOGIC_ERROR",
            status_code=400,
            details=details,
        )


class AuthenticationException(BaseDomainException):
    def __init__(
        self,
        message: str = "Authentication failed",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, code="UNAUTHORIZED", status_code=401, details=details)


class AuthorizationException(BaseDomainException):
    def __init__(
        self,
        message: str = "Permission denied",
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message, code="FORBIDDEN", status_code=403, details=details)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catches all BaseDomainExceptions and formats them into a standard JSON response.
    Also logs the error with the trace ID.
    """
    req_id = request_id_ctx.get()

    if isinstance(exc, BaseDomainException):
        logger.warning(f"Domain error: {exc.message}", extra={"error_code": exc.code})
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                    "trace_id": req_id,
                },
            },
        )

    # Unhandled exceptions
    logger.exception(f"Unhandled error occurred: {exc!s}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred.",
                "trace_id": req_id,
            },
        },
    )
