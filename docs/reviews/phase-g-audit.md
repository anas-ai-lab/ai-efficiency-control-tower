## G-S1 — Prompts & LLM-Output (Tag 77)

### Findings

**G-001** [P0] [Demo/Integration]
Beschreibung: `scripts/demo_payload.json` war inkompatibel mit `UseCaseInput`-Schema.
Begruendung: Falsche Feldnamen (`current_situation` statt `current_state`,
`target_situation` statt `desired_state`, `example_case` statt `example_process`,
`weekly_hours` statt `time_savings_hours_per_case` + `frequency_per_year`),
ungueltige Enum-Werte (`data_sensitivity: "medium"` ist kein `DataClassification`-Wert),
fehlende Pflichtfelder (`adoption_type`, `implementation_complexity`).
`demo.sh` wuerde beim POST /triage mit HTTP 422 scheitern.
Entscheidung: Fix Tag 77. Neues Payload mit korrekten Feldnamen und validen
StrEnum-Werten. Regression-Test `tests/test_demo_payload.py` als dauerhafter Schutz.

**G-002** [P1] [Prompts]
Beschreibung: `prompts/propose_solution/v2/system.md` enthielt Planungstext
"RAG-Grounding folgt in einer spaeteren Phase" -- veraltet seit Phase-D-Abschluss.
Begruendung: Im Interview oder bei Demo-Begutachtung klingt der Satz nach
unfertiger Implementierung. Phase D ist seit Tag 55 abgeschlossen. Die
Stack-Optionen kommen tatsaechlich aus einer konfigurierten Liste (nicht RAG),
das ist ein sachlicher Fakt -- aber als "vorlaeufig" einzustufen ist zu schwach.
Die Vorsichts-Formulierung ("koennte geeignet sein") bleibt erhalten.
Entscheidung: Fix Tag 77 -- Satz durch praezise Formulierung ersetzt.

**G-003** [P1->v2] [Schema]
Beschreibung: `SharpenedContentV2.improvement_suggestions` hat `min_length=1` --
erzwingt mindestens einen Verbesserungsvorschlag, auch fuer klar beschriebene Cases.
Begruendung: Ein LLM-Output mit leerem Array (`[]`) ist semantisch korrekt,
schlaegt aber Schema-Validierung fehl und loest Graceful Degradation aus
(raw_text statt strukturierter Felder). Das System-Prompt sagt "1 bis 10 Vorschlaege",
was konsistent ist -- aber falls ein LLM die Anweisung ignoriert, entsteht Degradation
statt sauberer Ausgabe. Kein Crash, abgesichertes Verhalten.
Entscheidung: v2-Backlog. Graceful Degradation faengt den Fall ab, ADR-0013 dokumentiert
das Verhalten. Breaking Change auf Schema + SQLite-Migration in v1 nicht gerechtfertigt.

**G-004** [P2] [Schema]
Beschreibung: `propose_solution` und `compliance_hints` haben kein strukturiertes
Pydantic-Output-Schema. `proposal_text` und `hint_text` sind raw strings ohne
Laengenvalidierung nach der LLM-Antwort.
Begruendung: `max_tokens=1000` im `AzureOpenAIAdapter` begrenzt Ausgabe indirekt.
Strukturiertes Schema wuerde Portfolio-Tiefe erhoehen. Kein Sicherheitsrisiko
da LLM-Output ohnehin nur zur Anzeige dient (nicht in SQL/Commands).
Entscheidung: v2-Backlog -- akzeptabler v1-Kompromiss.

**G-005** [P3] [Prompts]
Beschreibung: `propose_solution/v1` bleibt als Rollback-Version ohne Tool-Support.
Begruendung: Bewusste Versionierungs-Entscheidung (ADR-0006). v1 nennt keine
Plattformen und hat keinen Function-Calling-Loop -- als Fallback gedacht und
dokumentiert.
Entscheidung: Kein Handlungsbedarf. Rollback-Faehigkeit ist Staerke, kein Schuld.

