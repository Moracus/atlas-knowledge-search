# app/llm/base.py

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(slots=True)
class Message:
    role: Role
    content: str


class LLMProvider(ABC):
    """Abstract interface for all LLM providers."""

    @abstractmethod
    async def generate(
        self,
        messages: list[Message],
        model: str,
    ) -> str:
        """
        Generate a complete response from the model.

        Implementations are responsible for translating these
        messages into the provider's API format.
        """
        raise NotImplementedError

    @abstractmethod
    async def stream(
        self,
        messages: list[Message],
        model: str,
    ):
        """
        Yield response tokens/chunks as they arrive.

        Returns an async generator of strings.
        """
        raise NotImplementedError