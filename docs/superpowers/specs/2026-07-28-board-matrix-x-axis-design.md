# Portfolio-Matrix-Board: X-Achse, Breite, Legende — Design

Status: approved (2026-07-28), X-Achsen-Abschnitt korrigiert (2026-07-28)

> **Korrektur 2026-07-28:** Die ursprünglich spezifizierte feste 0–3-Mio-€-Achse
> ist ersetzt durch eine dynamische Nice-Number-Achse (Abschnitte "Ziel",
> "Dynamische Nice-Number-Domain", 1, 2, 4, 5). Grund siehe
> "Warum keine feste Achse". Der X-Achsen-Teil ist bereits umgesetzt; Breite
> (Abschnitt 3), horizontale Zonenlegende und Achsentitel-Pfeil stehen noch aus.

## Kontext

`BoardMatrix` (`frontend/src/components/board-matrix.tsx`) zeigt bewertete Use
Cases als Scatter (recharts): x = erwarteter Nettonutzen/Jahr (EUR), y =
Machbarkeit (invertierter Aufwand-Score 1-9), Blasengröße = eingesparte
Stunden/Jahr, Farbe = Triage-Zone. Aktuell berechnet die Komponente die
X-Domain dynamisch aus den Daten (`xDomain`-`useMemo`) und nutzt die volle
Container-Breite nicht (Seite ist auf `max-w-5xl` begrenzt). Es existiert
kein recharts-`<Legend>` — die Zonenfarben stehen nur als vertikale Liste im
aufklappbaren "How to read"-Panel neben dem Chart.

## Ziel

- X-Achse skaliert aus den Daten, Obergrenze auf eine runde Zahl gehoben
  (Nice-Number-Domain) — die Punktwolke nutzt die volle Chart-Breite.
- Achsenskala ist filterunabhängig: Datenbasis sind alle Cases, nicht die
  gefilterte Teilmenge.
- Chart nutzt die volle Breite des Seiten-Containers (nur `/board`).
- Horizontale, immer sichtbare Zonenfarb-Legende außerhalb der Plot-Fläche.
- Achsentitel X bekommt einen Richtungspfeil (DE+EN), Y bleibt unverändert.
- Unter `md` horizontales Scrollen statt gestauchter Achse.

## Warum keine feste Achse

Eine feste 0–3-Mio-€-Achse war die ursprüngliche Vorgabe. Sie scheitert an der
realen Wertverteilung: Nettonutzen-Werte liegen überwiegend im fünfstelligen
Bereich, die gesamte Punktwolke staucht sich damit auf die linken ~2 % der
Achse. Das Chart soll Cases gegeneinander einordnen — bei dieser Stauchung sind
zwei Cases mit 20.000 € und 60.000 € optisch nicht mehr unterscheidbar, obwohl
der Unterschied genau die Aussage ist.

Mit einer datengetriebenen Domain entfallen zwei Folgekonstrukte ersatzlos:
Klemm-Logik für Überlauf-Werte und der Dreieck-Marker, der geklemmte Punkte
kennzeichnet. Punkte können nicht mehr außerhalb der Achse liegen, wenn die
Achse aus den Punkten selbst berechnet wird.

## Quadranten entfallen

Die `QUADRANT_X`-Hilfslinie (50.000 €) und die vier Ecklabels
(`quadNiceToHave`/`quadQuickWins`/`quadAvoid`/`quadStrategic`) werden ersatzlos
entfernt. Bei realistischer Wertverteilung (überwiegend fünfstellige
Nettonutzen) liegen praktisch alle Punkte auf derselben Seite der Linie — drei
der vier aufgespannten Quadranten bleiben dauerhaft leer und suggerieren eine
Trennschärfe, die die Daten nicht hergeben.

`QUADRANT_Y = 5` (Machbarkeits-Mittellinie) bleibt unverändert: die
Composite-Skala ist fest 1–9, ihre Mitte ist datenunabhängig sinnvoll. Die
Quadranten-Problematik betraf ausschließlich die X-Achse.

## Dynamische Nice-Number-Domain

- **Domain-Max** = kleinste Zahl der Folge {1, 2, 2.5, 5, 10} × 10^n, die
  ≥ `1,15 × höchster net_expected_benefit_eur` ist. Der Faktor 1,15 ist Luft,
  damit die äußerste Blase nicht am Achsenrand klebt.
