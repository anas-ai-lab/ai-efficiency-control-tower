"""Tests für UseCaseInput — TDD: erst Tests, dann Implementation."""

import pytest
from pydantic import ValidationError

from aect.domain.models import EvidenceQuality, UseCaseInput


class TestUseCaseInputValideEingaben:
    """Happy-Path: gültige Eingaben müssen durchgehen."""

    def test_minimale_pflichtfelder(self) -> None:
        """Nur Pflichtfelder — alle optionalen Felder fehlen."""
        uc = UseCaseInput(
            title="Automatische Rechnungsprüfung",
            submitter="Maria Muster",
            department="Finanzen",
            current_state="Rechnungen werden manuell geprüft, 3 FTEs, 2h/Rechnung",
            desired_state="KI prüft Rechnungen vor, Mensch entscheidet nur noch bei Ausreißern",
            example_process="Eingehende Rechnung → PDF-Extraktion → Regelprüfung → Freigabe",
        )
        assert uc.title == "Automatische Rechnungsprüfung"
        assert uc.contains_pii is False  # sicherer Default

    def test_alle_felder_gueltig(self) -> None:
        """Vollständige Eingabe mit allen optionalen Feldern."""
        uc = UseCaseInput(
            title="Ticket-Klassifizierung IT-Support",
            submitter="Klaus Klein",
            department="IT",
            current_state="Tickets landen im allgemeinen Postfach, manuelle Zuweisung",
            desired_state="Automatische Kategorisierung und Zuweisung in <30s",
            example_process="Ticket eingehend → Kategorie bestimmen → Queue zuweisen",
            contains_pii=True,
            evidence_quality=EvidenceQuality.ESTIMATE,
            time_savings_hours_per_case=0.5,
            frequency_per_year=5000,
        )
        assert uc.contains_pii is True
        assert uc.evidence_quality == EvidenceQuality.ESTIMATE


class TestUseCaseInputValidierung:
    """Validierungsfehler müssen korrekt ausgelöst werden."""

    def test_leerer_title_wird_abgelehnt(self) -> None:
        with pytest.raises(ValidationError):
            UseCaseInput(
                title="",  # leer → ungültig
                submitter="Test",
                department="Test",
                current_state="IST",
                desired_state="SOLL",
                example_process="Beispiel",
            )

    def test_title_zu_lang_wird_abgelehnt(self) -> None:
        with pytest.raises(ValidationError):
            UseCaseInput(
                title="x" * 201,  # max_length=200 → überschritten
                submitter="Test",
                department="Test",
                current_state="IST",
                desired_state="SOLL",
                example_process="Beispiel",
            )

    def test_current_state_zu_lang_wird_abgelehnt(self) -> None:
        with pytest.raises(ValidationError):
            UseCaseInput(
                title="Titel",
                submitter="Test",
                department="Test",
                current_state="x" * 2001,  # max_length=2000 → überschritten
                desired_state="SOLL",
                example_process="Beispiel",
            )

    def test_extra_felder_werden_abgelehnt(self) -> None:
        """extra='forbid' — unbekannte Felder dürfen nicht durchkommen."""
        with pytest.raises(ValidationError):
            UseCaseInput(
                title="Titel",
                submitter="Test",
                department="Test",
                current_state="IST",
                desired_state="SOLL",
                example_process="Beispiel",
                unbekanntes_feld="sollte nicht gehen",  # extra-Feld
            )

    def test_negative_time_savings_werden_abgelehnt(self) -> None:
        with pytest.raises(ValidationError):
            UseCaseInput(
                title="Titel",
                submitter="Test",
                department="Test",
                current_state="IST",
                desired_state="SOLL",
                example_process="Beispiel",
                time_savings_hours_per_case=-1.0,  # negativ → ungültig
            )

    def test_negative_frequency_wird_abgelehnt(self) -> None:
        with pytest.raises(ValidationError):
            UseCaseInput(
                title="Titel",
                submitter="Test",
                department="Test",
                current_state="IST",
                desired_state="SOLL",
                example_process="Beispiel",
                frequency_per_year=-100,
            )


class TestUseCaseInputModelValidate:
    """model_validate() vs. direkter Konstruktor — Verhalten bei Dict-Input."""

    def test_model_validate_aus_dict(self) -> None:
        """model_validate() akzeptiert ein Dict — wichtig für JSON-Payloads."""
        data = {
            "title": "Aus Dictionary",
            "submitter": "Test",
            "department": "Test",
            "current_state": "IST",
            "desired_state": "SOLL",
            "example_process": "Beispiel",
        }
        uc = UseCaseInput.model_validate(data)
        assert uc.title == "Aus Dictionary"
