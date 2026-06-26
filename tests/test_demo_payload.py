"""Smoke-Test: scripts/demo_payload.json ist kompatibel mit UseCaseInput.

G-001-Fix-Verifikation (Phase-G-Audit, Tag 77): verhindert, dass Feldnamen
im Demo-Payload wieder vom Schema abweichen -- ein driftendes Payload
wuerde demo.sh beim POST /triage mit HTTP 422 scheitern lassen.
"""

from __future__ import annotations

import json
from pathlib import Path

from aect.domain.models import UseCaseInput


def test_demo_payload_is_valid_use_case_input() -> None:
    """demo_payload.json muss ein gueltiges UseCaseInput-Schema haben."""
    repo_root = Path(__file__).resolve().parents[1]
    payload = json.loads((repo_root / "scripts" / "demo_payload.json").read_text())
    uc = UseCaseInput(**payload)
    assert uc.title == "Automatische Klassifikation eingehender Kundenreklamationen"
    assert uc.frequency_per_year == 6000
    assert uc.data_classification.value == "personal"
