#!/usr/bin/env python3
"""G-S1 Aktiv-Test: Gibt konstruierte Prompt-Texte fuer den Demo-Case aus.

Zeigt exakt was sharpen_use_case/v3, propose_solution/v2 und
compliance_hints/v1 an das LLM schicken wuerden -- ohne echten API-Call.
Voraussetzung: scripts/demo_payload.json muss ein gueltiges UseCaseInput-
Schema haben (sichergestellt durch tests/test_demo_payload.py).
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_prompt(name: str, role: str, version: str = "v1") -> str:
    """Laedt Prompt-Datei aus prompts/<name>/<version>/<role>.md."""
    path = REPO_ROOT / "prompts" / name / version / f"{role}.md"
    return path.read_text(encoding="utf-8")


def hr(title: str) -> str:
    return f"\n{'=' * 60}\n{title}\n{'=' * 60}"


def main() -> None:
    payload = json.loads(
        (REPO_ROOT / "scripts" / "demo_payload.json").read_text(encoding="utf-8")
    )
    title = payload["title"]
    current_state = payload["current_state"]
    desired_state = payload["desired_state"]
    example_process = payload["example_process"]

    # -- sharpen_use_case v3 (nur Soll-Felder, siehe S4-Scope) --
    print(hr("sharpen_use_case v3 | SYSTEM"))
    print(load_prompt("sharpen_use_case", "system", "v3"))

    print(hr("sharpen_use_case v3 | USER (konstruiert)"))
    print(
        load_prompt("sharpen_use_case", "user", "v3").format(
            desired_state=desired_state,
            desired_example_process=example_process,
        )
    )

    # -- propose_solution v2 --
    print(hr("propose_solution v2 | SYSTEM"))
    print(load_prompt("propose_solution", "system", "v2"))

    print(hr("propose_solution v2 | USER (konstruiert)"))
    print(
        load_prompt("propose_solution", "user", "v2").format(
            title=title,
            current_state=current_state,
            desired_state=desired_state,
            example_process=example_process,
        )
    )

    # -- compliance_hints v1 (mit Beispiel-Chunks) --
    print(hr("compliance_hints v1 | SYSTEM"))
    print(load_prompt("compliance_hints", "system", "v1"))

    example_chunks = (
        "[1] DSGVO Art. 13: Bei der Erhebung personenbezogener Daten sind "
        "Zweck und Rechtsgrundlage der Verarbeitung offenzulegen.\n\n"
        "[2] EU AI Act Art. 50: Systeme, die mit natuerlichen Personen "
        "interagieren, muessen als KI-System kenntlich gemacht werden."
    )
    print(hr("compliance_hints v1 | USER (konstruiert)"))
    print(
        load_prompt("compliance_hints", "user", "v1").format(
            title=title,
            retrieved_chunks=example_chunks,
        )
    )


if __name__ == "__main__":
    main()
