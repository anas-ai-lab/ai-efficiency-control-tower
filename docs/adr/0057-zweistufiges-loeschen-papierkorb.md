# ADR-0057: Zweistufiges Loeschen ueber einen Papierkorb

**Status:** Accepted
**Datum:** 2026-08-30
**Autor:** Anas
**Ergaenzt:** ADR-0038 (DSGVO Art. 17 kaskadierter Loeschpfad)

## Kontext

`DELETE /cases/{id}` loeschte bisher sofort und physisch: Case-Zeile,
Monitoring-Zeitleiste, Vektor-Store-Eintrag. Ein Fehlklick war damit
irreversibel -- es gibt kein Backup, kein Undo und keine zweite Kopie eines
Case. Der teuerste Zustand des Systems (ein bewerteter Case samt geschaerftem
Inhalt, Loesungsvorschlag, Skizze und Zeitleiste) hing an einer einzelnen
unbestaetigten Aktion.

DSGVO Art. 17 verlangt Loeschbarkeit, nicht Sofortloeschung. Die Verordnung
schreibt vor, dass eine betroffene Person die Loeschung verlangen kann und dass
sie dann auch tatsaechlich erfolgt -- sie schreibt nicht vor, dass jeder
Bedienvorgang im Werkzeug ohne Zwischenschritt durchschlaegt. Ein Papierkorb
zwischen Absicht und Vollzug widerspricht Art. 17 also nicht, solange der
Vollzug erhalten bleibt und nicht verwaessert wird.

## Entscheidung

Loeschen wird zweistufig.

**Stufe eins -- Papierkorb.** `POST /cases/{id}/trash` setzt die neue nullable
Spalte `deleted_at`. Nichts wird geloescht. `POST /cases/{id}/restore` setzt sie
zurueck auf `NULL`, `GET /cases/trash` listet den Papierkorb (admin-only, kein
oeffentliches Gegenstueck -- ein Papierkorb ist keine oeffentliche Sicht).

**Stufe zwei -- physisch.** `DELETE /cases/{id}` bleibt in Pfad, Methode und
Statuscode unveraendert und bleibt der einzige Weg zur echten Loeschung. Neu ist
nur ein Guard: ein Case, der nicht im Papierkorb liegt, ergibt `409` mit dem
Code `case_not_in_trash`. Der Sprung von "aktiv" direkt auf "physisch geloescht"
existiert nicht mehr.

**Der Filter sitzt an genau einer Stelle.** `_SELECT_ALL_SQL` bekommt
`WHERE deleted_at IS NULL`; das In-Memory-Gegenstueck filtert entsprechend in
`list_all()`. Damit sind Ideenliste, Board, Monitoring, Kennzahlen, Top-Cases
und Dedup-Paare automatisch papierkorb-frei, ohne dass `list_cases()`,
`compute_stats()`, `list_top_cases()` oder `list_similarity_pairs()` angefasst
werden mussten -- alle vier laufen ueber `list_all()`/`list_all_async()`. Die
Alternative, den Filter in jedem Aufrufer nachzubauen, war der eigentlich
gefaehrliche Weg: eine vergessene Stelle haette einen getrashten Case still in
einer Kennzahl weitergezaehlt, ohne Fehler, ohne Symptom. Genau die Sorte
stiller Falschwert, die dieses Projekt an anderer Stelle (Config-Key-Mismatch,
ROI=0) schon einmal teuer bezahlt hat.

`_SELECT_BY_ID_SQL` bleibt ausdruecklich UNGEFILTERT. Ein Case im Papierkorb
muss per ID ladbar bleiben, sonst haetten weder Wiederherstellen noch
endgueltiges Loeschen etwas zu greifen, und die Detailseite koennte nicht zeigen,
was da eigentlich im Papierkorb liegt.

`soft_delete_case()` ist idempotent und behaelt beim zweiten Aufruf den ersten
Zeitstempel: `deleted_at` soll den Moment der Loeschhandlung festhalten, nicht
den des letzten Klicks.

## Bewusst kein Auto-Purge

Es gibt keine Frist, keinen Cron, kein TTL und keine automatische endgueltige
Loeschung aus dem Papierkorb heraus. Der Zeitpunkt der endgueltigen Loeschung
bleibt eine explizite menschliche Handlung.

Der Grund ist nicht Bequemlichkeit, sondern Zurechenbarkeit: eine Frist wuerde
genau die Irreversibilitaet wiederherstellen, die dieser ADR beseitigt -- nur
zeitversetzt und ohne dass jemand im Moment des Vollzugs hinsieht. Ein
"30 Tage, dann weg" ist ein Loeschvorgang ohne Urheber. Der Papierkorb waechst
in einem privaten Portfolio-Build mit einer Handvoll Cases nicht in eine
Groessenordnung, in der eine automatische Bereinigung noetig waere.

Ausnahme mit eigener Grundlage: `scripts/enforce_retention.py` (ADR-0042,
DSGVO Art. 5(1)(e) Speicherbegrenzung) loescht weiterhin fristbasiert. Dieser
Job durchlaeuft seit ADR-0057 beide Stufen im selben Lauf --
`soft_delete_case()`, dann `delete_case()` -- statt den Guard zu umgehen. Der
Papierkorb ist dort ein Durchgangszustand von Millisekunden; die Retention-Frist
bleibt unveraendert scharf. Ein abgelaufener Case im Papierkorb zu parken waere
eine Abschwaechung von Art. 5(1)(e) gewesen.

## Stufe zwei loescht physisch

Kein Anonymisieren, kein Archiv, kein Tombstone. Der bestehende Kaskadenpfad aus
ADR-0038 bleibt vollstaendig erhalten: Case-Zeile und Monitoring-Eintraege
verschwinden in derselben Transaktion, der Vektor-Store wird best-effort
bereinigt, und das Loesch-Ereignis selbst bleibt als Audit-Trail im Log
(DSGVO Art. 5(2) Rechenschaftspflicht -- der Loesch-Nachweis ist keine
personenbezogene Information und muss gerade deshalb erhalten bleiben).

Ein anonymisierter Restdatensatz waere hier die schlechtere Loesung: er sieht
aus wie Compliance, haelt aber genau die Struktur fest, die den Case
identifizierbar macht (Abteilung, Zeitpunkt, Kennzahlen). "Geloescht" soll
heissen, dass die Zeile weg ist.

## Konsequenzen

- Eine neue Spalte `deleted_at TEXT` (nullable) mit PRAGMA-Migration nach dem
  bestehenden Muster. Altbestand laedt mit `NULL` und gilt damit als aktiv.
- `_row_to_case` ist jetzt ein 20-Tupel; die vier SQL-Stellen (CREATE_TABLE,
  INSERT, SELECT_BY_ID, SELECT_ALL) plus `save()` sind synchron zu halten.
- Der Port waechst um `list_deleted`/`set_deleted_at` (je sync + async).
  `list_all()` liefert laut Port-Vertrag nur noch AKTIVE Cases -- das ist eine
  Vertragsaenderung, keine Adapter-Eigenheit, und beide Adapter erfuellen sie an
  je genau einer Stelle.
- Bestehende Tests, die direkt loeschten, mussten um den Papierkorb-Schritt
  ergaenzt werden. Das ist der sichtbare Beleg dafuer, dass der Guard greift.
- Der Frontend-Vertrag waechst um `GET /cases/trash` (`TrashedCaseSummary`),
  `POST /cases/{id}/trash` und `POST /cases/{id}/restore`. Die Papierkorb-Sicht
  im Frontend selbst ist NICHT Teil dieses ADR.
