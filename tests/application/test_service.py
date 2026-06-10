"""Tests fuer TriageService -- demonstriert Dependency Inversion in Aktion."""

from __future__ import annotations

import datetime

from aect.adapters.in_memory.repository import InMemoryRepository
from aect.application.models import SubmittedCase
from aect.application.service import TriageService
from aect.domain import UseCaseInput
from aect.domain.roi import ROIConfig

# ---------------------------------------------------------------------------
# Fake-Implementierungen (kein Mocking-Framework -- strukturelles Subtyping)
# ---------------------------------------------------------------------------
_FIXED_TIME = datetime.datetime(2026, 6, 10, 10, 0, 0, tzinfo=datetime.UTC)


class _FakeClock:
    """Liefert immer denselben Zeitstempel -- macht Tests deterministisch."""

    def __init__(self, fixed: datetime.datetime = _FIXED_TIME) -> None:
        self._fixed = fixed

    def now(self) -> datetime.datetime:
        return self._fixed


class _FakeIdGenerator:
    """Gibt IDs aus einer vordefinierten Liste zurueck -- vorhersagbar fuer Assertions."""

    def __init__(self, ids: list[str]) -> None:
        self._iter = iter(ids)

    def generate(self) -> str:
        return next(self._iter)


# ---------------------------------------------------------------------------
# Hilfsfunktion: Service mit vollstaendig kontrollierten Abhaengigkeiten
# ---------------------------------------------------------------------------
def _make_service(
    roi_config: ROIConfig,
    ids: list[str] | None = None,
) -> tuple[TriageService, InMemoryRepository]:
    repo = InMemoryRepository()
    service = TriageService(
        repository=repo,
        clock=_FakeClock(),
        id_generator=_FakeIdGenerator(ids=ids or ["id-001", "id-002", "id-003"]),
        roi_config=roi_config,
    )
    return service, repo


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class TestTriageServiceSubmit:
    def test_returns_submitted_case_with_expected_fields(
        self, sample_use_case: UseCaseInput, roi_config: ROIConfig
    ) -> None:
        service, _ = _make_service(roi_config)
        case = service.submit_use_case(sample_use_case)

        assert isinstance(case, SubmittedCase)
        assert case.id == "id-001"
        assert case.submitted_at == _FIXED_TIME
        assert case.use_case is sample_use_case

    def test_result_title_matches_input_title(
        self, sample_use_case: UseCaseInput, roi_config: ROIConfig
    ) -> None:
        service, _ = _make_service(roi_config)
        case = service.submit_use_case(sample_use_case)
        assert case.result.title == sample_use_case.title

    def test_case_is_persisted_after_submit(
        self, sample_use_case: UseCaseInput, roi_config: ROIConfig
    ) -> None:
        service, repo = _make_service(roi_config)
        service.submit_use_case(sample_use_case)
        assert repo.get("id-001") is not None


class TestTriageServiceGet:
    def test_get_returns_correct_case(
        self, sample_use_case: UseCaseInput, roi_config: ROIConfig
    ) -> None:
        service, _ = _make_service(roi_config)
        submitted = service.submit_use_case(sample_use_case)
        retrieved = service.get_case(submitted.id)
        assert retrieved is not None
        assert retrieved.id == submitted.id

    def test_get_nonexistent_id_returns_none(self, roi_config: ROIConfig) -> None:
        service, _ = _make_service(roi_config)
        assert service.get_case("does-not-exist") is None


class TestTriageServiceList:
    def test_list_empty_initially(self, roi_config: ROIConfig) -> None:
        service, _ = _make_service(roi_config)
        assert service.list_cases() == []

    def test_list_contains_all_submitted_cases(
        self, sample_use_case: UseCaseInput, roi_config: ROIConfig
    ) -> None:
        service, _ = _make_service(roi_config, ids=["a", "b"])
        service.submit_use_case(sample_use_case)
        service.submit_use_case(sample_use_case)
        assert len(service.list_cases()) == 2
