# ADR-008: Abschaltbares Config-Layering (layer_local) fuer CI-reproduzierbare Eval-Artefakte

**Status:** Accepted
**Datum:** 2026-07-12
**Autor:** Anas

## Kontext

`load_roi_config()` (`src/aect/domain/roi.py`) layert seit dem V4-Config-Layering
(SDR-0003 Abschnitt 5) automatisch `config/roi_config.local.toml` ueber die
getrackte Platzhalter-Config `config/roi_config.toml`, sobald die local-Datei
neben der Basis existiert. Die local-Datei ist gitignored (echte Stundensaetze je
Land x Level, IP-Trennung) und in CI nicht vorhanden.

Drei Eval-Scripts erzeugen committete Artefakte ueber genau diesen Loader:
`run_golden_eval.py` -> `evals/golden/report.json`, `run_score_breakdown.py` ->
`evals/golden/score_breakdown.json`, `zone_threshold_backtest.py` ->
`scripts/analysis/zone_threshold_backtest_results.json`. Weil der Loader lokal die
realen Raten einmischt, wurden diese Artefakte mit local-Raten committed. CI
rechnet ohne local mit Platzhaltern -- unterschiedliche `expected_benefit_eur`,
und golden-018 kippt ueber die `likely_win_min_benefit`-Schwelle (50000 EUR):
62562,50 EUR (lokal -> LIKELY_WIN) vs. 43312,50 EUR (Platzhalter ->
CALCULATED_RISK). Der Regressionstest `test_baseline_reproduces_golden_report_exactly`
schlug in CI mit `assert 15 == 14` fehl, weil die committete `report.json` (14/24,
lokal) nicht dem CI-Ergebnis (15/24, Platzhalter) entspricht.

Zwei Anforderungen stehen dabei in Spannung: (1) committete Eval-Artefakte muessen
CI-reproduzierbar sein (nur getrackte Config), (2) derselbe Test muss lokal gruen
bleiben, waehrend `local.toml` vorhanden ist. Zusaetzlich sollen keine
local-rate-abgeleiteten EUR-Werte in oeffentlichen Artefakten stehen (IP-Trennung).

## Entscheidung

Wir ergaenzen `load_roi_config()` um einen additiven, keyword-only Parameter
`layer_local: bool = True`. Der Default haelt das Runtime-Verhalten unveraendert
(App/Adapter layern local weiter). Nur `layer_local=False` ueberspringt den
local-Merge und erzwingt reine Platzhalter-Config. Die drei Eval-Scripts und der
Backtest-Test rufen `load_roi_config(..., layer_local=False)` -- ihre Artefakte
haengen damit deterministisch an der getrackten Config, unabhaengig davon, ob
`local.toml` vorhanden ist.

## Begruendung

| Alternative | Warum verworfen |
|---|---|
| (a) Kein Struktur-Eingriff, Entwickler-Disziplin | Vor jedem Commit `local.toml` temporaer entfernen und Artefakte neu erzeugen. Fragil, nicht erzwingbar, fehleranfaellig -- und der Test layert lokal weiter local ein, waere also lokal rot, sobald die Artefakte auf Platzhalter stehen. Loest die Spannung (1) vs. (2) nicht. |
| (b) Separater Platzhalter-Loader in den Scripts | Eigener Lade-/Konstruktions-Pfad nur fuer die Eval-Scripts, ohne `load_roi_config` anzufassen. Dupliziert die `ROIConfig`-Konstruktion (Decimal-Casts, KeyError-fail-loud, Section-Mapping) -- Drift-Risiko gegen den Domain-Loader, zwei Wahrheiten fuer dasselbe Schema. |
| (c) Additiver `layer_local`-Parameter am Domain-Loader (gewaehlt) | Eine Codestelle, rueckwaertskompatibel (Default = Status quo), keine Duplikation. Runtime unveraendert; nur die Artefakt-Erzeugung und ihre Verifikation waehlen explizit die reine Platzhalter-Config. |

Option (c) ist die kleinste Aenderung, die beide Anforderungen erfuellt: die
committeten Artefakte werden CI-reproduzierbar, und der Test bleibt lokal gruen,
weil er dieselbe `layer_local=False`-Semantik nutzt wie der Generator. Kein
Eingriff in Zonen-/Scoring-Logik, keine Schwellen-Aenderung.

## Konsequenzen

**Positiv:**
- `report.json` / `score_breakdown.json` / `backtest_results.json` sind aus der
  getrackten Config allein reproduzierbar -- CI == lokal, unabhaengig von
  `local.toml`.
- Keine local-rate-abgeleiteten EUR-Werte mehr in oeffentlichen Artefakten
  (score_breakdown.json trug zuvor z. B. 62562,50 EUR aus realen Raten).
- Runtime/Adapter unveraendert: die App layert local weiter (Default True), die
  reale ROI-Rechnung fuer den Demo-Betrieb bleibt wie zuvor.

**Negativ / Trade-offs:**
- Zwei Config-Semantiken koexistieren (mit/ohne Layering). Wer ein neues
  committetes Config-abhaengiges Artefakt erzeugt, muss `layer_local=False` aktiv
  waehlen -- vergisst er es, kehrt die local-Kontamination zurueck. Konvention,
  kein Zwang (dokumentiert in den Script-Kommentaren + diesem ADR).

**Neutral / Folgeentscheidungen:**
- Die committeten Golden-Zahlen verschieben sich von 14/24 (58,3 %, kappa 0,25;
  local-kontaminiert) auf 15/24 (62,5 %, kappa 0,34; Platzhalter). Nur golden-018
  wechselt die Zone; `known_limitations.md` #26 und der README-Eval-Abschnitt sind
  auf die Platzhalter-Zahl nachgezogen (Zweitannotator-Messung kappa 0,33
  unberuehrt).
- Ein spaeteres, allgemeineres Config-Layering (mehrere Overlays, Environment-
  Ebenen) kann denselben Schalter erweitern, statt den Default zu aendern.
