"""Tests fuer structured_output.py (ADR-0013, Teil 1/2)."""

from __future__ import annotations

import json

import pytest

from aect.application.structured_output import (
    InvalidLLMOutputError,
    SharpenedContentV2,
    SolutionProposalV2,
    parse_structured_llm_output,
)


def test_solution_proposal_v2_valid() -> None:
    raw = json.dumps(
        {
            "solution_business": (
                "Die Vorgaenge werden kuenftig automatisch vorbereitet und den "
                "Mitarbeitenden vorgelegt."
            ),
            "solution_technical": (
                "Ein Dienst liest die Felder aus und uebergibt sie an das Zielsystem."
            ),
        }
    )
    parsed = parse_structured_llm_output(raw, SolutionProposalV2)
    assert parsed.solution_business
    assert parsed.solution_technical


def test_solution_proposal_v2_rejects_extra_field() -> None:
    raw = json.dumps(
        {
            "solution_business": "Ein ausreichend langer Geschaeftsleitungs-Absatz.",
            "solution_technical": "Ein ausreichend langer technischer Absatz hier.",
            "unexpected": "x",
        }
    )
    with pytest.raises(InvalidLLMOutputError):
        parse_structured_llm_output(raw, SolutionProposalV2)


def test_solution_proposal_v2_rejects_too_short() -> None:
    raw = json.dumps({"solution_business": "kurz", "solution_technical": "auch kurz"})
    with pytest.raises(InvalidLLMOutputError):
        parse_structured_llm_output(raw, SolutionProposalV2)


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
    "improvement_suggestions": [
        {
            "bezugsfeld": "evidence_level",
            "vorschlag": "Belege die Zeitersparnis mit einer Vorher-Nachher-Messung.",
            "hebel": "Evidenzfaktor steigt von 0,40 auf 0,90.",
        },
        {
            "bezugsfeld": "adoption_type",
            "vorschlag": "Lege die Nutzung als verbindlich fest.",
            "hebel": "Nutzungsfaktor steigt, der erwartete Nutzen im ROI waechst.",
        },
    ],
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
        assert len(result.improvement_suggestions) == 2


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

    def test_empty_suggestions_list_raises(self) -> None:
        payload = {**_VALID_PAYLOAD, "improvement_suggestions": []}
        with pytest.raises(InvalidLLMOutputError):
            parse_structured_llm_output(json.dumps(payload), SharpenedContentV2)

    def test_too_many_suggestions_raises(self) -> None:
        # max_length=3 (V4, Hebel-Pflicht -- Fokus statt Floskel-Liste).
        payload = {
            **_VALID_PAYLOAD,
            "improvement_suggestions": [
                {
                    "bezugsfeld": "notes",
                    "vorschlag": f"Vorschlag Nummer {i} mit genug Zeichen",
                    "hebel": "Aufwand-Score sinkt.",
                }
                for i in range(4)
            ],
        }
        with pytest.raises(InvalidLLMOutputError):
            parse_structured_llm_output(json.dumps(payload), SharpenedContentV2)

    def test_suggestion_vorschlag_too_long_raises(self) -> None:
        payload = {
            **_VALID_PAYLOAD,
            "improvement_suggestions": [
                {"bezugsfeld": "notes", "vorschlag": "x" * 501, "hebel": "ROI steigt."}
            ],
        }
        with pytest.raises(InvalidLLMOutputError):
            parse_structured_llm_output(json.dumps(payload), SharpenedContentV2)

    def test_suggestion_missing_bezugsfeld_raises(self) -> None:
        # Fehlt bezugsfeld -> Schema-Fehler (Hebel-Pflicht, V4).
        payload = {
            **_VALID_PAYLOAD,
            "improvement_suggestions": [
                {"vorschlag": "Ohne Feldbezug.", "hebel": "ROI steigt."}
            ],
        }
        with pytest.raises(InvalidLLMOutputError):
            parse_structured_llm_output(json.dumps(payload), SharpenedContentV2)

    def test_suggestion_missing_hebel_raises(self) -> None:
        payload = {
            **_VALID_PAYLOAD,
            "improvement_suggestions": [
                {"bezugsfeld": "notes", "vorschlag": "Ohne Hebel."}
            ],
        }
        with pytest.raises(InvalidLLMOutputError):
            parse_structured_llm_output(json.dumps(payload), SharpenedContentV2)

    def test_suggestion_unknown_bezugsfeld_raises(self) -> None:
        payload = {
            **_VALID_PAYLOAD,
            "improvement_suggestions": [
                {
                    "bezugsfeld": "nicht_existentes_feld",
                    "vorschlag": "Bezieht sich auf nichts.",
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
