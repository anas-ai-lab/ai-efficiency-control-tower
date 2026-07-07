"""Tests fuer ResilientLLMAdapter -- Retry/Backoff/Timeout via tenacity."""

from __future__ import annotations

import asyncio

import pytest

from aect.adapters.llm.resilient import ResilientLLMAdapter
from aect.application.ports.llm import LLMMessage, LLMResponse, ToolDefinition
from aect.application.structured_output import (
    ArchitectureSketch,
    IdeationResult,
    InvalidLLMOutputError,
)

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


# ---------------------------------------------------------------------------
# F-014: Gesamtdeadline ueber alle Retries
# ---------------------------------------------------------------------------


async def test_overall_deadline_caps_retry_storm() -> None:
    """Die Gesamtdeadline begrenzt Retries+Backoff, nicht nur den Einzelversuch.

    Ohne overall_timeout_seconds wuerde diese Konfiguration (100 Versuche
    a 50 ms) mehrere Sekunden laufen -- die Deadline von 0.2 s bricht frueher
    ab und wirft TimeoutError.
    """
    inner = _SlowLLMAdapter(delay_seconds=10.0)
    adapter = ResilientLLMAdapter(
        inner,
        max_attempts=100,
        timeout_seconds=0.05,
        min_wait_seconds=0.0,
        max_wait_seconds=0.0,
        overall_timeout_seconds=0.2,
    )
    started = asyncio.get_running_loop().time()
    with pytest.raises(TimeoutError):
        await adapter.complete(_MESSAGES)
    elapsed = asyncio.get_running_loop().time() - started
    assert elapsed < 2.0  # deutlich unter den ~5 s der 100 Einzelversuche
    assert inner.call_count < 100


async def test_overall_deadline_does_not_interfere_with_fast_success() -> None:
    inner = _FlakyLLMAdapter(fail_times=1)
    adapter = ResilientLLMAdapter(
        inner, max_attempts=3, overall_timeout_seconds=5.0, **_FAST
    )
    response = await adapter.complete(_MESSAGES)
    assert response.content == "ok"
    assert inner.call_count == 2


# ---------------------------------------------------------------------------
# H-042: generate_ideation / generate_architecture_sketch teilen denselben
# Retry-/Timeout-Kern (_run_resilient) -- hier explizit gepinnt.
# ---------------------------------------------------------------------------


class _SlowIdeationAdapter:
    def __init__(self, delay_seconds: float) -> None:
        self._delay_seconds = delay_seconds
        self.call_count = 0

    async def generate_ideation(self, problem_description: str) -> IdeationResult:
        self.call_count += 1
        await asyncio.sleep(self._delay_seconds)
        raise AssertionError("unreached: wird vom Timeout abgebrochen")


class _NonRetryableIdeationAdapter:
    def __init__(self) -> None:
        self.call_count = 0

    async def generate_ideation(self, problem_description: str) -> IdeationResult:
        self.call_count += 1
        raise InvalidLLMOutputError("schema kaputt")


class _SlowSketchAdapter:
    def __init__(self, delay_seconds: float) -> None:
        self._delay_seconds = delay_seconds
        self.call_count = 0

    async def generate_architecture_sketch(
        self, case_id: str, title: str, description: str, proposal_text: str
    ) -> ArchitectureSketch:
        self.call_count += 1
        await asyncio.sleep(self._delay_seconds)
        raise AssertionError("unreached: wird vom Timeout abgebrochen")


class _NonRetryableSketchAdapter:
    def __init__(self) -> None:
        self.call_count = 0

    async def generate_architecture_sketch(
        self, case_id: str, title: str, description: str, proposal_text: str
    ) -> ArchitectureSketch:
        self.call_count += 1
        raise InvalidLLMOutputError("schema kaputt")


async def test_ideation_timeout_is_retried_then_raises() -> None:
    inner = _SlowIdeationAdapter(delay_seconds=1.0)
    adapter = ResilientLLMAdapter(inner, max_attempts=2, timeout_seconds=0.01, **_FAST)

    with pytest.raises(TimeoutError):
        await adapter.generate_ideation("Problem")

    assert inner.call_count == 2


async def test_ideation_non_retryable_propagates_immediately() -> None:
    inner = _NonRetryableIdeationAdapter()
    adapter = ResilientLLMAdapter(inner, max_attempts=3, **_FAST)

    with pytest.raises(InvalidLLMOutputError):
        await adapter.generate_ideation("Problem")

    assert inner.call_count == 1


async def test_sketch_timeout_is_retried_then_raises() -> None:
    inner = _SlowSketchAdapter(delay_seconds=1.0)
    adapter = ResilientLLMAdapter(inner, max_attempts=2, timeout_seconds=0.01, **_FAST)

    with pytest.raises(TimeoutError):
        await adapter.generate_architecture_sketch("id-1", "T", "D", "P")

    assert inner.call_count == 2


async def test_sketch_non_retryable_propagates_immediately() -> None:
    inner = _NonRetryableSketchAdapter()
    adapter = ResilientLLMAdapter(inner, max_attempts=3, **_FAST)

    with pytest.raises(InvalidLLMOutputError):
        await adapter.generate_architecture_sketch("id-1", "T", "D", "P")

    assert inner.call_count == 1
