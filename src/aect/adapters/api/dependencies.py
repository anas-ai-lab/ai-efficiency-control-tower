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
InMemoryRepository: prozessgebunden, kein State nach Neustart.
Phase B: SQLiteRepository ersetzt dies.

Idempotency (aect-security-checklist v2.1, Phase B):
  get_idempotency_store() folgt demselben Muster wie get_triage_service():
  AECT_DB_PATH gesetzt -> SQLiteIdempotencyStore (persistent), sonst
  InMemoryIdempotencyStore (Singleton, prozessgebunden).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader
from openai import AsyncAzureOpenAI

from aect.adapters.api.settings import Settings
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


def get_retriever_port() -> RetrieverPort:
    """Liefert den Retriever-Adapter fuer TriageService (ADR-0024).

    Bewusst noch MockRetriever, analog get_llm_adapter() vor dem
    Azure-Zweig (Tag 33-45): ChromaRetriever existiert bereits
    (adapters/rag/retriever.py, ADR-0019/0023), wird hier aber noch nicht
    verdrahtet -- braucht einen laufenden ChromaDB-Collection-Client und
    eine Embedder-Wahl (ADR-0016/0018), eigener Folge-Tag, kein
    Vollausbau heute (Scope-Disziplin, session-protocol v3 SS5.2).
    """
    return MockRetriever()


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
    """
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
        HTTPException 500: Server hat keinen API-Key konfiguriert.
        HTTPException 401: Key fehlt oder stimmt nicht.

    /health ist explizit exempt -- kein Depends(require_api_key) dort.
    """
    if not settings.api_key:
        raise HTTPException(
            status_code=500,
            detail="API key not configured on server",
        )
    if api_key != settings.api_key:
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
    retriever: Depends(get_retriever_port) -- aktuell MockRetriever (Phase D,
    ADR-0024); TriageService kennt nur RetrieverPort.
    """
    repo: RepositoryPort = (
        SQLiteRepository(Path(settings.db_path)) if settings.db_path else _repository
    )
    return TriageService(
        repository=repo,
        clock=SystemClock(),
        id_generator=UUIDGenerator(),
        roi_config=get_roi_config(),
        llm=llm,
        retriever=retriever,
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
