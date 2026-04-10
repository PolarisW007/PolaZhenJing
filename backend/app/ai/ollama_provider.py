"""
=============================================================================
Module: ai.ollama_provider
Description: Ollama local LLM provider – calls the Ollama REST API running
             on localhost (or a custom host).
             Ollama本地LLM提供商 - 调用运行在本地（或自定义主机）的Ollama REST API。
Created: 2026-04-06
Author: PolaZhenjing Team
Dependencies: httpx
=============================================================================
"""

import json
import logging

import httpx

from app.ai.base_provider import BaseAIProvider
from app.config import settings

logger = logging.getLogger("polazj.ai.ollama")


class OllamaProvider(BaseAIProvider):
    """
    Concrete AI provider that calls a local Ollama instance.

    Configuration via settings:
        OLLAMA_BASE_URL, OLLAMA_MODEL
    """

    def __init__(self) -> None:
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.OLLAMA_MODEL

    # ── Internal helper ──────────────────────────────────────────────────
    async def _chat(self, system_prompt: str, user_prompt: str) -> str:
        """
        Call Ollama's /api/chat endpoint and return the assistant reply.

        Raises:
            RuntimeError: On HTTP or API errors.
        """
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                logger.error("Ollama API error: %s %s", resp.status_code, resp.text)
                raise RuntimeError(f"AI provider returned {resp.status_code}")
            data = resp.json()
            return data["message"]["content"].strip()

    # ── Interface implementations ────────────────────────────────────────
    async def polish_text(self, text: str, style: str = "professional") -> str:
        system = (
            f"You are a writing assistant. Polish the following text to be {style}, "
            "clear, and well-structured. Keep the original meaning. "
            "Return only the polished text, no explanations."
        )
        return await self._chat(system, text)

    async def generate_summary(self, text: str, max_length: int = 200) -> str:
        system = (
            f"Summarise the following text in no more than {max_length} characters. "
            "Return only the summary."
        )
        return await self._chat(system, text)

    async def suggest_tags(self, text: str, max_tags: int = 5) -> list[str]:
        system = (
            f"Suggest up to {max_tags} short keyword tags for the following text. "
            'Return them as a JSON array of strings, e.g. ["tag1","tag2"]. '
            "No other text."
        )
        raw = await self._chat(system, text)
        try:
            tags = json.loads(raw)
            if isinstance(tags, list):
                return [str(t) for t in tags[:max_tags]]
        except json.JSONDecodeError:
            logger.warning("Could not parse AI tag response: %s", raw)
        return []

    async def expand_thought(self, text: str, direction: str = "elaborate") -> str:
        system = (
            f"You are a creative writing assistant. {direction.capitalize()} on the "
            "following brief thought into a well-written paragraph or short article. "
            "Return only the expanded text."
        )
        return await self._chat(system, text)
