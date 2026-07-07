"""Tests: Logging-Deny-Liste-Processor setzt die Allowlist strukturell durch (H-027).

Macht die dokumentierte Logging-Allowlist von Call-Site-Konvention zu
Defense-in-Depth: Freitext-Keys (prompt/body/output) werden aus jedem Event
entfernt, bevor gerendert wird.
"""

from __future__ import annotations

from aect.adapters.api.logging_config import _drop_denied_keys


class TestDropDeniedKeys:
    def test_drops_freetext_keys(self) -> None:
        event = {
            "event": "llm_call",
            "case_id": "id-001",
            "operation": "sharpen_case",
            "prompt": "geheimer Prompt-Body",
            "output": "LLM-Antwort mit PII",
            "body": "roher Request-Body",
        }
        result = _drop_denied_keys(None, "info", event)
        assert "prompt" not in result
        assert "output" not in result
        assert "body" not in result

    def test_keeps_allowlisted_metadata(self) -> None:
        event = {
            "event": "llm_call",
            "case_id": "id-001",
            "operation": "sharpen_case",
            "input_tokens": 10,
            "cost_eur_estimate": 0.0001,
            "fields": {"title": ["ignore_instructions"]},
        }
        result = _drop_denied_keys(None, "info", dict(event))
        assert result == event