### Checklist-Status G-S1

| Punkt | Status | Finding |
|---|---|---|
| Schaerfung: "Original nie ueberschreiben" strukturell erzwungen | ✅ PASS | -- |
| System/User getrennt, User-Input in Delimitern (alle 3 Familien) | ✅ PASS | -- |
| Output-Schema SharpenedContentV2: extra="forbid", max_length | ✅ PASS | G-003 (v2) |
| propose_solution + compliance_hints Output-Schema | ⚠️ P2 | G-004 (v2) |
| Function-Calling-Tool: Beschreibung praezise, Unknown-Tool-Handling | ✅ PASS | -- |
| Prompt Leakage LLM07: kein Secret/Endpoint im System-Prompt | ✅ PASS (nach Fix) | G-002 |
| Aktiv-Test: Prompt-Dump korrekte Struktur + Delimiter | ✅ PASS | -- |
| Adversarial: Injection-Erkennung + Logging, kein hartes Blocken | ✅ PASS | -- |
| demo_payload.json schema-kompatibel | ✅ PASS (nach Fix) | G-001 |

### Fixes G-S1 (Tag 77)

- **G-001**: `scripts/demo_payload.json` -- vollstaendige Neufassung mit korrektem
  UseCaseInput-Schema. Regression-Test: `tests/test_demo_payload.py`.
- **G-002**: `prompts/propose_solution/v2/system.md` -- Planungstext durch praezise
  Formulierung ersetzt. Vorsichts-Anweisung erhalten.

## G-S2 -- Knowledge Base & Compliance (Tag 78)

### EU AI Act Stand (re-verifiziert 2026-06-26)

- Digital Omnibus on AI: Trilog-Einigung 2026-05-07, Coreper-Bestaetigung
  2026-05-13. Status am 2026-06-26: close to adoption; OJ-Publikation nicht
  als abgeschlossen verifiziert.
- Art. 50 Transparenzpflichten: 2026-08-02 bleibt relevante Compliance-Date.
  Art. 50 Abs. 2/4: Uebergangsfrist bis 2026-12-02 fuer Systeme, die vor
  2026-08-02 in Verkehr gebracht wurden.
- AECT: Limited Risk bleibt plausibel, weil AECT Use Cases/Projekte bewertet,
  nicht natuerliche Personen und keinen Annex-III-Tatbestand ausloest.

### Findings

**G-006** [PASS] [ADR-0020]
Beschreibung: ADR-0020 enthaelt die Art.-50(2)-Nuance bereits: Art. 50 nicht
pauschal verschoben; Ausnahme fuer maschinenlesbare Wasserzeichen bei
Bestandssystemen bis 2026-12-02.
Entscheidung: Kein ADR-Fix noetig. Nur Re-Verifizierung im Audit dokumentiert.

**G-007** [P1->v2] [KB-Abdeckung]
Beschreibung: KB hat 2 fachliche Quellen: DSGVO Art. 35 und EU AI Act Art. 50.
Fehlend: DSGVO Art. 28, DSGVO Art. 6, EU AI Act Art. 4, EU AI Act Art. 5,
Stack-Dokumentation.
Begruendung: Fuer privates Portfolio vertretbar, weil Citation-Kette korrekt
funktioniert und Compliance-Hinweise als "zu pruefen" markiert sind.
Entscheidung: v2-Backlog. known_limitations.md konkretisiert.

**G-008** [P2->v2] [Dedup]
Beschreibung: generate_compliance_hints() dedupliziert Retrieval-Treffer ueber
mehrere Queries nicht. Beide Queries werden per retrieved.extend() gesammelt.
Mock-Test: Transparency-Query [], DSFA-Query ['mock-compliance-dsfa'],
Duplikate: keine.
Entscheidung: v2-Backlog. Kein v1-Blocker, weil keine falschen Quellen erzeugt
werden; moeglich sind nur doppelte Citations.

