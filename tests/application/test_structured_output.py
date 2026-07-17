"""Tests fuer structured_output.py (ADR-0013, Teil 1/2)."""

from __future__ import annotations

import json

import pytest

from aect.application.structured_output import (
    InvalidLLMOutputError,
    SharpenedContentV2,
    SolutionProposalV3,
    parse_structured_llm_output,
)

# Schema-valider Loesungsvorschlag (ADR-0054): beide Ebenen strukturiert.
_VALID_SOLUTION: dict = {
    "management_summary": (
        "Die Vorgaenge werden kuenftig automatisch vorbereitet und den "
        "Mitarbeitenden strukturiert vorgelegt. Die Fachkraft prueft nur noch "
        "Zweifelsfaelle und gibt frei."
    ),
    "management_benefits": [
        "Die Sachbearbeitung konzentriert sich auf Zweifelsfaelle.",
        "Der Rueckstau bei Lastspitzen faellt geringer aus.",
    ],
    "architecture_summary": (
        "Ein Dienst liest die Felder aus und uebergibt sie an das Zielsystem. "
        "Eine Klassifizierung markiert Zweifelsfaelle."
    ),
    "components": [
        "Texterkennung: liest die Felder aus dem Dokument.",
        "Klassifizierung: markiert Zweifelsfaelle.",
    ],
    "data_flow": [
        "Eingang -> Texterkennung -> strukturierter Datensatz",
        "Datensatz -> Klassifizierung -> Zielsystem",
    ],
    "integration_points": ["Zielsystem der Fachabteilung ueber eine Schnittstelle."],
    "open_assumptions": ["Die Dokumente liegen digital lesbar vor."],
}


class TestSolutionProposalV3:
    def test_valid_payload_parses(self) -> None:
        parsed = parse_structured_llm_output(
            json.dumps(_VALID_SOLUTION), SolutionProposalV3
        )
        assert parsed.management_summary
        assert len(parsed.management_benefits) == 2
        assert len(parsed.components) == 2
        assert parsed.open_assumptions == ["Die Dokumente liegen digital lesbar vor."]

    def test_rejects_extra_field(self) -> None:
        payload = {**_VALID_SOLUTION, "unexpected": "x"}
        with pytest.raises(InvalidLLMOutputError):
            parse_structured_llm_output(json.dumps(payload), SolutionProposalV3)

    def test_rejects_legacy_v2_shape(self) -> None:
        # Die alte Zwei-Felder-Form ist kein gueltiger Output mehr -- sie laeuft in
        # den Schema-Fehler (Retry, dann 422), nicht still durch.
        payload = {
            "solution_business": "Ein ausreichend langer Geschaeftsleitungs-Absatz.",
            "solution_technical": "Ein ausreichend langer technischer Absatz hier.",
        }
        with pytest.raises(InvalidLLMOutputError):
            parse_structured_llm_output(json.dumps(payload), SolutionProposalV3)

    def test_rejects_summary_too_short(self) -> None:
        payload = {**_VALID_SOLUTION, "management_summary": "kurz"}
        with pytest.raises(InvalidLLMOutputError):
            parse_structured_llm_output(json.dumps(payload), SolutionProposalV3)

    def test_rejects_summary_wall_of_text(self) -> None:
        # max_length=700 ist die Schema-Haelfte der "keine Absatz-Wand"-Regel:
        # 2-3 Saetze brauchen sie nicht, eine Textwueste sprengt sie.
        payload = {**_VALID_SOLUTION, "management_summary": "x" * 701}
        with pytest.raises(InvalidLLMOutputError):
            parse_structured_llm_output(json.dumps(payload), SolutionProposalV3)

    def test_rejects_more_than_three_benefits(self) -> None:
        payload = {
            **_VALID_SOLUTION,
            "management_benefits": [f"Nutzen Nummer {i} mit Text." for i in range(4)],
        }
        with pytest.raises(InvalidLLMOutputError):
            parse_structured_llm_output(json.dumps(payload), SolutionProposalV3)

    def test_rejects_empty_benefits(self) -> None:
        payload = {**_VALID_SOLUTION, "management_benefits": []}
        with pytest.raises(InvalidLLMOutputError):
            parse_structured_llm_output(json.dumps(payload), SolutionProposalV3)

    def test_rejects_bullet_that_is_a_paragraph(self) -> None:
        # Ein Stichpunkt ist eine Zeile (max 200) -- kein Absatz.
        payload = {**_VALID_SOLUTION, "components": ["x" * 201, "Zweite Komponente."]}
        with pytest.raises(InvalidLLMOutputError):
            parse_structured_llm_output(json.dumps(payload), SolutionProposalV3)

    def test_rejects_single_component(self) -> None:
        # min_length=2: eine einzelne Komponente ist keine Architektur-Uebersicht.
        payload = {**_VALID_SOLUTION, "components": ["Nur ein Baustein."]}
        with pytest.raises(InvalidLLMOutputError):
            parse_structured_llm_output(json.dumps(payload), SolutionProposalV3)

    def test_rejects_missing_technical_list(self) -> None:
        payload = {k: v for k, v in _VALID_SOLUTION.items() if k != "data_flow"}
        with pytest.raises(InvalidLLMOutputError):
            parse_structured_llm_output(json.dumps(payload), SolutionProposalV3)


