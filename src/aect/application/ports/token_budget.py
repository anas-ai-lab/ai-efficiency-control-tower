"""TokenBudgetPort -- Persistenz-Abstraktion fuer stuendliche Token-Budgets
pro API-Key (Phase G Security-Haertung).

Ergaenzt die bestehenden Request-Rate-Limits (slowapi, 10/min LLM-Endpoints,
rate_limit.py) um eine Token-MENGEN-Grenze: 10 Requests mit je max_length-
langem Freitext verbrauchen deutlich mehr Tokens als 10 kurze Requests --
Request-Count allein deckt das nicht ab.

Fixed-Window pro Stunde. Schluessel ist ein sha256-Hash des API-Keys
(api_key_hash) -- NIE der Klartext-Key selbst, gleicher Fingerprint-
Mechanismus wie kid in dependencies.key_fingerprint() (Key-Rotation,
Phase G).
"""

from __future__ import annotations

from typing import Protocol


class TokenBudgetPort(Protocol):
    """Prueft und verbraucht ein stuendliches Token-Budget pro API-Key-Hash.

    Aktuelle Impl.: InMemoryTokenBudgetStore (Dev/Test),
    SQLiteTokenBudgetStore (persistent).
    """

    def try_consume(self, api_key_hash: str, tokens: int) -> bool:
        """Versucht, `tokens` aus dem aktuellen Stunden-Fenster zu verbrauchen.

        Returns:
            True  -- im Budget, tokens wurden verbucht.
            False -- Budget ueberschritten (auch wenn diese eine Anfrage
                     allein schon das gesamte Stundenbudget uebersteigt) --
                     in diesem Fall wird nichts verbucht.
        """
        ...

    def remaining(self, api_key_hash: str) -> int:
        """Verbleibendes Budget im aktuellen Stunden-Fenster (nie negativ)."""
        ...
