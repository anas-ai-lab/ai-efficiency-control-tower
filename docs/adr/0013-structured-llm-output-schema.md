# ADR-0013: Strukturiertes Ausgabe-Schema fuer LLM-Output (Teil 1/2: Schema + Validator)

**Status:** Accepted
**Datum:** Juni 2026

## Kontext

ADR-0006 haelt als offenen Punkt fest: `SharpenedUseCase.sharpened_text` ist
`str`; ein striktes Pydantic-Schema fuer die LLM-Antwort
(aect-security-checklist v2.1, Phase C: "LLM-Output gegen striktes
Pydantic-Schema; als untrusted behandeln") wird eingefuehrt, "sobald ein
Provider strukturierte Antworten liefert". ADR-0011 (Report-Renderer)
verweist auf denselben offenen Punkt fuer einen spaeteren
LLM-Fliesstext-Report.

Der Azure-OpenAI-Adapter (Tag 40, ADR-0010) setzt aktuell kein
`response_format` -- `complete()` baut `kwargs` ohne JSON-Mode-Parameter
(`src/aect/adapters/llm/azure_openai.py`). Die in ADR-0006 genannte
Bedingung ("sobald ein Provider strukturierte Antworten liefert") ist damit
auch nach dem Azure-Adapter-Tag noch nicht erfuellt -- der offene Punkt bleibt
offen.

interne Referenz (entfernt) SS3.1 Punkt 1 fordert fuer die Use-Case-Schaerfung "die geschaerfte
Version plus konkrete Verbesserungsvorschlaege". Der aktuelle v1-Prompt
(`prompts/sharpen_use_case/v1/`) liefert reinen Fliesstext ("Antworte
ausschliesslich mit der geschaerften Version als Fliesstext, ohne Einleitung
oder Meta-Kommentar") -- Verbesserungsvorschlaege sind darin nicht als
separates Feld abgebildet.

## Entscheidung

Wir definieren das Ziel-Schema fuer eine strukturierte Schaerfung sowie einen
generischen Validator -- ohne heute etwas Bestehendes zu aendern:

1. Neues Modul `src/aect/application/structured_output.py`:
   - `SharpenedContentV2` (Pydantic V2, `extra="forbid"`, `frozen=True`,
     `max_length` auf allen Feldern): `sharpened_title`,
     `sharpened_current_state`, `sharpened_desired_state`,
     `improvement_suggestions: list[str]` (1-10 Eintraege, je 5-500
     Zeichen). Bounds orientieren sich an `UseCaseInput`
     (`domain/models.py`: title 5-200, current_state/desired_state 30-2000).
   - `parse_structured_llm_output(raw: str, schema: type[T]) -> T`:
     generische Funktion, validiert einen rohen JSON-String gegen ein
     beliebiges Pydantic-Schema.
   - `InvalidLLMOutputError(Exception)`: einheitlicher Fehlertyp fuer
     JSON-Decode-Fehler und Pydantic-`ValidationError` (Exceptions statt
     Result-Pattern, Master-Plan v3.1 Phase B).

2. **Teil 2 (eigener Tag, nicht heute):** Wiring in `sharpen_case()` --
   `SharpenedUseCase.sharpened_text: str` -> strukturierte Felder. Das ist
   ein Breaking Change auf `SharpenedUseCase`, `SubmittedCase.sharpened_text`
   (Typ-Aenderung, betrifft ADR-0012-Persistenz + SQLite-Spalte),
   `SharpenedCaseResponse`/`ReportResponse` (`routes/cases.py`), sowie alle
   Tests in `test_service.py`, `test_sharpen.py`,
   `test_sqlite_repository.py`, `test_report.py`. Zusaetzlich notwendig fuer
   Teil 2: `response_format`/JSON-Schema im Azure-Adapter (ADR-0010-Update)
   und ein neuer Prompt `prompts/sharpen_use_case/v2/` mit
   JSON-Output-Instruktion -- v1 fordert explizit Fliesstext und ist damit
   fuer Teil 2 nicht weiterverwendbar.

## Begruendung

| Alternative | Warum verworfen |
|---|---|
| Sofortiges Wiring (Teil 1+2 an einem Tag) | Breaking Change auf SharpenedUseCase/SubmittedCase/SQLite-Schema/API-Response + ~20 Bestandstests an einem Tag ohne eigenes Review -- Profil eines nicht-additiven Schritts (vgl. Hexagonal-Move), verstoesst gegen "Ein Tag = aktueller Scope" (session-protocol v3 SS5.2.6) |
| Weiteres Verschieben (Status quo) | ADR-0006/ADR-0011 offene Punkte bleiben unbearbeitet; Schema-Design ist unabhaengig vom Wiring sinnvoll machbar und liefert ein eigenstaendiges, testbares Artefakt |
| Dataclass statt Pydantic fuer das Schema | Security-Checkliste verlangt explizit "striktes Pydantic-Schema"; Pydantic liefert `extra="forbid"` + `max_length`-Validierung direkt, Dataclass muesste das selbst nachbauen |

## Konsequenzen

**Positiv:**
- Additiv: kein bestehender Code geaendert, vollstaendig isoliert testbar
  ohne MockLLMAdapter/Service-Aenderung.
- Schema-Design (Feld-Namen, Bounds, `improvement_suggestions`) liegt vor
  Teil 2 fest -- Teil 2 wird dadurch kleiner und fokussierter (Migration +
  Wiring + Prompt v2 + Adapter-Update).
- Reduziert die offenen Punkte aus ADR-0006/ADR-0011 auf den Wiring-Teil.

**Negativ / Trade-offs:**
- `SharpenedContentV2` ist bis Teil 2 unverdrahtetes Schema -- kein
  Nutzer-sichtbarer Effekt heute.
- Risiko, dass Teil 2 (der eigentliche Breaking-Change-Tag) verschoben wird,
  solange Budget-Sentinel und andere Themen Vorrang haben.

**Neutral / Folgeentscheidungen:**
- Teil 2 ist ein eigener Tag mit Charakter des Hexagonal-Moves
  (nicht-additiv, viele Bestandstests betroffen) -- Claude weist bei Aufruf
  explizit darauf hin, auch ohne formelles Gate in session-protocol v3 SS2.
- `response_format`-Ergaenzung im Azure-Adapter und Prompt-v2 sind
  Voraussetzung fuer Teil 2 und werden dort als eigene Unterschritte
  gefuehrt, nicht vorab.

## Teil 2 (Juni 2026): Wiring + Graceful Degradation

**Entscheidung:** Bei InvalidLLMOutputError (kaputtes JSON, fehlendes Feld,
Laengenverstoss) faellt sharpen_case() auf raw_text=response.content zurueck
-- strukturierte Felder None/leer, Validierungsfehler geloggt
(structured_output_validation_failed), kein Abbruch. Konsistent mit dem
Injection-Detection-Muster (Tag 32): flaggen, nicht blocken.

**Persistenz:** SubmittedCase.sharpened_text -> sharpened_content_json
(JSON-String, SQLite-Spalte umbenannt). Breaking Change wie in ADR-0012
dokumentiert -- lokale Dev-DB muss geloescht werden (CREATE TABLE IF NOT
EXISTS legt das neue Schema nicht nachtraeglich in einer bestehenden Tabelle an).

**Report unveraendert:** BusinessSummary.sharpened_text bleibt str | None.
Neue reine Funktion _render_sharpened_content() (service.py, ADR-0011-
konform, kein LLM-Call) uebersetzt das persistierte JSON in lesbaren Text.
/report-Schema und alle bestehenden /report-Tests bleiben unveraendert.

**Mock-Strategie:** MockLLMAdapter bleibt unveraendert (Echo, kein JSON) --
deckt den Degradation-Pfad ab. Neuer Fake _StructuredSharpenLLMAdapter
(test_service.py) deckt den Erfolgspfad ab. Kein Differenzieren von
MockLLMAdapter nach `tools`-Parameter -- haette den allgemeinen Test-Mock
an Service-interne Aufrufmuster gekoppelt.

**Prompt v2:** prompts/sharpen_use_case/v2/ -- JSON-Output-Anweisung statt
Fliesstext (v1). Default prompt_version in sharpen_case(): "v2". v1 bleibt
fuer Rollback erhalten (Versionierung, ADR-0006).

Schliesst ADR-0006 offenen Punkt "Output-Validation" und ADR-0011 offenen
Punkt "Persistenz sharpened_text" (Spalte umbenannt, Konzept unveraendert).