_VALID_PAYLOAD: dict = {
    "sharpened_desired_state": (
        "Ein KI-System liest eingehende Rechnungen automatisch aus, "
        "ordnet Pflichtfelder zu und befuellt SAP direkt. Ziel ist eine "
        "Bearbeitungszeit unter 2 Minuten pro Rechnung bei einer "
        "Fehlerquote unter 1 Prozent."
    ),
    "sharpened_desired_example_process": (
        "Eine eingehende Lieferantenrechnung wird automatisch ausgelesen, "
        "den Kostenstellen zugeordnet und als SAP-Buchungsvorschlag "
        "bereitgestellt; nur ein Zweifelsfall geht an eine Fachkraft."
    ),
}


class TestParseStructuredLLMOutputValid:
    def test_valid_payload_parses_to_schema(self) -> None:
        result = parse_structured_llm_output(
            json.dumps(_VALID_PAYLOAD), SharpenedContentV2
        )
        assert isinstance(result, SharpenedContentV2)
        assert (
            result.sharpened_desired_state == _VALID_PAYLOAD["sharpened_desired_state"]
        )


class TestParseStructuredLLMOutputInvalidJSON:
    def test_malformed_json_raises(self) -> None:
        with pytest.raises(InvalidLLMOutputError):
            parse_structured_llm_output("{not valid json", SharpenedContentV2)

    def test_empty_string_raises(self) -> None:
        with pytest.raises(InvalidLLMOutputError):
            parse_structured_llm_output("", SharpenedContentV2)


class TestParseStructuredLLMOutputSchemaViolations:
    def test_missing_required_field_raises(self) -> None:
        payload = {
            k: v for k, v in _VALID_PAYLOAD.items() if k != "sharpened_desired_state"
        }
        with pytest.raises(InvalidLLMOutputError):
            parse_structured_llm_output(json.dumps(payload), SharpenedContentV2)

    def test_unknown_field_raises(self) -> None:
        payload = {**_VALID_PAYLOAD, "unexpected_field": "x"}
        with pytest.raises(InvalidLLMOutputError):
            parse_structured_llm_output(json.dumps(payload), SharpenedContentV2)

    def test_desired_state_too_long_raises(self) -> None:
        payload = {**_VALID_PAYLOAD, "sharpened_desired_state": "x" * 2001}
        with pytest.raises(InvalidLLMOutputError):
            parse_structured_llm_output(json.dumps(payload), SharpenedContentV2)

    def test_desired_state_too_short_raises(self) -> None:
        payload = {**_VALID_PAYLOAD, "sharpened_desired_state": "x" * 29}
        with pytest.raises(InvalidLLMOutputError):
            parse_structured_llm_output(json.dumps(payload), SharpenedContentV2)

    def test_legacy_suggestions_field_now_rejected(self) -> None:
        # ADR-0054: improvement_suggestions ist ersatzlos entfallen. extra="forbid"
        # laesst ein Modell, das den Block weiterhin emittiert, in den Schema-
        # Fehler laufen (Retry, dann 422) statt ihn still zu schlucken.
        payload = {
            **_VALID_PAYLOAD,
            "improvement_suggestions": [
                {
                    "bezugsfeld": "notes",
                    "vorschlag": "Ein Vorschlag mit genug Zeichen.",
                    "hebel": "ROI steigt.",
                }
            ],
        }
        with pytest.raises(InvalidLLMOutputError):
            parse_structured_llm_output(json.dumps(payload), SharpenedContentV2)


_VALID_SKETCH: dict = {
    "nodes": [
        {"id": "user", "label": "Sachbearbeiter", "kind": "user"},
        {"id": "sys", "label": "Eingangs-System", "kind": "system"},
        {"id": "db", "label": "Fall-Datenbank", "kind": "data_store"},
    ],
    "edges": [
        {"source": "user", "target": "sys", "label": "reicht ein"},
        {"source": "sys", "target": "db"},
    ],
}


