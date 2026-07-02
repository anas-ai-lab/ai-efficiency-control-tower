"""FastAPI Dependency-Provider fuer AECT.

Verdrahtet Application-Service mit seinen Infrastruktur-Abhaengigkeiten.
Kein Routing, keine Business-Logik -- nur Komposition.

Architektur: adapters/api/ darf aus adapters/in_memory/ importieren (beide
sind Infrastruktur-Schicht). Verboten waere ein Import aus domain/ oder
application/ IN Richtung adapters/ -- das laeuft in die andere Richtung.

Security (aect-security-checklist v2.1, Phase B):
  get_settings() ohne lru_cache: Tests ueberschreiben per dependency_overrides
  statt Cache leeren zu muessen.
  require_api_key(): prueft X-API-Key-Header, wirft 401 bei fehlendem/
  falschem Key, 500 wenn Server-seitig kein Key konfiguriert.
  APIKeyHeader auto_error=False: fehlender Header gibt None statt 403 --
  wir liefern einheitlich 401 (kein Info-Leak ueber Mechanismus).
  Schluessel-Vergleich via secrets.compare_digest (konstante Laufzeit) --
  kein timing-basiertes Byte-fuer-Byte-Erraten des Keys (G-S5-Hardening).
InMemoryRepository: prozessgebunden, kein State nach Neustart.
Phase B: SQLiteRepository ersetzt dies.

Idempotency (aect-security-checklist v2.1, Phase B):
  get_idempotency_store() folgt demselben Muster wie get_triage_service():
  AECT_DB_PATH gesetzt -> SQLiteIdempotencyStore (persistent), sonst
  InMemoryIdempotencyStore (Singleton, prozessgebunden).
"""

from __future__ import annotations

import secrets
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import Depends, HTTPException, Request
from fastapi.security import APIKeyHeader
from openai import AsyncAzureOpenAI

from aect.adapters.api.settings import Settings, check_azure_eu_region
from aect.adapters.in_memory.clock import SystemClock
from aect.adapters.in_memory.id_generator import UUIDGenerator
from aect.adapters.in_memory.idempotency_store import InMemoryIdempotencyStore
from aect.adapters.in_memory.llm import MockLLMAdapter
from aect.adapters.in_memory.repository import InMemoryRepository
from aect.adapters.in_memory.retriever import MockRetriever
from aect.adapters.llm.azure_openai import AzureOpenAIAdapter
from aect.adapters.llm.resilient import ResilientLLMAdapter
from aect.adapters.sqlite.idempotency_store import SQLiteIdempotencyStore
from aect.adapters.sqlite.repository import SQLiteRepository
from aect.application.ports.embedder import EmbedderPort
from aect.application.ports.idempotency_store import IdempotencyStorePort
from aect.application.ports.llm import LLMPort
from aect.application.ports.repository import RepositoryPort
from aect.application.ports.retriever import RetrieverPort
from aect.application.service import TriageService
from aect.domain.roi import ROIConfig, load_roi_config

# Singleton -- Repository-State lebt fuer die Prozess-Lebensdauer.
_repository: InMemoryRepository = InMemoryRepository()

# Singleton -- Idempotency-Key-State lebt fuer die Prozess-Lebensdauer
# (analog _repository; nur relevant ohne AECT_DB_PATH).
_idempotency_store: InMemoryIdempotencyStore = InMemoryIdempotencyStore()

# auto_error=False: fehlender Header liefert None statt automatischem 403.
# Unser require_api_key gibt dann einheitlich 401 zurueck.
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Standard-Reranking-Modell aus dem sentence-transformers-Oekosystem
# (trainiert auf MS MARCO Passage Ranking, ADR-0028). Generischer,
# oeffentlicher Modellname -- kein firmenspezifischer Wert, daher als
# Code-Konstante gefuehrt statt als Settings-Feld (anders als kb_dir/
# chroma_host, die Infrastruktur-Adressen sind, kein Modell-Identifier).
_CROSS_ENCODER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"


@lru_cache
def get_roi_config() -> ROIConfig:
    """Laedt ROIConfig einmalig aus config/roi_config.toml.

    lru_cache: Config-Datei wird beim ersten Aufruf gelesen und gecacht.
    """
    return load_roi_config()


