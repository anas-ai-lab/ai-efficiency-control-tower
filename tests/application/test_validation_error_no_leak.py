"""Tests: InvalidLLMOutputError leakt keine LLM-Output-Fragmente (H-031).

str(pydantic.ValidationError) enthaelt input_value = Ausschnitte des
LLM-Outputs (ggf. PII/Secrets). Diese duerfen weder in der Exception-Message
(-> 502-Antwort) noch im Log auftauchen.
"""

from __future__ import annotations

import json

import pytest

from aect.application.structured_output import (
    InvalidLLMOutputError,
    SharpenedContentV2,
    parse_structured_llm_output,
)

_SENTINEL = "GEHEIMER_LEAK_WERT_abc123"


class TestValidationErrorRedaction:
    def test_message_excludes_input_value(self) -> None:
        # Valides JSON, aber schema-verletzend: ein verbotenes Extra-Feld traegt
        # den Sentinel als input_value in den pydantic-ValidationError.
        raw = json.dumps(
            {
                "sharpened_desired_state": "Soll-Zustand mit mehr als dreissig Zeichen.",
                "sharpened_desired_example_process": (
                    "Soll-Beispiel mit mehr als dreissig Zeichen im Text."
                ),
                "improvement_suggestions": [
                    {
                        "bezugsfeld": "notes",
                        "vorschlag": "Konkreter Vorschlag.",
                        "hebel": "ROI steigt.",
                    }
                ],
                "leak_field": _SENTINEL,
            }
        )

        with pytest.raises(InvalidLLMOutputError) as exc_info:
            parse_structured_llm_output(raw, SharpenedContentV2)

        message = str(exc_info.value)
        assert _SENTINEL not in message
        # Struktur-Info (loc/type) bleibt erhalten -- der Fehler ist diagnostizierbar.
        assert "leak_field" in message
        assert "extra_forbidden" in message

    def test_json_decode_error_still_wrapped(self) -> None:
        with pytest.raises(InvalidLLMOutputError):
            parse_structured_llm_output("kein json", SharpenedContentV2)
