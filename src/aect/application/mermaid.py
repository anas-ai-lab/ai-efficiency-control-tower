"""Deterministischer Mermaid-Builder fuer Architektur-Skizzen (ADR-0049/0055).

Schicht: application -- importiert aus aect.application.structured_output,
aect.domain.i18n (reiner Typ + Sprach-Konvention) und Python stdlib. Importiert
NICHT aus aect.adapters.

Kernentscheidung (D18, ADR-0049): Das LLM erzeugt NIE Mermaid-Syntax, sondern
nur das schema-validierte Graph-JSON (ArchitectureSketch).
build_architecture_diagram() ist eine reine Funktion, die daraus deterministisch
die Mermaid-Zeichenkette baut. Das eliminiert die Syntaxfehler-Klasse (kein LLM
kann invalides Mermaid emittieren) und minimiert die Injection-Flaeche: nur die
Labels stammen aus dem Graph, und die werden vor der Einbettung escaped und
gekappt -- kein HTML, keine Form-brechenden Klammern.

Nachtrag ADR-0055: der Builder verantwortet jetzt auch das LAYOUT, nicht mehr
nur die Serialisierung. Er gruppiert die Knoten nach ihrer Fluss-Ebene
(SketchLayer) in Subgraphen, kappt auf eine lesbare Groesse und wirft Kanten
weg, die der Ebenen-Ordnung widersprechen. Damit entscheidet nicht mehr das LLM
ueber die Lesbarkeit der Skizze, sondern eine Regel, die man nachlesen kann.
Kein Mermaid-Rendering hier, nur String-Bau.
"""

from __future__ import annotations

from aect.application.structured_output import (
    ArchitectureSketch,
    SketchEdge,
    SketchLayer,
    SketchNode,
)
from aect.domain.i18n import Lang

# Zeichen, die eine Mermaid-Knoten-/Kantenform brechen oder HTML einschleusen
# koennten: Anfuehrungszeichen, alle Klammerarten, spitze Klammern, Pipe (Kanten-
# Label-Trenner) und Backtick. Sie werden aus jedem Label entfernt, bevor es in
# die Form eingesetzt wird -- die Node-ID selbst ist bereits per Pattern auf
# [a-z0-9_] beschraenkt und braucht kein Escaping.
_FORBIDDEN_LABEL_CHARS = frozenset('"[]{}()<>|`')

#: Maximale Knotenzahl IM DIAGRAMM. Bewusst kleiner als die Schema-Grenze
#: (ArchitectureSketch: 20): das Schema begrenzt, was das LLM ueberhaupt liefern
#: darf, diese Konstante begrenzt, was ein Mensch auf einen Blick liest.
_MAX_NODES = 12

#: Maximale Kantenzahl im Diagramm (nach allen Filtern).
_MAX_EDGES = 15

#: Maximale Label-Laenge im Diagramm. Laengere Labels werden hart gekappt und
#: mit "..." markiert -- ein 60-Zeichen-Label sprengt sonst die Knotenbreite.
_MAX_LABEL_LEN = 40

#: Subgraph-Titel je Fluss-Ebene. Liegt bewusst HIER und nicht in
#: domain/i18n.py: SketchLayer ist ein Application-Typ (Teil des LLM-Output-
#: Schemas), und die Domain darf nicht auf die Application zurueckimportieren.
#: Der Katalog gehoert damit zu seinem Enum, nicht zu den Domain-Katalogen.
SKETCH_LAYER_LABELS: dict[Lang, dict[SketchLayer, str]] = {
    "de": {
        SketchLayer.SOURCE: "Eingang",
        SketchLayer.PROCESSING: "Verarbeitung",
        SketchLayer.AI: "KI-Bausteine",
        SketchLayer.STORAGE: "Datenhaltung",
        SketchLayer.OUTPUT: "Ausgabe",
    },
    "en": {
        SketchLayer.SOURCE: "Input",
        SketchLayer.PROCESSING: "Processing",
        SketchLayer.AI: "AI components",
        SketchLayer.STORAGE: "Storage",
        SketchLayer.OUTPUT: "Output",
    },
}

#: Label des Sammelknotens, der die gekappten Knoten einer Ebene vertritt.
#: {n} ist die Zahl der NICHT gezeigten Knoten dieser Ebene.
SKETCH_OVERFLOW_LABEL: dict[Lang, str] = {
    "de": "+ {n} weitere",
    "en": "+ {n} more",
}

