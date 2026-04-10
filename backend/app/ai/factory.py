"""
=============================================================================
Module: ai.factory
Description: Factory that creates the correct AI provider instance based on
             the application configuration (Strategy pattern).
             AI提供商工厂 - 根据应用配置创建正确的AI提供商实例（策略模式）。
Created: 2026-04-06
Author: PolaZhenjing Team
Dependencies: app.ai.base_provider, app.config
=============================================================================
"""

from functools import lru_cache

from app.ai.base_provider import BaseAIProvider
from app.config import settings


@lru_cache(maxsize=1)
def get_ai_provider() -> BaseAIProvider:
    """
    Return a singleton AI provider based on settings.AI_PROVIDER.

    Supported values:
        - "openai" -> OpenAIProvider (also works for any OpenAI-compatible API)
        - "ollama" -> OllamaProvider (local LLM)

    Raises:
        ValueError: If the configured provider name is unknown.
    """
    provider_name = settings.AI_PROVIDER.lower()

    if provider_name == "openai":
        from app.ai.openai_provider import OpenAIProvider
        return OpenAIProvider()

    if provider_name == "ollama":
        from app.ai.ollama_provider import OllamaProvider
        return OllamaProvider()

    raise ValueError(
        f"Unknown AI provider '{provider_name}'. "
        "Supported: 'openai', 'ollama'."
    )
