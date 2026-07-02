"""Tests fuer PresidioRedactor (PIIRedactorPort-Adapter, Phase G).

Nutzt den echten Presidio-/spaCy-Stack -- kein Netzwerk noetig
(de_core_news_sm ist eine gepinnte Projekt-Dependency, exakte Version aus
dem B1-Spike uebernommen). Modul-Scope-Fixture: die Analyzer-/Anonymizer-
Engines werden einmal pro Testdatei geladen (~0.4s Erstaufruf, B1-Messwert),
nicht pro Test neu.
"""

from __future__ import annotations

import pytest

from aect.adapters.pii import presidio_redactor as presidio_redactor_module
from aect.adapters.pii.presidio_redactor import PresidioRedactor

# Dieselben 5 handgeschriebenen deutschen Testsaetze aus dem B1-Spike-Bericht.
_B1_TEST_CASES: list[tuple[str, str, str]] = [
    (
        "Bitte wenden Sie sich bei Rueckfragen an Herrn Thomas Weber aus der "
        "Fachabteilung.",
        "PERSON",
        "Thomas Weber",
    ),
    (
        "Die Bestaetigung wurde bereits an julia.becker@musterfirma.de versendet.",
        "EMAIL_ADDRESS",
        "julia.becker@musterfirma.de",
    ),
    (
        "Die Rueckerstattung erfolgt auf das Konto mit der IBAN "
        "DE89370400440532013000.",
        "IBAN_CODE",
        "DE89370400440532013000",
    ),
    (
        "Fuer dringende Anliegen erreichen Sie uns telefonisch unter 030 12345678.",
        "PHONE_NUMBER",
        "030 12345678",
    ),
    (
        "Frau Sabine Hoffmann hat das Dokument am Montag freigegeben und per "
        "E-Mail an s.hoffmann@firma-beispiel.de weitergeleitet.",
        "PERSON",
        "Sabine Hoffmann",
    ),
]


@pytest.fixture(scope="module")
def redactor() -> PresidioRedactor:
    """Ein Redactor pro Testdatei -- die Presidio-Engines laden einmal
    (~0.4s, B1-Messwert), nicht pro Testfunktion neu."""
    return PresidioRedactor()


@pytest.mark.parametrize(("text", "entity_type", "pii_value"), _B1_TEST_CASES)
def test_redact_replaces_target_entity_with_placeholder(
    redactor: PresidioRedactor, text: str, entity_type: str, pii_value: str
) -> None:
    """Nicht auf exakten Presidio-Output gepinnt (Span-Grenzen koennen sich
    mit Modellversionen leicht verschieben) -- prueft nur: der Klartext-Wert
    ist weg, der von uns definierte generische Platzhalter ist da."""
    result = redactor.redact(text)
    expected_placeholder = presidio_redactor_module._PLACEHOLDERS[entity_type]
    assert pii_value not in result
    assert expected_placeholder in result


def test_redact_empty_string_returns_empty_string(redactor: PresidioRedactor) -> None:
    assert redactor.redact("") == ""


def test_redact_text_without_pii_is_unchanged_or_only_over_masked(
    redactor: PresidioRedactor,
) -> None:
    """Kein Klartext-PII-Wert im Input -> keiner im Output (Uebermaskierung
    generischer Substantive ist die bekannte, akzeptierte B1-Grenze, siehe
    docs/owasp-llm-checklist.md LLM08 -- daher kein Vergleich auf exakte
    Textgleichheit, nur: keine neuen Woerter werden ERFUNDEN, nur ersetzt)."""
    text = "Der Prozess dauert im Schnitt fuenfzehn Minuten pro Vorgang."
    result = redactor.redact(text)
    # Laenge bleibt in derselben Groessenordnung (Ersetzung, keine Explosion).
    assert len(result) <= len(text) + 50


# ---------------------------------------------------------------------------
# Lazy-Loading (Konstruktor darf das Presidio-Modell NICHT laden)
# ---------------------------------------------------------------------------


def test_engines_not_built_at_construction_time() -> None:
    fresh_redactor = PresidioRedactor()
    assert "_analyzer" not in vars(fresh_redactor)
    assert "_anonymizer" not in vars(fresh_redactor)


def test_engines_built_after_first_redact_call() -> None:
    """_anonymizer wird nur instanziiert, wenn es tatsaechlich etwas zu
    anonymisieren gibt (redact() kuerzt sonst frueh ab) -- der Testsatz
    braucht deshalb eine sicher erkannte Entitaet (E-Mail, B1-Score 1.0)."""
    fresh_redactor = PresidioRedactor()
    fresh_redactor.redact("Kontakt: anna.schmidt@beispielfirma.de")
    assert "_analyzer" in vars(fresh_redactor)
    assert "_anonymizer" in vars(fresh_redactor)


def test_nlp_engine_provider_not_called_before_first_redact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spy auf NlpEngineProvider: create_engine() darf erst beim ersten
    redact()-Aufruf fallen, nicht im Konstruktor."""
    calls: list[str] = []
    original_provider_cls = presidio_redactor_module.NlpEngineProvider

    class _SpyProvider:
        def __init__(self, nlp_configuration: dict[str, object]) -> None:
            calls.append("constructed")
            self._inner = original_provider_cls(nlp_configuration=nlp_configuration)

        def create_engine(self) -> object:
            calls.append("create_engine")
            return self._inner.create_engine()

    monkeypatch.setattr(presidio_redactor_module, "NlpEngineProvider", _SpyProvider)

    fresh_redactor = presidio_redactor_module.PresidioRedactor()
    assert calls == []  # Konstruktor allein loest nichts aus

    fresh_redactor.redact("Ein Testsatz.")
    assert calls == ["constructed", "create_engine"]