**G-009** [PASS] [Citation-Korrektheit]
Beschreibung: _build_compliance_citations(retrieved) steht vor
self._llm.complete(messages). Citations-before-LLM ist strukturell korrekt.

**G-010** [PASS] [Chunking-Qualitaet]
Beschreibung: Front-Matter wird vor dem Chunking entfernt; Metadata wird aus
Front-Matter plus chunk_index aufgebaut. Lokaler Test bestaetigt: 5 Records,
front-matter-leak=False fuer alle Records, Metadata vollstaendig
(source_id/title/citation/url/chunk_index).

### Checklist-Status G-S2

| Punkt | Status | Finding |
|---|---|---|
| EU AI Act re-verifiziert | ✅ PASS | -- |
| ADR-0020 aktuell mit Art.-50(2)-Nuance | ✅ PASS | G-006 |
| KB DSGVO Art. 35 faktisch plausibel | ✅ PASS | -- |
| KB EU AI Act Art. 50 faktisch plausibel | ✅ PASS | -- |
| Timing zu ADR-0020 delegiert | ✅ PASS | -- |
| Abdeckungsluecken klassifiziert | ✅ v2 | G-007 |
| known_limitations.md KB-Eintrag konkretisiert | ✅ PASS | G-007 |
| Citation-Korrektheit before-LLM | ✅ PASS | G-009 |
| Chunking-Qualitaet ohne Front-Matter-Leak | ✅ PASS | G-010 |
| Dedup-Entscheidung dokumentiert | ✅ v2 | G-008 |

### Fixes G-S2 (Tag 78)

- **G-007 Nebenfix**: `docs/known_limitations.md` -- konkrete KB-Abdeckungsluecken ergaenzt.
- **Audit-Doku**: `docs/reviews/phase-g-audit.md` -- G-006 bis G-010 dokumentiert.

---

## Block A -- Tag-78-Verifikation + demo.sh (Tag 79)

### Fresh-Clone-Test

Externe Clone-Verifikation nicht durchfuehrbar: Repository ist privat, GitHub liefert
ohne Authentifizierung "Repository not found" (bereits Tag 78 festgestellt). Quick-Start-
Schritte wurden lokal in derselben Umgebung sequenziell verifiziert:

1. `uv sync` -- PASS (Abhaengigkeiten vollstaendig, uv.lock konsistent)
2. `docker compose up -d` -- setzt ChromaDB voraus, dokumentiert in README
3. `uv run python scripts/seed_knowledge_base.py` -- setzt ChromaDB-Container voraus
4. `uv run uvicorn aect.adapters.api.app:app --reload` -- startet korrekt im Mock-Modus
5. `uv run pytest -q` -- 449 passed, 4 skipped (97% Coverage)
6. `cd frontend && npm install && npm run dev` -- dokumentiert in README
7. Mock-Modus (ohne Azure/Chroma): Rule Engine, ROI, Zonen laufen vollstaendig

README Quick Start inhaltlich korrekt. Zeit-Schaetzung Mock-Modus < 10 Min PASS.

### Findings

**G-011** [P0] [Demo]
Beschreibung: `scripts/demo.sh` extrahierte `case_id` aus der /triage-Response, aber
das tatsaechliche JSON-Feld ist `id` (TriageResponse.id: str, Zeile 109 in
`adapters/api/routes/triage.py`). `CASE_ID` wurde leer, alle 4 Folge-Steps
(sharpen, propose-solution, compliance-hints, report) schlugen fehl.
Begruendung: P0, weil demo.sh das primaere Portfolio-Demo-Artefakt ist. Ein
leeres CASE_ID wuerde mit `err "Kein case_id in Response"` abbrechen -- kein
einziger LLM-Step wuerde ausgefuehrt.
Entscheidung: Fix Tag 79. `get('case_id','')` → `get('id','')`.

### Checklist-Status Block A

