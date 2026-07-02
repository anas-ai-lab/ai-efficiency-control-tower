"""InMemoryTokenBudgetStore -- implementiert TokenBudgetPort mit einem dict.

Fixed-Window pro Stunde: die Fenstergrenze ist die volle Stunde (Minute/
Sekunde/Mikrosekunde auf 0), aus dem injizierten ClockPort -- niemals
datetime.now() direkt (Testbarkeit ohne echte Wartezeit, analog allen
anderen ClockPort-Konsumenten im Projekt).
"""

from __future__ import annotations

from datetime import datetime

from aect.application.ports.clock import ClockPort


class InMemoryTokenBudgetStore:
    """In-Memory-dict als Token-Budget-Speicher.

    Lebensdauer: Prozess-gebunden -- kein State nach Neustart, analog
    InMemoryIdempotencyStore/InMemoryRepository. Alte Fenster werden nicht
    aufgeraeumt (dict waechst mit der Anzahl distinkter (Key, Stunde)-Paare)
    -- fuer Portfolio-/Testbetrieb unkritisch, dieselbe akzeptierte Grenze
    wie bei den anderen In-Memory-Adaptern.

    Security: kein Locking -- Single-Thread-Only (analog InMemoryRepository).
    """

    def __init__(self, clock: ClockPort, budget_per_hour: int) -> None:
        self._clock = clock
        self._budget_per_hour = budget_per_hour
        self._usage: dict[tuple[str, datetime], int] = {}

    def try_consume(self, api_key_hash: str, tokens: int) -> bool:
        # Eine Einzelanfrage, die schon allein das Stundenbudget sprengt,
        # kann nie durchgehen -- unabhaengig vom bisherigen Verbrauch im
        # Fenster (reiner Funktionswert, keine Race-Moeglichkeit).
        if tokens > self._budget_per_hour:
            return False
        window = self._window_start()
        used = self._usage.get((api_key_hash, window), 0)
        if used + tokens > self._budget_per_hour:
            return False
        self._usage[(api_key_hash, window)] = used + tokens
        return True

    def remaining(self, api_key_hash: str) -> int:
        window = self._window_start()
        used = self._usage.get((api_key_hash, window), 0)
        return max(self._budget_per_hour - used, 0)

    def _window_start(self) -> datetime:
        now = self._clock.now()
        return now.replace(minute=0, second=0, microsecond=0)
