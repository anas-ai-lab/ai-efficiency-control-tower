"""Tests fuer solution_content.py (ADR-0054).

Deckt die drei Wege, auf denen eine Loesung durch die Spalten laeuft:
Schema -> Spalte -> Anzeige (Round-Trip), Legacy-Klartext -> Anzeige (Fallback)
und Struktur -> Skizzen-Prompt (deterministischer Text-Renderer).
"""

from __future__ import annotations

import json

from aect.application.models import ManagementSolution, TechnicalSolution
from aect.application.solution_content import (
    dump_management,
    dump_technical,
    management_from_schema,
    read_management_solution,
    read_technical_solution,
    render_technical_text,
    technical_from_schema,
)
from aect.application.structured_output import SolutionProposalV3


def _proposal() -> SolutionProposalV3:
    return SolutionProposalV3(
        management_summary=(
            "Die Vorgaenge werden kuenftig automatisch vorbereitet. Die Fachkraft "
            "prueft nur noch Zweifelsfaelle."
        ),
        management_benefits=["Weniger Routine.", "Kein Rueckstau bei Lastspitzen."],
        architecture_summary=(
            "Ein Dienst liest die Felder aus und uebergibt sie an das Zielsystem."
        ),
        components=["Texterkennung: liest aus.", "Klassifizierung: markiert."],
        data_flow=["Eingang -> Texterkennung", "Texterkennung -> Zielsystem"],
        integration_points=["Zielsystem der Fachabteilung."],
        open_assumptions=["Dokumente liegen digital vor."],
    )


class TestRoundTrip:
    def test_management_survives_column_round_trip(self) -> None:
        original = management_from_schema(_proposal())
        assert read_management_solution(dump_management(original)) == original

    def test_technical_survives_column_round_trip(self) -> None:
        original = technical_from_schema(_proposal())
        assert read_technical_solution(dump_technical(original)) == original

    def test_dumped_management_is_json_not_prose(self) -> None:
        # Die Struktur muss die Spalte ueberleben -- sonst rendert der Report
        # wieder Fliesstext (der Befund, der ADR-0054 ausgeloest hat).
        data = json.loads(dump_management(management_from_schema(_proposal())))
        assert data["management_benefits"] == [
            "Weniger Routine.",
            "Kein Rueckstau bei Lastspitzen.",
        ]


class TestNeverCalled:
    def test_management_none_stays_none(self) -> None:
        assert read_management_solution(None) is None

    def test_technical_none_stays_none(self) -> None:
        assert read_technical_solution(None) is None


class TestLegacyPlainText:
    """Vor ADR-0054 persistierte Cases tragen Klartext in denselben Spalten."""

    def test_legacy_management_text_becomes_summary(self) -> None:
        result = read_management_solution("Ein alter Freitext-Absatz.")
        assert result == ManagementSolution(
            summary="Ein alter Freitext-Absatz.", benefits=()
        )

    def test_legacy_technical_text_becomes_architecture_summary(self) -> None:
        result = read_technical_solution("Ein alter technischer Absatz.")
        assert result is not None
        assert result.architecture_summary == "Ein alter technischer Absatz."
        assert result.components == ()

    def test_json_without_expected_key_is_treated_as_text(self) -> None:
        # Fremdes JSON ist kein Loesungs-JSON -- lieber als Klartext anzeigen als
        # mit einem KeyError die Report-Ansicht abreissen.
        raw = json.dumps({"etwas": "anderes"})
        result = read_management_solution(raw)
        assert result is not None
        assert result.summary == raw

    def test_non_object_json_is_treated_as_text(self) -> None:
        result = read_management_solution("42")
        assert result is not None
        assert result.summary == "42"

    def test_non_list_bullets_do_not_crash(self) -> None:
        raw = json.dumps({"management_summary": "Text.", "management_benefits": "x"})
        result = read_management_solution(raw)
        assert result is not None
        assert result.benefits == ()


class TestRenderTechnicalText:
    def test_render_contains_summary_and_all_sections(self) -> None:
        text = render_technical_text(technical_from_schema(_proposal()))
        assert text.startswith("Ein Dienst liest die Felder aus")
        for heading in ("Komponenten:", "Datenfluss:", "Integrationspunkte:"):
            assert heading in text
        assert "- Texterkennung: liest aus." in text

    def test_render_is_text_not_json(self) -> None:
        # Der Skizzen-Prompt bekaeme sonst rohes JSON als Beschreibungsmaterial.
        text = render_technical_text(technical_from_schema(_proposal()))
        assert not text.lstrip().startswith("{")

    def test_legacy_text_renders_without_empty_headings(self) -> None:
        legacy = TechnicalSolution(
            architecture_summary="Nur ein alter Absatz.",
            components=(),
            data_flow=(),
            integration_points=(),
            open_assumptions=(),
        )
        assert render_technical_text(legacy) == "Nur ein alter Absatz."
