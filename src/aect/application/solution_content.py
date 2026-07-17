"""Persistenz- und Anzeige-Form des Loesungsvorschlags (ADR-0054).

Schicht: application -- Python stdlib + aect.application.models. Kein I/O, kein
Framework-Import, kein LLM.

Der Loesungsvorschlag ist seit ADR-0054 strukturiert (SolutionProposalV3):
Management-Ebene = Kernaussage + Nutzen-Stichpunkte, Technik-Ebene =
Architektur-Kurzbeschreibung + vier Stichpunkt-Listen. Die Struktur muss die
Persistenz ueberleben, sonst rendert der Report wieder Fliesstext.

Speicherform: strukturiertes JSON in den BESTEHENDEN Spalten -- solution_business
(Management) und proposal_text (Technik). Keine neuen Spalten, keine Migration.

Legacy-Fallback: vor ADR-0054 persistierte Cases tragen in denselben Spalten
reinen Klartext. read_*() erkennt das (JSON-Parse schlaegt fehl oder liefert kein
Objekt mit den erwarteten Schluesseln) und bildet den Klartext auf das
Summary-Feld ab; die Stichpunkt-Listen bleiben leer. Das rendert als ruhiger
Absatz statt zu brechen -- dasselbe Muster wie der raw_text-Zweig in
_render_sharpened_content() (application/service.py).
"""

from __future__ import annotations

import json
from typing import Any

from aect.application.models import ManagementSolution, TechnicalSolution
from aect.application.structured_output import SolutionProposalV3


def management_from_schema(parsed: SolutionProposalV3) -> ManagementSolution:
    """Management-Ebene aus dem validierten LLM-Schema."""
    return ManagementSolution(
        summary=parsed.management_summary,
        benefits=tuple(parsed.management_benefits),
    )


def technical_from_schema(parsed: SolutionProposalV3) -> TechnicalSolution:
    """Technik-Ebene aus dem validierten LLM-Schema."""
    return TechnicalSolution(
        architecture_summary=parsed.architecture_summary,
        components=tuple(parsed.components),
        data_flow=tuple(parsed.data_flow),
        integration_points=tuple(parsed.integration_points),
        open_assumptions=tuple(parsed.open_assumptions),
    )


def dump_management(solution: ManagementSolution) -> str:
    """Management-Ebene -> JSON-String fuer die Spalte solution_business."""
    return json.dumps(
        {
            "management_summary": solution.summary,
            "management_benefits": list(solution.benefits),
        }
    )


def dump_technical(solution: TechnicalSolution) -> str:
    """Technik-Ebene -> JSON-String fuer die Spalte proposal_text."""
    return json.dumps(
        {
            "architecture_summary": solution.architecture_summary,
            "components": list(solution.components),
            "data_flow": list(solution.data_flow),
            "integration_points": list(solution.integration_points),
            "open_assumptions": list(solution.open_assumptions),
        }
    )


def _load_object(raw: str) -> dict[str, Any] | None:
    """Parst einen Spaltenwert als JSON-Objekt, oder None bei Legacy-Klartext.

    None heisst: kein JSON (Legacy-Klartext) ODER JSON, das kein Objekt ist
    (z. B. eine Beschreibung, die zufaellig aus einer Zahl besteht). Beides
    behandelt der Aufrufer als Klartext.
    """
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _str_list(value: Any) -> tuple[str, ...]:
    """Liest eine Stichpunkt-Liste defensiv aus persistiertem JSON.

    Der Spalteninhalt ist zwar von uns geschrieben, stammt aber urspruenglich
    aus LLM-Output -- ein Nicht-Listen-Wert oder Nicht-String-Eintrag darf die
    Report-Ansicht nicht mit einem TypeError abreissen (Anzeige ist read-only).
    """
    if not isinstance(value, list):
        return ()
    return tuple(str(item) for item in value)


def read_management_solution(raw: str | None) -> ManagementSolution | None:
    """Spaltenwert solution_business -> Management-Ebene.

    None (nie erzeugt) -> None. Strukturiertes JSON -> volle Fassung. Alles
    andere (Legacy-Klartext) -> Klartext als summary, ohne Stichpunkte.
    """
    if raw is None:
        return None
    data = _load_object(raw)
    if data is None or "management_summary" not in data:
        return ManagementSolution(summary=raw, benefits=())
    return ManagementSolution(
        summary=str(data["management_summary"]),
        benefits=_str_list(data.get("management_benefits")),
    )


def read_technical_solution(raw: str | None) -> TechnicalSolution | None:
    """Spaltenwert proposal_text -> Technik-Ebene.

    None (nie erzeugt) -> None. Strukturiertes JSON -> volle Fassung. Alles
    andere (Legacy-Klartext) -> Klartext als architecture_summary, ohne Listen.
    """
    if raw is None:
        return None
    data = _load_object(raw)
    if data is None or "architecture_summary" not in data:
        return TechnicalSolution(
            architecture_summary=raw,
            components=(),
            data_flow=(),
            integration_points=(),
            open_assumptions=(),
        )
    return TechnicalSolution(
        architecture_summary=str(data["architecture_summary"]),
        components=_str_list(data.get("components")),
        data_flow=_str_list(data.get("data_flow")),
        integration_points=_str_list(data.get("integration_points")),
        open_assumptions=_str_list(data.get("open_assumptions")),
    )


def render_technical_text(solution: TechnicalSolution) -> str:
    """Technik-Ebene -> lesbarer Fliesstext (deterministisch, kein LLM).

    Gebraucht dort, wo ein nachgelagerter Schritt Beschreibungsmaterial als Text
    erwartet statt Felder -- konkret der Architektur-Skizzen-Prompt
    (generate_sketch, prompts/architecture_sketch/v1/user.md). Das Skizzen-LLM
    bekaeme sonst rohes JSON in den Prompt.

    Leere Listen (Legacy-Klartext, siehe Modul-Docstring) erzeugen keine
    Ueberschrift ohne Inhalt -- der Klartext steht dann allein.
    """
    parts = [solution.architecture_summary]
    sections = (
        ("Komponenten", solution.components),
        ("Datenfluss", solution.data_flow),
        ("Integrationspunkte", solution.integration_points),
        ("Offene Annahmen", solution.open_assumptions),
    )
    for heading, items in sections:
        if items:
            parts.append(heading + ":\n" + "\n".join(f"- {item}" for item in items))
    return "\n\n".join(parts)
