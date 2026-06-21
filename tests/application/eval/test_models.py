"""Tests fuer das EvalCase-Schema (Master-Plan v3.1 Phase E, ADR-0029)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from aect.application.eval import EvalCase
from aect.domain import TriageZone, UseCaseInput


def test_eval_case_accepts_valid_use_case(sample_use_case: UseCaseInput) -> None:
    case = EvalCase(case_id="t-001", use_case=sample_use_case)
    assert case.case_id == "t-001"
    assert case.expected_zone is None
    assert case.notes == ""


def test_eval_case_accepts_expected_zone(sample_use_case: UseCaseInput) -> None:
    case = EvalCase(
        case_id="t-002",
        use_case=sample_use_case,
        expected_zone=TriageZone.LIKELY_WIN,
        notes="Klarer Fall.",
    )
    assert case.expected_zone is TriageZone.LIKELY_WIN


def test_eval_case_rejects_unknown_field(sample_use_case: UseCaseInput) -> None:
    with pytest.raises(ValidationError):
        EvalCase(case_id="t-003", use_case=sample_use_case, unexpected_field="x")  # type: ignore[call-arg]


def test_eval_case_requires_case_id(sample_use_case: UseCaseInput) -> None:
    with pytest.raises(ValidationError):
        EvalCase(use_case=sample_use_case)  # type: ignore[call-arg]
