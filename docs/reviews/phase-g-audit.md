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
