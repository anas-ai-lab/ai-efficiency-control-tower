# ADR-0012: Persistenz von sharpened_text und proposal_text auf SubmittedCase

## Status
Accepted

## Kontext

ADR-0011 (Tag 41) hielt als offenen Punkt fest: Persistenz von
sharpened_text/proposal_text auf SubmittedCase ist ein eigener Tag, sobald
eine Case-Detail-Ansicht (Phase F Frontend) das verlangt -- betrifft
Repository-Interface + SQLite-Adapter + Bestandstests.

Ohne Persistenz muss der Client bei jedem /report-Aufruf die zuvor von
/sharpen bzw. /propose-solution erhaltenen Texte erneut im Request-Body
mitschicken. Fuer ein Frontend (Phase F) ist das unnoetiger Re-Transport
von LLM-Output, der serverseitig bereits einmal erzeugt wurde.

## Entscheidung

**1. SubmittedCase um zwei optionale Felder erweitert:**
`sharpened_text: str | None = None`, `proposal_text: str | None = None`.
Kein neues Dataclass, keine Versionierung -- letzter Aufruf von
sharpen_case() bzw. propose_solution() ueberschreibt den vorherigen Wert.

**2. RepositoryPort-Interface bleibt unveraendert.** save() war bereits ein
Upsert (InMemory: dict-Ueberschreibung per ID, SQLite: INSERT OR REPLACE).
sharpen_case()/propose_solution() laden den Case, setzen das jeweilige Feld,
rufen save() erneut auf. Kein neues "update"-Verb im Port noetig.

**3. SQLite-Schema additiv erweitert:** zwei neue nullable Spalten
(sharpened_text, proposal_text). _row_to_case(), save(), get(), list_all()
entsprechend angepasst (6-Spalten-Select statt 4).

**4. generate_report() liest die persistierten Werte als Default.** Ein im
Request-Body uebergebener Wert (ReportRequest) ueberschreibt den
persistierten -- fuer Vorschauen oder Tests ohne erneuten Persist.

## Konsequenzen

Positiv: additiv (keine Breaking Change an bestehenden Routen/Tests
ausserhalb der direkt betroffenen Dateien), Phase-F-Frontend kann /report
ohne vorherigen Re-Transport der LLM-Narrative aufrufen, sharpen_case()/
propose_solution() bleiben fachlich unveraendert (geben weiterhin
SharpenedUseCase/SolutionProposal zurueck, persistieren zusaetzlich).

Negativ / Limitation: CREATE TABLE IF NOT EXISTS migriert keine
bestehenden SQLite-Dateien -- eine vor Tag 42 angelegte DB-Datei hat die
neuen Spalten nicht und wuerde bei get()/save() einen sqlite3.OperationalError
werfen (Spalte fehlt). Im privaten Build kein Problem (Test-DBs sind
tmp_path-basiert, keine produktive DB existiert). Falls doch eine lokale
DB-Datei aus Tag <42 existiert: loeschen, wird beim naechsten _init_db()
mit neuem Schema neu angelegt. Keine Migrations-Tooling (Alembic) im Stack -- bewusst, fuer ein Solo-Portfolio-Projekt unverhaeltnismaessig.

## Offene Punkte

Keine neuen. ADR-0011 Punkt 2 ist hiermit geschlossen. ADR-0011 Punkt 1
(LLM-generierter Fliesstext-Report mit strikter JSON-Validierung) bleibt offen.

## Addendum (ADR-0013 Teil 2, Juni 2026)

Spalte sharpened_text -> sharpened_content_json umbenannt (JSON statt
Fliesstext, strukturierte Schaerfung + Graceful-Degradation-raw_text).
Konzept (Persistenz, Upsert-Semantik, "letzter Aufruf gewinnt") unveraendert.
