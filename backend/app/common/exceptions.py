"""
=============================================================================
Module: common.exceptions
Description: Unified exception classes and FastAPI exception handlers.
             Provides consistent JSON error responses across the API.
             统一异常类和FastAPI异常处理器 - 提供一致的JSON错误响应。
Created: 2026-04-06
Author: PolaZhenjing Team
Dependencies: fastapi
=============================================================================
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


# ── Custom Exceptions ────────────────────────────────────────────────────
class AppException(Exception):
    """Base application exception with HTTP status code and detail message."""

    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str = "Internal server error",
    ):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class NotFoundException(AppException):
    """Resource not found (404)."""

    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class BadRequestException(AppException):
    """Invalid client request (400)."""

    def __init__(self, detail: str = "Bad request"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class UnauthorizedException(AppException):
    """Authentication required or failed (401)."""

    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class ForbiddenException(AppException):
    """Insufficient permissions (403)."""

    def __init__(self, detail: str = "Forbidden"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ConflictException(AppException):
    """Resource conflict, e.g. duplicate entry (409)."""

    def __init__(self, detail: str = "Conflict"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


# ── Handler Registration ─────────────────────────────────────────────────
def register_exception_handlers(app: FastAPI) -> None:
    """
    Register global exception handlers on the FastAPI application.

    Call this once during app startup (in main.py).
    """

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Log unexpected errors in production; return generic message
        import logging; logging.getLogger("polazj").exception("Unhandled: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected error occurred"},
        )
