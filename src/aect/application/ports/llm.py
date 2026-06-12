# src/aect/application/ports/llm.py
"""LLMPort -- testbarer Kontrakt fuer LLM-Provider (Mock, Azure OpenAI, ...)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

Role = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class LLMMessage:
    """Eine Nachricht im Messages-API-Format (System/User/Assistant getrennt).

    Kein String-Concat (aect-security-checklist v2.1, Phase C): System- und
    User-Anteile bleiben strukturell getrennt, damit kein Adapter sie
    versehentlich vermischt.
    """

    role: Role
    content: str


@dataclass(frozen=True)
class LLMResponse:
    """Antwort eines LLM-Providers."""

    content: str


class LLMPort(Protocol):
    """Kontrakt fuer LLM-Provider.

    Warum ein Port? Schaerfung, Loesungsvorschlag und Report (Phase C)
    duerfen nicht von einem konkreten Provider abhaengen. MockLLMAdapter
    liefert deterministische Antworten fuer Tests; ein spaeterer
    Azure-OpenAI-Adapter implementiert denselben Kontrakt mit echten Calls.
    """

    async def complete(self, messages: list[LLMMessage]) -> LLMResponse: ...
