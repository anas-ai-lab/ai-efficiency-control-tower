"""Shared Fixtures fuer die API-Adapter-Tests."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

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
