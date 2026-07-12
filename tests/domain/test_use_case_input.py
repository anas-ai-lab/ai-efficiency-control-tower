"""Tests für UseCaseInput — Pydantic V2 Validierung."""

import pytest
from pydantic import ValidationError

from aect.domain.models import UseCaseInput
from aect.domain.types import (
    DataClassification,
    EvidenceLevel,
)

# Zentrale Fixture — alle Pflichtfelder korrekt befüllt.
# Wird in Validierungs-Tests via {**VALID_PAYLOAD, "feld": "ungültig"} überschrieben.
VALID_PAYLOAD: dict = {
    "title": "Automatische Rechnungsprüfung im AP-Prozess",
    "submitter": "Maria Muster",
    "department": "Finanzen",
    "country": "de",
    "current_state": "Rechnungen werden manuell geprüft, 3 FTEs, durchschnittlich 2 Stunden pro Rechnung",
    "desired_state": "KI prüft Rechnungen vor, Mensch entscheidet nur noch bei Ausreißern und Grenzfällen",
    "example_process": "Eingehende Rechnung → PDF-Extraktion → Regelprüfung → Freigabe",
    "time_per_case_hours_current": 0.4,
    "time_per_case_hours_with_ai": 0.2,
    "occurrences_per_employee_per_year": 7200,
    "affected_employees_count": 6,
    "employee_category": "professional",
    "evidence_level": "pure_estimate",
    "adoption_type": "fixed_process_step",
    "implementation_approach": "api_integration",
    "data_classification": "personal",
}


class TestUseCaseInputValideEingaben:
    """Happy-Path: gültige Eingaben müssen durchgehen."""

    def test_minimale_pflichtfelder(self) -> None:
        model = UseCaseInput.model_validate(VALID_PAYLOAD)
        assert model.title == "Automatische Rechnungsprüfung im AP-Prozess"
        assert model.contains_pii is False
        # evidence_level ist seit V4.1 Pflicht (kein Default) -- der Wert kommt
        # explizit aus VALID_PAYLOAD (ADR-0050).
        assert model.evidence_level is EvidenceLevel.PURE_ESTIMATE
        assert model.estimated_license_cost_eur == 0.0

    def test_alle_felder_gueltig(self) -> None:
        model = UseCaseInput.model_validate(
            {
                **VALID_PAYLOAD,
                "contains_pii": True,
                "evidence_level": "similar_project",
                "estimated_license_cost_eur": 18_000.0,
                "regulatory_pressure": True,
                "competitive_pressure": True,
                "strategic_priority": True,
            }
        )
        assert model.contains_pii is True
        assert model.evidence_level is EvidenceLevel.SIMILAR_PROJECT
        assert model.regulatory_pressure is True

    def test_alle_evidence_levels_akzeptiert(self) -> None:
        for level in EvidenceLevel:
            model = UseCaseInput.model_validate(
                {**VALID_PAYLOAD, "evidence_level": level.value}
            )
            assert model.evidence_level is level

    def test_alle_data_classifications_akzeptiert(self) -> None:
        for dc in DataClassification:
            model = UseCaseInput.model_validate(
                {**VALID_PAYLOAD, "data_classification": dc.value}
            )
            assert model.data_classification is dc


