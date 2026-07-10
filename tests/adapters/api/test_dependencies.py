"""Tests fuer FastAPI-Dependency-Provider (dependencies.py)."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException
from structlog.testing import capture_logs

from aect.adapters.api.dependencies import (
    get_llm_adapter,
    get_retriever_port,
    key_fingerprint,
    require_api_key,
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
        # Region explizit "" (Fund Tag 45, wie die Mock-Schwestertests oben):
        # schirmt gegen ein aus der lokalen .env geleaktes
        # AECT_AZURE_OPENAI_REGION ab -- ein dort gesetztes Nicht-EU-Region-Wort
        # wuerde den swedencentral-Hostnamen sonst ueberschreiben und diesen
        # Test je nach Entwicklerumgebung kippen (Test-Isolation darf nicht vom
        # Inhalt einer lokalen, nicht versionierten Datei abhaengen).
        azure_openai_region="",
    )
    adapter = get_llm_adapter(settings=settings)

    assert isinstance(adapter, ResilientLLMAdapter)
    assert isinstance(adapter._inner, AzureOpenAIAdapter)


async def test_resolve_retriever_empty_host_raises() -> None:
    """Fail loud (V4-P2): ein leerer AECT_CHROMA_HOST ist eine Fehlkonfiguration
    -- resolve_retriever wirft ValueError statt still auf MockRetriever zu fallen.
    MockRetriever gibt es nur noch ueber einen expliziten Test-Override.

    chroma_host explizit "" (analog Azure-Fund Tag 45): Test-Isolation darf nicht
    vom Inhalt einer lokalen .env abhaengen (Default ist seit V4-P2 127.0.0.1).
    """
    with pytest.raises(ValueError, match="AECT_CHROMA_HOST"):
        resolve_retriever(Settings(chroma_host=""))


async def test_resolve_retriever_unreachable_host_raises_connectionerror() -> None:
    """Fail loud (V4-P2): ist der konfigurierte Chroma-Host nicht erreichbar,
    wirft resolve_retriever eine ConnectionError (kein stiller Mock-Fallback) und
    loggt "chroma_unreachable" mit Host/Port. Port 1 ist garantiert geschlossen --
    der chromadb-HttpClient-Preflight schlaegt sofort fehl, noch bevor torch bzw.
    Modelle geladen werden (Erreichbarkeits-Check zuerst in _build_real_retriever).
    """
    import aect.adapters.api.dependencies as deps_module

    # lru_cache leeren: ein evtl. gecachtes (127.0.0.1, 1) aus einem frueheren
    # Lauf koennte den erneuten Erreichbarkeits-Check ueberspringen (Exceptions
    # cacht lru_cache zwar nicht, ein Erfolg mit gleicher Signatur aber schon).
    deps_module._get_chroma_collection.cache_clear()

    with (
        capture_logs() as logs,
        pytest.raises(ConnectionError, match="nicht erreichbar"),
    ):
        resolve_retriever(Settings(chroma_host="127.0.0.1", chroma_port=1))

    events = [log for log in logs if log["event"] == "chroma_unreachable"]
    assert len(events) == 1
    assert events[0]["host"] == "127.0.0.1"
    assert events[0]["port"] == 1


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


async def test_get_retriever_port_falls_back_to_resolve_without_preload() -> None:
    """Kein app.state.retriever (Lifespan lief nicht) -> Fallback auf
    resolve_retriever(), das seit V4-P2 fail-loud ist: ein leerer chroma_host
    wirft ValueError statt MockRetriever zurueckzugeben."""
    with pytest.raises(ValueError, match="AECT_CHROMA_HOST"):
        get_retriever_port(
            request=_fake_request(retriever=None),
            settings=Settings(chroma_host=""),
        )


async def test_lifespan_skips_warmup_when_chroma_host_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Leerer chroma_host -> Lifespan-Startup laedt keine Heavy-Resources,
    app.state.retriever bleibt ungesetzt. get_retriever_port faellt dann auf
    resolve_retriever, das mit leerem Host fail-loud wirft (V4-P2) -- der
    Container-Betrieb setzt AECT_CHROMA_HOST (Default 127.0.0.1)."""
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


