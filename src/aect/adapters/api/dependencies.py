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
  Key-Rotation (Phase G): require_api_key prueft gegen BEIDE konfigurierten
  Keys (api_key + optional api_key_next), jeweils per eigenem
  compare_digest-Aufruf -- niemals `api_key in {...}`, das waere
  timing-unsicher (Python-String-Gleichheit bricht beim ersten
  abweichenden Byte ab). key_fingerprint() liefert einen kurzen sha256-
  Fingerprint (kid) fuer Logs -- NIE den Klartext-Key selbst.
InMemoryRepository: prozessgebunden, kein State nach Neustart.
Phase B: SQLiteRepository ersetzt dies.

Idempotency (aect-security-checklist v2.1, Phase B):
  get_idempotency_store() folgt demselben Muster wie get_triage_service():
  AECT_DB_PATH gesetzt -> SQLiteIdempotencyStore (persistent), sonst
  InMemoryIdempotencyStore (Singleton, prozessgebunden).

Token-Budget (Phase G Security-Haertung): get_token_budget_store() folgt
  demselben Persistenz-Muster wie get_idempotency_store(). require_token_budget()
  ist eine eigene FastAPI-Dependency (nicht Teil von require_api_key): schaetzt
  Tokens VOR dem LLM-Call ueber count_tokens() (cost_logger.py, F-031-gehaertet)
  auf den vier gebundenen Freitextfeldern des persistierten Case und prueft das
  Stundenbudget des aufrufenden API-Keys (api_key_hash = key_fingerprint(),
  voller Hash -- Wiederverwendung des Rotation-Mechanismus aus Phase G).
