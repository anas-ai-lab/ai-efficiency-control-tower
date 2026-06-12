# tests/adapters/in_memory/test_llm.py
"""Tests fuer MockLLMAdapter."""

from __future__ import annotations

import pytest

from aect.adapters.in_memory.llm import MockLLMAdapter
from aect.application.ports.llm import LLMMessage


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
