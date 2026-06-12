"""Tests fuer FastAPI-Dependency-Provider (dependencies.py)."""

from __future__ import annotations

from aect.adapters.api.dependencies import get_llm_adapter
from aect.adapters.llm.resilient import ResilientLLMAdapter
from aect.application.ports.llm import LLMMessage


async def test_get_llm_adapter_returns_resilient_wrapped_adapter() -> None:
    """get_llm_adapter() liefert ResilientLLMAdapter (Retry/Timeout-Wrapper,
    Tag 34) um den Mock-Adapter -- DI-Wiring Tag 35.

    complete() wird hier bewusst real durchgerufen (nicht nur isinstance-
    Check): das ist der einzige Test, der den Resilience-Wrapper ueber den
    tatsaechlichen DI-Pfad ausfuehrt (Phase-C-Pflicht "Circuit Breaker"
    ist sonst nur in test_resilient.py isoliert getestet, nie verdrahtet).
    """
    adapter = get_llm_adapter()

    assert isinstance(adapter, ResilientLLMAdapter)

    response = await adapter.complete([LLMMessage(role="user", content="Hallo")])

    assert "[mock-response]" in response.content
    assert "Hallo" in response.content