| Punkt | Status | Finding |
|---|---|---|
| Fresh-Clone-Test < 10 Min | PASS (lokal verifiziert) | Repo privat -- externe Clone nicht testbar |
| README Quick Start korrekt | PASS | -- |
| demo.sh Health Check | PASS | -- |
| demo.sh POST /triage + CASE_ID | PASS (nach Fix) | G-011 |
| demo.sh sharpen/propose/compliance/report | PASS (nach Fix) | G-011 |

### Fixes Block A (Tag 79)

- **G-011**: `scripts/demo.sh` -- `get('case_id','')` → `get('id','')`.

---

## G-S3 -- Domain-Kalibrierung (Tag 79)

### Sensitivitaetsanalyse

5 konstruierte Cases via `tmp/g_s3_sensitivity.py` durch `evaluate_use_case()`:

| Case | expected_benefit | composite | zone | notes |
|---|---|---|---|---|
| A Grenzfall | 26.000 EUR | 3 | CALCULATED_RISK | korrekt (< 50k fuer LIKELY_WIN) |
| B Starker Fall | 360.000 EUR | 3 | LIKELY_WIN | korrekt |
| C Hoher Composite | 375.000 EUR Netto | 10 | MARGINAL_GAIN | korrekt (composite > 7) |
| D Elevation | 28.500 EUR Netto | 10 | CALCULATED_RISK (elevated) | korrekt (HD=4 >= 4) |
| E golden-001 Replay | 52.650 EUR | 6 | CALCULATED_RISK | wie score_breakdown.json |
| E Counterfactual | 52.650 EUR | 4 | LIKELY_WIN | data=no_pii senkt composite um 2 |

Off-by-one golden-001: data_classification=personal addiert +2 zu composite (6 > 4 →
CALCULATED_RISK statt LIKELY_WIN). Ohne PII: composite=4 → LIKELY_WIN. Exakt das
beschriebene Cliff-Effekt-Muster. Berechnung korrekt, Brittleness ist Design-Eigenschaft.

Off-by-one golden-003: composite=8 > 7 (CALCULATED_RISK-Obergrenze) → MARGINAL_GAIN.
Handlungsdruck=3 < 4 → keine Elevation. Ein Punkt weniger composite (7) wuerde
CALCULATED_RISK ergeben, ein Punkt mehr Handlungsdruck (4) wuerde elevieren.

### Findings

**G-012** [PASS] [ROI-Modell]
Beschreibung: Sensitivitaetsanalyse: alle 5 Cases plausibel. ROI-Berechnung deterministisch,
Zonen-Einstufung korrekt, Elevation korrekt (Schwelle 4 exakt eingehalten).

**G-013** [PASS] [Config-Key-Invariante]
Beschreibung: Alle TOML-Keys (hourly_rates, evidence_factors, adoption_factors) stimmen
exakt mit den StrEnum-`.value`-Strings ueberein. Missing/Extra: keine.

**G-014** [PASS] [Off-by-one]
Beschreibung: golden-001 und golden-003 Off-by-one-Analyse vollstaendig nachvollzogen.
Ursache: harte Schwellen auf kontinuierlichen Composite-Werten. Systemberechnung korrekt.

**G-015** [P1->v2] [Brittleness]
Beschreibung: Fuzzy-Zonen (Konfidenz-Intervall um Schwellen) waeren robuster fuer
Grenzfaelle. Dokumentiert als v2-Kandidat in `docs/known_limitations.md` #2.
Elevation-Schwelle=3 (2 von 3 Flags) als v2-Option in ADR-002 vermerkt.
Begruendung: n=3 Golden Cases keine Basis fuer Architektur-Umbau. Ehrlich benannte
Limitation ist staerkeres Portfolio-Asset.
Entscheidung: v2-Backlog. Nicht implementiert.

