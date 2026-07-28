# ADR-0055: Fluss-Ebenen statt Bausteintypen, Layout im Builder

**Status:** Accepted
**Datum:** 2026-07-28
**Autor:** Anas
**Nachtrag zu:** ADR-0049 (Architektur-Skizze als strukturierter Graph)

## Kontext

ADR-0049 hat die Skizze richtig aufgeteilt: das LLM liefert nur ein
schema-validiertes Graph-JSON, ein deterministischer Builder macht daraus
Mermaid. Diese Grenze bleibt. Was in der Praxis nicht traegt, ist die Seite
davon, die das AUSSEHEN bestimmt.

Zwei Befunde aus dem Demo-Betrieb:

**1. `kind` beschreibt die falsche Eigenschaft.** Die fuenf Werte (user, system,
ai_service, data_store, external) sagen, welcher SORTE ein Baustein angehoert.
Daraus laesst sich keine Anordnung ableiten -- "external" kann am Anfang oder am
Ende des Flusses stehen, "system" ueberall. Der Builder hatte deshalb kein
Layout-Wissen und legte die Knoten in der Reihenfolge ab, in der das LLM sie
aufzaehlte. Zwei Laeufe mit demselben Inhalt, aber anderer Aufzaehlungsreihenfolge
ergaben zwei verschieden aussehende Diagramme.

**2. Das LLM entschied ueber die Lesbarkeit.** Knotenzahl (max. 10),
Kantenmenge (max. 15) und Label-Laenge (max. 60 Zeichen) waren Schema-Grenzen.
Ein Modell, das 11 Knoten fuer noetig hielt, bekam einen 422 statt einer
gekuerzten Skizze -- die Grenze bestrafte den Inhalt, statt die Darstellung zu
regeln. Umgekehrt erzeugten 10 Knoten mit 60-Zeichen-Labels und
Rueckwaertskanten ein technisch valides, aber unlesbares Bild.

## Entscheidung

**`SketchNodeKind` wird durch `SketchLayer` ersetzt** -- ein Bedeutungswechsel,
kein Rename. Die fuenf Werte `source`, `processing`, `ai`, `storage`, `output`
beschreiben die POSITION eines Bausteins im Datenfluss. Die Enum-Reihenfolge ist
damit die Links-nach-rechts-Ordnung der Skizze und zugleich die Regel, welche
Kante vorwaerts (behalten) und welche rueckwaerts (verworfen) laeuft.

**Das Layout wandert vollstaendig in den Builder** (`build_architecture_diagram`,
application/mermaid.py). Er ist weiterhin eine reine, snapshot-getestete
Funktion und verantwortet jetzt zusaetzlich:

- **Gruppierung** in `subgraph`-Bloecke je belegter Ebene, in Enum-Reihenfolge
  (nicht in Eingabereihenfolge). Innerhalb einer Ebene bleibt die Eingabefolge.
  Leere Ebenen entfallen.
- **Knoten-Kappung auf 12.** Basisquote = 12 // belegte Ebenen, Restquote an die
  vorderen Ebenen; ungenutzte Quote wandert in einen Pool fuer spaetere Ebenen.
  Eine uebervolle Ebene zeigt `quote-1` echte Knoten plus einen Sammelknoten
  `overflow_<layer>` mit "+ n weitere" / "+ n more".
- **Nachkorrektur gegen degenerierte Sammelknoten.** Liegt die Belegung einer
  Ebene nur um 1 ueber ihrer Quote, spart ihr Sammelknoten genau einen Platz --
  er kostet aber selbst einen und verdeckt zwei echte Knoten. Solche Ebenen
  werden iterativ auf volle Belegung angehoben; den einen noetigen Platz gibt
  die Ebene mit dem groessten Ueberschuss ab (bei Gleichstand: Enum-Reihenfolge),
  sofern sie schon einen Sammelknoten traegt und dabei nicht unter "1 echter
  Knoten neben dem Sammler" faellt. Findet sich kein Geber, bleibt der Fall
  stehen -- 12 Plaetze sind eine harte Grenze, die keine Regel wegverteilt.
- **Kanten-Filter** in fester Reihenfolge: Kanten an gekappte Knoten raus,
  Rueckwaertskanten raus, Selbstkanten raus, Duplikate desselben Knotenpaars raus
  (erste gewinnt), dann Kappung auf 15.
- **Label-Kappung** auf 40 Zeichen (`label[:37].rstrip() + "..."`), fuer Knoten-
  und Kantenlabels, nach dem bestehenden Escaping.

**Die Schema-Grenzen werden geweitet** auf 2-20 Knoten und 0-30 Kanten. Das
Schema begrenzt jetzt nur noch, was ueberhaupt verwertbar ist
(Token-Flooding-Grenze, OWASP LLM10); ueber die Lesbarkeit entscheidet der
Builder.