#: Kleinste Quote, mit der ein Sammelknoten noch sinnvoll ist: ein echter Knoten
#: daneben. Bei Quote 1 bliebe von der Ebene nur der Sammler uebrig.
_MIN_QUOTA_WITH_OVERFLOW = 2

#: Position jeder Ebene im Fluss -- die Enum-Reihenfolge ist die Ordnung. Wird
#: fuer den Rueckwaertskanten-Filter gebraucht.
_LAYER_INDEX: dict[SketchLayer, int] = {
    layer: index for index, layer in enumerate(SketchLayer)
}


def _escape_label(label: str) -> str:
    """Entfernt form-brechende und HTML-faehige Zeichen aus einem Label.

    Bewusst Entfernen statt Ersetzen: ein escaptes Sonderzeichen wuerde die
    Skizze nicht lesbarer machen, aber die Injection-Flaeche vergroessern.
    Mehrfache Leerzeichen (z. B. aus entfernten Klammerpaaren) werden geglaettet.
    """
    cleaned = "".join(c for c in label if c not in _FORBIDDEN_LABEL_CHARS)
    return " ".join(cleaned.split())


def _clean_label(label: str) -> str:
    """Escaped ein Label und kappt es auf _MAX_LABEL_LEN Zeichen.

    Reihenfolge ist load-bearing: erst escapen, dann kappen. Andersherum koennte
    das Kappen ein Ellipsen-Label erzeugen, dessen Rest noch ein verbotenes
    Zeichen traegt. Gekappt wird auf 37 Zeichen + "..."; das rstrip() verhindert
    ein " ..." mit haengendem Leerzeichen.
    """
    escaped = _escape_label(label)
    if len(escaped) <= _MAX_LABEL_LEN:
        return escaped
    return escaped[: _MAX_LABEL_LEN - 3].rstrip() + "..."


def _render_shape(node_id: str, label: str, layer: SketchLayer) -> str:
    """Baut die Mermaid-Knotenzeile: Form aus der Ebene, Text aus dem Label.

    source -> Stadium `([...])`, processing -> Rechteck `[...]`, ai -> Hexagon
    `{{...}}`, storage -> Zylinder `[(...)]`, output -> Subroutine `[[...]]`.
    """
    match layer:
        case SketchLayer.SOURCE:
            return f"{node_id}([{label}])"
        case SketchLayer.PROCESSING:
            return f"{node_id}[{label}]"
        case SketchLayer.AI:
            return f"{node_id}{{{{{label}}}}}"
        case SketchLayer.STORAGE:
            return f"{node_id}[({label})]"
        case SketchLayer.OUTPUT:
            return f"{node_id}[[{label}]]"
    raise AssertionError(f"unreachable: unhandled SketchLayer {layer}")


def _group_by_layer(
    nodes: list[SketchNode],
) -> dict[SketchLayer, list[SketchNode]]:
    """Gruppiert die Knoten nach Ebene -- Ebenen in Enum-, Knoten in Eingabefolge.

    Die Gruppen-Reihenfolge stammt aus SketchLayer, NICHT aus der Reihenfolge,
    in der das LLM die Knoten geliefert hat: die Skizze soll bei gleichem Graph
    gleich aussehen, egal in welcher Folge das Modell die Knoten aufzaehlt.
    Innerhalb einer Ebene bleibt die Eingabefolge erhalten (das ist die einzige
    Ordnung, die das Modell sinnvoll ausdruecken kann). Leere Ebenen fallen raus.
    """
    grouped: dict[SketchLayer, list[SketchNode]] = {layer: [] for layer in SketchLayer}
    for node in nodes:
        grouped[node.layer].append(node)
    return {layer: layer_nodes for layer, layer_nodes in grouped.items() if layer_nodes}


