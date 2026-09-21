# app/llm/openai.py

from __future__ import annotations

from collections.abc import AsyncGenerator

import httpx

from app.core.config import settings
from app.llm.base import LLMProvider, Message


class OpenAIProvider(LLMProvider):
    BASE_URL = "https://api.openai.com/v1/chat/completions"

    def __init__(self) -> None:
        self.api_key = settings.OPENAI_API_KEY

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _serialize(messages: list[Message]) -> list[dict[str, str]]:
        return [
            {
                "role": msg.role.value,
                "content": msg.content,
            }
            for msg in messages
        ]

    async def generate(
        self,
        messages: list[Message],
        model: str,
    ) -> str:
        payload = {
            "model": model,
            "messages": self._serialize(messages),
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                self.BASE_URL,
                headers=self._headers(),
                json=payload,
            )

        response.raise_for_status()
        data = response.json()

        return data["choices"][0]["message"]["content"]

    async def stream(
        self,
        messages: list[Message],
        model: str,
    ) -> AsyncGenerator[str, None]:
        payload = {
            "model": model,
            "messages": self._serialize(messages),
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                self.BASE_URL,
                headers=self._headers(),
                json=payload,
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue

                    data = line.removeprefix("data: ")

                    if data == "[DONE]":
                        break

                    chunk = httpx.Response(200, content=data).json()

                    delta = chunk["choices"][0]["delta"]
                    content = delta.get("content")

                    if content:
                        yield content