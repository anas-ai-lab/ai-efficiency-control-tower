"""Tests fuer den deterministischen Mermaid-Builder (ADR-0049/0055).

Der Builder ist eine reine Funktion: gleiche Eingabe -> exakt gleiche Ausgabe.
Die Snapshot-Tests pinnen erwartete Zeichenketten; die uebrigen Tests decken die
Layout-Regeln aus ADR-0055 einzeln ab -- Gruppierung, Knoten-Kappung mit
Quoten-Umverteilung, Kanten-Filter und Label-Kappung.
"""

from __future__ import annotations

from aect.application.mermaid import (
    SKETCH_LAYER_LABELS,
    SKETCH_OVERFLOW_LABEL,
    build_architecture_diagram,
)
from aect.application.structured_output import (
    ArchitectureSketch,
    SketchEdge,
    SketchLayer,
    SketchNode,
)
from aect.domain.i18n import LANGS


def _node(node_id: str, label: str, layer: SketchLayer) -> SketchNode:
    return SketchNode(id=node_id, label=label, layer=layer)


def test_snapshot_all_five_layers_de() -> None:
    """Ein Beispiel-Graph -> exakt erwartete Mermaid-Zeichenkette (alle 5 Formen)."""
    sketch = ArchitectureSketch(
        nodes=[
            _node("u", "Sachbearbeiter", SketchLayer.SOURCE),
            _node("sys", "Eingangs-System", SketchLayer.PROCESSING),
            _node("ai", "Klassifikations-Service", SketchLayer.AI),
            _node("db", "Fall-Datenbank", SketchLayer.STORAGE),
            _node("out", "Ergebnis-Dokument", SketchLayer.OUTPUT),
        ],
        edges=[
            SketchEdge(source="u", target="sys", label="reicht ein"),
            SketchEdge(source="sys", target="ai"),
            SketchEdge(source="ai", target="db"),
            SketchEdge(source="db", target="out", label="uebergibt"),
        ],
    )

    expected = (
        "flowchart LR\n"
        '    subgraph layer_source["Eingang"]\n'
        "        u([Sachbearbeiter])\n"
        "    end\n"
        '    subgraph layer_processing["Verarbeitung"]\n'
        "        sys[Eingangs-System]\n"
        "    end\n"
        '    subgraph layer_ai["KI-Bausteine"]\n'
        "        ai{{Klassifikations-Service}}\n"
        "    end\n"
        '    subgraph layer_storage["Datenhaltung"]\n'
        "        db[(Fall-Datenbank)]\n"
        "    end\n"
        '    subgraph layer_output["Ausgabe"]\n'
        "        out[[Ergebnis-Dokument]]\n"
        "    end\n"
        "    u -->|reicht ein| sys\n"
        "    sys --> ai\n"
        "    ai --> db\n"
        "    db -->|uebergibt| out"
    )

    assert build_architecture_diagram(sketch, "de") == expected


def test_snapshot_all_five_layers_en() -> None:
    """Derselbe Graph auf Englisch: nur die Subgraph-Titel wechseln."""
    sketch = ArchitectureSketch(
        nodes=[
            _node("u", "Sachbearbeiter", SketchLayer.SOURCE),
            _node("sys", "Eingangs-System", SketchLayer.PROCESSING),
            _node("ai", "Klassifikations-Service", SketchLayer.AI),
            _node("db", "Fall-Datenbank", SketchLayer.STORAGE),
            _node("out", "Ergebnis-Dokument", SketchLayer.OUTPUT),
        ],
        edges=[SketchEdge(source="u", target="sys", label="reicht ein")],
    )

    expected = (
        "flowchart LR\n"
        '    subgraph layer_source["Input"]\n'
        "        u([Sachbearbeiter])\n"
        "    end\n"
        '    subgraph layer_processing["Processing"]\n'
        "        sys[Eingangs-System]\n"
        "    end\n"
        '    subgraph layer_ai["AI components"]\n'
        "        ai{{Klassifikations-Service}}\n"
        "    end\n"
        '    subgraph layer_storage["Storage"]\n'
        "        db[(Fall-Datenbank)]\n"
        "    end\n"
        '    subgraph layer_output["Output"]\n'
        "        out[[Ergebnis-Dokument]]\n"
        "    end\n"
        "    u -->|reicht ein| sys"
    )

    assert build_architecture_diagram(sketch, "en") == expected


