"""Custom exceptions and error handling."""

import logging
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, status
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

logger = logging.getLogger(__name__)


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        error_code: str = "APP_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(AppException):
    """Validation error exception."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class NotFoundError(AppException):
    """Resource not found exception."""

    def __init__(self, resource: str, identifier: str = None):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource, "identifier": identifier},
        )


class DuplicateError(AppException):
    """Duplicate resource exception."""

    def __init__(self, resource: str, field: str = None, value: str = None):
        message = f"{resource} already exists"
        if field and value:
            message += f": {field}={value}"
        
        super().__init__(
            message=message,
            error_code="DUPLICATE_ERROR",
            status_code=status.HTTP_409_CONFLICT,
            details={"resource": resource, "field": field, "value": value},
        )


class ExternalServiceError(AppException):
    """External service error exception."""

    def __init__(self, service: str, message: str = None):
        default_message = f"{service} service is currently unavailable"
        super().__init__(
            message=message or default_message,
            error_code="EXTERNAL_SERVICE_ERROR",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details={"service": service},
        )


class AuthenticationError(AppException):
    """Authentication error exception."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class AuthorizationError(AppException):
    """Authorization error exception."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=status.HTTP_403_FORBIDDEN,
        )


class RateLimitError(AppException):
    """Rate limit exceeded exception."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle application exceptions."""
    logger.error(
        f"Application error: {exc.error_code} - {exc.message}",
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method,
        },
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "timestamp": logger.handlers[0].formatter.formatTime(logger.makeRecord(
                    name="error", level=logging.ERROR, fn="", lno=0, msg="", args=(), exc_info=None
                )) if logger.handlers else None,
            }
        },
    )


async def http_exception_handler_custom(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions with consistent format."""
    logger.warning(
        f"HTTP error {exc.status_code}: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
        },
    )
    
    # Map common HTTP status codes to error codes
    error_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_SERVER_ERROR",
        503: "SERVICE_UNAVAILABLE",
    }
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": error_code_map.get(exc.status_code, "HTTP_ERROR"),
                "message": exc.detail,
                "details": {},
                "timestamp": logger.handlers[0].formatter.formatTime(logger.makeRecord(
                    name="error", level=logging.ERROR, fn="", lno=0, msg="", args=(), exc_info=None
                )) if logger.handlers else None,
            }
        },
    )


async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle Pydantic validation errors."""
    logger.warning(
        f"Validation error: {len(exc.errors())} field(s)",
        extra={
            "errors": exc.errors(),
            "path": request.url.path,
            "method": request.method,
        },
    )
    
    # Format validation errors
    formatted_errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        formatted_errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"],
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {
                    "validation_errors": formatted_errors,
                },
                "timestamp": logger.handlers[0].formatter.formatTime(logger.makeRecord(
                    name="error", level=logging.ERROR, fn="", lno=0, msg="", args=(), exc_info=None
                )) if logger.handlers else None,
            }
        },
    )


async def database_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle database errors."""
    logger.error(
        f"Database error: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
        },
        exc_info=True,
    )
    
    # Handle specific database errors
    if isinstance(exc, IntegrityError):
        error_code = "INTEGRITY_ERROR"
        message = "Data integrity constraint violation"
        status_code = status.HTTP_409_CONFLICT
        
        # Try to extract meaningful info from the error
        error_str = str(exc.orig) if hasattr(exc, 'orig') else str(exc)
        if "duplicate key" in error_str.lower() or "unique constraint" in error_str.lower():
            message = "A record with this information already exists"
        elif "foreign key" in error_str.lower():
            message = "Referenced record does not exist"
    else:
        error_code = "DATABASE_ERROR"
        message = "Database operation failed"
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": error_code,
                "message": message,
                "details": {},
                "timestamp": logger.handlers[0].formatter.formatTime(logger.makeRecord(
                    name="error", level=logging.ERROR, fn="", lno=0, msg="", args=(), exc_info=None
                )) if logger.handlers else None,
            }
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other exceptions."""
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
        },
        exc_info=True,
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": {},
                "timestamp": logger.handlers[0].formatter.formatTime(logger.makeRecord(
                    name="error", level=logging.ERROR, fn="", lno=0, msg="", args=(), exc_info=None
                )) if logger.handlers else None,
            }
        },
    )