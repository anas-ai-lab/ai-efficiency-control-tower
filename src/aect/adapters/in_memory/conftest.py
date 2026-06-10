"""Fixtures fuer In-Memory-Adapter-Tests."""

from __future__ import annotations

import datetime

import pytest

from aect.adapters.in_memory.repository import InMemoryRepository
from aect.application.models import SubmittedCase
from aect.domain import UseCaseInput, evaluate_use_case
from aect.domain.roi import ROIConfig


@pytest.fixture
def in_memory_repo() -> InMemoryRepository:
    """Leeres InMemoryRepository fuer jeden Test -- frischer State."""
    return InMemoryRepository()


@pytest.fixture
def submitted_case(
    sample_use_case: UseCaseInput, roi_config: ROIConfig
) -> SubmittedCase:
    """Fertiger SubmittedCase auf Basis des sample_use_case."""
    result = evaluate_use_case(sample_use_case, roi_config)
    return SubmittedCase(
        id="fixture-case-001",
        submitted_at=datetime.datetime(2026, 6, 10, 12, 0, 0, tzinfo=datetime.UTC),
        use_case=sample_use_case,
        result=result,
    )