def get_settings() -> Settings:
    """Liefert Settings-Instanz.

    Kein lru_cache: Tests koennen per app.dependency_overrides[get_settings]
    eine andere Settings-Instanz injizieren ohne Cache leeren zu muessen.
    """
    return Settings()


@lru_cache
def _get_chroma_collection(host: str, port: int) -> Any:
    """Baut (und cached) Chroma-HttpClient + Collection fuer die echte RAG-Wissensbasis.

    Lokaler Import (kein Modulkopf-Import): haelt src/ chromadb-frei fuer den
    Mock-Pfad (ADR-0016/0025) -- analog den Live-Tests
    (tests/adapters/rag/test_retriever_live.py), die denselben Import bewusst
    in die Testfunktion statt in den Modulkopf legen.

    lru_cache auf (host, port): Client + Collection-Handle werden einmal pro
    Prozess gebaut, nicht pro Request -- der Netzwerk-Handshake ist kein
    Pro-Request-Preis (anders als der guenstige AsyncAzureOpenAI-Client in
    get_llm_adapter(), der bewusst ungecached bleibt).

    name="aect-knowledge-base": feste, generische Collection -- kein
    firmenspezifischer Name (vertraglich bedingte IP-Trennung). Wird befuellt ueber
    scripts/seed_knowledge_base.py (ADR-0025), nicht hier.
    """
    import chromadb

    client = chromadb.HttpClient(host=host, port=port)
    return client.get_or_create_collection(name="aect-knowledge-base")


@lru_cache
def _get_local_embedding_model() -> Any:
    """Laedt (und cached) das lokale sentence-transformers-Modell.

    Lokaler Import, analog _get_chroma_collection -- haelt src/ torch-frei
    fuer den Mock-Pfad. lru_cache ohne Argumente: Modellgewichte werden genau
    einmal pro Prozess geladen (Sekunden-Kosten), nicht pro Request.

    all-MiniLM-L6-v2: identisch zum Index-seitigen Modell (ADR-0016) -- Index
    und Query MUESSEN denselben Embedder benutzen (ADR-0019), sonst ist die
    Vektor-Aehnlichkeit nicht vergleichbar.
    """
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("all-MiniLM-L6-v2")


@lru_cache
def _get_bm25_index(kb_dir: str) -> Any:
    """Baut (und cached) den BM25-Index aus der Wissensbasis fuer den Hybrid-Pfad.

    Lokaler Import, analog _get_chroma_collection/_get_local_embedding_model
    (Konsistenz mit dem etablierten Muster, auch wenn BM25 selbst keine
    schweren Dependencies zieht). lru_cache auf kb_dir: der Index wird
    einmal pro Prozess aus den *.md-Dateien gebaut, nicht pro Request --
    aendert sich die Wissensbasis, braucht es einen Prozess-Neustart
    (gleiche Limitation wie bei der Chroma-Collection und dem lokalen
    Embedding-Modell).
    """
    from aect.adapters.rag.bm25_retriever import build_bm25_index
    from aect.adapters.rag.indexing import build_index_records

    records = build_index_records(Path(kb_dir))
    return build_bm25_index(records)


@lru_cache
def _get_cross_encoder_model() -> Any:
    """Laedt (und cached) das lokale Cross-Encoder-Modell fuer Reranking.

    Lokaler Import, analog _get_local_embedding_model -- haelt src/
    torch-frei fuer den Mock-Pfad. lru_cache ohne Argumente: Modellgewichte
    werden genau einmal pro Prozess geladen, nicht pro Request.

    cross-encoder/ms-marco-MiniLM-L-6-v2: Standard-Reranking-Modell aus dem
    sentence-transformers-Oekosystem (trainiert auf MS MARCO Passage
    Ranking) -- bereits als Dependency vorhanden (sentence-transformers,
    pyproject.toml), kein neues Paket noetig (ADR-0028).
    """
    from sentence_transformers import CrossEncoder

    return CrossEncoder(_CROSS_ENCODER_MODEL_NAME)


