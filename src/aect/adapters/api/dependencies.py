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
"""

from __future__ import annotations

from functools import lru_cache

from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

from aect.adapters.api.settings import Settings
from aect.adapters.in_memory.clock import SystemClock
from aect.adapters.in_memory.id_generator import UUIDGenerator
from aect.adapters.in_memory.repository import InMemoryRepository
from aect.application.service import TriageService
from aect.domain.roi import ROIConfig, load_roi_config

# Singleton -- Repository-State lebt fuer die Prozess-Lebensdauer.
_repository: InMemoryRepository = InMemoryRepository()

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


def get_triage_service() -> TriageService:
    """Liefert TriageService mit echten Produktions-Abhaengigkeiten.

    SystemClock und UUIDGenerator sind zustandslos -- neue Instanz pro Call ok.
    """
    return TriageService(
        repository=_repository,
        clock=SystemClock(),
        id_generator=UUIDGenerator(),
        roi_config=get_roi_config(),
    )
