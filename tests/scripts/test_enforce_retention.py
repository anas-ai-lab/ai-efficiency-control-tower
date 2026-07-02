"""Tests fuer scripts/enforce_retention.py (DSGVO Art. 5(1)(e) Retention, Phase G).

scripts/ liegt bewusst ausserhalb von src/aect (kein Package auf
pythonpath) -- Laden per importlib ueber den Dateipfad, analog
test_zone_threshold_backtest.py.

Mirrors tests/application/test_service.py::TestTriageServiceDelete
(_SpyRetriever-Pattern) -- dieselben Assertions wie die bestehenden
Deletion-Cascade-Tests, nur getriggert vom Script statt vom Endpoint.
"""

from __future__ import annotations

import datetime
import importlib.util
import sys
from pathlib import Path

from structlog.testing import capture_logs

from aect.adapters.in_memory.id_generator import UUIDGenerator
from aect.adapters.in_memory.llm import MockLLMAdapter
from aect.adapters.in_memory.repository import InMemoryRepository
from aect.adapters.sqlite.repository import SQLiteRepository
from aect.application.ports.retriever import RetrievedChunk
from aect.application.service import TriageService
from aect.domain import UseCaseInput
from aect.domain.roi import ROIConfig

REPO_ROOT = Path(__file__).parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "enforce_retention.py"
_MODULE_NAME = "enforce_retention"


def _load_script_module():
    spec = importlib.util.spec_from_file_location(_MODULE_NAME, SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


class _MutableClock:
    """Testbarer Clock mit veraenderbarer Zeit -- kein echtes Warten noetig."""

    def __init__(self, now: datetime.datetime) -> None:
        self._now = now

    def now(self) -> datetime.datetime:
        return self._now

    def advance(self, delta: datetime.timedelta) -> None:
        self._now += delta


class _SpyRetriever:
    """Zeichnet delete_by_source_id-Aufrufe auf -- identisch zu
    tests/application/test_service.py::_SpyRetriever."""

    def __init__(self) -> None:
        self.deleted: list[str] = []

    async def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        return []

    async def delete_by_source_id(self, source_id: str) -> None:
        self.deleted.append(source_id)


# ---------------------------------------------------------------------------
# find_expired_case_ids -- reine Funktion, kein I/O
# ---------------------------------------------------------------------------


def test_find_expired_case_ids_filters_by_submitted_at(
    sample_use_case: UseCaseInput, roi_config: ROIConfig
) -> None:
    module = _load_script_module()
    clock = _MutableClock(datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC))
    service = TriageService(
        repository=InMemoryRepository(),
        clock=clock,
        id_generator=UUIDGenerator(),
        roi_config=roi_config,
        llm=MockLLMAdapter(),
        retriever=_SpyRetriever(),
    )
    old_case = service.submit_use_case(sample_use_case)  # submitted_at = 2026-01-01

    clock.advance(datetime.timedelta(days=95))
    boundary_case = service.submit_use_case(sample_use_case)  # 95 Tage vor "jetzt"

    clock.advance(datetime.timedelta(days=5))  # jetzt = 2026-01-01 + 100 Tage

    # old_case ist 100 Tage alt (> 90), boundary_case exakt 5 Tage alt (< 90).
    result = module.find_expired_case_ids(
        service.list_cases(), clock, retention_days=90
    )
    assert result == [old_case.id]
    assert boundary_case.id not in result


def test_find_expired_case_ids_keeps_case_exactly_at_boundary(
    sample_use_case: UseCaseInput, roi_config: ROIConfig
) -> None:
    """Ein Case, der exakt retention_days alt ist, gilt NICHT als abgelaufen
    ("aelter als", nicht "mindestens so alt wie")."""
    module = _load_script_module()
    clock = _MutableClock(datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC))
    service = TriageService(
        repository=InMemoryRepository(),
        clock=clock,
        id_generator=UUIDGenerator(),
        roi_config=roi_config,
        llm=MockLLMAdapter(),
        retriever=_SpyRetriever(),
    )
    case = service.submit_use_case(sample_use_case)

    clock.advance(datetime.timedelta(days=90))  # jetzt = exakt 90 Tage spaeter

    result = module.find_expired_case_ids(
        service.list_cases(), clock, retention_days=90
    )
    assert result == []
    assert case.id not in result


