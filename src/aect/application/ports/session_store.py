"""SessionStorePort -- Persistenz-Abstraktion fuer Admin-Login-Sessions.

Bildet ab: token_hash (sha256 des Session-Tokens) -> Ablaufzeitpunkt. Das
Klartext-Token wird NIE gespeichert -- nur sein sha256-Hash, analog dem
api_key_hash-Muster (key_fingerprint in dependencies.py). Ein Leak der
Session-Tabelle gibt damit keine gueltigen Tokens preis.

Der Application Service (TriageService) kennt dieses Interface nicht -- Sessions
sind ein reines HTTP-/Auth-Anliegen der Adapter-Schicht (analog
IdempotencyStorePort). Der Port liegt hier nur, weil er wie die uebrigen Stores
(Idempotency, Token-Budget) ueber FastAPI-DI mit In-Memory-/SQLite-Adaptern
verdrahtet wird.

Ablauf-Semantik: get() liefert die Session unabhaengig vom Ablauf zurueck; die
Ablaufpruefung (und das Verwerfen abgelaufener Sessions) macht der Aufrufer
(require_admin) gegen die Clock -- so bleibt der Store frei von Zeitlogik und
bleibt deterministisch testbar.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class AdminSession:
    """Eine Admin-Login-Session (nur der Token-Hash, nie das Klartext-Token)."""

    token_hash: str
    created_at: datetime
    expires_at: datetime


class SessionStorePort(Protocol):
    """Speichert und liest Admin-Sessions ueber ihren token_hash.

    Aktuelle Impl.: InMemorySessionStore (Dev/Test), SQLiteSessionStore
    (persistent, gleiche DB-Datei wie SQLiteRepository).
    """

    def create(self, session: AdminSession) -> None:
        """Legt eine neue Session an (token_hash ist Primary Key)."""
        ...

    def get(self, token_hash: str) -> AdminSession | None:
        """Liefert die Session zum token_hash oder None. Ohne Ablaufpruefung."""
        ...

    def delete(self, token_hash: str) -> None:
        """Loescht eine Session (Logout oder abgelaufen). No-op, wenn fehlend."""
        ...
