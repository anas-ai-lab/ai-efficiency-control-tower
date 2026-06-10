"""FastAPI App-Factory fuer AECT.

create_app() erzeugt eine konfigurierte Instanz -- Tests importieren die
Factory direkt statt die Modul-globale `app`, damit jeder Test eine
isolierte Instanz ohne geteilten State bekommt.

Security (aect-security-checklist v2.1, Phase B):
  debug=False: kein Stack-Trace in HTTP-Responses (OWASP LLM02).
  CORS allow_origins=[]: sicherer Default, explizit leer.
    Phase F setzt konkrete Origins per Env-Variable, wenn das Frontend existiert.
    Nie ["*"] mit allow_credentials=True (CORS-Bypass-Risiko).
  X-API-Key in allow_headers: vorbereitet fuer Tag 24.
Globaler Exception-Handler folgt in Tag 24.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from aect.adapters.api.routes import health


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

    app.include_router(health.router)

    return app


# Modul-globale Instanz fuer uvicorn:
#   uv run uvicorn aect.adapters.api.app:app --reload
app: FastAPI = create_app()
