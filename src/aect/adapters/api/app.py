"""FastAPI App-Factory fuer AECT.

create_app() erzeugt eine konfigurierte Instanz -- Tests importieren die
Factory direkt statt die Modul-globale `app`, damit jeder Test eine
isolierte Instanz ohne geteilten State bekommt.

Security (aect-security-checklist v2.1, Phase B):
  debug=False: kein Stack-Trace in HTTP-Responses (OWASP LLM02).
  CORS allow_origins=[]: sicherer Default, explizit leer.
  CorrelationIDMiddleware: UUID4 request_id pro Request,
    in structlog-Kontext gebunden, als X-Request-ID im Header.
  Rate Limiting (slowapi): 30/min POST /triage, 60/min GET /cases.
    RateLimitExceeded -> 429 mit Retry-After (kein PII im Header).
  Globaler Exception-Handler: kein Stack-Trace an Client (OWASP LLM02),
    request_id aus structlog-Kontext fuer Log-Korrelation.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from aect.adapters.api.dependencies import get_settings, resolve_retriever
from aect.adapters.api.logging_config import configure_logging
from aect.adapters.api.rate_limit import limiter
from aect.adapters.api.routes import cases, health, triage

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Laedt schwergewichtige Retrieval-Ressourcen beim Startup (AUDIT-013).

    Im echten RAG-Pfad (AECT_CHROMA_HOST gesetzt) werden Chroma-Collection,
    Embedding-Modell, BM25-Index und Cross-Encoder hier EINMAL gebaut und der
    fertige Retriever auf app.state.retriever gelegt -- der erste Request zahlt
    dann nicht den Init-Preis (Modell-Laden, Container-Handshake, BM25-Bau).

    Mock-/Test-Modus (AECT_CHROMA_HOST leer): kein Heavy-Init -- app.state.
    retriever bleibt ungesetzt, get_retriever_port() liefert MockRetriever.
    Identisch zum bisherigen Verhalten, kein Container/Torch noetig.

    Hinweis: get_settings() liest die echte Umgebung; dependency_overrides aus
    Tests wirken nur zur Request-Zeit, nicht im Lifespan. Unter httpx-
    ASGITransport laeuft dieser Lifespan nicht -- get_retriever_port faellt
    dort sauber auf resolve_retriever() zurueck.
    """
    settings = get_settings()
    if settings.chroma_host:
        logger.info("startup_loading_resources", chroma_host=settings.chroma_host)
        app.state.retriever = resolve_retriever(settings)
        logger.info("startup_resources_ready")
    else:
        logger.info("startup_mock_mode_no_heavy_resources")
    yield
    # Shutdown: Chroma-HttpClient hat keinen expliziten Close-Handshake;
    # Referenz wird mit dem Prozess freigegeben.
    logger.info("shutdown_complete")


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Bindet eine eindeutige request_id an den structlog-Kontext pro Request.

    X-Request-ID im Response-Header: erleichtert Log-Korrelation.
    Security: request_id ist UUID4, kein personenbezogener Wert (kein PII).
    structlog.contextvars: alle Log-Aufrufe innerhalb des Requests
      erhalten request_id und route automatisch ohne extra={}.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            route=request.url.path,
        )
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


def create_app() -> FastAPI:
    """Erzeugt und konfiguriert die FastAPI-Applikation."""
    configure_logging()

    app = FastAPI(
        title="AECT - AI Efficiency Control Tower",
        description="AI Use Case Intake & Triage Assistant",
        version="1.2.0",
        debug=False,
        docs_url="/docs",
        redoc_url=None,
        lifespan=lifespan,
    )

    # Rate Limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

    # Middleware -- letztes add_middleware = outermost = laeuft zuerst.
    # Reihenfolge: CorrelationIDMiddleware -> CORSMiddleware -> Routing.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-API-Key", "Idempotency-Key"],
    )
    app.add_middleware(CorrelationIDMiddleware)

    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        ctx = structlog.contextvars.get_contextvars()
        request_id = ctx.get("request_id", str(uuid.uuid4()))
        logger.exception("Unhandled exception")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal error", "request_id": request_id},
            headers={"X-Request-ID": request_id},
        )

    app.include_router(health.router)
    app.include_router(cases.router)
    app.include_router(triage.router)

    return app


# Modul-globale Instanz fuer uvicorn:
#   uv run uvicorn aect.adapters.api.app:app --reload
app: FastAPI = create_app()
