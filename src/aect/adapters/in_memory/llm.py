"""MockLLMAdapter -- deterministischer LLM-Adapter fuer Tests."""

from __future__ import annotations

from aect.application.ports.llm import (
    LLMMessage,
    LLMResponse,
    ToolCall,
    ToolDefinition,
)

_MOCK_TOOL_CALL_ID = "mock-tool-call-1"


class MockLLMAdapter:
    """Implementiert LLMPort ohne echten LLM-Call.

    Deterministisch: liefert eine feste, aus dem letzten User-Content
    abgeleitete Antwort. Macht Tests reproduzierbar ohne Netzwerk/Kosten.
    Implementiert LLMPort via strukturellem Subtyping.

    Tool-Call-Simulation (Tag 37, Function-Calling): werden `tools`
    angeboten UND enthaelt die Historie noch keine Tool-Antwort
    (role="tool"), fordert der Mock genau einen Aufruf des ersten
    angebotenen Tools an (Argumente: leeres Dict). Enthaelt die Historie
    bereits eine Tool-Antwort -- oder werden keine `tools` angeboten --
    verhaelt sich der Mock wie zuvor (Echo des letzten User-Contents).

    Bekannte Einschraenkung (siehe ADR-0008): Diese Heuristik bildet nur den
    Standard-Zweischritt "ein Tool, ein Aufruf" nach. Mehrere Tools oder
    mehrere Aufrufe in einer Antwort simuliert der Mock nicht -- ein
    Azure-OpenAI-Adapter kann hier abweichen.
    """

    async def complete(
        self,
        messages: list[LLMMessage],
        tools: list[ToolDefinition] | None = None,
    ) -> LLMResponse:
        if tools and not any(m.role == "tool" for m in messages):
            return LLMResponse(
                content="",
                tool_calls=[
                    ToolCall(id=_MOCK_TOOL_CALL_ID, name=tools[0].name, arguments={})
                ],
            )

        last_user = next(
            (m.content for m in reversed(messages) if m.role == "user"),
            "",
        )
        return LLMResponse(content=f"[mock-response] {last_user}")
