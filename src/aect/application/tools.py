"""Tool-Registry und Dispatch fuer Function-Calling (Phase C, Tag 37).

Importiert aus: aect.application.ports.llm (erlaubt).
Importiert NICHT aus: aect.adapters -- das waere eine DI-Verletzung
(Modul-Docstring service.py).

Erstes Tool: lookup_stack_options. Liest die Zielplattform-Kategorien aus
config/stack_options.toml -- IP-Trennung (vertraglich bedingt, AUDIT-011):
konkrete Plattform-/Vendor-Namen sind firmenspezifisch und gehoeren weder in
den generischen Code noch in die committete Config. Echte Namen liegen in
config/stack_options.local.toml (gitignored); existiert die Datei, hat sie
Vorrang, sonst greifen die committeten Kategorien-Platzhalter.

Tag 37 liefert nur die Registry + Dispatch-Funktion. Die eigentliche
Function-Calling-Loop (LLM fordert Tool an -> dispatch_tool_call() ->
Ergebnis zurueck an LLM) wird Tag 38 in TriageService.propose_solution()
verdrahtet (siehe ADR-0008, offener Punkt).

Security (aect-security-checklist v2.1, Phase C, LLM06 Excessive Agency):
dispatch_tool_call() wirft UnknownToolError fuer jeden Tool-Namen, der nicht
in TOOL_DEFINITIONS steht -- das LLM kann keine beliebigen Funktionen
aufrufen, nur die explizit registrierten.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from aect.application.ports.llm import ToolCall, ToolDefinition


class UnknownToolError(Exception):
    """Wird geworfen, wenn dispatch_tool_call() einen unregistrierten Tool-Namen erhaelt."""


LOOKUP_STACK_OPTIONS_TOOL = ToolDefinition(
    name="lookup_stack_options",
    description=(
        "Gibt die verfuegbaren Zielplattformen fuer einen "
        "Loesungsvorschlag zurueck (Name + Kurzbeschreibung pro "
        "Plattform). Parameterlos -- immer die vollstaendige Liste."
    ),
    parameters={"type": "object", "properties": {}, "additionalProperties": False},
)

TOOL_DEFINITIONS: list[ToolDefinition] = [LOOKUP_STACK_OPTIONS_TOOL]


def _load_stack_options() -> dict[str, Any]:
    """Laedt Stack-Optionen: local-Override vor committeten Platzhaltern.

    AUDIT-011 (gleiches Muster wie roi_config): config/stack_options.local.toml
    (gitignored, echte Plattform-Namen) hat Vorrang; fehlt sie, greifen die
    generischen Kategorien aus config/stack_options.toml. Ein Fresh Clone
    funktioniert damit ohne lokale Datei.

    Pfadauflösung analog aect.application.prompts.load_prompt():
    src/aect/application/ liegt auf derselben Tiefe wie src/aect/domain/ --
    parents[3] fuehrt zum Repo-Root.
    """
    # src/aect/application/tools.py -> parents[0]=application, [1]=aect,
    # [2]=src, [3]=repo_root
    repo_root = Path(__file__).resolve().parents[3]
    local_path = repo_root / "config" / "stack_options.local.toml"
    path = (
        local_path
        if local_path.exists()
        else (repo_root / "config" / "stack_options.toml")
    )
    with path.open("rb") as f:
        return tomllib.load(f)


def lookup_stack_options() -> dict[str, Any]:
    """Liefert alle konfigurierten Zielplattformen (Name + Beschreibung).

    Tag 37: Platzhalter-Daten aus config/stack_options.toml (bzw. der
    gitignorten local-Datei, AUDIT-011), noch ohne RAG-Beleg. Stack-Grounding mit zitierten Quellen folgt Phase D
    (Master-Plan v3.1) -- diese Funktionssignatur bleibt voraussichtlich
    stabil, nur die Datenquelle wechselt.
    """
    return _load_stack_options()


def dispatch_tool_call(tool_call: ToolCall) -> dict[str, Any]:
    """Fuehrt einen vom LLM angeforderten Tool-Call aus.

    Raises:
        UnknownToolError: tool_call.name ist nicht in TOOL_DEFINITIONS
        registriert.
    """
    if tool_call.name == "lookup_stack_options":
        return lookup_stack_options()
    raise UnknownToolError(f"Unknown tool: {tool_call.name}")
