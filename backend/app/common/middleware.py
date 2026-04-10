"""
=============================================================================
Module: common.middleware
Description: CORS configuration and request-logging middleware.
             CORS配置和请求日志中间件。
Created: 2026-04-06
Author: PolaZhenjing Team
Dependencies: fastapi, starlette
=============================================================================
"""

import logging
import time

from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware

from app.config import settings

logger = logging.getLogger("polazj")


# ── CORS Setup ───────────────────────────────────────────────────────────
def setup_cors(app: FastAPI) -> None:
    """
    Add CORS middleware.

    Allowed origins are read from settings.CORS_ORIGINS so they can be
    adjusted per environment without touching code.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# ── Request Logging ──────────────────────────────────────────────────────
def setup_request_logging(app: FastAPI) -> None:
    """
    Register middleware that logs every request with method, path, status
    code, and elapsed time in milliseconds.
    """

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s -> %s (%.1f ms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response
