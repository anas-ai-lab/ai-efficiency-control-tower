# 0046 -- Monitoring-Zeitleiste als append-only Tabelle

**Status:** Accepted
**Datum:** 2026-07-04
**Phase:** G (Post-v1-Audit)

## Kontext

Ein Case durchlaeuft nach der Einreichung einen Bearbeitungsfluss (Lifecycle-
Status, ADR-0045). Waehrend dieses Flusses fallen manuelle Beobachtungen an --
"Pilot mit Fachbereich gestartet", "Nutzer-Feedback eingeholt", "Integration
verschoben, wartet auf Freigabe". Der reine Lifecycle-Status (ein Enum-Wert)
haelt fest, WO der Case steht, aber nicht, WAS auf dem Weg dorthin beobachtet
wurde. Ohne einen Ort fuer solche Notizen bleibt diese Historie extern
(Ticketsystem, muendlich) -- die Nachvollziehbarkeit am Case ist unvollstaendig.

Gesucht: eine Zeitleiste manueller Notizen pro Case mit Audit-Charakter --
jeder Eintrag mit Zeitstempel und einer Momentaufnahme des damaligen Status.

## Entscheidung

Wir fuehren eine **eigene, append-only Tabelle `monitoring_entries`** ein
(id, case_id, created_at, note, status_snapshot). Ein Eintrag entsteht ueber
`POST /cases/{id}/monitoring` und wird danach **nie veraendert oder einzeln
geloescht**. Es gibt bewusst keine UPDATE- und keine Einzel-DELETE-Methode.
`status_snapshot` friert den `case.status` zum Zeitpunkt des Eintrags als String
ein -- eine Momentaufnahme, kein Live-Verweis. Gelesen wird die Zeitleiste
chronologisch aufsteigend (`ORDER BY created_at, id`; die id als
Sekundaerschluessel haelt die Reihenfolge stabil, wenn zwei Eintraege in
dieselbe sekundengenaue ISO-Zeit fallen).

Die einzige Loeschung ist die **DSGVO-Kaskade** (Art. 17, ADR-0038): loescht
`delete_case()` einen Case, loescht dieselbe Repository-Operation seine
Monitoring-Eintraege in derselben Transaktion mit -- die Zeitleiste ueberlebt
ihren Case nicht.

## Begruendung

| Alternative | Warum verworfen |
|---|---|
| JSON-Spalte am Case (`monitoring_json`, Liste von Eintraegen, per-Feld-UPDATE anhaengen) | Dasselbe Lost-Update-Risiko, das schon die per-Feld-UPDATEs motiviert hat (F-011, siehe `ports/repository.py`): "Eintrag anhaengen" heisst Liste lesen -> Element ergaenzen -> Spalte zurueckschreiben. Zwei parallele Notizen (oder eine Notiz parallel zu einem LLM-Feld-Write, der die ganze Zeile via `save()` ersetzt) lesen beide denselben Ausgangsstand; der langsamere Write gewinnt und verschluckt den Eintrag des schnelleren. Ein eigener INSERT je Eintrag hat dieses Problem strukturell nicht -- Zeilen kollidieren nicht. |
| Update-in-place (ein "aktueller Monitoring-Status"-Text, der ueberschrieben wird) | Zerstoert genau den Audit-Charakter, der der Zweck ist: die Historie WAER die Information. Ein ueberschreibbares Feld beantwortet "wie ist der Stand jetzt", aber nicht "was ist wann passiert". Append-only ist hier das Feature, nicht eine Einschraenkung. |
| Monitoring in den bestehenden structlog-Audit-Trail statt in eine Tabelle | Logs sind fluechtig (Rotation, nicht abfragbar pro Case) und nicht dafuer da, fachliche Nutzereingaben strukturiert zurueckzugeben. Zudem duerfen Freitext-Notizen (moegliche PII) nicht in die Log-Allowlist -- der Log fuehrt nur `entry_id`, nicht die `note`. |

Append-only statt update-in-place ist die tragende Entscheidung: eine Zeitleiste
mit Audit-Charakter verlangt, dass ein einmal festgehaltener Eintrag (inkl.
seines Status-Snapshots) unveraenderlich bleibt -- sonst waere die "Historie"
jederzeit umschreibbar und damit als Nachweis wertlos.

## Konsequenzen

**Positiv:**
- Kein Lost-Update: jeder Eintrag ist ein eigener INSERT, parallele Notizen
  kollidieren nicht (F-011-Lehre konsequent angewandt).
- Audit-Charakter strukturell garantiert -- keine UPDATE-/DELETE-Methode
  existiert, es gibt keinen Pfad, einen Eintrag nachtraeglich zu faelschen.
- `status_snapshot` macht die Zeitleiste selbsterklaerend: man sieht, in
  welchem Lifecycle-Zustand der Case bei jeder Notiz war, ohne den Status-
  Verlauf getrennt rekonstruieren zu muessen.
- DSGVO Art. 17 vollstaendig: die Loesch-Kaskade laesst keine verwaisten
  Eintraege zuruck (eine Transaktion, ein Case + seine Zeitleiste).

**Negativ / Trade-offs (die bewusste Deckung):**
- **Keine Korrektur eines Eintrags.** Ein Tippfehler in einer Notiz bleibt
  stehen -- die Korrektur ist ein neuer Eintrag, nicht eine Aenderung. Das ist
  der Preis des Audit-Charakters (bewusst).
- **Keine serverseitige Paginierung/Filterung.** Die Zeitleiste wird komplett
  je Case zurueckgegeben. Bei der Datenmenge eines privaten Portfolio-Builds
  unproblematisch (analog der CaseSummary-Entscheidung, P2); ein Migrationstrigger
  bei echtem Volumen.
- **Kein DB-Fremdschluessel-Constraint.** SQLite erzwingt FKs nur mit
  `PRAGMA foreign_keys` je Verbindung; die Integritaet (kein verwaister Eintrag)
  wird stattdessen durch die explizite Loesch-Kaskade in `delete()` garantiert.

**Neutral / Folgeentscheidungen:**
- `monitoring_entry_added` (structlog) haelt `case_id`/`entry_id`/`created_at`
  fest, OHNE `note` -- PII-Allowlist-konform, analog `case_decision_recorded`
  und `case_deleted`.