**Das Diagramm wird beim LESEN neu abgeleitet.** `get_sketch()` ruft
`build_architecture_diagram(graph, lang)` frisch auf, statt den persistierten
`mermaid_source` zu lesen. Der Schluessel bleibt aus Altbestands-Gruenden in der
JSON-Spalte, wird aber ignoriert. Beide Sketch-Endpoints tragen dafuer einen
`lang`-Parameter.

**Kein `classDef`, keine Farben** im erzeugten Mermaid. Die Form traegt die
Bedeutung (source=Stadium, processing=Rechteck, ai=Hexagon, storage=Zylinder,
output=Subroutine).

## Begruendung

| Alternative | Warum verworfen |
|---|---|
| `kind` behalten, Layout per Heuristik ableiten | Die Heuristik muesste raten, wo ein "system" im Fluss steht -- eine zweite, unbelegte Wahrheit neben dem Modell-Output |
| Layout vom LLM mitliefern lassen (Positionen/Ranks) | Genau die Klasse von Entscheidung, die ADR-0049 dem LLM abgenommen hat; nicht deterministisch, nicht snapshot-testbar |
| Harte Schema-Grenze bei 12 Knoten | Bestraft den Inhalt fuer ein Darstellungsproblem: der Nutzer bekommt einen 422 statt einer gekuerzten Skizze |
| `mermaid_source` beim Erzeugen einfrieren | Die Skizze bliebe fuer immer in der Sprache und der Layout-Regel ihres Erzeugungszeitpunkts; eine Regel-Aenderung wuerde alte Cases nie erreichen |
| Farbige Ebenen per `classDef` | Muesste das Theme des Betrachters kennen (hell/dunkel) -- der Builder kennt es nicht und soll es nicht kennen |

Der Sammelknoten statt stillem Abschneiden ist die Fail-loud-Anwendung auf die
Darstellung: eine gekuerzte Skizze, die aussieht wie eine vollstaendige, ist
genau der plausibel wirkende Fehler, den die Projekt-Regel verbietet.

Die Re-Ableitung beim Lesen folgt derselben Linie wie die
Read-Rand-Re-Ableitung der Routing-/Vorfilter-Texte aus V4.1-S6: die
persistierte Wahrheit ist der Graph, alles Darstellbare wird daraus abgeleitet.

## Konsequenzen

**Positiv:**
- Gleicher Graph -> gleiche Skizze, unabhaengig von der Aufzaehlungsreihenfolge
  des Modells.
- Die Skizze bleibt lesbar, auch wenn das Modell grosszuegig modelliert.
- Sprachwechsel wirkt sofort auf bestehende Skizzen, ohne Regenerieren.
- Layout-Regel-Aenderungen erreichen Altbestand ohne Migration.

**Negativ / Trade-offs:**
- Vor-ADR-0055-Skizzen (`kind` im persistierten Graphen) validieren nicht mehr.
  Bewusst KEINE Migration: die Skizze ist per D20 (ADR-0049) ein wegwerfbares
  Derivat. `GET /architecture-sketch` faengt die ValidationError ab, loggt
  `sketch_schema_stale` und liefert `200 {"sketch": null}` -- der Nutzer sieht
  den Erzeugen-Button und ist mit einem Klick wieder aktuell. Ein 500 waere hier
  falsch: der Case ist intakt, nur sein Derivat nicht.
- Ein Case mit vielen Bausteinen zeigt weniger, als der Graph traegt. Der
  Sammelknoten macht das sichtbar; das vollstaendige `nodes`/`edges`-Array
  bleibt in der API-Antwort.
- Der Builder ist deutlich mehr Logik als vorher (Quoten, Filter, Kappung) --
  aber alles davon rein und testbar, im Gegensatz zu einer Prompt-Regel.

**Neutral / Folgeentscheidungen:**
- Neuer Prompt `prompts/architecture_sketch/v2/` (Ebenen statt Typen, 20/30 als
  Grenzen, expliziter Hinweis auf den Vorwaerts-Fluss). v1 bleibt unberuehrt im
  Repo liegen.
- Das API-Feld heisst `layer` statt `kind` (Frontend-Typen nachgezogen). Das
  Frontend rendert ohnehin nur `mermaid_source`; `nodes`/`edges` sind dort
  Vertrag, kein Verbraucher.
- `409` bei fehlendem Loesungsvorschlag traegt jetzt ein typisiertes Detail
  (`{"code": "sketch_no_proposal", "message": ...}`) analog dem 422-Muster bei
  /sharpen und /propose-solution -- ein Sprachwechsel darf die
  Fehlerbehandlung im Frontend nicht brechen.
- `SKETCH_LAYER_LABELS` liegt in `application/mermaid.py`, NICHT in
  `domain/i18n.py`: `SketchLayer` ist ein Application-Typ (Teil des
  LLM-Output-Schemas), und die Domain darf nicht auf die Application
  zurueckimportieren. Der Katalog gehoert zu seinem Enum.