def _build_real_retriever(settings: Settings) -> RetrieverPort:
    """Baut den echten Hybrid+Reranker-Retriever (ADR-0024/0025/0027/0028).

    CrossEncoderReranker(HybridRetriever(ChromaRetriever, BM25Retriever), model):
    Hybrid-Retrieval (Vektor + BM25, RRF, ADR-0027) liefert eine breite
    Kandidatenmenge, der Cross-Encoder sortiert sie praeziser nach (ADR-0028).

    Die schwergewichtigen Ressourcen (Chroma-Collection, Embedding-Modell,
    BM25-Index, Cross-Encoder) entstehen ueber die lru_cache-Builder -- einmal
    pro Prozess. Aufgerufen vom Lifespan-Startup (Warmup, AUDIT-013) und als
    Fallback in resolve_retriever().

    Container-Hinweis: ist AECT_CHROMA_HOST gesetzt, der Container aber nicht
    gestartet, schlaegt der erste echte Chroma-Call mit einem Verbindungsfehler
    fehl -- kein stiller Fallback.

    Lokale Imports (statt Modulkopf): konsistent mit dem bestehenden Muster.
    """
    from aect.adapters.rag.bm25_retriever import BM25Retriever
    from aect.adapters.rag.embedder import SentenceTransformerEmbedder
    from aect.adapters.rag.hybrid_retriever import HybridRetriever
    from aect.adapters.rag.reranker import CrossEncoderReranker
    from aect.adapters.rag.retriever import ChromaRetriever

    collection = _get_chroma_collection(settings.chroma_host, settings.chroma_port)
    embedder = SentenceTransformerEmbedder(_get_local_embedding_model())
    vector_retriever = ChromaRetriever(collection, embedder)

    bm25_index = _get_bm25_index(settings.kb_dir)
    bm25_retriever = BM25Retriever(bm25_index)

    hybrid = HybridRetriever(vector_retriever, bm25_retriever)

    cross_encoder_model = _get_cross_encoder_model()
    return CrossEncoderReranker(hybrid, cross_encoder_model)


def resolve_retriever(settings: Settings) -> RetrieverPort:
    """Waehlt Mock- oder echten Retriever anhand settings.chroma_host.

    AECT_CHROMA_HOST leer (Default) -> MockRetriever -- kein Container, kein
    Modell-Laden, kein BM25-Bau, kein Cross-Encoder in normalen Testlaeufen.
    Gesetzt -> _build_real_retriever(). Kein app.state -- reine Settings-Logik,
    direkt testbar und vom Lifespan-Startup wiederverwendet (AUDIT-013).
    """
    if not settings.chroma_host:
        return MockRetriever()
    return _build_real_retriever(settings)


