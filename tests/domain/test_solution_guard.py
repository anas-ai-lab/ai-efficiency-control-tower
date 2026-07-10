"""Tests fuer den Vokabular-Guard des Geschaeftsleitungs-Absatzes (V4-P6)."""

from __future__ import annotations

import pytest

from aect.domain.solution_guard import find_vocabulary_violations


@pytest.mark.parametrize(
    "term",
    ["OCR", "LLM", "API", "ERP", "SAP", "Azure", "Backend", "Datenbank", "Pipeline"],
)
def test_detects_forbidden_terms(term: str) -> None:
    text = f"Der Ablauf nutzt {term} im Hintergrund."
    assert term in find_vocabulary_violations(text)


def test_clean_business_paragraph_has_no_violations() -> None:
    text = (
        "Eingehende Vorgaenge werden kuenftig automatisch vorbereitet und den "
        "Mitarbeitenden strukturiert vorgelegt. Die Fachkraft prueft nur noch "
        "Zweifelsfaelle und gibt frei; die Entscheidung bleibt beim Menschen."
    )
    assert find_vocabulary_violations(text) == []


def test_case_insensitive_and_deduplicated() -> None:
    text = "api und API und Api tauchen mehrfach auf."
    violations = find_vocabulary_violations(text)
    assert len(violations) == 1


def test_word_boundary_no_substring_false_positive() -> None:
    # "API" steckt in "Therapie", "ERP" in "Koerper" -- kein Treffer (Wortgrenze).
    text = "Die Therapie am Koerper bleibt unveraendert."
    assert find_vocabulary_violations(text) == []
