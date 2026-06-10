"""ClockPort -- testbarer Zeitstempel-Lieferant."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol


class ClockPort(Protocol):
    """Liefert den aktuellen Zeitstempel.

    Warum ein Port? Direkte datetime.now()-Aufrufe im Service machen Tests
    nicht-deterministisch. FakeClock im Test gibt feste Zeiten zurueck.
    """

    def now(self) -> datetime: ...
