"""Shared Fixtures fuer die API-Adapter-Tests."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from aect.adapters.api.dependencies import _get_in_memory_token_budget_store
from aect.adapters.api.rate_limit import limiter


@pytest.fixture(autouse=True)
def reset_rate_limiter() -> Iterator[None]:
    """Setzt den modul-globalen slowapi-Limiter vor jedem Test zurueck.

    Der Limiter (In-Memory-Storage) ist EIN Objekt fuer alle create_app()-
    Instanzen der Suite. Ohne Reset teilen sich alle Tests mit demselben
    X-API-Key das 30/minute-Budget von POST /triage -- die Suite wurde mit
    wachsender Testzahl flaky (429 statt 201 in spaeter laufenden Tests).
    """
    limiter.reset()
    yield


@pytest.fixture(autouse=True)
def reset_token_budget_store() -> Iterator[None]:
    """Leert den lru_cache von _get_in_memory_token_budget_store vor jedem Test.

    Der In-Memory-Token-Budget-Store wird pro budget_per_hour-Wert gecacht
    (dependencies.py, analog get_roi_config/_get_chroma_collection) -- ohne
    Reset teilen sich mehrere Tests mit demselben Budget-Wert UND demselben
    API-Key denselben Verbrauchszaehler, exakt dasselbe Cross-Test-Pollution-
    Muster wie beim slowapi-Limiter oben (reset_rate_limiter).
    """
    _get_in_memory_token_budget_store.cache_clear()
    yield