def test_deterministic_same_input_same_output() -> None:
    """Zweimal derselbe Graph -> zeichengleiche Ausgabe (keine Zeit/Zufalls-IDs)."""
    sketch = ArchitectureSketch(
        nodes=[
            _node("a", "A", SketchLayer.SOURCE),
            _node("b", "B", SketchLayer.AI),
        ],
        edges=[SketchEdge(source="a", target="b")],
    )
    assert build_architecture_diagram(sketch, "de") == build_architecture_diagram(
        sketch, "de"
    )


def test_layer_order_independent_of_input_order() -> None:
    """Die Subgraph-Folge kommt aus dem Enum, nicht aus der LLM-Reihenfolge."""
    reversed_input = ArchitectureSketch(
        nodes=[
            _node("out", "Ausgabe", SketchLayer.OUTPUT),
            _node("db", "Ablage", SketchLayer.STORAGE),
            _node("u", "Quelle", SketchLayer.SOURCE),
        ],
        edges=[],
    )
    result = build_architecture_diagram(reversed_input, "de")

    assert result.index("layer_source") < result.index("layer_storage")
    assert result.index("layer_storage") < result.index("layer_output")


def test_empty_layers_are_omitted() -> None:
    """Nicht belegte Ebenen erzeugen keinen leeren Subgraph."""
    sketch = ArchitectureSketch(
        nodes=[
            _node("u", "Quelle", SketchLayer.SOURCE),
            _node("ai", "Modell", SketchLayer.AI),
        ],
        edges=[],
    )
    result = build_architecture_diagram(sketch, "de")

    assert "layer_source" in result
    assert "layer_ai" in result
    assert "layer_processing" not in result
    assert "layer_storage" not in result
    assert "layer_output" not in result


def test_node_cap_at_twelve_with_overflow_marker() -> None:
    """15 Knoten in einer Ebene -> 11 echte + 1 Sammelknoten "+ 4 weitere"."""
    sketch = ArchitectureSketch(
        nodes=[
            _node(f"n{i}", f"Schritt {i}", SketchLayer.PROCESSING) for i in range(15)
        ],
        edges=[],
    )
    result = build_architecture_diagram(sketch, "de")

    node_lines = [line for line in result.splitlines() if line.startswith("        ")]
    assert len(node_lines) == 12
    assert "overflow_processing[+ 4 weitere]" in result
    # Der zwoelfte Original-Knoten ist nicht mehr dabei, der elfte schon.
    assert "n10[Schritt 10]" in result
    assert "n11[Schritt 11]" not in result


def test_node_cap_overflow_label_english() -> None:
    """Der Sammelknoten laeuft ueber denselben Sprachkatalog wie die Titel."""
    sketch = ArchitectureSketch(
        nodes=[_node(f"n{i}", f"Step {i}", SketchLayer.AI) for i in range(15)],
        edges=[],
    )
    assert "overflow_ai{{+ 4 more}}" in build_architecture_diagram(sketch, "en")


def test_quota_redistribution_across_three_uneven_layers() -> None:
    """Ungenutzte Quote wandert an spaetere Ebenen, statt zu verfallen.

    Drei belegte Ebenen -> Basisquote 4, Rest 0. source braucht nur 1 von 4,
    vererbt 3 an processing (Quote 7, braucht 2, vererbt 5) -- storage kommt
    damit auf 9 Plaetze und zeigt 8 echte Knoten + Sammelknoten.
    """
    sketch = ArchitectureSketch(
        nodes=[
            _node("s0", "Quelle", SketchLayer.SOURCE),
            _node("p0", "Schritt A", SketchLayer.PROCESSING),
            _node("p1", "Schritt B", SketchLayer.PROCESSING),
            *[_node(f"d{i}", f"Ablage {i}", SketchLayer.STORAGE) for i in range(12)],
        ],
        edges=[],
    )
    result = build_architecture_diagram(sketch, "de")

    node_lines = [line for line in result.splitlines() if line.startswith("        ")]
    assert len(node_lines) == 12
    assert "d7[(Ablage 7)]" in result
    assert "d8[(Ablage 8)]" not in result
    assert "overflow_storage[(+ 4 weitere)]" in result


