"""Tests fuer die deutsche Zahlenformatierung in generierten Texten (V4-P7).

format_de deckt den Helfer ab; der Integrationstest belegt, dass die
erklaerenden Fliesstexte (Empfehlungssatz, Zonen-Begruendung, Kosten-
Begruendung) deutsches Tausenderformat tragen -- der Befund aus dem manuellen
Durchlauf war "6,000 EUR" statt "6.000 EUR".
"""

from __future__ import annotations

import re
from decimal import Decimal

from aect.domain import evaluate_use_case
from aect.domain.explainability import build_recommendation_text, build_score_breakdown
from aect.domain.formatting import format_de, format_number
from aect.domain.models import UseCaseInput
from aect.domain.roi import load_roi_config

# Englisches Tausenderformat: Ziffer, dann Komma, dann genau drei Ziffern
# ("6,000"). Deutsche Dezimalkommas ("0,40") matchen NICHT (nur zwei Nachkomma-
# stellen), sind hier aber ohnehin nicht im Text.
_ENGLISH_THOUSANDS = re.compile(r"\d,\d{3}")
_GERMAN_THOUSANDS = re.compile(r"\d\.\d{3}")


def test_format_de_uses_german_thousands_separator() -> None:
    assert format_de(6000) == "6.000"
    assert format_de(6000, "EUR") == "6.000 EUR"
    assert format_de(3360, "Stunden") == "3.360 Stunden"
    assert format_de(Decimal("87139.2"), "EUR") == "87.139 EUR"
    assert format_de(1_234_567, "EUR") == "1.234.567 EUR"
    assert format_de(999) == "999"  # unter 1000 kein Trenner
    assert format_de(0) == "0"
    # Niemals englisches Format.
    assert "," not in format_de(1_000_000, "EUR")


# Hoher Durchsatz -> Netto-Nutzen und Stunden im Tausenderbereich, plus
# Kosten >= 10.000 EUR: alle betroffenen Textbausteine tragen Tausenderzahlen.
_HIGH_VOLUME: dict = {
    "title": "Automatische Rechnungsverarbeitung mit AI",
    "submitter": "Maria Muster",
    "department": "Finance",
    "country": "de",
    "current_state": (
        "Aktuell werden eingehende Rechnungen manuell gescannt und die "
        "relevanten Felder von Mitarbeitern in SAP eingetragen. Das bindet "
        "erhebliche Kapazitaet im Team."
    ),
    "desired_state": (
        "Kuenftig soll ein KI-System eingehende Rechnungen automatisch auslesen, "
        "Pflichtfelder erkennen und direkt in SAP befuellen. Ziel: unter 2 Minuten."
    ),
    "example_process": (
        "Rechnung von Lieferant X wird manuell gescannt und abgetippt."
    ),
    "time_per_case_hours_current": 0.2,
    "time_per_case_hours_with_ai": 0.0,
    "occurrences_per_employee_per_year": 5000,
    "affected_employees_count": 10,
    "employee_category": "professional",
    "adoption_type": "fixed_process_step",
    "evidence_level": "pure_estimate",
    "implementation_approach": "development_on_existing",
    "estimated_license_cost_eur": 12000.0,
    "implementation_cost_eur": 15000.0,
    "data_classification": "no_personal_data",
}


def test_generated_texts_use_german_thousands() -> None:
    uc = UseCaseInput(**_HIGH_VOLUME)
    result = evaluate_use_case(uc, load_roi_config())
    assert result.passed_vorfilter and result.zone is not None

    recommendation = build_recommendation_text(result, uc)  # == empfehlung_satz
    zone_reason = result.zone.reason
    cost_reason = (
        build_score_breakdown(
            uc,
            result.composite,
            impl_cost_point_min_eur=10_000.0,
            license_cost_point_min_eur=10_000.0,
        )
        .components[1]
        .begruendung
    )  # Kosten-Komponente

    for text in (recommendation, zone_reason, cost_reason):
        assert not _ENGLISH_THOUSANDS.search(text), f"englisches Format: {text}"
        assert _GERMAN_THOUSANDS.search(text), f"kein Tausenderwert: {text}"


def test_format_number_is_language_dependent() -> None:
    # Gleicher Wert, andere Tausendertrennung je Sprache (V4.1-S6).
    assert format_number(259200, "de", "EUR") == "259.200 EUR"
    assert format_number(259200, "en", "EUR") == "259,200 EUR"
    assert format_number(6000, "en") == "6,000"
    assert format_number(6000, "de") == "6.000"
    assert format_number(999, "en") == "999"  # unter 1000 kein Trenner
    assert format_number(Decimal("87139.2"), "en", "EUR") == "87,139 EUR"
    # DE-Variante identisch zu format_de (kein Verhaltenswechsel fuer de).
    assert format_number(1_234_567, "de", "EUR") == format_de(1_234_567, "EUR")


def test_en_recommendation_uses_english_thousands() -> None:
    # Derselbe bewertete Case, einmal DE, einmal EN: der Empfehlungssatz traegt
    # dieselben Zahlen, aber die Tausendertrennung folgt der Sprache
    # ("259.200 EUR" vs "259,200 EUR").
    uc = UseCaseInput(**_HIGH_VOLUME)
    result = evaluate_use_case(uc, load_roi_config())
    assert result.passed_vorfilter

    de_text = build_recommendation_text(result, uc, "de")
    en_text = build_recommendation_text(result, uc, "en")

    assert _GERMAN_THOUSANDS.search(de_text), f"DE ohne Tausenderwert: {de_text}"
    assert not _ENGLISH_THOUSANDS.search(de_text), f"DE englisch formatiert: {de_text}"

    assert _ENGLISH_THOUSANDS.search(en_text), f"EN ohne Tausenderwert: {en_text}"
    assert not _GERMAN_THOUSANDS.search(en_text), f"EN deutsch formatiert: {en_text}"
