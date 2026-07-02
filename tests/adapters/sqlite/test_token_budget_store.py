"""Unit-Tests fuer SQLiteTokenBudgetStore (TokenBudgetPort, Fixed-Window/Stunde)."""

from __future__ import annotations

import datetime
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from aect.adapters.sqlite.token_budget_store import SQLiteTokenBudgetStore

_START = datetime.datetime(2026, 7, 2, 10, 15, 0, tzinfo=datetime.UTC)


class _MutableClock:
    """Testbarer Clock mit veraenderbarer Zeit -- kein echtes Warten noetig."""

    def __init__(self, now: datetime.datetime) -> None:
        self._now = now

    def now(self) -> datetime.datetime:
        return self._now

    def advance(self, delta: datetime.timedelta) -> None:
        self._now += delta


def test_try_consume_within_budget_succeeds(tmp_path: Path) -> None:
    store = SQLiteTokenBudgetStore(
        tmp_path / "budget.db", _MutableClock(_START), budget_per_hour=100
    )
    assert store.try_consume("hash-a", 60) is True
    assert store.remaining("hash-a") == 40


def test_try_consume_accumulates_across_calls(tmp_path: Path) -> None:
    store = SQLiteTokenBudgetStore(
        tmp_path / "budget.db", _MutableClock(_START), budget_per_hour=100
    )
    store.try_consume("hash-a", 60)
    assert store.try_consume("hash-a", 30) is True
    assert store.remaining("hash-a") == 10


def test_try_consume_rejects_when_over_budget(tmp_path: Path) -> None:
    store = SQLiteTokenBudgetStore(
        tmp_path / "budget.db", _MutableClock(_START), budget_per_hour=100
    )
    store.try_consume("hash-a", 60)
    assert store.try_consume("hash-a", 50) is False
    assert store.remaining("hash-a") == 40  # unveraendert, nichts verbucht


def test_single_request_exceeding_whole_budget_is_rejected(tmp_path: Path) -> None:
    """Ein brandneuer Key mit einer Anfrage, die allein schon groesser als
    das Stundenbudget ist -- das plaine INSERT im Konfliktfreien Zweig
    ignoriert die WHERE-Klausel, deshalb der explizite Pre-Check."""
    store = SQLiteTokenBudgetStore(
        tmp_path / "budget.db", _MutableClock(_START), budget_per_hour=100
    )
    assert store.try_consume("hash-new", 150) is False
    assert store.remaining("hash-new") == 100


def test_exactly_at_budget_is_accepted(tmp_path: Path) -> None:
    store = SQLiteTokenBudgetStore(
        tmp_path / "budget.db", _MutableClock(_START), budget_per_hour=100
    )
    assert store.try_consume("hash-a", 100) is True
    assert store.remaining("hash-a") == 0


def test_keys_have_independent_budgets(tmp_path: Path) -> None:
    store = SQLiteTokenBudgetStore(
        tmp_path / "budget.db", _MutableClock(_START), budget_per_hour=100
    )
    store.try_consume("hash-a", 90)
    assert store.try_consume("hash-b", 90) is True
    assert store.remaining("hash-a") == 10
    assert store.remaining("hash-b") == 10


def test_budget_resets_after_window_rollover(tmp_path: Path) -> None:
    clock = _MutableClock(_START)
    store = SQLiteTokenBudgetStore(tmp_path / "budget.db", clock, budget_per_hour=100)
    store.try_consume("hash-a", 90)
    assert store.remaining("hash-a") == 10

    clock.advance(datetime.timedelta(hours=1))
    assert store.remaining("hash-a") == 100
    assert store.try_consume("hash-a", 90) is True


def test_persists_across_instances(tmp_path: Path) -> None:
    """Neue Instanz auf gleicher DB-Datei sieht denselben Verbrauch (Persistenz)."""
    db_path = tmp_path / "budget.db"
    SQLiteTokenBudgetStore(
        db_path, _MutableClock(_START), budget_per_hour=100
    ).try_consume("hash-a", 60)
    reopened = SQLiteTokenBudgetStore(
        db_path, _MutableClock(_START), budget_per_hour=100
    )
    assert reopened.remaining("hash-a") == 40


def test_try_consume_is_atomic_under_parallel_access(tmp_path: Path) -> None:
    """Budget=100, 8 Threads verbrauchen je 20 Tokens gleichzeitig -- genau 5
    duerfen gewinnen (5*20=100), 3 muessen abgelehnt werden. Ein GET-dann-SET
    (der alte F-010/F-011-Fehler) wuerde hier regelmaessig mehr als 5
    gewinnen lassen, weil parallele Reads denselben veralteten Stand sehen."""
    store = SQLiteTokenBudgetStore(
        tmp_path / "budget.db", _MutableClock(_START), budget_per_hour=100
    )
    barrier = threading.Barrier(8)

    def try_spend() -> bool:
        barrier.wait(timeout=5)
        return store.try_consume("hash-race", 20)

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: try_spend(), range(8)))

    assert sum(results) == 5
    assert store.remaining("hash-race") == 0
