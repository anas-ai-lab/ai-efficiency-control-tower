"""IdGeneratorPort -- testbarer ID-Generierungs-Kontrakt."""

from __future__ import annotations

from typing import Protocol


class IdGeneratorPort(Protocol):
    """Generiert eindeutige String-IDs.

    Warum ein Port? Tests benoetigen vorhersagbare IDs um Assertions zu schreiben.
    FakeIdGenerator im Test gibt feste IDs der Reihe nach zurueck.
    """

    def generate(self) -> str: ...