def test_single_node_overflow_is_resolved_when_a_layer_can_give_budget() -> None:
    """Ein Sammelknoten, der nur EINEN Platz spart, wird gegen Budget aufgeloest.

    16 Knoten in 4/4/3/3/2 -> Basisquoten 3/3/2/2/2, also vier uebervolle Ebenen,
    jede mit Ueberschuss 1 (ein Sammelknoten spart dort genau einen Platz -- das
    macht das Bild unuebersichtlicher, nicht klarer). Die Nachkorrektur hebt
    source auf volle Belegung und holt den einen Platz bei der Ebene mit dem
    groessten Ueberschuss, die ihn ohne Unterschreiten der Mindestquote
    (1 echter Knoten neben dem Sammler) abgeben kann: processing.
    """
    sketch = ArchitectureSketch(
        nodes=[
            *[_node(f"s{i}", f"Quelle {i}", SketchLayer.SOURCE) for i in range(4)],
            *[_node(f"p{i}", f"Schritt {i}", SketchLayer.PROCESSING) for i in range(4)],
            *[_node(f"a{i}", f"Modell {i}", SketchLayer.AI) for i in range(3)],
            *[_node(f"d{i}", f"Ablage {i}", SketchLayer.STORAGE) for i in range(3)],
            *[_node(f"o{i}", f"Ausgabe {i}", SketchLayer.OUTPUT) for i in range(2)],
        ],
        edges=[],
    )
    result = build_architecture_diagram(sketch, "de")

    # source zeigt jetzt alle vier Knoten statt zwei + Sammelknoten.
    assert "overflow_source" not in result
    assert all(f"s{i}([Quelle {i}])" in result for i in range(4))
    # Der eine Platz kam von processing -- dort steht jetzt "+ 3" statt "+ 2".
    assert "overflow_processing[+ 3 weitere]" in result
    # Budget unveraendert: 12 Plaetze, davon drei Sammelknoten (vorher vier).
    node_lines = [line for line in result.splitlines() if line.startswith("        ")]
    assert len(node_lines) == 12
    assert result.count("overflow_") == 3


def test_budget_donor_tie_is_broken_by_layer_enum_order() -> None:
    """Bei gleichem Ueberschuss gibt die vordere Ebene (Enum-Ordnung) den Platz ab.

    16 Knoten gleichmaessig auf vier Ebenen -> Basisquote 3 ueberall, vier
    Ebenen mit Ueberschuss 1. Erster Durchlauf: source wird voll, processing
    gibt ab (drei gleichwertige Kandidaten, processing kommt im Enum zuerst).
    Zweiter Durchlauf: ai wird voll, storage gibt ab (processing kann nicht
    mehr). Danach gibt es keinen "-1"-Fall mehr.
    """
    sketch = ArchitectureSketch(
        nodes=[
            *[_node(f"s{i}", f"Quelle {i}", SketchLayer.SOURCE) for i in range(4)],
            *[_node(f"p{i}", f"Schritt {i}", SketchLayer.PROCESSING) for i in range(4)],
            *[_node(f"a{i}", f"Modell {i}", SketchLayer.AI) for i in range(4)],
            *[_node(f"d{i}", f"Ablage {i}", SketchLayer.STORAGE) for i in range(4)],
        ],
        edges=[],
    )
    result = build_architecture_diagram(sketch, "de")

    assert "overflow_source" not in result
    assert "overflow_ai" not in result
    assert "overflow_processing[+ 3 weitere]" in result
    assert "overflow_storage[(+ 3 weitere)]" in result
    node_lines = [line for line in result.splitlines() if line.startswith("        ")]
    assert len(node_lines) == 12


