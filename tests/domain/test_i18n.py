"""Sprachkatalog-Tests (V4.1-S6): Paritaet de/en, Default = de, EN-Stichproben.

Die Paritaets-Tests iterieren die Kataloge generisch -- ein neuer Katalog-Key,
der nur in einer Sprache existiert, faellt sofort auf (fail loud statt stiller
Default). Das ist die CI-faehige Absicherung fuer beide i18n-Module.
"""

from __future__ import annotations

from types import ModuleType
from typing import Any

import aect.domain.i18n as di18n
from aect.adapters.api.i18n import API_ERRORS
from aect.domain.feasibility import FeasibilityFlag, build_feasibility_recommendation
from aect.domain.i18n import LANGS
from aect.domain.routing import collect_routing_signals

_LANGSET = set(LANGS)


def _nested_lang_maps(module: ModuleType) -> dict[str, dict[str, dict[Any, str]]]:
    """Alle sprach-gekeyten Maps mit dict-Wert (z. B. ZONE_LABELS[lang][zone])."""
    out: dict[str, dict[str, dict[Any, str]]] = {}
    for name in dir(module):
        obj = getattr(module, name)
        if (
            isinstance(obj, dict)
            and set(obj) == _LANGSET
            and all(isinstance(v, dict) for v in obj.values())
        ):
            out[name] = obj
    return out


def _scalar_lang_maps(module: ModuleType) -> dict[str, dict[str, str]]:
    """Alle sprach-gekeyten Maps mit str-Wert (z. B. FEASIBILITY_DEFINITION[lang])."""
    out: dict[str, dict[str, str]] = {}
    for name in dir(module):
        obj = getattr(module, name)
        if (
            isinstance(obj, dict)
            and set(obj) == _LANGSET
            and all(isinstance(v, str) for v in obj.values())
        ):
            out[name] = obj
    return out


def test_domain_nested_catalog_parity() -> None:
    """Jede innere Schluesselstruktur ist fuer de und en identisch."""
    maps = _nested_lang_maps(di18n)
    assert maps, "keine sprach-gekeyten Maps gefunden -- Test-Heuristik pruefen"
    for name, m in maps.items():
        de_keys = set(m["de"])
        for lang in LANGS:
            assert set(m[lang]) == de_keys, f"{name}: {lang} weicht von de ab"
            # Kein leerer Uebersetzungstext (fail loud).
            assert all(m[lang].values()), f"{name}: leerer Wert in {lang}"


def test_domain_scalar_catalog_parity() -> None:
    """Skalare Kataloge tragen beide Sprachen mit nicht-leerem Text."""
    for name, m in _scalar_lang_maps(di18n).items():
        for lang in LANGS:
            assert m[lang], f"{name}: {lang} leer"


def test_api_error_catalog_parity() -> None:
    de_keys = set(API_ERRORS["de"])
    for lang in LANGS:
        assert set(API_ERRORS[lang]) == de_keys, f"API_ERRORS: {lang} weicht ab"
        assert all(API_ERRORS[lang].values()), f"API_ERRORS: leerer Wert in {lang}"


def test_feasibility_recommendation_default_is_de() -> None:
    """Ohne lang-Argument reproduziert der Baustein die deutsche Fassung."""
    flags = [FeasibilityFlag.MISSING_EXAMPLE]
    assert build_feasibility_recommendation(flags) == build_feasibility_recommendation(
        flags, "de"
    )


def test_feasibility_recommendation_en_sample() -> None:
    flags = [FeasibilityFlag.MISSING_EXAMPLE]
    de = build_feasibility_recommendation(flags, "de")
    en = build_feasibility_recommendation(flags, "en")
    assert de == "Konkreten Beispielvorgang ergänzen."
    assert en == "Add a concrete example process."


def test_routing_signals_default_is_de_en_differs() -> None:
    """collect_routing_signals ist reine Funktion; Zaehler sprachunabhaengig,
    Wortlaut sprachabhaengig. Default = de."""
    from decimal import Decimal

    from aect.domain.models import UseCaseInput
    from aect.domain.types import (
        AdoptionType,
        Country,
        DataClassification,
        EmployeeCategory,
        EvidenceLevel,
        ImplementationApproach,
    )

    use_case = UseCaseInput(
        title="Testfall",
        submitter="Test",
        department="Ops",
        country=Country.DE,
        current_state="x" * 60,
        desired_state="y" * 60,
        example_process="z" * 40,
        time_per_case_hours_current=0.2,
        time_per_case_hours_with_ai=0.0,
        occurrences_per_employee_per_year=5000,
        affected_employees_count=10,
        employee_category=EmployeeCategory.PROFESSIONAL,
        adoption_type=AdoptionType.FIXED_PROCESS_STEP,
        evidence_level=EvidenceLevel.PURE_ESTIMATE,
        implementation_approach=ImplementationApproach.SIMPLE_INTEGRATION,
        data_classification=DataClassification.NO_PERSONAL_DATA,
        estimated_license_cost_eur=Decimal("0"),
        implementation_cost_eur=Decimal("0"),
    )

    de_auto, de_ai, de_risk = collect_routing_signals(use_case)
    en_auto, en_ai, en_risk = collect_routing_signals(use_case, "en")

    # Gleiche Anzahl Signale (Zaehler entscheiden die Empfehlung, nicht der Text).
    assert (len(de_auto), len(de_ai), len(de_risk)) == (
        len(en_auto),
        len(en_ai),
        len(en_risk),
    )
    # Default == de, en unterscheidet sich im Wortlaut.
    assert collect_routing_signals(use_case) == (de_auto, de_ai, de_risk)
    assert de_auto != en_auto
    # Umlaut-korrigierte deutsche Fassung + englische Fassung.
    assert any("Komplexität" in s for s in de_auto)
    assert any("Complexity" in s for s in en_auto)
