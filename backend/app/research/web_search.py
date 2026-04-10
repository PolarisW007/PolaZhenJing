"""
=============================================================================
Module: research.web_search
Description: Optional web search integration for deep research reports.
             Supports Tavily API with graceful fallback to a no-op provider.
             可选的网络搜索集成 - 支持Tavily API，无API密钥时优雅降级。
Created: 2026-04-06
Author: PolaZhenjing Team
Dependencies: httpx
=============================================================================
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import httpx

from app.config import settings

logger = logging.getLogger("polazj.research.search")


@dataclass
class SearchResult:
    """A single web search result."""
    title: str
    url: str
    snippet: str
    score: float = 0.0


class BaseSearchProvider(ABC):
    """Abstract search provider interface."""

    @abstractmethod
    async def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        ...

    @property
    @abstractmethod
    def is_available(self) -> bool:
        ...


class TavilySearchProvider(BaseSearchProvider):
    """Search provider using Tavily API."""

    def __init__(self) -> None:
        self.api_key = settings.TAVILY_API_KEY
        self.base_url = "https://api.tavily.com"

    @property
    def is_available(self) -> bool:
        return bool(self.api_key)

    async def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        url = f"{self.base_url}/search"
        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
            "include_answer": False,
            "search_depth": "advanced",
        }
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code != 200:
                    logger.warning("Tavily search failed: %s", resp.text)
                    return []
                data = resp.json()
                results = []
                for item in data.get("results", [])[:max_results]:
                    results.append(SearchResult(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        snippet=item.get("content", ""),
                        score=item.get("score", 0.0),
                    ))
                return results
        except Exception as e:
            logger.error("Tavily search error: %s", e)
            return []


class NoopSearchProvider(BaseSearchProvider):
    """Fallback no-op search provider when no API key is configured."""

    @property
    def is_available(self) -> bool:
        return False

    async def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        return []


def get_search_provider() -> BaseSearchProvider:
    """Return the appropriate search provider based on configuration."""
    if settings.TAVILY_API_KEY:
        provider = TavilySearchProvider()
        logger.info("Using Tavily search provider")
        return provider
    logger.info("No search API key configured, using NoopSearchProvider")
    return NoopSearchProvider()