def _assign_quotas(
    grouped: dict[SketchLayer, list[SketchNode]],
) -> dict[SketchLayer, int]:
    """Verteilt die _MAX_NODES Diagramm-Plaetze auf die belegten Ebenen.

    Basisquote = _MAX_NODES // Zahl der belegten Ebenen; die Restquote geht
    Stueck fuer Stueck an die vorderen Ebenen (Enum-Reihenfolge). Eine Ebene,
    die ihre Quote nicht ausschoepft, vererbt den Rest an einen Pool, aus dem
    sich die NACHFOLGENDEN Ebenen bedienen -- so bleiben immer genau _MAX_NODES
    Plaetze im Spiel, statt sie an duenn besetzten Ebenen verfallen zu lassen.

    Die zugewiesene Quote ist die Zahl der PLAETZE, nicht der echten Knoten: bei
    einer uebervollen Ebene faellt einer der Plaetze an den Sammelknoten. Eine
    Ebene, die weniger braucht, bekommt genau ihre Belegung zugewiesen.
    """
    base, remainder = divmod(_MAX_NODES, len(grouped))
    quotas: dict[SketchLayer, int] = {}
    pool = 0

    for index, (layer, layer_nodes) in enumerate(grouped.items()):
        quota = base + (1 if index < remainder else 0) + pool
        if len(layer_nodes) <= quota:
            quotas[layer] = len(layer_nodes)
            pool = quota - len(layer_nodes)
        else:
            quotas[layer] = quota
            pool = 0

    return quotas


def _relax_single_node_overflows(
    quotas: dict[SketchLayer, int],
    occupancy: dict[SketchLayer, int],
) -> dict[SketchLayer, int]:
    """Loest Sammelknoten auf, die nur EINEN Platz sparen -- gegen Budget.

    Der degenerierte Fall der Quoten-Regel ist die annaehernde Gleichverteilung:
    liegt die Belegung einer Ebene nur um 1 ueber ihrer Quote, dann spart der
    Sammelknoten dort genau einen Platz -- er kostet aber selbst einen und
    verdeckt zwei echte Knoten. Vier solcher Ebenen machen das Bild
    unuebersichtlicher, nicht klarer.

    Korrektur, iterativ und deterministisch: die erste Ebene mit Ueberschuss 1
    (Enum-Reihenfolge) wird auf ihre volle Belegung angehoben. Den einen dafuer
    noetigen Platz gibt die Ebene mit dem GROESSTEN Ueberschuss ab -- bei
    Gleichstand entscheidet wieder die Enum-Reihenfolge. Kandidat ist nur, wer
    ohnehin schon einen Sammelknoten traegt (sonst entstuende ein neuer) und wer
    dabei nicht unter _MIN_QUOTA_WITH_OVERFLOW faellt.

    Findet sich kein Geber, bleibt der Fall wie er ist: die Gesamtzahl der
    Plaetze ist eine harte Grenze, und ein Sammelknoten mit zwei verdeckten
    Knoten ist immer noch besser als eine Ebene, die nur aus einem Sammler
    besteht. Terminiert, weil jeder Durchlauf genau einen Ueberschuss-1-Fall
    aufloest und keinen neuen erzeugt (der Geber hatte Ueberschuss >= 1 und hat
    danach >= 2).
    """
    relaxed = dict(quotas)

    while True:
        target = next(
            (
                layer
                for layer, quota in relaxed.items()
                if occupancy[layer] - quota == 1
            ),
            None,
        )
        if target is None:
            return relaxed

        candidates = sorted(
            (
                layer
                for layer, quota in relaxed.items()
                if layer is not target and occupancy[layer] > quota
            ),
            key=lambda layer: (
                -(occupancy[layer] - relaxed[layer]),
                _LAYER_INDEX[layer],
            ),
        )
        donor = next(
            (
                layer
                for layer in candidates
                if relaxed[layer] - 1 >= _MIN_QUOTA_WITH_OVERFLOW
            ),
            None,
        )
        if donor is None:
            return relaxed

        relaxed[target] = occupancy[target]
        relaxed[donor] -= 1


def _apply_node_cap(
    grouped: dict[SketchLayer, list[SketchNode]],
) -> tuple[dict[SketchLayer, list[SketchNode]], dict[SketchLayer, int]]:
    """Kappt auf _MAX_NODES Knoten und meldet je Ebene die Zahl der Verworfenen.

    Zwei Schritte: die Quoten-Verteilung (_assign_quotas) und die Nachkorrektur
    der Sammelknoten, die nur einen Platz sparen (_relax_single_node_overflows).

    Eine uebervolle Ebene zeigt quote-1 echte Knoten; der letzte Platz geht an
    einen Sammelknoten, der die Restzahl traegt. Bewusst nicht stilles Abschneiden:
    der Betrachter muss sehen, dass die Skizze unvollstaendig ist.

    Returns:
        (gekappte Gruppen, Zahl der verworfenen Knoten je uebervoller Ebene).
    """
    occupancy = {layer: len(layer_nodes) for layer, layer_nodes in grouped.items()}
    quotas = _relax_single_node_overflows(_assign_quotas(grouped), occupancy)

    kept: dict[SketchLayer, list[SketchNode]] = {}
    dropped: dict[SketchLayer, int] = {}

    for layer, layer_nodes in grouped.items():
        quota = quotas[layer]
        if len(layer_nodes) <= quota:
            kept[layer] = list(layer_nodes)
        else:
            kept[layer] = layer_nodes[: quota - 1]
            dropped[layer] = len(layer_nodes) - (quota - 1)

    return kept, dropped


