"""Tool-Registry und Dispatch fuer Function-Calling (Phase C, Tag 37).

Importiert aus: aect.application.ports.llm (erlaubt).
Importiert NICHT aus: aect.adapters -- das waere eine DI-Verletzung
(Modul-Docstring service.py).

Erstes Tool: lookup_stack_options. Liest die Zielplattformen (Open WebUI,
Copilot Studio, Foundry, SAP BTP, Andere) aus config/stack_options.toml --
IP-Trennung (interne Referenz (entfernt) §5): Plattform-Namen sind firmenspezifisch und
gehoeren nicht in den generischen Code.

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
    """Laedt config/stack_options.toml.

    Pfadauflösung analog aect.application.prompts.load_prompt():
    src/aect/application/ liegt auf derselben Tiefe wie src/aect/domain/ --
    parents[3] fuehrt zum Repo-Root.
    """
    # src/aect/application/tools.py -> parents[0]=application, [1]=aect,
    # [2]=src, [3]=repo_root
    repo_root = Path(__file__).resolve().parents[3]
    path = repo_root / "config" / "stack_options.toml"
    with path.open("rb") as f:
        return tomllib.load(f)


def lookup_stack_options() -> dict[str, Any]:
    """Liefert alle konfigurierten Zielplattformen (Name + Beschreibung).

    Tag 37: Platzhalter-Daten aus config/stack_options.toml, noch ohne
    RAG-Beleg. Stack-Grounding mit zitierten Quellen folgt Phase D
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
