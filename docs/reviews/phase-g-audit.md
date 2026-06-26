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
