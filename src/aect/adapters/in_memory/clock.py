"""SystemClock -- implementiert ClockPort mit datetime.now(UTC)."""

from __future__ import annotations

from datetime import UTC, datetime


class SystemClock:
    """Liefert die echte Systemzeit in UTC.

    Implementiert ClockPort via strukturellem Subtyping (typing.Protocol):
    kein explizites Erben noetig -- mypy prueft die Kompatibilitaet statisch.
    """

    def now(self) -> datetime:
        return datetime.now(tz=UTC)
