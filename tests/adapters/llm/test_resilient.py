"""Tests fuer ResilientLLMAdapter -- Retry/Backoff/Timeout via tenacity."""

from __future__ import annotations

import asyncio

import pytest

from aect.adapters.llm.resilient import ResilientLLMAdapter
from aect.application.ports.llm import LLMMessage, LLMResponse, ToolDefinition

_FAST: dict[str, float] = {"min_wait_seconds": 0.0, "max_wait_seconds": 0.0}
_MESSAGES = [LLMMessage(role="user", content="Hallo")]


class _FlakyLLMAdapter:
    """Faellt `fail_times`-mal mit ConnectionError, dann liefert eine Antwort."""

    def __init__(self, fail_times: int) -> None:
        self._fail_times = fail_times
        self.call_count = 0

    async def complete(
        self, messages: list[LLMMessage], tools: list[ToolDefinition] | None = None
    ) -> LLMResponse:
        self.call_count += 1
        if self.call_count <= self._fail_times:
            raise ConnectionError("transient")
        return LLMResponse(content="ok")


class _AlwaysFailingLLMAdapter:
    """Wirft bei jedem Aufruf ConnectionError."""

    def __init__(self) -> None:
        self.call_count = 0

    async def complete(
        self, messages: list[LLMMessage], tools: list[ToolDefinition] | None = None
    ) -> LLMResponse:
        self.call_count += 1
        raise ConnectionError("permanent")


class _SlowLLMAdapter:
    """Schlaeft laenger als der konfigurierte Timeout."""

    def __init__(self, delay_seconds: float) -> None:
        self._delay_seconds = delay_seconds
        self.call_count = 0

    async def complete(
        self, messages: list[LLMMessage], tools: list[ToolDefinition] | None = None
    ) -> LLMResponse:
        self.call_count += 1
        await asyncio.sleep(self._delay_seconds)
        return LLMResponse(content="too late")


class _NonRetryableLLMAdapter:
    """Wirft einen Fehler, der nicht zur Retry-Policy gehoert."""

    def __init__(self) -> None:
        self.call_count = 0

    async def complete(
        self, messages: list[LLMMessage], tools: list[ToolDefinition] | None = None
    ) -> LLMResponse:
        self.call_count += 1
        raise ValueError("not retryable")


class _RecordingLLMAdapter:
    """Zeichnet die zuletzt empfangenen `tools` auf -- prueft Passthrough."""

    def __init__(self) -> None:
        self.received_tools: list[ToolDefinition] | None = None

    async def complete(
        self, messages: list[LLMMessage], tools: list[ToolDefinition] | None = None
    ) -> LLMResponse:
        self.received_tools = tools
        return LLMResponse(content="ok")


async def test_succeeds_on_first_attempt() -> None:
    inner = _FlakyLLMAdapter(fail_times=0)
    adapter = ResilientLLMAdapter(inner, max_attempts=3, **_FAST)

    response = await adapter.complete(_MESSAGES)

    assert response.content == "ok"
    assert inner.call_count == 1


async def test_retries_after_transient_failure_then_succeeds() -> None:
    inner = _FlakyLLMAdapter(fail_times=2)
    adapter = ResilientLLMAdapter(inner, max_attempts=3, **_FAST)

    response = await adapter.complete(_MESSAGES)

    assert response.content == "ok"
    assert inner.call_count == 3


async def test_raises_after_max_attempts_exhausted() -> None:
    inner = _AlwaysFailingLLMAdapter()
    adapter = ResilientLLMAdapter(inner, max_attempts=3, **_FAST)

    with pytest.raises(ConnectionError):
        await adapter.complete(_MESSAGES)

    assert inner.call_count == 3


async def test_timeout_is_retried_then_raises() -> None:
    inner = _SlowLLMAdapter(delay_seconds=1.0)
    adapter = ResilientLLMAdapter(inner, max_attempts=2, timeout_seconds=0.01, **_FAST)

    with pytest.raises(TimeoutError):
        await adapter.complete(_MESSAGES)

    assert inner.call_count == 2


async def test_non_retryable_exception_propagates_immediately() -> None:
    inner = _NonRetryableLLMAdapter()
    adapter = ResilientLLMAdapter(inner, max_attempts=3, **_FAST)

    with pytest.raises(ValueError):
        await adapter.complete(_MESSAGES)

    assert inner.call_count == 1


async def test_tools_parameter_is_passed_through_to_inner() -> None:
    inner = _RecordingLLMAdapter()
    adapter = ResilientLLMAdapter(inner, max_attempts=3, **_FAST)
    tool = ToolDefinition(name="lookup_stack_options", description="...", parameters={})

    await adapter.complete(_MESSAGES, tools=[tool])

    assert inner.received_tools == [tool]
