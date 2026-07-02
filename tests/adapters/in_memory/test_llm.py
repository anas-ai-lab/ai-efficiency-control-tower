"""Tests fuer MockLLMAdapter."""

from __future__ import annotations

import pytest

from aect.adapters.in_memory.llm import MockLLMAdapter
from aect.application.ports.llm import LLMMessage, ToolCall, ToolDefinition

_LOOKUP_TOOL = ToolDefinition(
    name="lookup_stack_options",
    description="Gibt verfuegbare Zielplattformen zurueck.",
    parameters={"type": "object", "properties": {}},
)


@pytest.fixture
def adapter() -> MockLLMAdapter:
    return MockLLMAdapter()


async def test_complete_echoes_last_user_message(adapter: MockLLMAdapter) -> None:
    messages = [
        LLMMessage(role="system", content="Du bist ein Assistent."),
        LLMMessage(role="user", content="Hallo Welt"),
    ]
    response = await adapter.complete(messages)
    assert response.content == "[mock-response] Hallo Welt"


async def test_complete_is_deterministic(adapter: MockLLMAdapter) -> None:
    messages = [LLMMessage(role="user", content="Test")]
    first = await adapter.complete(messages)
    second = await adapter.complete(messages)
    assert first == second


async def test_complete_with_no_user_message_returns_empty_echo(
    adapter: MockLLMAdapter,
) -> None:
    messages = [LLMMessage(role="system", content="Nur System")]
    response = await adapter.complete(messages)
    assert response.content == "[mock-response] "


async def test_complete_uses_last_user_message_when_multiple(
    adapter: MockLLMAdapter,
) -> None:
    messages = [
        LLMMessage(role="user", content="Erste Frage"),
        LLMMessage(role="assistant", content="Antwort"),
        LLMMessage(role="user", content="Zweite Frage"),
    ]
    response = await adapter.complete(messages)
    assert response.content == "[mock-response] Zweite Frage"


async def test_complete_with_tools_and_no_tool_response_returns_tool_call(
    adapter: MockLLMAdapter,
) -> None:
    messages = [LLMMessage(role="user", content="Welche Plattform passt?")]

    response = await adapter.complete(messages, tools=[_LOOKUP_TOOL])

    assert response.content == ""
    assert response.tool_calls is not None
    assert len(response.tool_calls) == 1
    call = response.tool_calls[0]
    assert call.name == "lookup_stack_options"
    assert call.arguments == {}


async def test_complete_with_tools_and_existing_tool_response_falls_back_to_echo(
    adapter: MockLLMAdapter,
) -> None:
    """Zweiter complete()-Call nach Tool-Ergebnis: Mock liefert wieder Text,
    nicht erneut einen Tool-Call -- analog dem erwarteten Provider-Verhalten
    (LLM synthetisiert die finale Antwort aus dem Tool-Ergebnis)."""
    messages = [
        LLMMessage(role="user", content="Welche Plattform passt?"),
        LLMMessage(
            role="assistant",
            content="",
            tool_calls=[
                ToolCall(
                    id="mock-tool-call-1",
                    name="lookup_stack_options",
                    arguments={},
                )
            ],
        ),
        LLMMessage(
            role="tool",
            content='{"self_hosted_chat_ui": {"name": "Self-hosted Chat-UI"}}',
            tool_call_id="mock-tool-call-1",
        ),
    ]

    response = await adapter.complete(messages, tools=[_LOOKUP_TOOL])

    assert response.tool_calls is None
    assert response.content == "[mock-response] Welche Plattform passt?"
