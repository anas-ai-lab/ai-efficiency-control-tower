"""FastAPI App-Factory fuer AECT.

create_app() erzeugt eine konfigurierte Instanz -- Tests importieren die
Factory direkt statt die Modul-globale `app`, damit jeder Test eine
isolierte Instanz ohne geteilten State bekommt.

Security (aect-security-checklist v2.1, Phase B):
  debug=False: kein Stack-Trace in HTTP-Responses (OWASP LLM02).
  CORS allow_origins=[]: sicherer Default, explizit leer.
    Phase F setzt konkrete Origins per Env-Variable, wenn das Frontend existiert.
    Nie ["*"] mit allow_credentials=True (CORS-Bypass-Risiko).
  X-API-Key in allow_headers: vorbereitet fuer require_api_key.
  Globaler Exception-Handler (Tag 24): kein Stack-Trace an Client,
    generische 500-Response mit request_id fuer Log-Korrelation.
    HTTPException wird von FastAPI separat behandelt -- nicht durch
    diesen Handler abgefangen.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from aect.adapters.api.routes import cases, health

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Erzeugt und konfiguriert die FastAPI-Applikation."""
    app = FastAPI(
        title="AECT — AI Efficiency Control Tower",
        description="AI Use Case Intake & Triage Assistant",
        version="0.1.0",
        debug=False,  # Security: kein Stack-Trace an Client (OWASP LLM02)
        docs_url="/docs",
        redoc_url=None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[],  # Phase F: per Env-Variable befuellen
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-API-Key"],
    )

    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Faengt alle unbehandelten non-HTTP-Exceptions ab.

        Security (OWASP LLM02): kein Stack-Trace in der Response.
        request_id: ermoeglicht Log-Korrelation ohne PII-Leak.
        Intern: Exception wird mit logger.exception geloggt.
        """
        request_id = str(uuid.uuid4())
        logger.exception(
            "Unhandled exception",
            extra={"request_id": request_id, "path": str(request.url.path)},
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal error", "request_id": request_id},
        )

    app.include_router(health.router)
    app.include_router(cases.router)

    return app


# Modul-globale Instanz fuer uvicorn:
#   uv run uvicorn aect.adapters.api.app:app --reload
app: FastAPI = create_app()
