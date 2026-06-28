"""Tests fuer FastAPI-Dependency-Provider (dependencies.py)."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from aect.adapters.api.dependencies import (
    get_llm_adapter,
    get_retriever_port,
    resolve_retriever,
)
from aect.adapters.api.settings import Settings, check_azure_eu_region
from aect.adapters.in_memory.llm import MockLLMAdapter
from aect.adapters.in_memory.retriever import MockRetriever
from aect.adapters.llm.azure_openai import AzureOpenAIAdapter
from aect.adapters.llm.resilient import ResilientLLMAdapter
from aect.adapters.rag.bm25_retriever import BM25Index
from aect.adapters.rag.hybrid_retriever import HybridRetriever
from aect.adapters.rag.reranker import CrossEncoderReranker
from aect.adapters.rag.retriever import ChromaRetriever
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
        # EU-Data-Zone-Endpoint (AUDIT-008) -- sonst wuerde get_llm_adapter
        # mit ValueError abbrechen statt den Azure-Adapter zu bauen.
        azure_openai_endpoint="https://fake.swedencentral.openai.azure.com",
        azure_openai_api_key="fake-key",
        azure_openai_deployment="gpt-4o-mini",
        azure_openai_api_version="2024-10-21",
    )
    adapter = get_llm_adapter(settings=settings)

    assert isinstance(adapter, ResilientLLMAdapter)
    assert isinstance(adapter._inner, AzureOpenAIAdapter)


async def test_get_retriever_port_returns_mock_without_chroma_host() -> None:
    """Ohne AECT_CHROMA_HOST: MockRetriever (Default, kein Netzwerk/Torch).

    chroma_host wird explizit auf "" gesetzt, analog zum Azure-Fund Tag 45 --
    Test-Isolation darf nicht vom Inhalt einer lokalen .env abhaengen.
    """
    settings = Settings(chroma_host="")
    retriever = resolve_retriever(settings)
    assert isinstance(retriever, MockRetriever)


async def test_get_retriever_port_wires_cross_encoder_reranker_with_host_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Mit AECT_CHROMA_HOST gesetzt:
    CrossEncoderReranker(HybridRetriever(ChromaRetriever, BM25Retriever), model).

    _get_chroma_collection/_get_local_embedding_model/_get_bm25_index/
    _get_cross_encoder_model werden gefakt -- der Test prueft die
    Verdrahtungs-Entscheidung, nicht echte Netzwerk-/Modell-/Datei-
    Operationen (die deckt der Live-Test ab).
    """
    import aect.adapters.api.dependencies as deps_module

    fake_collection = object()
    fake_model = object()
    fake_bm25_index = BM25Index([])
    fake_cross_encoder = object()
    monkeypatch.setattr(
        deps_module, "_get_chroma_collection", lambda host, port: fake_collection
    )
    monkeypatch.setattr(deps_module, "_get_local_embedding_model", lambda: fake_model)
    monkeypatch.setattr(deps_module, "_get_bm25_index", lambda kb_dir: fake_bm25_index)
    monkeypatch.setattr(
        deps_module, "_get_cross_encoder_model", lambda: fake_cross_encoder
    )

    settings = Settings(chroma_host="127.0.0.1", chroma_port=8001)
    retriever = resolve_retriever(settings)

    assert isinstance(retriever, CrossEncoderReranker)
    assert retriever._model is fake_cross_encoder

    hybrid = retriever._inner
    assert isinstance(hybrid, HybridRetriever)
    assert isinstance(hybrid._vector, ChromaRetriever)
    assert hybrid._vector._collection is fake_collection
    assert hybrid._vector._embedder._model is fake_model
    assert hybrid._bm25._index is fake_bm25_index


# ---------------------------------------------------------------------------
# Lifespan-Preload (AUDIT-013): get_retriever_port bevorzugt app.state.retriever
# ---------------------------------------------------------------------------


def _fake_request(retriever: object | None = None) -> Any:
    """Minimaler Request-Stub mit .app.state -- get_retriever_port liest nur das."""
    state = SimpleNamespace()
    if retriever is not None:
        state.retriever = retriever
    return SimpleNamespace(app=SimpleNamespace(state=state))


async def test_get_retriever_port_prefers_preloaded_app_state() -> None:
    """Vorgeladener Retriever (Lifespan-Startup) wird ohne Neubau verwendet --
    selbst mit gesetztem chroma_host (sonst wuerde ein echter Build versucht)."""
    sentinel = MockRetriever()
    result = get_retriever_port(
        request=_fake_request(retriever=sentinel),
        settings=Settings(chroma_host="127.0.0.1"),
    )
    assert result is sentinel


async def test_get_retriever_port_falls_back_without_preload() -> None:
    """Kein app.state.retriever (Lifespan lief nicht / Mock-Modus) -> Fallback
    auf resolve_retriever(): ohne chroma_host der MockRetriever."""
    result = get_retriever_port(
        request=_fake_request(retriever=None),
        settings=Settings(chroma_host=""),
    )
    assert isinstance(result, MockRetriever)


async def test_lifespan_mock_mode_skips_heavy_resources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Lifespan im Mock-Modus (kein chroma_host) laedt keine Heavy-Resources --
    app.state.retriever bleibt ungesetzt (kein Container/Torch im Testlauf)."""
    import aect.adapters.api.app as app_module

    monkeypatch.setattr(app_module, "get_settings", lambda: Settings(chroma_host=""))
    fake_app = SimpleNamespace(state=SimpleNamespace())
    async with app_module.lifespan(fake_app):  # type: ignore[arg-type]
        pass
    assert not hasattr(fake_app.state, "retriever")


# ---------------------------------------------------------------------------
# EU-Datenresidenz-Check (AUDIT-008): check_azure_eu_region
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://aect.swedencentral.openai.azure.com",
        "https://aect.westeurope.openai.azure.com",
    ],
)
def test_check_azure_eu_region_accepts_eu_endpoints(endpoint: str) -> None:
    assert check_azure_eu_region(endpoint) == "ok"


def test_check_azure_eu_region_rejects_non_eu_endpoint() -> None:
    with pytest.raises(ValueError, match="EU Data Zone"):
        check_azure_eu_region("https://aect.eastus.openai.azure.com")


@pytest.mark.parametrize(
    "endpoint",
    ["", "mock", "http://localhost:8000", "https://mock.openai.azure.com"],
)
def test_check_azure_eu_region_skips_mock_endpoints(endpoint: str) -> None:
    assert check_azure_eu_region(endpoint) == "skipped_mock"


def test_get_llm_adapter_rejects_non_eu_endpoint() -> None:
    """Fail-Fast (AUDIT-008): nicht-EU-Endpoint -> ValueError beim Adapter-Init."""
    settings = Settings(
        azure_openai_endpoint="https://aect.eastus.openai.azure.com",
        azure_openai_api_key="fake-key",
        azure_openai_deployment="gpt-4o-mini",
    )
    with pytest.raises(ValueError, match="EU Data Zone"):
        get_llm_adapter(settings=settings)
