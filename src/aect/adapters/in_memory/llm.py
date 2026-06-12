# src/aect/adapters/in_memory/llm.py
"""MockLLMAdapter -- deterministischer LLM-Adapter fuer Tests."""

from __future__ import annotations

from aect.application.ports.llm import LLMMessage, LLMResponse


class MockLLMAdapter:
    """Implementiert LLMPort ohne echten LLM-Call.

    Deterministisch: liefert eine feste, aus dem letzten User-Content
    abgeleitete Antwort. Macht Tests reproduzierbar ohne Netzwerk/Kosten.
    Implementiert LLMPort via strukturellem Subtyping.
    """

    async def complete(self, messages: list[LLMMessage]) -> LLMResponse:
        last_user = next(
            (m.content for m in reversed(messages) if m.role == "user"),
            "",
        )
        return LLMResponse(content=f"[mock-response] {last_user}")