def _filter_edges(
    edges: list[SketchEdge],
    layer_by_id: dict[str, SketchLayer],
) -> list[SketchEdge]:
    """Wirft Kanten weg, die das Layout brechen -- in fester Reihenfolge.

    1. Kanten an gekappte Knoten (die Ziel-ID gibt es im Diagramm nicht mehr).
    2. Rueckwaertskanten (Quell-Ebene liegt hinter der Ziel-Ebene): in einem
       `flowchart LR` erzeugen sie die Schleifen, die das Bild unlesbar machen.
       Der Datenfluss laeuft in dieser Skizze definitionsgemaess nach vorn.
    3. Selbstkanten (Quelle == Ziel).
    4. Duplikate desselben Knotenpaars -- die erste Kante gewinnt und behaelt
       damit ihr Label.
    5. Harte Kappung auf _MAX_EDGES.
    """
    filtered: list[SketchEdge] = []
    seen: set[tuple[str, str]] = set()

    for edge in edges:
        if edge.source not in layer_by_id or edge.target not in layer_by_id:
            continue
        if (
            _LAYER_INDEX[layer_by_id[edge.source]]
            > _LAYER_INDEX[layer_by_id[edge.target]]
        ):
            continue
        if edge.source == edge.target:
            continue
        pair = (edge.source, edge.target)
        if pair in seen:
            continue
        seen.add(pair)
        filtered.append(edge)
        if len(filtered) == _MAX_EDGES:
            break

    return filtered


def build_architecture_diagram(sketch: ArchitectureSketch, lang: Lang) -> str:
    """Baut aus einem validierten ArchitectureSketch die Mermaid-Zeichenkette.

    Reine Funktion, deterministisch: gleiche Eingabe -> exakt gleiche Ausgabe
    (snapshot-testbar). Kein classDef, keine Farben -- die Form traegt die
    Bedeutung, und ein farbloses Diagramm bleibt in hellem wie dunklem Theme
    lesbar, ohne dass der Builder das Theme kennen muesste.

    Aufbau: `flowchart LR`, danach je belegter Ebene ein `subgraph` mit den
    Knoten dieser Ebene, danach die gefilterten Kanten. Der Subgraph-Titel
    kommt aus SKETCH_LAYER_LABELS[lang] -- die Skizze wird bei jedem Lesen aus
    dem gespeicherten Graphen neu abgeleitet, deshalb traegt sie die Sprache
    des Aufrufs und nicht die der Erzeugung.

    Args:
        sketch: der schema-validierte Graph (bis zu 20 Knoten / 30 Kanten).
        lang: Anzeigesprache der Subgraph-Titel und des Sammelknotens.
    """
    grouped = _group_by_layer(list(sketch.nodes))
    kept, dropped = _apply_node_cap(grouped)

    layer_by_id = {node.id: layer for layer, nodes in kept.items() for node in nodes}

    lines = ["flowchart LR"]
    for layer, layer_nodes in kept.items():
        title = SKETCH_LAYER_LABELS[lang][layer]
        lines.append(f'    subgraph layer_{layer.value}["{title}"]')
        for node in layer_nodes:
            lines.append(
                f"        {_render_shape(node.id, _clean_label(node.label), layer)}"
            )
        if layer in dropped:
            overflow_label = SKETCH_OVERFLOW_LABEL[lang].format(n=dropped[layer])
            lines.append(
                f"        {_render_shape(f'overflow_{layer.value}', overflow_label, layer)}"
            )
        lines.append("    end")

    for edge in _filter_edges(list(sketch.edges), layer_by_id):
        if edge.label:
            lines.append(
                f"    {edge.source} -->|{_clean_label(edge.label)}| {edge.target}"
            )
        else:
            lines.append(f"    {edge.source} --> {edge.target}")

    return "\n".join(lines)
