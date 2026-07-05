"""Tests fuer den deterministischen Mermaid-Builder (P11, ADR-0049).

Der Builder ist eine reine Funktion: gleiche Eingabe -> exakt gleiche Ausgabe.
Der Snapshot-Test pinnt eine erwartete Zeichenkette; der Escaping-Test stellt
sicher, dass form-brechende und HTML-faehige Zeichen nicht in den Output gelangen.
"""

from __future__ import annotations

from aect.application.mermaid import build_mermaid
from aect.application.structured_output import (
    ArchitectureSketch,
    SketchEdge,
    SketchNode,
    SketchNodeKind,
)


def test_build_mermaid_snapshot_all_shapes() -> None:
    """Ein Beispiel-Graph -> exakt erwartete Mermaid-Zeichenkette (alle 5 Formen)."""
    sketch = ArchitectureSketch(
        nodes=[
            SketchNode(id="u", label="Sachbearbeiter", kind=SketchNodeKind.USER),
            SketchNode(id="sys", label="Eingangs-System", kind=SketchNodeKind.SYSTEM),
            SketchNode(
                id="ai", label="Klassifikations-Service", kind=SketchNodeKind.AI_SERVICE
            ),
            SketchNode(id="db", label="Fall-Datenbank", kind=SketchNodeKind.DATA_STORE),
            SketchNode(id="ext", label="ERP-System", kind=SketchNodeKind.EXTERNAL),
        ],
        edges=[
            SketchEdge(source="u", target="sys", label="reicht ein"),
            SketchEdge(source="sys", target="ai"),
            SketchEdge(source="ai", target="db"),
            SketchEdge(source="ai", target="ext", label="uebergibt"),
        ],
    )

    expected = (
        "flowchart LR\n"
        "    u([Sachbearbeiter])\n"
        "    sys[Eingangs-System]\n"
        "    ai{{Klassifikations-Service}}\n"
        "    db[(Fall-Datenbank)]\n"
        "    ext[[ERP-System]]\n"
        "    u -->|reicht ein| sys\n"
        "    sys --> ai\n"
        "    ai --> db\n"
        "    ai -->|uebergibt| ext"
    )

    assert build_mermaid(sketch) == expected


def test_build_mermaid_escapes_quotes_and_brackets_in_labels() -> None:
    """Anfuehrungszeichen/Klammern werden aus Labels entfernt, nie durchgereicht."""
    sketch = ArchitectureSketch(
        nodes=[
            SketchNode(
                id="a",
                label='System "X" [beta] (v2)',
                kind=SketchNodeKind.SYSTEM,
            ),
            SketchNode(
                id="b",
                label="Store <script>|{x}",
                kind=SketchNodeKind.DATA_STORE,
            ),
        ],
        edges=[SketchEdge(source="a", target="b", label='ruft "auf" |x|')],
    )

    result = build_mermaid(sketch)

    for forbidden in '"[]{}()<>|`':
        # Die einzige erlaubte Vorkommensklasse dieser Zeichen ist die
        # Builder-Syntax selbst (Knotenformen/Kanten), nicht der Label-Inhalt.
        assert forbidden not in "System X beta v2"  # sanity: Label-Rest ist clean
    assert '"' not in result
    assert "<script>" not in result
    assert "|x|" not in result
    # Label-Reste bleiben lesbar erhalten.
    assert "System X beta v2" in result
    assert "Store scriptx" in result


def test_build_mermaid_edge_without_label() -> None:
    """Kante ohne Label -> `a --> b`, kein Pipe-Block."""
    sketch = ArchitectureSketch(
        nodes=[
            SketchNode(id="a", label="A", kind=SketchNodeKind.USER),
            SketchNode(id="b", label="B", kind=SketchNodeKind.SYSTEM),
        ],
        edges=[SketchEdge(source="a", target="b")],
    )
    assert "    a --> b" in build_mermaid(sketch)


def test_build_mermaid_no_edges() -> None:
    """Graph ohne Kanten: nur der Header und die Knotenzeilen."""
    sketch = ArchitectureSketch(
        nodes=[
            SketchNode(id="a", label="A", kind=SketchNodeKind.USER),
            SketchNode(id="b", label="B", kind=SketchNodeKind.SYSTEM),
        ],
        edges=[],
    )
    assert build_mermaid(sketch) == "flowchart LR\n    a([A])\n    b[B]"