- **Domain-Min** = `min(0, kleinster Wert)` — wie zuvor. Nettonutzen kann
  rechnerisch negativ sein; 0 bleibt sonst der linke Rand.
- **Datenbasis**: ALLE Cases aus dem `cases`-Prop, ungefiltert. Eine Achse, die
  bei jedem Filterklick neu skaliert, verändert die optische Distanz zwischen
  zwei Punkten, obwohl sich deren Werte nicht geändert haben. Das untergräbt
  den Zweck des Charts (Portfolio-Einordnung) — ein Interpretationsrisiko,
  keine Performance-Frage.
- **Ticks**: 4–6 Stück, Vielfache eines runden Schritts zwischen 0 und
  Domain-Max (Beispiel: Max = 200.000 → Schritt 50.000 →
  0/50k/100k/150k/200k). Der negative Teilbereich bekommt keinen eigenen Tick;
  bewusst akzeptiert, da er nur bei defizitären Cases auftritt.
- **Tick-Format** schaltet nach Domain-Max: ≥ 1.000.000 → Mio-Kompaktformat
  (`Intl.NumberFormat` + i18n-Key `xAxisTickCompact`); < 1.000.000 → voller
  EUR-Betrag über den bestehenden `fmt.eur()`-Formatter (`lib/use-format.ts`).
  Bei fünfstelligen Portfolios wäre "0,1 Mio €" schlechter lesbar als "100.000 €".

## Architektur / Änderungen

### 1. `frontend/src/lib/board-format.ts` (neu)

Reine, framework-freie Funktionen — testbar ohne React/next-intl-Kontext:

```ts
export function computeNiceDomainMax(maxValue: number): number {
  // kleinste Zahl aus {1,2,2.5,5,10} x 10^n mit candidate >= maxValue * 1.15.
  // maxValue <= 0 (leeres/defizitäres Portfolio) -> Default 100_000: die Achse
  // braucht trotzdem eine Skala, und 100k deckt den typischen Einzel-Case ab.
  // Deterministisch — keine Zufalls-/Heuristik-Rundung außerhalb der Folge.
}

export function computeAxisTicks(domainMax: number, count?: number): number[] {
  // 0 .. domainMax als Vielfache eines runden Schritts. Ohne `count` wird die
  // Teilung gewählt (5, sonst 4 Intervalle), deren Schritt selbst eine
  // Nice-Number ist -> 6 bzw. 5 Ticks.
}

export function formatAxisTickValue(value: number, locale: string): string {
  // dividiert durch 1 Mio., formatiert über Intl.NumberFormat(locale, ...).
  // value === 0 -> "0". Kein manuelles String-Bauen der Zahl selbst.
}
```

Die lokalisierte Zahl aus `formatAxisTickValue` wird im Component mit dem
i18n-Key `xAxisTickCompact` kombiniert (`t("xAxisTickCompact", { value })`),
NICHT durch manuelle String-Konkatenation eines Einheiten-Suffix.

