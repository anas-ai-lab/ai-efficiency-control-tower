"""Tests fuer FastAPI-Dependency-Provider (dependencies.py)."""

from __future__ import annotations

from aect.adapters.api.dependencies import get_llm_adapter
from aect.adapters.api.settings import Settings
from aect.adapters.in_memory.llm import MockLLMAdapter
from aect.adapters.llm.azure_openai import AzureOpenAIAdapter
from aect.adapters.llm.resilient import ResilientLLMAdapter
from aect.application.ports.llm import LLMMessage


async def test_get_llm_adapter_returns_resilient_wrapped_mock_without_credentials() -> (
    None
):
    """Ohne Azure-Credentials: ResilientLLMAdapter(MockLLMAdapter()).

    Azure-Felder werden explizit auf "" gesetzt statt sich auf eine leere
    .env zu verlassen (Fund Tag 45: Settings() liest automatisch aus .env --
    sobald dort echte Azure-Credentials stehen, wuerde dieser Test sonst je
    nach Entwicklerumgebung undeterministisch durchfallen. Test-Isolation
    darf nicht vom Inhalt einer lokalen, nicht versionierten Datei abhaengen).
    complete() wird real durchgefuehrt: einziger Test der den Mock-Pfad
    ueber den echten DI-Pfad ausfuehrt.
    """
    settings = Settings(
        azure_openai_endpoint="",
        azure_openai_api_key="",
        azure_openai_deployment="",
    )
    adapter = get_llm_adapter(settings=settings)

    assert isinstance(adapter, ResilientLLMAdapter)
    assert isinstance(adapter._inner, MockLLMAdapter)

    response = await adapter.complete([LLMMessage(role="user", content="Hallo")])
    assert "[mock-response]" in response.content
    assert "Hallo" in response.content


async def test_get_llm_adapter_returns_resilient_wrapped_azure_with_credentials() -> (
    None
):
    """Mit Azure-Credentials: ResilientLLMAdapter(AzureOpenAIAdapter(...)).

    Gefakte Settings-Instanz -- kein echter Azure-Call, nur DI-Wiring.
    """
    settings = Settings(
        azure_openai_endpoint="https://fake.openai.azure.com",
        azure_openai_api_key="fake-key",
        azure_openai_deployment="gpt-4o-mini",
        azure_openai_api_version="2024-10-21",
    )
    adapter = get_llm_adapter(settings=settings)

    assert isinstance(adapter, ResilientLLMAdapter)
    assert isinstance(adapter._inner, AzureOpenAIAdapter)
