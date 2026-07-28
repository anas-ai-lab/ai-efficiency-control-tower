# Portfolio-Matrix-Board: feste X-Achse, Breite, Legende — Design

Status: approved (2026-07-28)

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

- X-Achse fest auf 0–3.000.000 € (statt datengetrieben).
- Werte über 3 Mio. € werden am rechten Rand geklemmt und visuell markiert,
  nicht abgeschnitten.
- Chart nutzt die volle Breite des Seiten-Containers (nur `/board`).
- Horizontale, immer sichtbare Zonenfarb-Legende außerhalb der Plot-Fläche.
- Achsentitel X bekommt einen Richtungspfeil (DE+EN), Y bleibt unverändert.
- Unter `md` horizontales Scrollen statt gestauchter Achse.

## Bekannter Trade-off (bewusst akzeptiert)

`QUADRANT_X = 50_000` (bestehende statische Näherung an die
`LIKELY_WIN`-Schwelle, siehe `config/zone_thresholds.yaml:
min_expected_benefit_eur: 50000.0`) liegt bei einer 0–3-Mio-Achse auf ca. 1,7 %
der Achsenbreite. Realistische Case-Werte im Zehntausender-Bereich stauchen
sich links; Quick-Win/Avoid-Quadranten werden optisch schwerer unterscheidbar.
Das ist explizite Vorgabe (feste 0–3-Mio-Achse), keine Fehlkonfiguration.
Nutzer hat das nach Rückfrage bestätigt.

## Architektur / Änderungen

### 1. `frontend/src/lib/board-format.ts` (neu)

Reine, framework-freie Funktionen — testbar ohne React/next-intl-Kontext:

```ts
export const AXIS_MAX_EUR = 3_000_000;

export function formatAxisTickValue(value: number, locale: string): string {
  // dividiert durch 1 Mio., formatiert über Intl.NumberFormat(locale, ...).
  // value === 0 -> "0". Kein manuelles String-Bauen der Zahl selbst.
}

export function clampToAxisMax(
  value: number,
): { plotValue: number; clamped: boolean } {
  // value > AXIS_MAX_EUR -> { plotValue: AXIS_MAX_EUR, clamped: true }
  // sonst -> { plotValue: value, clamped: false }
}
```

Die lokalisierte Zahl aus `formatAxisTickValue` wird im Component mit dem
i18n-Key `xAxisTickCompact` kombiniert (`t("xAxisTickCompact", { value })`),
NICHT durch manuelle String-Konkatenation eines Einheiten-Suffix.

### 2. `frontend/src/components/board-matrix.tsx`

- `MatrixPoint` bekommt `plotX: number` (= `clampToAxisMax(x).plotValue`) und
  `clamped: boolean`. `x` bleibt der echte Wert (Tooltip).
- `xDomain`-`useMemo` entfällt. `XAxis`: `domain={[0, AXIS_MAX_EUR]}`,
  `allowDataOverflow={false}`, `dataKey="plotX"`,
  `ticks={[0, 500000, 1000000, 1500000, 2000000, 2500000, 3000000]}`,
  `tickFormatter={(v) => t("xAxisTickCompact", { value: formatAxisTickValue(v, locale) })}`.
  `locale` über `useLocale()` (next-intl), gleiches Muster wie
  `lang-toggle.tsx`.
- `<Scatter>`: `<Cell>`-Kinder werden durch einen custom `shape`-Handler
  ersetzt, der für `clamped === true` ein Dreieck (statt Kreis) in der
  Zonenfarbe zeichnet (`tokens[p.zone]`), sonst unverändert einen Kreis.
  Farbquelle bleibt ausschließlich der bestehende `useThemeTokens`-Hook
  (`getComputedStyle`) — keine CSS-Variablen direkt im SVG-`fill`.
  Klick-Handler (`router.push`) bleibt unverändert für beide Formen.
- Neuer Hinweistext (nur wenn `points.some(p => p.clamped)`): Marker-Legende
  "▶ über 3 Mio. €" / "▶ over €3M" (neuer i18n-Key `clampedNote`).
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
| `clampedNote` (neu) | "▶ über 3 Mio. €" | "▶ over €3M" |

`yAxisTitle` unverändert. Nach jeder Änderung `npm run i18n:check`
(Parität + Usage).

### 5. Tests — `frontend/src/lib/board-format.test.ts` (neu)

Neue devDependency `vitest` (kein bestehender JS-Unit-Test-Runner im Repo;
CI hat bisher nur eslint/tsc/Playwright-e2e/i18n-check). Neues npm-Script
`"test": "vitest run"`. Deckt ab:

- `formatAxisTickValue`: 0, 500000, 1500000, 3000000 je für `"de"` und
  `"en"` — erwartete Strings exakt.
- `clampToAxisMax`: Wert unter Max (unverändert, `clamped:false`), Wert
  exakt `AXIS_MAX_EUR` (Grenzfall, `clamped:false`), Wert über Max
  (`plotValue === AXIS_MAX_EUR`, `clamped:true`).

Vitest wird NICHT in `ci.yml` verdrahtet (separater Scope-Schritt, im
Abschlussreport als offener Punkt vermerkt).

## Nicht angetastet

- `QUADRANT_X`/`QUADRANT_Y`-Referenzlinien-Logik (Semantik unverändert).
- Y-Achse, Tooltip-Feldliste, Status-Filter, "How to read"-Panel-Struktur.
- `cases`/`monitoring`-Seiten-Breite.
- CI-Workflow (`ci.yml`) — Vitest bewusst nicht angeschlossen.

## Verifikation vor Abschluss

- `npm run --prefix frontend build` grün.
- `npx vitest run` (im frontend) grün.
- `npm run --prefix frontend i18n:check` grün.
- `uv run pytest -q` grün (unverändert, da kein Backend-Code berührt wird).
- Manuelle Prüfung Production-Build bei 1440px/390px, Light/Dark,
  Screenshots im Abschlussreport.