def test_check_azure_eu_region_explicit_region_overrides_hostname() -> None:
    """AUDIT-008-Fix: explizite Region validiert, auch wenn der Hostname
    (Custom-Subdomain-Format https://<resource>.openai.azure.com) die Region
    gar nicht enthaelt -- der Fall, der den Guard bisher blockierte."""
    assert (
        check_azure_eu_region(
            "https://aect-openai-dev.openai.azure.com", "swedencentral"
        )
        == "ok"
    )


def test_check_azure_eu_region_explicit_region_rejects_non_eu() -> None:
    """Explizite nicht-EU-Region schlaegt fehl, selbst wenn der Hostname
    zufaellig eine EU-Region enthaelt -- explicit_region ignoriert den
    Hostnamen vollstaendig, statt ihn als zusaetzlichen Fallback zu pruefen."""
    with pytest.raises(ValueError, match="Configured AECT_AZURE_OPENAI_REGION"):
        check_azure_eu_region("https://aect.swedencentral.openai.azure.com", "eastus")


def test_check_azure_eu_region_hostname_fallback_logs_warning() -> None:
    """Regressionsschutz: ohne explicit_region bleibt die bisherige
    Hostname-Heuristik aktiv (gleiches Ergebnis wie vor dem AUDIT-008-Fix),
    aber jetzt mit einem Warn-Log, das die geratene Region sichtbar macht."""
    with capture_logs() as logs:
        result = check_azure_eu_region("https://aect.westeurope.openai.azure.com")
    assert result == "ok"
    warn_logs = [
        log for log in logs if log["event"] == "azure_eu_region_guessed_from_hostname"
    ]
    assert len(warn_logs) == 1
    assert warn_logs[0]["log_level"] == "warning"


def test_check_azure_eu_region_no_explicit_region_no_hostname_match_still_fails() -> (
    None
):
    """Fail-safe-Default bleibt bestehen: ohne explicit_region UND ohne
    Hostname-Match weiterhin ein harter Fehler, keine Aufweichung."""
    with pytest.raises(ValueError, match="EU Data Zone"):
        check_azure_eu_region("https://aect.eastus.openai.azure.com")


def test_get_llm_adapter_rejects_non_eu_endpoint() -> None:
    """Fail-Fast (AUDIT-008): nicht-EU-Endpoint -> ValueError beim Adapter-Init.

    azure_openai_region explizit "" (Fund Tag 45, wie die Mock-Schwestertests
    oben): sonst zieht Settings() ein gesetztes AECT_AZURE_OPENAI_REGION aus der
    lokalen .env, das die eastus-Hostname-Heuristik vollstaendig umginge und den
    erwarteten ValueError unterdrueckte -- der Test war lokal rot, CI gruen
    (dort ist die Env-Var nicht gesetzt).
    """
    settings = Settings(
        azure_openai_endpoint="https://aect.eastus.openai.azure.com",
        azure_openai_api_key="fake-key",
        azure_openai_deployment="gpt-4o-mini",
        azure_openai_region="",
    )
    with pytest.raises(ValueError, match="EU Data Zone"):
        get_llm_adapter(settings=settings)


def test_get_llm_adapter_accepts_custom_subdomain_with_explicit_region() -> None:
    """AUDIT-008-Fix: ein Custom-Subdomain-Endpoint (Region nicht im
    Hostnamen, das reale Azure-AI-Foundry-Format) wird hier nicht mehr
    per-Request abgelehnt, wenn azure_openai_region explizit gesetzt ist --
    sonst wuerde jede Triage-Anfrage scheitern, obwohl der Lifespan-Check
    beim App-Start bereits erfolgreich war."""
    settings = Settings(
        azure_openai_endpoint="https://aect-openai-dev.openai.azure.com",
        azure_openai_api_key="fake-key",
        azure_openai_deployment="gpt-4o-mini",
        azure_openai_region="swedencentral",
    )
    adapter = get_llm_adapter(settings=settings)
    assert isinstance(adapter, ResilientLLMAdapter)


