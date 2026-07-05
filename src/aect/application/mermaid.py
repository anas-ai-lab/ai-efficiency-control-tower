"""Deterministischer Mermaid-Builder fuer Architektur-Skizzen (P11, ADR-0049).

Schicht: application -- importiert nur aus aect.application.structured_output
und Python stdlib. Importiert NICHT aus aect.adapters.

Kernentscheidung (D18): Das LLM erzeugt NIE Mermaid-Syntax, sondern nur das
schema-validierte Graph-JSON (ArchitectureSketch). build_mermaid() ist eine
reine Funktion, die daraus deterministisch die Mermaid-Zeichenkette baut. Das
eliminiert die Syntaxfehler-Klasse (kein LLM kann invalides Mermaid emittieren)
und minimiert die Injection-Flaeche: nur die Labels stammen aus dem Graph, und
die werden vor der Einbettung escaped -- kein HTML, keine Form-brechenden
Klammern. Kein Mermaid-Rendering hier, nur String-Bau.
"""

from __future__ import annotations

from aect.application.structured_output import (
    ArchitectureSketch,
    SketchNode,
    SketchNodeKind,
)

# Zeichen, die eine Mermaid-Knoten-/Kantenform brechen oder HTML einschleusen
# koennten: Anfuehrungszeichen, alle Klammerarten, spitze Klammern, Pipe (Kanten-
# Label-Trenner) und Backtick. Sie werden aus jedem Label entfernt, bevor es in
# die Form eingesetzt wird -- die Node-ID selbst ist bereits per Pattern auf
# [a-z0-9_] beschraenkt und braucht kein Escaping.
_FORBIDDEN_LABEL_CHARS = frozenset('"[]{}()<>|`')


def _escape_label(label: str) -> str:
    """Entfernt form-brechende und HTML-faehige Zeichen aus einem Label.

    Bewusst Entfernen statt Ersetzen: ein escaptes Sonderzeichen wuerde die
    Skizze nicht lesbarer machen, aber die Injection-Flaeche vergroessern.
    Mehrfache Leerzeichen (z. B. aus entfernten Klammerpaaren) werden geglaettet.
    """
    cleaned = "".join(c for c in label if c not in _FORBIDDEN_LABEL_CHARS)
    return " ".join(cleaned.split())


def _render_node(node: SketchNode) -> str:
    """Baut die Mermaid-Knotenzeile fuer einen Knoten (Form je kind).

    user -> Stadium `([...])`, system -> Rechteck `[...]`, ai_service -> Hexagon
    `{{...}}`, data_store -> Zylinder `[(...)]`, external -> Subroutine `[[...]]`.
    """
    label = _escape_label(node.label)
    node_id = node.id
    match node.kind:
        case SketchNodeKind.USER:
            return f"{node_id}([{label}])"
        case SketchNodeKind.SYSTEM:
            return f"{node_id}[{label}]"
        case SketchNodeKind.AI_SERVICE:
            return f"{node_id}{{{{{label}}}}}"
        case SketchNodeKind.DATA_STORE:
            return f"{node_id}[({label})]"
        case SketchNodeKind.EXTERNAL:
            return f"{node_id}[[{label}]]"
    raise AssertionError(f"unreachable: unhandled SketchNodeKind {node.kind}")


def build_mermaid(sketch: ArchitectureSketch) -> str:
    """Baut aus einem validierten ArchitectureSketch die Mermaid-Zeichenkette.

    Reine Funktion, deterministisch: gleiche Eingabe -> exakt gleiche Ausgabe
    (snapshot-testbar). flowchart LR; danach je eine Knotenzeile in
    Definitionsreihenfolge, danach je eine Kantenzeile. Kanten mit Label:
    `a -->|label| b`, ohne Label: `a --> b`. Vier Leerzeichen Einrueckung fuer
    Lesbarkeit im Mermaid-Quelltext.
    """
    lines = ["flowchart LR"]
    lines.extend(f"    {_render_node(node)}" for node in sketch.nodes)
    for edge in sketch.edges:
        if edge.label:
            label = _escape_label(edge.label)
            lines.append(f"    {edge.source} -->|{label}| {edge.target}")
        else:
            lines.append(f"    {edge.source} --> {edge.target}")
    return "\n".join(lines)