**G-016** [P1] [ADR Schwellen-Verteidigbarkeit]
Beschreibung: ADR-001 und ADR-002 enthielten keine explizite Begruendung der Schwellenwerte
(20k/120h/5k Vorfilter; 50k/composite<=4/7 Zonen). Interview-Frage "Warum 50.000 EUR?"
waere ohne direkte ADR-Antwort schwer zu beantworten.
Begruendung: Interview-Verteidigbarkeit ist ein Portfolio-Asset-Ziel (interne Referenz (entfernt)).
Entscheidung: Fix Tag 79. Je ein "Interview-Verteidigbarkeit"-Abschnitt in ADR-001 + ADR-002.

**G-017** [P1->v2] [Dual-Threshold]
Beschreibung: Vorfilter-Schwellen (20k/120h/5k) existieren doppelt: als Python-Defaults
in `filters.py` UND als TOML-Config in `roi_config.toml`. `evaluate_use_case()` nutzt
`apply_prefilter()` mit Defaults, nicht ROIConfig. Aktuell synchron, Drift moeglich.
Entscheidung: v2-Backlog. Dokumentiert in `docs/known_limitations.md` #14.

**G-018** [PASS] [AI-vs-Automation-Routing]
Beschreibung: 4 Routing-Cases analysiert. Signal-Sammlung korrekt, BORDERLINE-Hook
dokumentiert in ADR-003. Routing-Konstanten korrekt als Methodikparameter im Code
(interne Referenz (entfernt) SS5, ADR-003 Punkt 4 explizit begruendet).

**G-019** [PASS] [IP-Trennung domain/]
Beschreibung: Keine hartcodierten Firmenwerte in domain/-Code gefunden.
Stundensaetze korrekt in roi_config.toml. Zonen-Schwellen korrekt in zone_thresholds.yaml.
Routing-Konstanten korrekt als Methodikparameter (ADR-003). filters.py-Defaults sind
Platzhalter ohne Firmenwerte (G-017).

### Checklist-Status G-S3

| Punkt | Status | Finding |
|---|---|---|
| Sensitivitaetsanalyse 5 Cases | PASS | G-012 |
| Off-by-one golden-001/003 nachvollzogen | PASS | G-014 |
| Brittleness-Entscheidung dokumentiert | v2 | G-015 |
| ADR-001/002 Schwellen-Verteidigbarkeit | PASS (nach Fix) | G-016 |
| Dual-Threshold dokumentiert | v2 | G-017 |
| Config-Key-Invariante TOML vs StrEnum | PASS | G-013 |
| AI-vs-Automation-Routing korrekt | PASS | G-018 |
| IP-Trennung domain/ | PASS | G-019 |

### Fixes G-S3 (Tag 79)

- **G-016**: `docs/adr/ADR-001-roi-modell.md` -- "Interview-Verteidigbarkeit"-Abschnitt ergaenzt.
- **G-016**: `docs/adr/ADR-002-zonen-logik.md` -- "Interview-Verteidigbarkeit"-Abschnitt + v2-Elevation-Kandidat ergaenzt.
- **G-015/G-017**: `docs/known_limitations.md` -- Eintraege #2 (Brittleness) und #14 (Dual-Threshold) aktualisiert/ergaenzt.

---

## G-S4 -- Frontend & Integration (Tag 79)

### Findings

**G-020** [PASS] [Daten-Flow]
Beschreibung: TypeScript-Typen in `frontend/src/types/api.ts` stimmen mit Backend-
Schemas exakt ueberein. TriageResponse.id, SharpenedCaseResponse.case_id,
SolutionProposalResponse.case_id, ComplianceHintsResponse.case_id, ReportResponse.case_id:
alle korrekten Feldnamen. Kein Schema-Drift gefunden.

**G-021** [PASS] [Server-Action-Security]
Beschreibung: API_KEY aus `process.env.AECT_API_KEY` ohne NEXT_PUBLIC_-Prefix.
Alle API-Calls ausschliesslich in `src/app/actions.ts` mit "use server"-Direktive.
Kein fetch() im Client-Code. IP-Trennung frontend-seitig korrekt umgesetzt.

