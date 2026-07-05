# 0047 -- Portfolio-Board: Nutzen-Machbarkeits-Matrix (recharts)

**Status:** Accepted
**Datum:** 2026-07-05
**Phase:** G (Post-v1-Audit)

## Kontext

Mit dem Lifecycle-Status (ADR-0045) und der CaseSummary-Projektion (P2) liegen
alle bewerteten Cases als Liste vor. Eine Liste beantwortet "welche Cases gibt
es?", aber nicht "wo im Portfolio steht jeder Case relativ zu den anderen?".
Fuer eine Priorisierungssicht -- viel Nutzen bei geringem Aufwand zuerst --
braucht es eine zweidimensionale Streuung, keine Tabelle.

Die Rohdaten dafuer liegen bereits in der CaseSummary: `net_expected_benefit_eur`,
`composite_total` (Aufwand-Score 2-10) und `hours_per_year`. Gesucht ist eine
reine Lese-/Visualisierungsschicht im Frontend -- kein neuer Backend-Endpoint,
keine neue Geschaeftsregel.

## Entscheidung

Wir rendern ein **Streudiagramm (Bubble-Scatter)** mit `recharts` auf der
`/board`-Route. Die Achsen:

- **x-Achse: erwarteter Nettonutzen pro Jahr** (`net_expected_benefit_eur`) --
  NETTO, nicht das theoretische Brutto-Potenzial. Der Nettowert ist Potenzial x
  Nutzungsfaktor x Evidenzfaktor abzueglich Lizenzkosten; er ist die
  entscheidungsrelevante Zahl (was bleibt real uebrig), waehrend das Brutto-
  Potenzial vor Abzuegen systematisch zu optimistisch ist und Cases mit hohen
  Lizenzkosten faelschlich nach rechts zoege.
- **y-Achse: Machbarkeit** -- der `composite_total`-Aufwand-Score (2-10)
  **invertiert** dargestellt (recharts `reversed`): oben = niedriger Aufwand =
  hohe Machbarkeit. Invertiert, damit die intuitive "gut = oben rechts"-Lesart
  gilt (hoher Nutzen + hohe Machbarkeit = Quick Win). Ein nicht invertierter
  Aufwand-Score haette "gut" nach unten rechts verschoben -- gegen die
  Konvention der Nutzwert-Machbarkeits-Matrix.
- **Blasengroesse: eingesparte Stunden pro Jahr** (`hours_per_year`) -- eine
  dritte Dimension ohne dritte Achse.
- **Farbe: Triage-Zone** (`--zone-*`-Tokens, konsistent mit dem restlichen UI).

Cases ohne vollstaendige Bewertung (Vorfilter nicht bestanden -> zone/net/
composite/hours gemeinsam `null`) erscheinen nicht als Punkt, sondern als
Rest-Zaehler mit Verweis auf die Ideenliste.

## Begruendung

**recharts als neue Dependency (statt custom SVG):**

| Alternative | Warum verworfen |
|---|---|
| Custom SVG von Hand (kein neues Paket) | Ein Scatter mit korrekt skalierten Achsen, invertierter y-Domain, Bubble-ZAxis, Tooltip mit Hit-Testing, responsivem Reflow und Klick-Navigation ist genau die Menge Arbeit, die eine Chart-Lib loest. Selbstbau haette Achsen-Ticks, Domain-Padding, Hover-Treffererkennung und ResizeObserver-Logik reproduziert -- viel fehleranfaelliger Code fuer null Differenzierung. Der Nettonutzen einer Portfolio-Ansicht liegt in der Aussage, nicht in einer handgeschriebenen Rendering-Engine. |
| Schwergewichtige Viz-Lib (D3 direkt, Plotly) | D3 ist maechtig, aber imperativ und React-fremd (eigene DOM-Kontrolle) -- unnoetige Reibung fuer ein einzelnes Chart. Plotly ist gross (Bundle) und bringt Interaktivitaet mit, die hier nicht gebraucht wird. recharts ist deklarativ, React-nativ (Komposition aus `<ScatterChart>`/`<XAxis>`/`<Scatter>`) und passt zum bestehenden Komponentenmodell. |

Die Dependency ist bewusst und dokumentiert (`frontend/package.json`,
`recharts ^3.9.2`). Ein Chart ist kein Anlass, eine Rendering-Engine selbst zu
schreiben -- dieselbe Build-vs-Buy-Abwaegung wie bei Formular-Validierung (zod)
oder UI-Primitives (shadcn/ui).

Eine Reibung ist dokumentiert: recharts setzt `fill`/`stroke` als SVG-Attribut,
in dem `var(--token)` NICHT aufgeloest wird. Die konkreten Farbstrings werden
darum via `getComputedStyle` gelesen und bei `.dark`-Wechsel auf `<html>` per
`MutationObserver` neu aufgeloest (`board-matrix.tsx`).

**Quadranten-Linien sind reine Visualisierung, keine Schwellen:**

Die zwei gestrichelten `ReferenceLine`s (x = 50.000 EUR, y = 6) und die vier
Ecklabels ("Quick Wins", "Nice to have", "Strategische Wetten", "Vermeiden")
sind eine **statische Lese-Hilfe**, KEINE aus der Config gelesene Geschaeftsregel.
50.000 EUR ist optisch an die LIKELY_WIN-Groessenordnung angelehnt, aber
bewusst hartcodiert: das Backend exponiert die Schwellen aus
`zone_thresholds.yaml` nicht, und die Zonen-Farbe der Punkte transportiert die
tatsaechliche Triage-Entscheidung bereits. y = 6 ist schlicht die Mitte der
Aufwand-Skala (2-10). Die Linien gruppieren visuell, sie klassifizieren nicht.
Diese Trennung ist explizit dokumentiert (Code-Kommentar `QUADRANT_X` +
known_limitations #17), damit die Hilfslinie nie mit einer Schwelle verwechselt
wird.

## Konsequenzen

**Positiv:**
- Portfolio-Priorisierung auf einen Blick: Nutzen gegen Machbarkeit, Zone als
  Farbe, Einsparvolumen als Blasengroesse -- vier Dimensionen in einem Chart.
- Keine neue Backend-Flaeche: rein aus der bestehenden CaseSummary gerendert,
  kein neuer Endpoint, keine neue Geschaeftsregel.
- Konsistent mit dem UI-Farbsystem (`--zone-*`-Tokens, Dark-Mode-fest).
- Klick auf einen Punkt navigiert in das Case-Detail -- die Matrix ist ein
  Einstieg, keine Sackgasse.

**Negativ / Trade-offs (die bewusste Deckung):**
- **Neue Frontend-Dependency** (recharts + transitive). Bewusst akzeptiert;
  Build-vs-Buy zugunsten Buy wie oben begruendet.
- **Quadranten-Linien koennen ueberlesen als Schwellen wirken.** Gegen-
  massnahme: Achsen-Untertitel, Erklaer-Panel und known_limitations #17 machen
  den Platzhalter-Charakter explizit.
- **getComputedStyle/MutationObserver-Kopplung an das Token-System.** Notwendig,
  weil recharts CSS-Variablen nicht aufloest -- eine dokumentierte Reibung, kein
  sauberer Mechanismus.

**Neutral / Folgeentscheidungen:**
- Keine serverseitige Aggregation/Paginierung -- die komplette (bereits
  vorhandene) Case-Liste wird client-seitig gefiltert und projiziert. Analog zur
  CaseSummary-Entscheidung (P2) fuer die Datenmenge eines privaten Portfolio-
  Builds ausreichend; Migrationstrigger bei echtem Volumen.