def get_retriever_port(
    request: Request,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> RetrieverPort:
    """Liefert den Retriever-Adapter fuer TriageService (ADR-0024/0025/0027/0028).

    Bevorzugt die im Lifespan-Startup vorgeladene Ressource
    (request.app.state.retriever, AUDIT-013) -- so zahlt der erste echte
    Request nicht den Init-Preis (Chroma-Handshake, Modell-Laden, BM25-Bau,
    Cross-Encoder-Laden). Ist nichts vorgeladen (Mock-Modus, oder Lifespan lief
    nicht -- z. B. unter httpx-ASGITransport in Tests), faellt er auf
    resolve_retriever(settings) zurueck.
    """
    preloaded: RetrieverPort | None = getattr(request.app.state, "retriever", None)
    if preloaded is not None:
        return preloaded
    return resolve_retriever(settings)


def get_llm_adapter(
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> LLMPort:
    """Liefert den LLM-Adapter fuer TriageService (ADR-0010).

    Azure-Pfad: AECT_AZURE_OPENAI_ENDPOINT und AECT_AZURE_OPENAI_API_KEY
    gesetzt -> AzureOpenAIAdapter (echter Azure-Call, EU-Data-Zone-Pflicht
    ADR-0003). AsyncAzureOpenAI-Client wird hier gebaut und per
    Constructor-DI uebergeben (kein patch() in Tests noetig).

    Mock-Pfad: Credentials fehlen -> MockLLMAdapter (deterministisch,
    kein Netzwerk, fuer Tests und lokale Entwicklung ohne Azure-Setup).

    Beide Pfade: inner wird mit ResilientLLMAdapter gewrappt (Retry +
    Backoff + Timeout, ADR-0007). TriageService kennt nur LLMPort --
    der Pfadwechsel ist fuer ihn vollstaendig unsichtbar (ADR-0002).

    EU-Datenresidenz (AUDIT-008): ein gesetzter, nicht-Mock-Endpoint muss in
    der EU-Data-Zone liegen -- sonst ValueError (Fail-Fast). Greift auch im
    httpx-Testpfad, wo der Lifespan-Startup-Check nicht laeuft.
    """
    check_azure_eu_region(settings.azure_openai_endpoint)
    inner: LLMPort
    if settings.azure_openai_endpoint and settings.azure_openai_api_key:
        client = AsyncAzureOpenAI(
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint,
        )
        inner = AzureOpenAIAdapter(
            client=client,
            deployment=settings.azure_openai_deployment,
        )
    else:
        inner = MockLLMAdapter()
    return ResilientLLMAdapter(inner)


async def require_api_key(
    api_key: str | None = Depends(_api_key_header),
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> str:
    """FastAPI-Dependency: prueft X-API-Key-Header gegen konfigurierter Key.

    Raises:
        HTTPException 503: Server hat keinen API-Key konfiguriert (fehlende
            .env/AECT_API_KEY) -- bewusst 503 statt 500: der Server ist
            nicht betriebsbereit, es ist kein Crash und kein Client-Fehler.
        HTTPException 401: Key fehlt oder stimmt nicht.

    /health ist explizit exempt -- kein Depends(require_api_key) dort.
    """
    if not settings.api_key:
        raise HTTPException(
            status_code=503,
            detail="API key not configured on server",
        )
    # Konstante Laufzeit: compare_digest verhindert, dass die Vergleichsdauer
    # die Anzahl korrekter Praefix-Bytes verraet (Timing-Side-Channel). Bytes
    # statt str -- compare_digest auf str wirft TypeError bei Nicht-ASCII.
    if api_key is None or not secrets.compare_digest(
        api_key.encode("utf-8"), settings.api_key.encode("utf-8")
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "X-API-Key"},
        )
    return api_key


def get_triage_service(
    settings: Settings = Depends(get_settings),  # noqa: B008
    llm: LLMPort = Depends(get_llm_adapter),  # noqa: B008
    retriever: RetrieverPort = Depends(get_retriever_port),  # noqa: B008
) -> TriageService:
    """Liefert TriageService mit echten Produktions-Abhaengigkeiten.

    Persistenz: AECT_DB_PATH gesetzt -> SQLiteRepository (ueberlebt Neustart).
                AECT_DB_PATH leer  -> InMemoryRepository (prozessgebunden, Dev/Test).
    SystemClock und UUIDGenerator sind zustandslos -- neue Instanz pro Call ok.
    llm: Depends(get_llm_adapter) -- aktuell ResilientLLMAdapter(MockLLMAdapter())
    (Phase C); TriageService kennt nur LLMPort und merkt vom Wrapping nichts.
    retriever: Depends(get_retriever_port) -- MockRetriever per Default,
    CrossEncoderReranker(HybridRetriever(...)) wenn AECT_CHROMA_HOST gesetzt
    ist (ADR-0024, ADR-0025, ADR-0027, ADR-0028); TriageService kennt nur
    RetrieverPort.
    """
    repo: RepositoryPort = (
        SQLiteRepository(Path(settings.db_path)) if settings.db_path else _repository
    )

    # Dedup-Embedder (L-3, ADR-0039): nur im echten ML-Pfad (AECT_CHROMA_HOST
    # gesetzt -- dann ist das lokale Embedding-Modell ohnehin geladen, lru_cache).
    # Im Mock-/Testbetrieb None -> TriageService.check_similarity ueberspringt.
    embedder: EmbedderPort | None = None
    if settings.chroma_host:
        from aect.adapters.rag.embedder import SentenceTransformerEmbedder

        embedder = SentenceTransformerEmbedder(_get_local_embedding_model())

    return TriageService(
        repository=repo,
        clock=SystemClock(),
        id_generator=UUIDGenerator(),
        roi_config=get_roi_config(),
        llm=llm,
        retriever=retriever,
        embedder=embedder,
    )


def get_idempotency_store(
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> IdempotencyStorePort:
    """Liefert IdempotencyStore passend zur Persistenz-Wahl.

    AECT_DB_PATH gesetzt -> SQLiteIdempotencyStore (eigene Tabelle in
    derselben DB-Datei wie SQLiteRepository).
    AECT_DB_PATH leer  -> InMemoryIdempotencyStore (Singleton, prozessgebunden,
    Dev/Test).
    """
    if settings.db_path:
        return SQLiteIdempotencyStore(Path(settings.db_path))
    return _idempotency_store