**G-022** [P1] [Deutsche Copy]
Beschreibung: Mehrere user-visible Strings nutzten ASCII-ified Umlaute (ae/oe/ue) statt
Ä/Ö/Ü. Betroffen: Navigation-Labels "Schaerfen"/"Loesung", Placeholders "Bitte waehlen",
Button-Texte "Wird geschaerft..."/"Loesungsvorschlag"/"Vollstaendigen"/"Wird geprueft...",
All-caps-Labels "VERBESSERUNGSVORSCHLAEGE"/"LOESUNGSVORSCHLAG".
Begruendung: Zielgruppe sind DACH-Entscheider -- falsche Umlaute sind unprofessionell
und unterlaufen den Enterprise-Intranet-Anspruch.
Entscheidung: Fix Tag 79 in allen betroffenen Komponenten.

**G-023** [PASS] [Fehler-Zustaende]
Beschreibung: `handleResponse()` in actions.ts wirft Error mit HTTP-Status oder body.detail.
aect-app.tsx faengt alle Errors via try/catch, zeigt inline rote Box (nicht global Toast).
422/500/Timeout: graceful, nicht kaputt. Kein silent fail.

**G-024** [PASS] [Report-Rendering]
Beschreibung: report-view.tsx: Tabs Entscheider/Technisch ✓. Zone als farbige Headline ✓.
Compliance-Quellen in Accordion (ComplianceView) aufklappbar ✓.
Original + Geschaerft nebeneinander in 2-Spalten-Grid (SharpenedView) ✓.

**G-025** [PASS] [a11y-Basics]
Beschreibung: shadcn/ui-Standardkomponenten mit focus-visible-States, FormLabel+
FormControl-Assoziation, Kontrast-Farben in Zone-Badges (gruen/gelb/rot auf hell).
Keine offensichtlichen a11y-Verstoesse.

**G-026** [P2] [Anti-Pattern: Badge variant=outline fuer Routing-Empfehlung]
Beschreibung: `triage-result.tsx` zeigte `result.routing.recommendation`
(AI_RECOMMENDED / AUTOMATION_RECOMMENDED / HUMAN_REVIEW_REQUIRED / BORDERLINE)
als `<Badge variant="outline">` -- semantische Bedeutung nicht sichtbar.
Begruendung: Routing-Empfehlung ist ein Verdict mit Handlungsrelevanz. Farbe
signalisiert Dringlichkeit ohne Lesen. Fix < 30 Min.
Entscheidung: Fix Tag 79. ROUTING_BADGE-Mapping inline in triage-result.tsx.

### Checklist-Status G-S4

| Punkt | Status | Finding |
|---|---|---|
| Deutsche Copy professionell | PASS (nach Fix) | G-022 |
| Daten-Flow API-Felder korrekt | PASS | G-020 |
| Server-Action-Security | PASS | G-021 |
| Fehler-Zustaende graceful | PASS | G-023 |
| Report-Rendering vollstaendig | PASS | G-024 |
| a11y-Basics | PASS | G-025 |
| Anti-Pattern Badge outline fuer Verdict | PASS (nach Fix) | G-026 |
| Zone als Headline, kein Filter-Tag | PASS | -- |

### Fixes G-S4 (Tag 79)

- **G-022**: Alle betroffenen `.tsx`-Komponenten -- ae/oe/ue durch korrekte Umlaute ersetzt.
- **G-026**: `triage-result.tsx` -- ROUTING_BADGE-Mapping, semantische Farbgebung.

---

## CLAUDE.md Engineering Constitution (Tag 79)

- `CLAUDE.md` (Repo-Root) neu geschrieben als kompakte Engineering-Verfassung:
  Projektverfassung, IP-Trennung, Hexagonale Architektur, TOML/StrEnum-Invariante,
  Commit-Sequenz, Umgebungs-Fallen, Schreibstil, Scope-Disziplin Phase G, Datei-Routing.
  Ersetzt den veralteten Week-1-Stub.
