"""Tests fuer structured_output.py (ADR-0013, Teil 1/2)."""

from __future__ import annotations

import json

import pytest

from aect.application.structured_output import (
    InvalidLLMOutputError,
    SharpenedContentV2,
    parse_structured_llm_output,
)

_VALID_PAYLOAD: dict = {
    "sharpened_title": (
        "Automatisierte Rechnungsverarbeitung mit OCR-Erkennung und "
        "direkter SAP-Integration"
    ),
    "sharpened_current_state": (
        "Mitarbeiter im Finance-Team scannen taeglich rund 50 eingehende "
        "Rechnungen manuell und uebertragen Betraege, Kostenstellen und "
        "Lieferantendaten per Hand in SAP. Pro Rechnung werden ca. 15 "
        "Minuten benoetigt."
    ),
    "sharpened_desired_state": (
        "Ein KI-System liest eingehende Rechnungen automatisch aus, "
        "ordnet Pflichtfelder zu und befuellt SAP direkt. Ziel ist eine "
        "Bearbeitungszeit unter 2 Minuten pro Rechnung bei einer "
        "Fehlerquote unter 1 Prozent."
    ),
    "improvement_suggestions": [
        "Lege fest, wer bei Erkennungsfehlern eskaliert.",
        "Definiere die Fehlerquote-Messung vor dem Rollout.",
    ],
}


class TestParseStructuredLLMOutputValid:
    def test_valid_payload_parses_to_schema(self) -> None:
        result = parse_structured_llm_output(
            json.dumps(_VALID_PAYLOAD), SharpenedContentV2
        )
        assert isinstance(result, SharpenedContentV2)
        assert result.sharpened_title == _VALID_PAYLOAD["sharpened_title"]
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
        payload = {k: v for k, v in _VALID_PAYLOAD.items() if k != "sharpened_title"}
        with pytest.raises(InvalidLLMOutputError):
            parse_structured_llm_output(json.dumps(payload), SharpenedContentV2)

    def test_unknown_field_raises(self) -> None:
        payload = {**_VALID_PAYLOAD, "unexpected_field": "x"}
        with pytest.raises(InvalidLLMOutputError):
            parse_structured_llm_output(json.dumps(payload), SharpenedContentV2)

    def test_title_too_long_raises(self) -> None:
        payload = {**_VALID_PAYLOAD, "sharpened_title": "x" * 201}
        with pytest.raises(InvalidLLMOutputError):
            parse_structured_llm_output(json.dumps(payload), SharpenedContentV2)

    def test_title_too_short_raises(self) -> None:
        payload = {**_VALID_PAYLOAD, "sharpened_title": "x"}
        with pytest.raises(InvalidLLMOutputError):
            parse_structured_llm_output(json.dumps(payload), SharpenedContentV2)

    def test_empty_suggestions_list_raises(self) -> None:
        payload = {**_VALID_PAYLOAD, "improvement_suggestions": []}
        with pytest.raises(InvalidLLMOutputError):
            parse_structured_llm_output(json.dumps(payload), SharpenedContentV2)

    def test_too_many_suggestions_raises(self) -> None:
        payload = {
            **_VALID_PAYLOAD,
            "improvement_suggestions": [
                f"Vorschlag Nummer {i} mit genug Zeichen" for i in range(11)
            ],
        }
        with pytest.raises(InvalidLLMOutputError):
            parse_structured_llm_output(json.dumps(payload), SharpenedContentV2)

    def test_suggestion_item_too_long_raises(self) -> None:
        payload = {**_VALID_PAYLOAD, "improvement_suggestions": ["x" * 501]}
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
