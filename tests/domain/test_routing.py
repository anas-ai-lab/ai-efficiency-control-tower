"""Tests fuer den AI-vs-Automation-Router (V4: Komplexitaet aus Umsetzungsansatz)."""

from __future__ import annotations

import dataclasses

import pytest

from aect.domain.models import UseCaseInput
from aect.domain.routing import RoutingRecommendation, route_use_case
from aect.domain.types import (
    AdoptionType,
    DataClassification,
    EmployeeCategory,
    EvidenceLevel,
    ImplementationApproach,
)

# ---------------------------------------------------------------------------
# Hilfsfunktion
# ---------------------------------------------------------------------------


def _use_case(**overrides: object) -> UseCaseInput:
    """Baut einen neutralen UseCaseInput; einzelne Felder ueberschreibbar.

    Default-Ansatz API_INTEGRATION -> Komplexitaet 3 (weder Automation- noch
    AI-Signal), damit einzelne Overrides die Routing-Signale isolieren.
    """
    defaults: dict[str, object] = {
        "title": "Test AI Router",
        "submitter": "Tester",
        "department": "IT",
        "country": "de",
        "current_state": (
            "Aktuell wird der Prozess vollstaendig manuell durchgefuehrt."
            " Das kostet viel Zeit und ist fehleranfaellig."
        ),
        "desired_state": "Nach Unterstuetzung soll der Prozess effizienter ablaufen.",
        "example_process": "Ein einzelner Vorgang dauert 30 Minuten und mehrere Schritte.",
        "time_per_case_hours_current": 0.5,
        "time_per_case_hours_with_ai": 0.0,
        "occurrences_per_employee_per_year": 500,
        "affected_employees_count": 3,
        "employee_category": EmployeeCategory.PROFESSIONAL,
        "evidence_level": EvidenceLevel.SIMILAR_PROJECT,
        "adoption_type": AdoptionType.VOLUNTARY,
        "implementation_approach": ImplementationApproach.API_INTEGRATION,
        "estimated_license_cost_eur": 0.0,
        "contains_pii": False,
        "data_classification": DataClassification.NO_PERSONAL_DATA,
        "regulatory_pressure": False,
        "competitive_pressure": False,
        "strategic_priority": False,
    }
    defaults.update(overrides)
    return UseCaseInput.model_validate(defaults)


# ---------------------------------------------------------------------------
# Struktur-Tests
# ---------------------------------------------------------------------------


class TestRoutingResultStruktur:
    @pytest.mark.unit
    def test_result_ist_frozen(self) -> None:
        result = route_use_case(_use_case())
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.recommendation = RoutingRecommendation.BORDERLINE  # type: ignore[misc]

    @pytest.mark.unit
    def test_signals_und_flags_sind_tuples(self) -> None:
        result = route_use_case(_use_case())
        assert isinstance(result.automation_signals, tuple)
        assert isinstance(result.ai_signals, tuple)
        assert isinstance(result.risk_flags, tuple)

    @pytest.mark.unit
    def test_confidence_ist_valider_wert(self) -> None:
        result = route_use_case(_use_case())
        assert result.confidence in {"HIGH", "MEDIUM", "LOW"}


# ---------------------------------------------------------------------------
# AUTOMATION_RECOMMENDED
# ---------------------------------------------------------------------------


class TestAutomationRecommended:
    @pytest.mark.unit
    def test_niedrige_komplexitaet_liefert_automation_signal(self) -> None:
        # SIMPLE_INTEGRATION -> Komplexitaet 1 (aus dem Ansatz abgeleitet, V4).
        result = route_use_case(
            _use_case(implementation_approach=ImplementationApproach.SIMPLE_INTEGRATION)
        )
        assert any("1" in s for s in result.automation_signals)

    @pytest.mark.unit
    def test_hohes_volumen_liefert_automation_signal(self) -> None:
        result = route_use_case(_use_case(occurrences_per_employee_per_year=5000))
        assert any("5000" in s for s in result.automation_signals)

    @pytest.mark.unit
    def test_fester_prozessschritt_liefert_automation_signal(self) -> None:
        result = route_use_case(
            _use_case(adoption_type=AdoptionType.FIXED_PROCESS_STEP)
        )
        assert any("Prozessschritt" in s for s in result.automation_signals)

    @pytest.mark.unit
    def test_eindeutig_automation_hohe_konfidenz(self) -> None:
        use_case = _use_case(
            implementation_approach=ImplementationApproach.SIMPLE_INTEGRATION,
            occurrences_per_employee_per_year=5000,
            adoption_type=AdoptionType.FIXED_PROCESS_STEP,
            evidence_level=EvidenceLevel.TESTED_PILOTED,
        )
        result = route_use_case(use_case)
        assert result.recommendation == RoutingRecommendation.AUTOMATION_RECOMMENDED
        assert result.confidence in {"HIGH", "MEDIUM"}
        assert len(result.ai_signals) == 0