# ---------------------------------------------------------------------------
# Key-Rotation (Phase G): require_api_key gegen zwei Keys, kid-Logging
# ---------------------------------------------------------------------------


async def test_require_api_key_accepts_primary_key() -> None:
    settings = Settings(api_key="primary-key")
    result = await require_api_key(api_key="primary-key", settings=settings)
    assert result == "primary-key"


async def test_require_api_key_accepts_next_key_during_rotation() -> None:
    settings = Settings(api_key="primary-key", api_key_next="next-key")
    result = await require_api_key(api_key="next-key", settings=settings)
    assert result == "next-key"


async def test_require_api_key_rejects_unknown_key_with_rotation_active() -> None:
    settings = Settings(api_key="primary-key", api_key_next="next-key")
    with pytest.raises(HTTPException) as exc_info:
        await require_api_key(api_key="something-else", settings=settings)
    assert exc_info.value.status_code == 401


async def test_require_api_key_rejects_next_key_when_rotation_not_active() -> None:
    """api_key_next leer (kein Rotation-Modus) -- _matches("") ist nie True,
    sonst wuerde ein leerer AECT_API_KEY_NEXT versehentlich jeden Key akzeptieren."""
    settings = Settings(api_key="primary-key", api_key_next="")
    with pytest.raises(HTTPException) as exc_info:
        await require_api_key(api_key="", settings=settings)
    assert exc_info.value.status_code == 401


async def test_require_api_key_still_returns_503_when_unconfigured() -> None:
    """Bestehendes 503-Verhalten (b44b016) bleibt durch die Rotation unveraendert."""
    settings = Settings(api_key="", api_key_next="next-key")
    with pytest.raises(HTTPException) as exc_info:
        await require_api_key(api_key="next-key", settings=settings)
    assert exc_info.value.status_code == 503


async def test_require_api_key_logs_kid_of_primary_key_used() -> None:
    """require_api_key holt sich structlog.get_logger() frisch pro Aufruf
    (kein Modul-globaler Logger) -- capture_logs() faengt sie zuverlaessig
    ab, unabhaengig davon, wie viele andere Tests vorher geloggt haben."""
    settings = Settings(api_key="primary-key")
    with capture_logs() as logs:
        await require_api_key(api_key="primary-key", settings=settings)
    auth_logs = [log for log in logs if log["event"] == "api_key_authenticated"]
    assert len(auth_logs) == 1
    assert auth_logs[0]["kid"] == key_fingerprint("primary-key")


async def test_require_api_key_logs_kid_of_next_key_used() -> None:
    settings = Settings(api_key="primary-key", api_key_next="next-key")
    with capture_logs() as logs:
        await require_api_key(api_key="next-key", settings=settings)
    auth_logs = [log for log in logs if log["event"] == "api_key_authenticated"]
    assert len(auth_logs) == 1
    assert auth_logs[0]["kid"] == key_fingerprint("next-key")
    assert auth_logs[0]["kid"] != key_fingerprint("primary-key")


def test_key_fingerprint_is_deterministic() -> None:
    assert key_fingerprint("abc") == key_fingerprint("abc")


def test_key_fingerprint_differs_for_different_secrets() -> None:
    assert key_fingerprint("key-a") != key_fingerprint("key-b")


def test_key_fingerprint_default_length_is_8_hex_chars() -> None:
    fingerprint = key_fingerprint("some-secret")
    assert len(fingerprint) == 8
    int(fingerprint, 16)  # wirft ValueError, wenn kein gueltiger Hex-String


def test_key_fingerprint_never_contains_raw_secret() -> None:
    secret = "super-secret-value-123"
    assert secret not in key_fingerprint(secret)


def test_key_fingerprint_full_length_when_length_zero() -> None:
    fingerprint = key_fingerprint("some-secret", length=0)
    assert len(fingerprint) == 64
