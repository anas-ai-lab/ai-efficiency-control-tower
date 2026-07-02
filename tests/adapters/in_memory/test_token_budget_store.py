"""Unit-Tests fuer InMemoryTokenBudgetStore (TokenBudgetPort, Fixed-Window/Stunde)."""

from __future__ import annotations

import datetime

from aect.adapters.in_memory.token_budget_store import InMemoryTokenBudgetStore

_START = datetime.datetime(2026, 7, 2, 10, 15, 0, tzinfo=datetime.UTC)


class _MutableClock:
    """Testbarer Clock mit veraenderbarer Zeit -- kein echtes Warten noetig."""

    def __init__(self, now: datetime.datetime) -> None:
        self._now = now

    def now(self) -> datetime.datetime:
        return self._now

    def advance(self, delta: datetime.timedelta) -> None:
        self._now += delta


def test_try_consume_within_budget_succeeds() -> None:
    store = InMemoryTokenBudgetStore(_MutableClock(_START), budget_per_hour=100)
    assert store.try_consume("hash-a", 60) is True
    assert store.remaining("hash-a") == 40


def test_try_consume_accumulates_across_calls() -> None:
    store = InMemoryTokenBudgetStore(_MutableClock(_START), budget_per_hour=100)
    store.try_consume("hash-a", 60)
    assert store.try_consume("hash-a", 30) is True
    assert store.remaining("hash-a") == 10


def test_try_consume_rejects_when_over_budget() -> None:
    store = InMemoryTokenBudgetStore(_MutableClock(_START), budget_per_hour=100)
    store.try_consume("hash-a", 60)
    assert store.try_consume("hash-a", 50) is False
    assert store.remaining("hash-a") == 40  # unveraendert, nichts verbucht


def test_single_request_exceeding_whole_budget_is_rejected() -> None:
    """Ein brandneuer Key mit einer Anfrage, die allein schon groesser als
    das Stundenbudget ist -- muss abgelehnt werden, nicht teilweise verbucht."""
    store = InMemoryTokenBudgetStore(_MutableClock(_START), budget_per_hour=100)
    assert store.try_consume("hash-new", 150) is False
    assert store.remaining("hash-new") == 100


def test_exactly_at_budget_is_accepted() -> None:
    store = InMemoryTokenBudgetStore(_MutableClock(_START), budget_per_hour=100)
    assert store.try_consume("hash-a", 100) is True
    assert store.remaining("hash-a") == 0


def test_keys_have_independent_budgets() -> None:
    store = InMemoryTokenBudgetStore(_MutableClock(_START), budget_per_hour=100)
    store.try_consume("hash-a", 90)
    assert store.try_consume("hash-b", 90) is True
    assert store.remaining("hash-a") == 10
    assert store.remaining("hash-b") == 10


def test_budget_resets_after_window_rollover() -> None:
    clock = _MutableClock(_START)
    store = InMemoryTokenBudgetStore(clock, budget_per_hour=100)
    store.try_consume("hash-a", 90)
    assert store.remaining("hash-a") == 10

    clock.advance(datetime.timedelta(hours=1))
    assert store.remaining("hash-a") == 100
    assert store.try_consume("hash-a", 90) is True


def test_remaining_never_negative() -> None:
    store = InMemoryTokenBudgetStore(_MutableClock(_START), budget_per_hour=100)
    store.try_consume("hash-a", 100)
    store.try_consume("hash-a", 50)  # abgelehnt, No-op
    assert store.remaining("hash-a") == 0