# ---------------------------------------------------------------------------
# AI_RECOMMENDED
# ---------------------------------------------------------------------------


class TestAiRecommended:
    @pytest.mark.unit
    def test_hohe_komplexitaet_liefert_ai_signal(self) -> None:
        # CUSTOM_DEVELOPMENT -> Komplexitaet 4.
        result = route_use_case(
            _use_case(implementation_approach=ImplementationApproach.CUSTOM_DEVELOPMENT)
        )
        assert any("4" in s for s in result.ai_signals)

    @pytest.mark.unit
    def test_neues_tool_liefert_ai_signal_ueber_komplexitaet(self) -> None:
        # NEW_TOOL -> Komplexitaet 5 -> AI-Signal (Ansatz treibt die Komplexitaet).
        result = route_use_case(
            _use_case(implementation_approach=ImplementationApproach.NEW_TOOL)
        )
        assert any("5" in s for s in result.ai_signals)

    @pytest.mark.unit
    def test_pure_estimate_liefert_ai_signal(self) -> None:
        result = route_use_case(_use_case(evidence_level=EvidenceLevel.PURE_ESTIMATE))
        assert any("pure_estimate" in s for s in result.ai_signals)

    @pytest.mark.unit
    def test_eindeutig_ai_hohe_konfidenz(self) -> None:
        use_case = _use_case(
            implementation_approach=ImplementationApproach.CUSTOM_DEVELOPMENT,
            evidence_level=EvidenceLevel.PURE_ESTIMATE,
            occurrences_per_employee_per_year=100,  # kein Volumen-Signal
        )
        result = route_use_case(use_case)
        assert result.recommendation == RoutingRecommendation.AI_RECOMMENDED
        assert result.confidence in {"HIGH", "MEDIUM"}
        assert len(result.automation_signals) == 0


# ---------------------------------------------------------------------------
# HUMAN_REVIEW_REQUIRED
# ---------------------------------------------------------------------------


class TestHumanReviewRequired:
    @pytest.mark.unit
    def test_ein_risk_flag_setzt_requires_human_review(self) -> None:
        use_case = _use_case(
            data_classification=DataClassification.SENSITIVE_PERSONAL,
            contains_pii=True,
        )
        result = route_use_case(use_case)
        assert result.requires_human_review
        assert len(result.risk_flags) == 1

    @pytest.mark.unit
    def test_regulatory_plus_pii_setzt_risk_flag(self) -> None:
        use_case = _use_case(regulatory_pressure=True, contains_pii=True)
        result = route_use_case(use_case)
        assert result.requires_human_review

    @pytest.mark.unit
    def test_zwei_risk_flags_ergibt_human_review_required(self) -> None:
        use_case = _use_case(
            data_classification=DataClassification.SENSITIVE_PERSONAL,
            contains_pii=True,
            regulatory_pressure=True,
        )
        result = route_use_case(use_case)
        assert result.recommendation == RoutingRecommendation.HUMAN_REVIEW_REQUIRED
        assert result.confidence == "HIGH"
        assert len(result.risk_flags) == 2

    @pytest.mark.unit
    def test_ohne_risk_flags_kein_human_review_required(self) -> None:
        use_case = _use_case(
            data_classification=DataClassification.NO_PERSONAL_DATA,
            contains_pii=False,
            regulatory_pressure=False,
        )
        result = route_use_case(use_case)
        assert len(result.risk_flags) == 0
        assert result.recommendation != RoutingRecommendation.HUMAN_REVIEW_REQUIRED
        assert not result.requires_human_review


# ---------------------------------------------------------------------------
# BORDERLINE
# ---------------------------------------------------------------------------


class TestBorderline:
    @pytest.mark.unit
    def test_gleiche_signalanzahl_ergibt_borderline_oder_low(self) -> None:
        """Kein klares Signal -> BORDERLINE oder LOW-Konfidenz."""
        use_case = _use_case(
            implementation_approach=ImplementationApproach.API_INTEGRATION,  # Komplexitaet 3, kein Signal
            occurrences_per_employee_per_year=500,  # kein Signal
            adoption_type=AdoptionType.VOLUNTARY,
            evidence_level=EvidenceLevel.SIMILAR_PROJECT,
        )
        result = route_use_case(use_case)
        # Neutrale Eingabe -> BORDERLINE oder LOW confidence
        assert (
            result.confidence == "LOW"
            or result.recommendation == RoutingRecommendation.BORDERLINE
        )
