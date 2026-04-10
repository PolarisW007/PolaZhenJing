"""
=============================================================================
Module: ai.openai_provider
Description: OpenAI-compatible AI provider.  Works with any API that follows
             the OpenAI chat-completions schema (OpenAI, Azure OpenAI,
             DeepSeek, Moonshot, etc.) by configuring base_url.
             OpenAI兼容AI提供商 - 适用于任何遵循OpenAI聊天完成模式的API。
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

logger = logging.getLogger("polazj.ai.openai")


class OpenAIProvider(BaseAIProvider):
    """
    Concrete AI provider that calls any OpenAI-compatible chat API.

    Configuration via settings:
        OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
    """

    def __init__(self) -> None:
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = settings.OPENAI_BASE_URL.rstrip("/")
        self.model = settings.OPENAI_MODEL

    # ── Internal helper ──────────────────────────────────────────────────
    async def _chat(self, system_prompt: str, user_prompt: str) -> str:
        """
        Send a chat completion request and return the assistant's reply.

        Raises:
            RuntimeError: On HTTP or API errors.
        """
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.7,
        }

        timeout_cfg = httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0)
        async with httpx.AsyncClient(timeout=timeout_cfg) as http_client:
            try:
                resp = await http_client.post(url, json=payload, headers=headers)
            except httpx.ConnectError as e:
                logger.error("Cannot connect to AI provider at %s: %s", self.base_url, e)
                raise RuntimeError(
                    f"无法连接AI服务 ({self.base_url})，请检查网络或API配置"
                ) from e
            except httpx.TimeoutException as e:
                logger.error("AI provider request timed out: %s", e)
                raise RuntimeError("AI服务请求超时，请稍后重试") from e
            if resp.status_code != 200:
                logger.error("OpenAI API error: %s %s", resp.status_code, resp.text[:500])
                raise RuntimeError(
                    f"AI服务返回错误 (HTTP {resp.status_code})"
                )
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()

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