class TestUseCaseInputValidierung:
    """Validierungsfehler müssen korrekt ausgelöst werden."""

    def test_leerer_title_wird_abgelehnt(self) -> None:
        with pytest.raises(ValidationError):
            UseCaseInput.model_validate({**VALID_PAYLOAD, "title": ""})

    def test_title_zu_lang_wird_abgelehnt(self) -> None:
        with pytest.raises(ValidationError):
            UseCaseInput.model_validate({**VALID_PAYLOAD, "title": "x" * 201})

    def test_current_state_zu_lang_wird_abgelehnt(self) -> None:
        with pytest.raises(ValidationError):
            UseCaseInput.model_validate({**VALID_PAYLOAD, "current_state": "x" * 2001})

    def test_extra_felder_werden_abgelehnt(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            UseCaseInput.model_validate(
                {**VALID_PAYLOAD, "unbekanntes_feld": "sollte nicht gehen"}
            )
        assert any(e["type"] == "extra_forbidden" for e in exc_info.value.errors())

    def test_current_time_null_wird_abgelehnt(self) -> None:
        # time_per_case_hours_current muss > 0 sein (ein Vorgang dauert Zeit).
        with pytest.raises(ValidationError):
            UseCaseInput.model_validate(
                {**VALID_PAYLOAD, "time_per_case_hours_current": 0.0}
            )

    def test_current_time_ueber_8h_wird_abgelehnt(self) -> None:
        with pytest.raises(ValidationError):
            UseCaseInput.model_validate(
                {**VALID_PAYLOAD, "time_per_case_hours_current": 8.01}
            )

    def test_with_ai_time_negativ_wird_abgelehnt(self) -> None:
        with pytest.raises(ValidationError):
            UseCaseInput.model_validate(
                {**VALID_PAYLOAD, "time_per_case_hours_with_ai": -0.1}
            )

    def test_with_ai_time_null_ist_gueltig(self) -> None:
        # with_ai == 0 ist erlaubt (volle Automatisierung des Vorgangs).
        model = UseCaseInput.model_validate(
            {**VALID_PAYLOAD, "time_per_case_hours_with_ai": 0.0}
        )
        assert model.time_per_case_hours_with_ai == 0.0

    def test_negative_occurrences_wird_abgelehnt(self) -> None:
        with pytest.raises(ValidationError):
            UseCaseInput.model_validate(
                {**VALID_PAYLOAD, "occurrences_per_employee_per_year": -100}
            )

    def test_occurrences_null_wird_abgelehnt(self) -> None:
        with pytest.raises(ValidationError):
            UseCaseInput.model_validate(
                {**VALID_PAYLOAD, "occurrences_per_employee_per_year": 0}
            )

    def test_ungueltige_adoption_type_wird_abgelehnt(self) -> None:
        with pytest.raises(ValidationError):
            UseCaseInput.model_validate({**VALID_PAYLOAD, "adoption_type": "optional"})

    # -- Governance-Pflichtfelder ohne Default (V4.1, ADR-0050) --------------

    def test_evidence_level_ist_pflicht(self) -> None:
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "evidence_level"}
        with pytest.raises(ValidationError):
            UseCaseInput.model_validate(payload)

    def test_data_classification_ist_pflicht(self) -> None:
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "data_classification"}
        with pytest.raises(ValidationError):
            UseCaseInput.model_validate(payload)

    def test_adoption_type_ist_pflicht(self) -> None:
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "adoption_type"}
        with pytest.raises(ValidationError):
            UseCaseInput.model_validate(payload)

    def test_implementation_approach_ist_optional(self) -> None:
        # V4.1 (ADR-0050): ohne Ansatz ist der Input gueltig (None) -- der Case
        # landet dann im Vor-Bewertungs-Zustand.
        payload = {
            k: v for k, v in VALID_PAYLOAD.items() if k != "implementation_approach"
        }
        model = UseCaseInput.model_validate(payload)
        assert model.implementation_approach is None


class TestUseCaseInputImmutability:
    """frozen=True — Instanzen sind nach Erstellung unveränderlich."""

    def test_zuweisung_nach_erstellung_wirft_fehler(self) -> None:
        model = UseCaseInput.model_validate(VALID_PAYLOAD)
        with pytest.raises(ValidationError):
            model.title = "Mutation"  # type: ignore[misc]


class TestUseCaseInputModelValidate:
    """model_validate() vs. direkter Konstruktor — Verhalten bei Dict-Input."""

    def test_model_validate_aus_dict(self) -> None:
        model = UseCaseInput.model_validate(VALID_PAYLOAD)
        assert model.title == "Automatische Rechnungsprüfung im AP-Prozess"