def test_single_node_overflow_stays_when_no_layer_can_give_budget() -> None:
    """Gleichverteilung ueber fuenf Ebenen: der "-1"-Fall bleibt -- kein Budget da.

    16 Knoten in 4/3/3/3/3 -> Basisquoten 3/3/2/2/2. Vier Ebenen haben
    Ueberschuss 1, aber keine davon kann einen Platz abgeben: die drei mit
    Quote 2 wuerden auf 0 echte Knoten neben dem Sammler fallen, processing ist
    nicht uebervoll und wuerde selbst einen neuen Sammelknoten bekommen. Die
    Nachkorrektur laesst deshalb alles unveraendert, statt das Problem zu
    verschieben.

    Das ist eine harte arithmetische Grenze, keine Schwaeche der Regel: bei 12
    Plaetzen und 16 Knoten muessen 4 + (Zahl der Sammelknoten) Knoten verborgen
    werden, und eine Ebene mit hoechstens 4 Knoten verbirgt hoechstens 3.
    """
    sketch = ArchitectureSketch(
        nodes=[
            *[_node(f"s{i}", f"Quelle {i}", SketchLayer.SOURCE) for i in range(4)],
            *[_node(f"p{i}", f"Schritt {i}", SketchLayer.PROCESSING) for i in range(3)],
            *[_node(f"a{i}", f"Modell {i}", SketchLayer.AI) for i in range(3)],
            *[_node(f"d{i}", f"Ablage {i}", SketchLayer.STORAGE) for i in range(3)],
            *[_node(f"o{i}", f"Ausgabe {i}", SketchLayer.OUTPUT) for i in range(3)],
        ],
        edges=[],
    )
    result = build_architecture_diagram(sketch, "de")

    node_lines = [line for line in result.splitlines() if line.startswith("        ")]
    assert len(node_lines) == 12
    assert result.count("overflow_") == 4


def test_backward_edge_is_dropped() -> None:
    """Eine Kante gegen die Ebenen-Ordnung wird verworfen, die Vorwaertskante bleibt."""
    sketch = ArchitectureSketch(
        nodes=[
            _node("u", "Quelle", SketchLayer.SOURCE),
            _node("db", "Ablage", SketchLayer.STORAGE),
        ],
        edges=[
            SketchEdge(source="u", target="db"),
            SketchEdge(source="db", target="u", label="zurueck"),
        ],
    )
    result = build_architecture_diagram(sketch, "de")

    assert "    u --> db" in result
    assert "db --> u" not in result
    assert "zurueck" not in result


def test_same_layer_edge_is_kept() -> None:
    """Kanten INNERHALB einer Ebene sind nicht rueckwaerts -- sie bleiben."""
    sketch = ArchitectureSketch(
        nodes=[
            _node("p0", "A", SketchLayer.PROCESSING),
            _node("p1", "B", SketchLayer.PROCESSING),
        ],
        edges=[SketchEdge(source="p1", target="p0")],
    )
    assert "    p1 --> p0" in build_architecture_diagram(sketch, "de")


def test_self_edge_and_duplicates_are_dropped() -> None:
    """Selbstkante raus; bei Duplikaten gewinnt die erste (mit ihrem Label)."""
    sketch = ArchitectureSketch(
        nodes=[
            _node("a", "A", SketchLayer.SOURCE),
            _node("b", "B", SketchLayer.AI),
        ],
        edges=[
            SketchEdge(source="a", target="a", label="selbst"),
            SketchEdge(source="a", target="b", label="erste"),
            SketchEdge(source="a", target="b", label="zweite"),
        ],
    )
    result = build_architecture_diagram(sketch, "de")

    assert "a --> a" not in result
    assert "selbst" not in result
    assert "a -->|erste| b" in result
    assert "zweite" not in result


def test_edges_to_capped_nodes_are_dropped() -> None:
    """Eine Kante auf einen weggekappten Knoten verschwindet mit ihm."""
    sketch = ArchitectureSketch(
        nodes=[
            _node("src", "Quelle", SketchLayer.SOURCE),
            *[
                _node(f"n{i}", f"Schritt {i}", SketchLayer.PROCESSING)
                for i in range(15)
            ],
        ],
        edges=[
            SketchEdge(source="src", target="n0"),
            SketchEdge(source="src", target="n14"),
        ],
    )
    result = build_architecture_diagram(sketch, "de")

    assert "src --> n0" in result
    assert "src --> n14" not in result