# ---------------------------------------------------------------------------
# enforce_retention -- End-zu-Ende ueber SQLiteRepository + Spy-Retriever
# ---------------------------------------------------------------------------


async def test_enforce_retention_deletes_expired_cases_from_sqlite_and_chromadb(
    tmp_path: Path, sample_use_case: UseCaseInput, roi_config: ROIConfig
) -> None:
    module = _load_script_module()
    clock = _MutableClock(datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC))
    repo = SQLiteRepository(tmp_path / "retention.db")
    spy = _SpyRetriever()
    service = TriageService(
        repository=repo,
        clock=clock,
        id_generator=UUIDGenerator(),
        roi_config=roi_config,
        llm=MockLLMAdapter(),
        retriever=spy,
    )
    old_case = service.submit_use_case(sample_use_case)

    clock.advance(datetime.timedelta(days=50))
    recent_case = service.submit_use_case(sample_use_case)

    clock.advance(datetime.timedelta(days=45))  # old=95 Tage, recent=45 Tage

    deleted = await module.enforce_retention(
        service, clock, retention_days=90, dry_run=False
    )

    assert deleted == [old_case.id]
    # SQLite-Row weg.
    assert repo.get(old_case.id) is None
    assert repo.get(recent_case.id) is not None
    # ChromaDB-Loeschung angestossen (Spy zeichnet den source_id-Aufruf auf).
    assert spy.deleted == [old_case.id]


async def test_enforce_retention_dry_run_deletes_nothing(
    tmp_path: Path, sample_use_case: UseCaseInput, roi_config: ROIConfig
) -> None:
    module = _load_script_module()
    clock = _MutableClock(datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC))
    repo = SQLiteRepository(tmp_path / "retention.db")
    spy = _SpyRetriever()
    service = TriageService(
        repository=repo,
        clock=clock,
        id_generator=UUIDGenerator(),
        roi_config=roi_config,
        llm=MockLLMAdapter(),
        retriever=spy,
    )
    old_case = service.submit_use_case(sample_use_case)
    clock.advance(datetime.timedelta(days=95))

    listed = await module.enforce_retention(
        service, clock, retention_days=90, dry_run=True
    )

    assert listed == [old_case.id]
    assert repo.get(old_case.id) is not None  # unveraendert, nichts geloescht
    assert spy.deleted == []


async def test_enforce_retention_logs_structured_event_without_freetext(
    tmp_path: Path, sample_use_case: UseCaseInput, roi_config: ROIConfig
) -> None:
    """PII-Allowlist-konform: nur case_count/case_ids, kein Freitext-Inhalt."""
    module = _load_script_module()
    clock = _MutableClock(datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC))
    repo = SQLiteRepository(tmp_path / "retention.db")
    service = TriageService(
        repository=repo,
        clock=clock,
        id_generator=UUIDGenerator(),
        roi_config=roi_config,
        llm=MockLLMAdapter(),
        retriever=_SpyRetriever(),
    )
    old_case = service.submit_use_case(sample_use_case)
    clock.advance(datetime.timedelta(days=95))

    with capture_logs() as logs:
        await module.enforce_retention(service, clock, retention_days=90, dry_run=False)

    events = [e for e in logs if e.get("event") == "retention_enforced"]
    assert len(events) == 1
    assert events[0]["case_count"] == 1
    assert events[0]["case_ids"] == [old_case.id]
    assert set(events[0]) <= {"event", "log_level", "case_count", "case_ids"}


async def test_enforce_retention_no_expired_cases_is_noop(
    tmp_path: Path, sample_use_case: UseCaseInput, roi_config: ROIConfig
) -> None:
    module = _load_script_module()
    clock = _MutableClock(datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC))
    repo = SQLiteRepository(tmp_path / "retention.db")
    spy = _SpyRetriever()
    service = TriageService(
        repository=repo,
        clock=clock,
        id_generator=UUIDGenerator(),
        roi_config=roi_config,
        llm=MockLLMAdapter(),
        retriever=spy,
    )
    case = service.submit_use_case(sample_use_case)

    deleted = await module.enforce_retention(
        service, clock, retention_days=90, dry_run=False
    )

    assert deleted == []
    assert repo.get(case.id) is not None
    assert spy.deleted == []
