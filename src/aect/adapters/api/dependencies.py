"""FastAPI Dependency-Provider fuer AECT.

Verdrahtet Application-Service mit seinen Infrastruktur-Abhaengigkeiten.
Kein Routing, keine Business-Logik -- nur Komposition.

Architektur: adapters/api/ darf aus adapters/in_memory/ importieren (beide
sind Infrastruktur-Schicht). Verboten waere ein Import aus domain/ oder
application/ IN Richtung adapters/ -- das laeuft in die andere Richtung.

Security (Tag 24): API-Key-Pruefung wird als FastAPI-Dependency ergaenzt.
InMemoryRepository: prozessgebunden, kein State nach Neustart.
Phase B: SQLiteRepository ersetzt dies.
"""

from __future__ import annotations

from functools import lru_cache

from aect.adapters.in_memory.clock import SystemClock
from aect.adapters.in_memory.id_generator import UUIDGenerator
from aect.adapters.in_memory.repository import InMemoryRepository
from aect.application.service import TriageService
from aect.domain.roi import ROIConfig, load_roi_config

# Singleton -- Repository-State lebt fuer die Prozess-Lebensdauer.
_repository: InMemoryRepository = InMemoryRepository()


@lru_cache
def get_roi_config() -> ROIConfig:
    """Laedt ROIConfig einmalig aus config/roi_config.toml.

    lru_cache ohne Parameter: Config-Datei wird beim ersten Aufruf gelesen
    und gecacht -- kein wiederholter Dateisystem-Zugriff.
    """
    return load_roi_config()


def get_triage_service() -> TriageService:
    """Liefert TriageService mit echten Produktions-Abhaengigkeiten.

    Wird in Tag 24 als FastAPI Depends(get_triage_service) eingesetzt.
    SystemClock und UUIDGenerator sind zustandslos -- neue Instanz pro Call ok.
    """
    return TriageService(
        repository=_repository,
        clock=SystemClock(),
        id_generator=UUIDGenerator(),
        roi_config=get_roi_config(),
    )