"""

from __future__ import annotations

import hashlib
import secrets
from functools import lru_cache
from pathlib import Path
from typing import Any

import structlog
from fastapi import Depends, HTTPException, Request
from fastapi.security import APIKeyHeader
from openai import AsyncAzureOpenAI

from aect.adapters.api.settings import Settings, check_azure_eu_region
from aect.adapters.in_memory.clock import SystemClock
from aect.adapters.in_memory.id_generator import UUIDGenerator
from aect.adapters.in_memory.idempotency_store import InMemoryIdempotencyStore
from aect.adapters.in_memory.llm import MockLLMAdapter
from aect.adapters.in_memory.repository import InMemoryRepository
from aect.adapters.in_memory.session_store import InMemorySessionStore
from aect.adapters.in_memory.token_budget_store import InMemoryTokenBudgetStore
from aect.adapters.llm.azure_openai import AzureOpenAIAdapter
from aect.adapters.llm.resilient import ResilientLLMAdapter
from aect.adapters.sqlite.idempotency_store import SQLiteIdempotencyStore
from aect.adapters.sqlite.repository import SQLiteRepository
from aect.adapters.sqlite.session_store import SQLiteSessionStore
from aect.adapters.sqlite.token_budget_store import SQLiteTokenBudgetStore
from aect.application.cost_logger import count_tokens
from aect.application.ports.embedder import EmbedderPort
from aect.application.ports.idempotency_store import IdempotencyStorePort
from aect.application.ports.llm import LLMPort
from aect.application.ports.pii_redactor import PIIRedactorPort
from aect.application.ports.repository import RepositoryPort
from aect.application.ports.retriever import RetrieverPort
from aect.application.ports.session_store import SessionStorePort
from aect.application.ports.token_budget import TokenBudgetPort
from aect.application.service import TriageService
from aect.domain.roi import ROIConfig, load_roi_config

# Kein Modul-globaler Logger hier (bewusst, analog cost_logger.log_llm_cost
# und service.py injection_pattern_detected): cache_logger_on_first_use=True
# (logging_config.py) bindet einen Logger beim ERSTEN echten Aufruf permanent
# an die zu dem Zeitpunkt aktuelle Processor-Kette -- structlog.get_logger()
# wird an den Log-Aufrufstellen deshalb frisch geholt, sonst sieht
# capture_logs() in Tests je nach Ausfuehrungsreihenfolge nichts mehr.

# Singleton -- Repository-State lebt fuer die Prozess-Lebensdauer.
_repository: InMemoryRepository = InMemoryRepository()

# Singleton -- Idempotency-Key-State lebt fuer die Prozess-Lebensdauer
# (analog _repository; nur relevant ohne AECT_DB_PATH).
_idempotency_store: InMemoryIdempotencyStore = InMemoryIdempotencyStore()

# Singleton -- Admin-Session-State lebt fuer die Prozess-Lebensdauer (analog
# _idempotency_store; nur relevant ohne AECT_DB_PATH, sonst SQLiteSessionStore).
_session_store: InMemorySessionStore = InMemorySessionStore()

# auto_error=False: fehlender Header liefert None statt automatischem 403.
# Unser require_api_key gibt dann einheitlich 401 zurueck.
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Admin-Login (V4-P-Auth). Cookie-Name und Gueltigkeit (12 h) sind fest --
# ein Single-User-Demo braucht keine konfigurierbare Session-Laufzeit.
SESSION_COOKIE_NAME = "aect_session"
SESSION_TTL_HOURS = 12

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

    Fail loud (V4-P2, CLAUDE.md): ein expliziter Heartbeat prueft die
    Erreichbarkeit. Ist Chroma nicht erreichbar, wird das als ConnectionError
    durchgereicht und als "chroma_unreachable" (Host/Port) geloggt -- NIE ein
    stiller MockRetriever-Fallback. chromadb.HttpClient() macht bereits einen
    Preflight (ValueError bei geschlossenem Port); heartbeat() sichert zusaetzlich
    den Fall ab, dass der Konstruktor kuenftig nicht mehr eager verbindet.
    """
    import chromadb

    try:
        client = chromadb.HttpClient(host=host, port=port)
        client.heartbeat()
    except Exception as exc:
        structlog.get_logger().error(
            "chroma_unreachable",
            host=host,
            port=port,
            error_type=type(exc).__name__,
        )
        raise ConnectionError(
            f"ChromaDB unter {host}:{port} nicht erreichbar -- laeuft der "
            f"Container (docker compose up -d) und ist er geseedet? Kein "
            f"stiller Mock-Fallback (CLAUDE.md fail loud)."
        ) from exc
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

    Container-Hinweis: ist der Container nicht gestartet, schlaegt der
    Erreichbarkeits-Check in _get_chroma_collection mit einer ConnectionError
    fehl -- kein stiller Fallback.

    Reihenfolge (V4-P2): der Chroma-Erreichbarkeits-Check laeuft ZUERST, BEVOR
    die schweren rag-/torch-Imports und das Modell-Laden -- ein toter Container
    faellt so in Millisekunden durch, ohne erst Modellgewichte zu laden.

    Lokale Imports (statt Modulkopf): konsistent mit dem bestehenden Muster.
    """
    # Erreichbarkeit zuerst (fail loud), bevor torch/Modelle geladen werden:
    collection = _get_chroma_collection(settings.chroma_host, settings.chroma_port)

    from aect.adapters.rag.bm25_retriever import BM25Retriever
    from aect.adapters.rag.embedder import SentenceTransformerEmbedder
    from aect.adapters.rag.hybrid_retriever import HybridRetriever
    from aect.adapters.rag.reranker import CrossEncoderReranker
    from aect.adapters.rag.retriever import ChromaRetriever

    embedder = SentenceTransformerEmbedder(_get_local_embedding_model())
    vector_retriever = ChromaRetriever(collection, embedder)

    bm25_index = _get_bm25_index(settings.kb_dir)
    bm25_retriever = BM25Retriever(bm25_index)

    hybrid = HybridRetriever(vector_retriever, bm25_retriever)

    cross_encoder_model = _get_cross_encoder_model()
    return CrossEncoderReranker(hybrid, cross_encoder_model)


def resolve_retriever(settings: Settings) -> RetrieverPort:
    """Baut den echten Retriever aus settings.chroma_host -- fail loud (V4-P2).

    KEIN stiller MockRetriever-Fallback mehr (CLAUDE.md): der Default-Host ist
    127.0.0.1 (settings.py), ein leerer AECT_CHROMA_HOST ist eine
    Fehlkonfiguration und wirft ValueError. Ist der konfigurierte Host nicht
    erreichbar, wirft _build_real_retriever() (via _get_chroma_collection) eine
    ConnectionError mit "chroma_unreachable"-Log -- die Instanz faellt nie
    stillschweigend auf das synthetische Mock-Korpus zurueck. MockRetriever ist
    nur noch ueber einen expliziten Test-Override erreichbar (z. B.
    app.dependency_overrides[get_retriever_port] in Tests).

    Kein app.state -- reine Settings-Logik, direkt testbar und vom
    Lifespan-Startup wiederverwendet (AUDIT-013).
    """
    if not settings.chroma_host:
        raise ValueError(
            "AECT_CHROMA_HOST ist leer -- kein Retriever konfiguriert (Default "
            "127.0.0.1). MockRetriever gibt es nur ueber einen expliziten "
            "Test-Override, nicht als stillen Fallback (CLAUDE.md fail loud)."
        )
    return _build_real_retriever(settings)


def get_retriever_port(
    request: Request,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> RetrieverPort:
    """Liefert den Retriever-Adapter fuer TriageService (ADR-0024/0025/0027/0028).

    Bevorzugt die im Lifespan-Startup vorgeladene Ressource
    (request.app.state.retriever, AUDIT-013) -- so zahlt der erste echte
    Request nicht den Init-Preis (Chroma-Handshake, Modell-Laden, BM25-Bau,
    Cross-Encoder-Laden). Ist nichts vorgeladen (Lifespan lief nicht -- z. B.
    unter httpx-ASGITransport in Tests), faellt er auf resolve_retriever(settings)
    zurueck, das seit V4-P2 fail-loud ist (kein stiller Mock-Fallback; Tests
    injizieren MockRetriever per app.dependency_overrides[get_retriever_port]).
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
    httpx-Testpfad, wo der Lifespan-Startup-Check nicht laeuft. Explizite
    settings.azure_openai_region (falls gesetzt) umgeht dabei die Hostname-
    Heuristik -- sonst wuerde jeder reale Custom-Subdomain-Endpoint hier
    erneut abgelehnt, selbst wenn der Lifespan-Check ihn schon akzeptiert hat.
    """
    check_azure_eu_region(settings.azure_openai_endpoint, settings.azure_openai_region)
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


def key_fingerprint(secret: str, length: int = 8) -> str:
    """Kurzer sha256-Fingerprint eines Secrets -- NIE der Klartext selbst.

    Genutzt als kid (Key-ID) in Logs (Rotation, Phase G) und als
    api_key_hash zur Token-Budget-Zuordnung (Phase G, Token-Budget-Limiter)
    -- ein Mechanismus, zwei Verwendungen. length=8 (Default) reicht fuer
    Log-Unterscheidbarkeit zwischen wenigen aktiven Keys; length=0 liefert
    den vollen 64-Zeichen-Hexdigest (Kollisionsresistenz fuer Persistenz-
    Schluessel, z. B. token_budget-Tabellen).
    """
    digest = hashlib.sha256(secret.encode("utf-8")).hexdigest()
    return digest[:length] if length else digest


def _matches(candidate: bytes, secret: str) -> bool:
    """Konstante-Laufzeit-Vergleich gegen ein einzelnes konfiguriertes Secret.

    Leeres secret ist nie ein gueltiger Match (verhindert, dass ein leerer
    api_key_next versehentlich jeden Key akzeptiert).
    """
    return bool(secret) and secrets.compare_digest(candidate, secret.encode("utf-8"))


def _match_api_key(api_key: str | None, settings: Settings) -> str | None:
    """Prueft den X-API-Key gegen die konfigurierten Keys (mit Rotation).

    Rotation ohne Downtime (Phase G): akzeptiert sowohl settings.api_key
    (primaer) als auch settings.api_key_next (optional, waehrend einer Rotation)
    -- jeweils per eigenem compare_digest-Aufruf, nie per Listen-Mitgliedschaft
    (`in`), das waere timing-unsicher. Loggt bei Erfolg api_key_authenticated
    (kid = kurzer Fingerprint, nie der Klartext-Key).

    Returns:
        den uebergebenen Key bei Match, sonst None (fehlender Header, leerer
        Server-Key oder kein Treffer).
    """
    if api_key is None:
        return None
    # Bytes statt str: compare_digest auf str wirft TypeError bei Nicht-ASCII.
    candidate = api_key.encode("utf-8")
    if _matches(candidate, settings.api_key):
        structlog.get_logger().info(
            "api_key_authenticated", kid=key_fingerprint(settings.api_key)
        )
        return api_key
    if _matches(candidate, settings.api_key_next):
        structlog.get_logger().info(
            "api_key_authenticated", kid=key_fingerprint(settings.api_key_next)
        )
        return api_key
    return None


async def require_api_key(
    api_key: str | None = Depends(_api_key_header),
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> str:
    """FastAPI-Dependency: prueft X-API-Key-Header gegen konfigurierte Keys.

    Bleibt fuer den reinen API-Key-Zugriff bestehen (Skripte/Tests). Die
    Admin-Routen laufen ueber require_admin, das zusaetzlich Session-Cookies
    akzeptiert und den API-Key-Zweig via _match_api_key wiederverwendet.

    Raises:
        HTTPException 503: Server hat keinen primaeren API-Key konfiguriert
            (fehlende .env/AECT_API_KEY) -- bewusst 503 statt 500: der
            Server ist nicht betriebsbereit, es ist kein Crash und kein
            Client-Fehler.
        HTTPException 401: Key fehlt oder stimmt gegen keinen der
            konfigurierten Keys.
    """
    if not settings.api_key:
        raise HTTPException(
            status_code=503,
            detail="API key not configured on server",
        )
    matched = _match_api_key(api_key, settings)
    if matched is not None:
        return matched
    raise HTTPException(
        status_code=401,
        detail="Invalid or missing API key",
        headers={"WWW-Authenticate": "X-API-Key"},
    )


def get_session_store(
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> SessionStorePort:
    """Liefert den Session-Store passend zur Persistenz-Wahl (analog
    get_idempotency_store).

    AECT_DB_PATH gesetzt -> SQLiteSessionStore (persistent, eigene Tabelle in
    derselben DB-Datei wie SQLiteRepository -- Sessions ueberleben Neustart).
    AECT_DB_PATH leer  -> In-Memory-Singleton (Dev/Test/Demo).
    """
    if settings.db_path:
        return SQLiteSessionStore(Path(settings.db_path))
    return _session_store


def authenticate_admin(
    request: Request,
    api_key: str | None,
    settings: Settings,
    session_store: SessionStorePort,
) -> str | None:
    """Ermittelt die Admin-Identitaet aus Session-Cookie ODER API-Key.

    Reihenfolge: zuerst das Session-Cookie (der Browser-Weg nach dem Login),
    dann der X-API-Key (Skripte/Tests). Eine abgelaufene Session wird beim
    Zugriff verworfen (delete) und zaehlt als nicht authentifiziert.

    Returns:
        "session"      -- gueltige, nicht abgelaufene Admin-Session.
        <der API-Key>  -- gueltiger X-API-Key (Wert dient als Budget-/Log-ID).
        None           -- weder gueltige Session noch gueltiger Key.

    Kein Raise -- der Aufrufer entscheidet ueber 401/503 (require_admin) bzw.
    ueber das authenticated-Flag (GET /auth/me).
    """
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        token_hash = key_fingerprint(token, length=0)
        session = session_store.get(token_hash)
        if session is not None:
            if session.expires_at <= SystemClock().now():
                # Abgelaufen -> verwerfen (Vorgabe: "beim Zugriff verworfen").
                session_store.delete(token_hash)
                structlog.get_logger().info("admin_session_expired")
            else:
                structlog.get_logger().info("admin_session_authenticated")
                return "session"
    return _match_api_key(api_key, settings)


async def require_admin(
    request: Request,
    api_key: str | None = Depends(_api_key_header),
    settings: Settings = Depends(get_settings),  # noqa: B008
    session_store: SessionStorePort = Depends(get_session_store),  # noqa: B008
) -> str:
    """FastAPI-Dependency fuer alle Admin-Routen: Session-Cookie ODER API-Key.

    Public-Routen (POST /triage, POST /ideation, GET /cases, GET /auth/me,
    POST /auth/login, Health/Docs) haengen NICHT an dieser Dependency -- sie
    sind bewusst ohne Auth erreichbar (anonyme Einreichung/Ideen/Ideenliste).

    Raises:
        HTTPException 503: Server hat WEDER einen API-Key NOCH einen
            Admin-Passwort-Hash konfiguriert -- die Admin-Flaeche ist gar nicht
            eingerichtet (ehrliches "nicht betriebsbereit" statt 401).
        HTTPException 401: keine gueltige Session und kein gueltiger API-Key.
    """
    identity = authenticate_admin(request, api_key, settings, session_store)
    if identity is not None:
        return identity
    if not settings.api_key and not settings.admin_password_hash:
        raise HTTPException(
            status_code=503,
            detail="Admin auth not configured on server",
        )
    raise HTTPException(
        status_code=401,
        detail="Invalid or missing admin credentials",
        headers={"WWW-Authenticate": "X-API-Key"},
    )


async def is_admin_request(
    request: Request,
    api_key: str | None = Depends(_api_key_header),
    settings: Settings = Depends(get_settings),  # noqa: B008
    session_store: SessionStorePort = Depends(get_session_store),  # noqa: B008
) -> bool:
    """Nicht-werfende Variante von require_admin (V4-P7-Sichtbarkeit).

    True, wenn der Aufrufer eine gueltige Admin-Session ODER einen gueltigen
    API-Key traegt, sonst False -- ohne 401/503. Fuer Endpoints, die PUBLIC
    erreichbar bleiben, ihren Inhalt aber fuer Admins erweitern: GET /cases/{id}
    zeigt dem AI Board (Admin) die Bewertung schon vor der Entscheidung, dem
    anonymen Einreicher erst danach. Reine Erkennung -- kein Zugriffsschutz;
    schuetzende Routen nutzen weiterhin require_admin.
    """
    return authenticate_admin(request, api_key, settings, session_store) is not None


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
    #
    # PII-Redactor (Phase G Privacy-Haertung, B1-Spike): denselben Gate wie
    # embedder -- ohne Embedder findet ohnehin kein Dedup-Embedding statt,
    # ein Redactor waere toter Code. PresidioRedactor selbst laedt sein
    # Modell lazy (erster redact()-Aufruf, siehe presidio_redactor.py) --
    # die Konstruktion hier ist billig, unabhaengig vom lru_cache-Muster der
    # anderen schweren Ressourcen oben (_get_chroma_collection etc.).
    embedder: EmbedderPort | None = None
    redactor: PIIRedactorPort | None = None
    if settings.chroma_host:
        from aect.adapters.pii.presidio_redactor import PresidioRedactor
        from aect.adapters.rag.embedder import SentenceTransformerEmbedder

        embedder = SentenceTransformerEmbedder(_get_local_embedding_model())
        redactor = PresidioRedactor()

    return TriageService(
        repository=repo,
        clock=SystemClock(),
        id_generator=UUIDGenerator(),
        roi_config=get_roi_config(),
        llm=llm,
        retriever=retriever,
        embedder=embedder,
        redactor=redactor,
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


@lru_cache
def _get_in_memory_token_budget_store(budget_per_hour: int) -> InMemoryTokenBudgetStore:
    """Gecachter In-Memory-Token-Budget-Store, ein Store pro distinktem
    budget_per_hour-Wert (analog get_roi_config/_get_chroma_collection).

    Der Store MUSS ueber Requests hinweg denselben Zustand behalten (sonst
    zaehlt jeder Request bei 0 an) -- lru_cache haelt hier keyed auf den
    Budget-Wert genau eine Instanz pro Prozess, ohne (anders als ein
    einfacher Modul-Singleton) einen veralteten Budget-Wert aus einem
    frueheren Settings-Override in Tests einzufrieren.
    """
    return InMemoryTokenBudgetStore(SystemClock(), budget_per_hour)


def get_token_budget_store(
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> TokenBudgetPort:
    """Liefert TokenBudgetPort passend zur Persistenz-Wahl (analog
    get_idempotency_store).

    AECT_DB_PATH gesetzt -> SQLiteTokenBudgetStore (persistent, eigene
    Tabelle in derselben DB-Datei wie SQLiteRepository).
    AECT_DB_PATH leer  -> gecachter InMemoryTokenBudgetStore (Dev/Test).
    """
    if settings.db_path:
        return SQLiteTokenBudgetStore(
            Path(settings.db_path), SystemClock(), settings.token_budget_per_hour
        )
    return _get_in_memory_token_budget_store(settings.token_budget_per_hour)


async def require_token_budget(
    case_id: str,
    identity: str = Depends(require_admin),
    service: TriageService = Depends(get_triage_service),  # noqa: B008
    token_budget: TokenBudgetPort = Depends(get_token_budget_store),  # noqa: B008
) -> None:
    """FastAPI-Dependency: schaetzt Tokens VOR dem LLM-Call und prueft das
    stuendliche Budget des aufrufenden API-Keys.

    Ergaenzt die Request-Rate-Limits (slowapi, 10/min LLM-Endpoints) um eine
    Token-MENGEN-Grenze: 10 Requests mit je max_length-langem Freitext
    verbrauchen deutlich mehr Tokens als 10 kurze -- Request-Count allein
    deckt das nicht ab.

    Eingabetext: die vier gebundenen Freitextfelder des persistierten Case
    (title, current_state, desired_state, example_process) -- das ist der
    Text, der in sharpen_case()/propose_solution()/generate_compliance_hints()
    tatsaechlich in den Prompt einfliesst (approximiert, kein exaktes Prompt-
    Rendering -- fuer eine Vorab-Budget-Schaetzung ausreichend).

    Case nicht gefunden -> kein Budget-Check (die Route liefert ihr eigenes
    404, keine Duplizierung der 404-Antwort hier).

    Raises:
        HTTPException 429: Stundenbudget des API-Keys ueberschritten.
    """
    case = service.get_case(case_id)
    if case is None:
        return
    text = (
        f"{case.use_case.title} {case.use_case.current_state} "
        f"{case.use_case.desired_state} {case.use_case.example_process}"
    )
    tokens = count_tokens(text)
    # identity ist "session" (Browser-Login) oder der API-Key (Skripte). Beide
    # bekommen ueber ihren Fingerprint einen eigenen Budget-Bucket -- im
    # Single-User-Demo teilen sich alle Session-Requests denselben "session"-
    # Bucket, was hier gewollt ist (ein Admin).
    identity_hash = key_fingerprint(identity, length=0)
    if not token_budget.try_consume(identity_hash, tokens):
        raise HTTPException(
            status_code=429,
            detail="Token budget exceeded for this API key",
        )
