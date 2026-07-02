# Inter-Annotator-Agreement -- Golden Cases (Zweitannotator: LLM)

Stand: 2026-07-02. Antwort auf known_limitations #3 ("Cross-Rater-Agreement
mit zweitem unabhaengigen Labeler messen").

## Protokoll

Zweitannotator ist ein **LLM (Claude, Blind-Protokoll), explizit KEIN
menschlicher Fachexperte**. Ablauf:

1. Gelesen wurden ausschliesslich die Input-Felder der 25 Cases aus
   `use_cases.jsonl` (Titel, Ist/Soll/Beispiel, numerische und Enum-Felder).
   `expected_zone`, `notes`, `report.json` und die Zonen-/ROI-Regeln wurden
   vor dem Labeln nicht eingesehen (mechanisch ausgefiltert).
2. Urteilsbasis: erwarteter Nutzen (Stundenvolumen x Wertigkeit, abgezinst
   um Evidenz und freiwillige Adoption) gegen Aufwand/Risiko/Unsicherheit --
   das Urteil eines erfahrenen AI-Strategie-Beraters, keine
   Schwellen-Anwendung. Zusatzkategorie REJECT fuer Cases, die den Intake
   nicht passieren sollten.
3. Alle 25 Labels wurden in `second_annotator_labels.jsonl` geschrieben,
   BEVOR Autor-Labels oder Engine-Ergebnisse gelesen wurden.

## Ergebnisse

Label-Verteilungen (n=25): Autor 16x LIKELY_WIN / 8x CALCULATED_RISK /
1x unlabeled (golden-004). Zweitannotator 11x LIKELY_WIN /
5x CALCULATED_RISK / 8x MARGINAL_GAIN / 1x REJECT (golden-004). Engine
5x LIKELY_WIN / 14x CALCULATED_RISK / 2x MARGINAL_GAIN / 4x ohne Zone
(Vorfilter nicht bestanden: golden-004/005/006/016).

### Zweitannotator vs. Autor (n=24 beidseitig gelabelt)

Raw Agreement **14/24 (58,3 %)**, Cohen's kappa **0,33** (p_e=0,375).

| Zweitannotator \ Autor | CALCULATED_RISK | LIKELY_WIN | MARGINAL_GAIN |
|---|---|---|---|
| CALCULATED_RISK | 3 | 2 | 0 |
| LIKELY_WIN | 0 | 11 | 0 |
| MARGINAL_GAIN | 5 | 3 | 0 |

Muster: Der Autor nutzt MARGINAL_GAIN nie; alle 8 MARGINAL_GAIN-Urteile des
Zweitannotators liegen beim Autor eine Zone hoeher (5x CALCULATED_RISK,
3x LIKELY_WIN). Bei LIKELY_WIN ist die Uebereinstimmung hoch (11/11 der
Zweitannotator-LIKELY_WINs bestaetigt der Autor). Der Autor labelt
durchgaengig optimistischer. Alle Abweichungen sind ordinal benachbart
(keine LIKELY_WIN<->MARGINAL_GAIN-Spruenge auf Autor-Seite... mit drei
Ausnahmen: golden-009/011/025, Autor LIKELY_WIN vs. Zweitannotator
MARGINAL_GAIN).

### Zweitannotator vs. Engine (n=21, Engine-Zone vorhanden)

Raw Agreement **8/21 (38,1 %)**, Cohen's kappa **0,11** (p_e=0,306).

| Zweitannotator \ Engine | CALCULATED_RISK | LIKELY_WIN | MARGINAL_GAIN |
|---|---|---|---|
| CALCULATED_RISK | 4 | 0 | 1 |
| LIKELY_WIN | 6 | 4 | 1 |
| MARGINAL_GAIN | 4 | 1 | 0 |

### Autor vs. Engine (n=21; report.json rechnet 9/24=37,5 % ueber alle gelabelten Cases inkl. Vorfilter-Fails)

Raw Agreement **9/21 (42,9 %)**, Cohen's kappa **0,13** (p_e=0,340).

| Autor \ Engine | CALCULATED_RISK | LIKELY_WIN | MARGINAL_GAIN |
|---|---|---|---|
| CALCULATED_RISK | 4 | 0 | 1 |
| LIKELY_WIN | 10 | 5 | 1 |
| MARGINAL_GAIN | 0 | 0 | 0 |

### Einordnung

Die drei Urteile bilden ein konsistentes Spektrum: **Engine (konservativ,
CALCULATED_RISK-lastig) < Zweitannotator < Autor (optimistisch,
LIKELY_WIN-lastig)**. Der Zweitannotator bestaetigt damit beide bereits
dokumentierten Befunde zugleich: (a) die enge LIKELY_WIN-Definition der
Engine drueckt viele klare Faelle nach CALCULATED_RISK (10 der 12
Autor-Engine-Mismatches), und (b) ein Teil der Autor-LIKELY_WINs haelt einem
zweiten Blick nicht stand (3 Faelle, die der Zweitannotator nur als
MARGINAL_GAIN sieht). Bemerkenswert: golden-004 wird von allen drei
Instanzen aussortiert (Autor: unlabeled, Engine: Vorfilter-Fail,
Zweitannotator: REJECT). Kappa 0,33 (Zweitannotator vs. Autor) gilt nach
gaengiger Lesart als "fair" -- die Zonen-Zuordnung ist also auch zwischen
zwei Bewertern mit gleichem Informationsstand deutlich interpretationsabhaengig,
was die dokumentierte Hard-Threshold-Brittleness von der Label-Seite her
bestaetigt.

## Limitations (ehrlich)

1. **LLM statt Mensch.** Der Zweitannotator ist ein einzelnes LLM, kein
   menschlicher Domaenenexperte. Das misst, ob ein zweites, anders
   kalibriertes Urteil zu denselben Zonen kommt -- es ist KEIN Ersatz fuer
   menschliche Inter-Rater-Reliabilitaet und erfuellt den "naechsten
   Schritt" aus known_limitations #3 nur naeherungsweise.
2. **Kontaminations-Risiko.** Das Blind-Protokoll war prozedural strikt
   (Labels vor Einsicht in Autor-Labels/Engine-Output geschrieben,
   expected_zone mechanisch ausgefiltert), aber nicht epistemisch perfekt:
   Der Annotator hatte in derselben Arbeitssitzung zuvor fuer Bugfixes die
   Zonen-Schwellen-Konfiguration und Portfolio-Dokumente gelesen, die die
   Autor-Engine-Agreement-Rate erwaehnen. Die Labels wurden bewusst als
   Berater-Urteil und nicht per Schwellen-Anwendung vergeben; eine
   unbewusste Beeinflussung ist trotzdem nicht ausschliessbar.
3. **Einzelner Annotator, Prompt-Sensitivitaet.** Ein LLM-Urteil haengt von
   Formulierung und Sprache des Prompts ab (hier: deutsche Cases, deutsches
   Bewertungsraster). Ein anderes Modell oder ein anderer Prompt kann
   systematisch anders kalibrieren; n=1 Annotator erlaubt keine Aussage
   ueber Annotator-Varianz.
4. **Kleines Sample.** n=24 gemeinsame Labels; ein einzelner Case bewegt
   die Agreement-Rate um ~4 Prozentpunkte. Kappa-Werte auf n<=24 haben
   breite Konfidenzintervalle (nicht berechnet).
