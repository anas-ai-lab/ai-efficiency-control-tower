"""SQLiteTokenBudgetStore -- implementiert TokenBudgetPort mit SQLite.

Fixed-Window pro Stunde, persistente Tabelle (api_key_hash, window_start,
tokens_used). Atomarer Budget-Check via ein einzelnes
INSERT ... ON CONFLICT DO UPDATE ... WHERE-Statement -- kein GET-dann-SET
(F-010/F-011: genau dieses Muster war die Race-Ursache bei Idempotency-Keys
bzw. Case-Narrativen; hier von Anfang an vermieden statt nachtraeglich
gefixt). WAL-Mode + busy_timeout ueber connection.connect() (F-013,
konsistent mit den anderen SQLite-Adaptern).
"""

from __future__ import annotations

from pathlib import Path

from aect.adapters.sqlite.connection import connect
from aect.application.ports.clock import ClockPort

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS token_budget (
    api_key_hash TEXT NOT NULL,
    window_start TEXT NOT NULL,
    tokens_used  INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (api_key_hash, window_start)
)
"""

# ON CONFLICT DO UPDATE ... WHERE: die UPDATE-Zweig laeuft nur, wenn die
# Bedingung haelt -- schlaegt sie fehl, ist das Statement ein No-op
# (rowcount=0), kein Fehler. Fuer eine bereits existierende Zeile ist das
# atomar: kein anderer Prozess kann zwischen Lesen und Schreiben eingreifen,
# weil beides EIN SQL-Statement ist (empirisch verifiziert, siehe
# Commit-Message). Fuer eine BRANDNEUE Zeile (kein Konflikt) greift die
# WHERE-Bedingung nicht -- deshalb der Pre-Check in try_consume() unten.
_TRY_CONSUME_SQL = """
INSERT INTO token_budget (api_key_hash, window_start, tokens_used)
VALUES (?, ?, ?)
ON CONFLICT(api_key_hash, window_start) DO UPDATE SET
    tokens_used = tokens_used + excluded.tokens_used
WHERE tokens_used + excluded.tokens_used <= ?
"""


class SQLiteTokenBudgetStore:
    """SQLite-Backend fuer stuendliche Token-Budgets pro API-Key-Hash.

    Jede DB-Operation oeffnet eine eigene, kurzlebige Verbindung ueber
    connection.connect() (WAL, busy_timeout=5000, explizites close) --
    kein geteilter State, analog SQLiteRepository/SQLiteIdempotencyStore.
    """

    def __init__(self, db_path: Path, clock: ClockPort, budget_per_hour: int) -> None:
        self._db_path = db_path
        self._clock = clock
        self._budget_per_hour = budget_per_hour
        self._init_db()

    def _init_db(self) -> None:
        with connect(self._db_path) as conn:
            conn.execute(_CREATE_TABLE_SQL)

    def _window_start_iso(self) -> str:
        now = self._clock.now()
        return now.replace(minute=0, second=0, microsecond=0).isoformat()

    def try_consume(self, api_key_hash: str, tokens: int) -> bool:
        # Eine Einzelanfrage, die schon allein das Stundenbudget sprengt:
        # das INSERT im brandneuen (Key, Fenster)-Fall unten ist
        # unconditional (die WHERE-Klausel gilt nur fuer den UPDATE-Zweig
        # bei einem Konflikt) -- ohne diesen Check wuerde der erste Request
        # in einem Fenster IMMER durchgehen, egal wie gross tokens ist.
        if tokens > self._budget_per_hour:
            return False
        window = self._window_start_iso()
        with connect(self._db_path) as conn:
            cursor = conn.execute(
                _TRY_CONSUME_SQL,
                (api_key_hash, window, tokens, self._budget_per_hour),
            )
            return cursor.rowcount == 1

    def remaining(self, api_key_hash: str) -> int:
        window = self._window_start_iso()
        with connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT tokens_used FROM token_budget "
                "WHERE api_key_hash = ? AND window_start = ?",
                (api_key_hash, window),
            ).fetchone()
        used = row[0] if row else 0
        return max(self._budget_per_hour - used, 0)