Keine `clampToAxisMax`-Funktion und keine `AXIS_MAX_EUR`-Konstante: mit
datengetriebener Domain gibt es keine Überlauf-Werte (siehe "Warum keine feste
Achse").

### 2. `frontend/src/components/board-matrix.tsx`

- `MatrixPoint` bleibt unverändert; `dataKey="x"` bleibt der echte Wert.
- `xDomain`-`useMemo` bleibt, rechnet aber über **alle** `cases` (Prop vor
  jeder Filterung), nicht über `points`/`filtered`, und liefert zusätzlich die
  Tick-Liste:
  `max = computeNiceDomainMax(Math.max(0, ...xs))`,
  `xDomain = [Math.min(0, ...xs), max]`, `xTicks = computeAxisTicks(max)`.
- `XAxis`: `domain={xDomain}`, `ticks={xTicks}`,
  `tickFormatter` verzweigt nach `xDomain[1] >= 1_000_000` →
  `t("xAxisTickCompact", { value: formatAxisTickValue(v, locale) })`, sonst
  `fmt.eur(v)`. `locale` über `useLocale()` (next-intl), gleiches Muster wie
  `lang-toggle.tsx`.
- `<Scatter>` bleibt bei `<Cell>`-Kindern (Kreise in Zonenfarbe aus
  `useThemeTokens`). Kein `shape`-Handler, kein Dreieck-Marker, kein
  `clampedNote`-Hinweistext.
- `ReferenceLine` bei `QUADRANT_X` und die vier absolut positionierten
  Quadranten-Ecklabel-`<span>`s entfallen; damit auch die Konstante
  `QUADRANT_X` und das `relative` am Chart-Wrapper.
  Die `QUADRANT_Y`-`ReferenceLine` bleibt unberührt.
- Neue horizontale Zonenfarb-Legende: eigene Zeile zwischen Chart-Box und der
  bestehenden `effortScoreNote`/`bubbleNote`-Zeile. Iteriert
  `["LIKELY_WIN","CALCULATED_RISK","MARGINAL_GAIN"]`, nutzt
  `ZONE_CONFIG[z].dot`/`.text` + `tz(\`${z}.label\`)` — gleiches Muster wie die
  bestehende Liste im "How to read"-Panel (bleibt zusätzlich unverändert
  bestehen, keine Entfernung).
- Responsive: der Grid-Wrapper (`grid-cols-[1.25rem_1fr]`, Zeile ~281) bekommt
  einen äußeren `overflow-x-auto`-Wrapper mit `min-w-[42rem]` auf dem Grid
  selbst; ab `md` bleibt `w-full`/100%-Verhalten unverändert.

### 3. `frontend/src/app/board/page.tsx`

`<main className="mx-auto max-w-5xl ...">` → `max-w-7xl`. Nur diese Seite;
`cases`/`monitoring` bleiben unverändert (kein shared Admin-Layout).

### 4. i18n (`frontend/messages/de.json`, `en.json`, Namespace `board`)

| Key | DE | EN |
|---|---|---|
| `xAxisTitle` (geändert) | "Erwarteter Nettonutzen / Jahr →" | "Expected net benefit / year →" |
| `xAxisTickCompact` (neu) | "{value} Mio €" | "{value}M €" |
| `quadNiceToHave`/`quadQuickWins`/`quadAvoid`/`quadStrategic` | entfernt | entfernt |

Kein `clampedNote`-Key (keine Klemm-Logik mehr). `yAxisTitle` unverändert.
Nach jeder Änderung `npm run i18n:check` (Parität + Usage).

### 5. Tests — `frontend/src/lib/board-format.test.ts` (neu)

Neue devDependency `vitest` (kein bestehender JS-Unit-Test-Runner im Repo;
CI hatte bisher nur eslint/tsc/Playwright-e2e/i18n-check). Neues npm-Script
`"test": "vitest run"`, `vitest.config.ts` mit `include: ["src/**/*.test.ts"]`
— sonst zieht der Default-Glob die Playwright-Specs aus `e2e/` mit ein.
Deckt ab:

- `computeNiceDomainMax`: Wert knapp unter / knapp über einer Nice-Stufe
  (43.478 → 50.000 vs. 43.480 → 100.000), 2,5er-Stufe (200.000 → 250.000),
  Zehntausender- und Millionen-Bereich, `0` und negativer Wert → Default.
- `computeAxisTicks`: 1er-/2er-/2,5er-Stufe und Millionen-Bereich mit exakter
  Tick-Liste, 4–6-Tick-Korridor über mehrere Stufen, explizite `count`,
  `domainMax = 0` → `[0]`.
- `formatAxisTickValue`: 0, 500000, 1500000, 3000000 je für `"de"` und
  `"en"` — erwartete Strings exakt.

Vitest wird in `ci.yml` (Job `frontend-quality`, Schritt nach eslint)
verdrahtet.

## Nicht angetastet

- `QUADRANT_Y`-Referenzlinie (Semantik unverändert).
- Y-Achse, Tooltip-Feldliste, Status-Filter, "How to read"-Panel-Struktur.
- `cases`/`monitoring`-Seiten-Breite.

## Verifikation vor Abschluss

- `npm run --prefix frontend build` grün.
- `npm run --prefix frontend test` (vitest) grün.
- `npm run --prefix frontend i18n:check` grün.
- `uv run pytest -q` grün (unverändert, da kein Backend-Code berührt wird).
- Manuelle Prüfung Production-Build bei 1440px/390px, Light/Dark,
  Screenshots im Abschlussreport.
