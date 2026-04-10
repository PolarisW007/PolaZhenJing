"""
=============================================================================
Module: main
Description: FastAPI application entry point.  Wires together all routers,
             middleware, exception handlers, and lifecycle events.
             FastAPI应用入口点 - 组装所有路由、中间件、异常处理和生命周期事件。
Created: 2026-04-06
Author: PolaZhenjing Team
Dependencies: fastapi, app.config, all sub-modules
=============================================================================
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.database import engine

# ── Logging ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger("polazj")


# ── Lifespan ─────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup / shutdown lifecycle."""
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    yield
    # Dispose of the DB engine pool on shutdown
    await engine.dispose()
    logger.info("Shut down gracefully")


# ── App Factory ──────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered personal knowledge wiki and sharing platform",
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────────────────
from app.common.middleware import setup_cors, setup_request_logging  # noqa: E402

setup_cors(app)
setup_request_logging(app)

# ── Exception Handlers ───────────────────────────────────────────────────
from app.common.exceptions import register_exception_handlers  # noqa: E402

register_exception_handlers(app)

# ── Routers ──────────────────────────────────────────────────────────────
from app.auth.router import router as auth_router  # noqa: E402
from app.thoughts.router import router as thoughts_router  # noqa: E402
from app.tags.router import router as tags_router  # noqa: E402
from app.ai.router import router as ai_router  # noqa: E402
from app.publish.router import router as publish_router  # noqa: E402
from app.sharing.router import router as sharing_router  # noqa: E402
from app.research.router import router as research_router  # noqa: E402

app.include_router(auth_router)
app.include_router(thoughts_router)
app.include_router(tags_router)
app.include_router(ai_router)
app.include_router(publish_router)
app.include_router(sharing_router)
app.include_router(research_router)


# ── Health Check ─────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health_check():
    """
    Lightweight health-check endpoint.

    Returns 200 with application name, version, and status.
    Used by Docker health checks and monitoring tools.
    """
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }
