"""
=============================================================================
Module: config
Description: Application settings loaded from environment variables using
             pydantic-settings. Centralises all configuration in one place.
             应用配置 - 通过pydantic-settings从环境变量加载，集中管理所有配置。
Created: 2026-04-06
Author: PolaZhenjing Team
Dependencies: pydantic-settings
=============================================================================
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration for the PolaZhenjing backend.

    All values can be overridden via environment variables or a .env file
    located in the backend/ directory.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Application ──────────────────────────────────────────────────────
    APP_NAME: str = "PolaZhenjing"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # ── Database ─────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://polazj:polazj_secret@localhost:5432/polazj_db"

    # ── JWT Authentication ───────────────────────────────────────────────
    JWT_SECRET_KEY: str = "change-me-in-production-use-strong-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── AI Provider ──────────────────────────────────────────────────────
    AI_PROVIDER: str = "openai"  # "openai" | "ollama"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"

    # ── Site / Publishing ────────────────────────────────────────────────
    SITE_BASE_URL: str = "https://yourusername.github.io/PolaZhenJing"
    SITE_DIR: str = "/site"  # path to MkDocs project root

    # ── Research ──────────────────────────────────────────────────────────
    TAVILY_API_KEY: str = ""  # Optional – enables web search for research
    RESEARCH_OUTPUT_DIR: str = "./research_output"  # Directory for generated HTML files

    # ── CORS ─────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]


# Singleton instance – import this across the app
settings = Settings()
