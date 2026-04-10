"""
=============================================================================
Module: ai.base_provider
Description: Abstract base class defining the interface every AI provider must
             implement.  Uses the Strategy pattern so providers can be swapped
             at runtime via configuration.
             AI提供商抽象基类 - 定义所有AI提供商必须实现的接口，
             使用策略模式，可通过配置在运行时切换提供商。
Created: 2026-04-06
Author: PolaZhenjing Team
Dependencies: (none – pure Python ABC)
=============================================================================
"""

from abc import ABC, abstractmethod


class BaseAIProvider(ABC):
    """
    Abstract AI provider interface.

    Every concrete provider (OpenAI, Ollama, etc.) must implement these
    methods.  The factory in `ai.factory` instantiates the correct provider
    based on the application config.
    """

    @abstractmethod
    async def polish_text(self, text: str, style: str = "professional") -> str:
        """
        Polish / rewrite text for clarity and style.

        Args:
            text: Raw text to polish.
            style: Target style – e.g. "professional", "casual", "academic".

        Returns:
            Polished text string.
        """
        ...

    @abstractmethod
    async def generate_summary(self, text: str, max_length: int = 200) -> str:
        """
        Generate a concise summary of the given text.

        Args:
            text: Source text.
            max_length: Approximate maximum character count.

        Returns:
            Summary string.
        """
        ...

    @abstractmethod
    async def suggest_tags(self, text: str, max_tags: int = 5) -> list[str]:
        """
        Suggest relevant tags/keywords for the given text.

        Args:
            text: Source text.
            max_tags: Maximum number of tags to return.

        Returns:
            List of tag name strings.
        """
        ...

    @abstractmethod
    async def expand_thought(self, text: str, direction: str = "elaborate") -> str:
        """
        Expand a short thought into a fuller piece of writing.

        Args:
            text: Seed text / brief thought.
            direction: How to expand – "elaborate", "argue", "storytell".

        Returns:
            Expanded text.
        """
        ...