def test_edge_cap_at_fifteen() -> None:
    """Mehr als 15 gueltige Kanten -> die ersten 15 gewinnen."""
    nodes = [_node("src", "Quelle", SketchLayer.SOURCE)]
    nodes += [_node(f"n{i}", f"S{i}", SketchLayer.PROCESSING) for i in range(11)]
    edges = [SketchEdge(source="src", target=f"n{i}") for i in range(11)]
    edges += [
        SketchEdge(source=f"n{i}", target=f"n{i + 1}") for i in range(10)
    ]  # 11 + 10 = 21 gueltige Kanten

    result = build_architecture_diagram(
        ArchitectureSketch(nodes=nodes, edges=edges), "de"
    )

    edge_lines = [line for line in result.splitlines() if "-->" in line]
    assert len(edge_lines) == 15


def test_long_labels_are_truncated_at_forty_chars() -> None:
    """Knoten- UND Kantenlabels werden bei >40 Zeichen mit "..." gekappt."""
    long_label = "A" * 55
    sketch = ArchitectureSketch(
        nodes=[
            _node("a", long_label, SketchLayer.SOURCE),
            _node("b", "B", SketchLayer.AI),
        ],
        edges=[SketchEdge(source="a", target="b", label="B" * 55)],
    )
    result = build_architecture_diagram(sketch, "de")

    assert f"a([{'A' * 37}...])" in result
    assert f"a -->|{'B' * 37}...| b" in result


def test_label_at_forty_chars_is_not_truncated() -> None:
    """Genau 40 Zeichen bleiben unangetastet -- die Grenze ist inklusiv."""
    label = "A" * 40
    sketch = ArchitectureSketch(
        nodes=[
            _node("a", label, SketchLayer.SOURCE),
            _node("b", "B", SketchLayer.AI),
        ],
        edges=[],
    )
    result = build_architecture_diagram(sketch, "de")

    assert f"a([{label}])" in result
    assert "..." not in result


def test_truncation_strips_trailing_space_before_ellipsis() -> None:
    """Faellt die Kappung auf ein Leerzeichen, entsteht kein " ..."."""
    # 37 Zeichen enden auf einem Leerzeichen -> rstrip() greift.
    label = "A" * 36 + " Rest der Beschreibung"
    sketch = ArchitectureSketch(
        nodes=[
            _node("a", label, SketchLayer.SOURCE),
            _node("b", "B", SketchLayer.AI),
        ],
        edges=[],
    )
    result = build_architecture_diagram(sketch, "de")

    assert f"a([{'A' * 36}...])" in result


def test_labels_are_escaped_before_truncation() -> None:
    """Form-brechende Zeichen werden entfernt, nie durchgereicht (ADR-0049)."""
    sketch = ArchitectureSketch(
        nodes=[
            _node("a", 'System "X" [beta] (v2)', SketchLayer.PROCESSING),
            _node("b", "Store <script>|{x}", SketchLayer.STORAGE),
        ],
        edges=[SketchEdge(source="a", target="b", label='ruft "auf" |x|')],
    )
    result = build_architecture_diagram(sketch, "de")

    assert '"System' not in result
    assert "<script>" not in result
    assert "|x|" not in result
    assert "System X beta v2" in result
    assert "Store scriptx" in result


def test_no_classdef_and_no_colors() -> None:
    """Kein classDef, kein style, keine Farben -- die Form traegt die Bedeutung."""
    sketch = ArchitectureSketch(
        nodes=[
            _node("a", "A", SketchLayer.SOURCE),
            _node("b", "B", SketchLayer.OUTPUT),
        ],
        edges=[SketchEdge(source="a", target="b")],
    )
    result = build_architecture_diagram(sketch, "de")

    assert "classDef" not in result
    assert "style " not in result
    assert "#" not in result
    assert result.startswith("flowchart LR")


def test_layer_catalog_parity_de_en() -> None:
    """Beide Sprachkataloge tragen alle fuenf Ebenen und keinen leeren Wert."""
    for lang in LANGS:
        assert set(SKETCH_LAYER_LABELS[lang]) == set(SketchLayer)
        assert all(SKETCH_LAYER_LABELS[lang].values())
        assert "{n}" in SKETCH_OVERFLOW_LABEL[lang]