class TestArchitectureSketchValid:
    def test_valid_graph_parses(self) -> None:
        from aect.application.structured_output import ArchitectureSketch

        result = parse_structured_llm_output(
            json.dumps(_VALID_SKETCH), ArchitectureSketch
        )
        assert isinstance(result, ArchitectureSketch)
        assert len(result.nodes) == 3
        assert len(result.edges) == 2

    def test_zero_edges_is_valid(self) -> None:
        from aect.application.structured_output import ArchitectureSketch

        payload = {**_VALID_SKETCH, "edges": []}
        result = parse_structured_llm_output(json.dumps(payload), ArchitectureSketch)
        assert result.edges == []


class TestArchitectureSketchViolations:
    def test_duplicate_node_id_raises(self) -> None:
        from aect.application.structured_output import ArchitectureSketch

        payload = {
            "nodes": [
                {"id": "dup", "label": "A", "kind": "user"},
                {"id": "dup", "label": "B", "kind": "system"},
            ],
            "edges": [],
        }
        with pytest.raises(InvalidLLMOutputError):
            parse_structured_llm_output(json.dumps(payload), ArchitectureSketch)

    def test_edge_to_unknown_id_raises(self) -> None:
        from aect.application.structured_output import ArchitectureSketch

        payload = {
            "nodes": [
                {"id": "a", "label": "A", "kind": "user"},
                {"id": "b", "label": "B", "kind": "system"},
            ],
            "edges": [{"source": "a", "target": "ghost"}],
        }
        with pytest.raises(InvalidLLMOutputError):
            parse_structured_llm_output(json.dumps(payload), ArchitectureSketch)

    def test_eleven_nodes_raises(self) -> None:
        from aect.application.structured_output import ArchitectureSketch

        payload = {
            "nodes": [
                {"id": f"n{i}", "label": f"Knoten {i}", "kind": "system"}
                for i in range(11)
            ],
            "edges": [],
        }
        with pytest.raises(InvalidLLMOutputError):
            parse_structured_llm_output(json.dumps(payload), ArchitectureSketch)

    def test_one_node_raises(self) -> None:
        from aect.application.structured_output import ArchitectureSketch

        payload = {"nodes": [{"id": "a", "label": "A", "kind": "user"}], "edges": []}
        with pytest.raises(InvalidLLMOutputError):
            parse_structured_llm_output(json.dumps(payload), ArchitectureSketch)

    def test_invalid_kind_raises(self) -> None:
        from aect.application.structured_output import ArchitectureSketch

        payload = {
            "nodes": [
                {"id": "a", "label": "A", "kind": "database"},
                {"id": "b", "label": "B", "kind": "system"},
            ],
            "edges": [],
        }
        with pytest.raises(InvalidLLMOutputError):
            parse_structured_llm_output(json.dumps(payload), ArchitectureSketch)

    def test_invalid_node_id_pattern_raises(self) -> None:
        from aect.application.structured_output import ArchitectureSketch

        payload = {
            "nodes": [
                {"id": "Has Space", "label": "A", "kind": "user"},
                {"id": "b", "label": "B", "kind": "system"},
            ],
            "edges": [],
        }
        with pytest.raises(InvalidLLMOutputError):
            parse_structured_llm_output(json.dumps(payload), ArchitectureSketch)

    def test_too_many_edges_raises(self) -> None:
        from aect.application.structured_output import ArchitectureSketch

        payload = {
            "nodes": [
                {"id": "a", "label": "A", "kind": "user"},
                {"id": "b", "label": "B", "kind": "system"},
            ],
            "edges": [{"source": "a", "target": "b"} for _ in range(16)],
        }
        with pytest.raises(InvalidLLMOutputError):
            parse_structured_llm_output(json.dumps(payload), ArchitectureSketch)


class TestParseStructuredLLMOutputFenceTolerance:
    """H-021: der Parser toleriert Markdown-Fences und umgebende Prosa."""

    def test_markdown_json_fence_is_tolerated(self) -> None:
        fenced = "```json\n" + json.dumps(_VALID_PAYLOAD) + "\n```"
        result = parse_structured_llm_output(fenced, SharpenedContentV2)
        assert isinstance(result, SharpenedContentV2)
        assert (
            result.sharpened_desired_state == _VALID_PAYLOAD["sharpened_desired_state"]
        )

    def test_surrounding_prose_is_tolerated(self) -> None:
        wrapped = "Hier das Ergebnis:\n" + json.dumps(_VALID_PAYLOAD) + "\nFertig."
        result = parse_structured_llm_output(wrapped, SharpenedContentV2)
        assert isinstance(result, SharpenedContentV2)
