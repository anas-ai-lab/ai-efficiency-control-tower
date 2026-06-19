# ADR-0026: Persistenz und Report-Integration von Compliance-Hinweisen

## Status
Accepted

## Kontext

ADR-0024 (Tag 56) lieferte generate_compliance_hints() als eigenstaendigen
Endpoint, analog zu sharpen_case()/propose_solution() vor Tag 42. Tag 57
schloss die naechsten offenen Punkte des Wissens-Pfads (ChromaRetriever-DI,
Seeding). Der Daily-Note-Folge-Punkt aus Tag 57 hielt explizit fest:
"Persistenz von compliance_hints auf SubmittedCase + Einbau in /report --
gleiches Muster wie sharpen_case/propose_solution vor Tag 42 (ADR-0012)."

Ohne Persistenz muesste ein Frontend (Phase F) bei jedem /report-Aufruf
hint_text + citations erneut im Request-Body mitschicken, obwohl der Server
sie bereits einmal erzeugt hat -- derselbe unnoetige Re-Transport, den
ADR-0012 fuer sharpened_text/proposal_text geloest hat.

## Entscheidung

**1. SubmittedCase um ein drittes optionales Feld erweitert:**
`compliance_hints_json: str | None = None`. JSON-Objekt mit `hint_text`
(str | None) und `citations` (Liste von Citation-Dicts: number, source_id,
citation, url). Letzter Aufruf von generate_compliance_hints() ueberschreibt
den vorherigen Wert -- identische Upsert-Semantik wie sharpened_content_json/
proposal_text (ADR-0012).

**2. Persistiert wird in BEIDEN Zweigen von generate_compliance_hints():**
sowohl beim No-Hit-Fall (Graceful Degradation, hint_text=None,
citations=[]) als auch beim vollen Pfad mit LLM-Call. Begruendung:
"kein Hinweis vorhanden" ist ein gueltiges, persistierbares Ergebnis --
unterscheidet sich vom "Endpoint nie aufgerufen"-Zustand
(compliance_hints_json bleibt dann None), genau wie bei sharpen_case().

**3. SQLite-Schema additiv erweitert:** eine dritte nullable Spalte
(compliance_hints_json), analog zur Tag-42-Erweiterung. _row_to_case(),
save(), get(), list_all() entsprechend angepasst (7-Spalten-Select statt 6).

**4. BusinessSummary (nicht TechnicalDetail) traegt compliance_hint_text +
compliance_citations als gekoppeltes Paar.** Abweichung vom reinen
sharpened_text/proposal_text-Muster (dort ein str-Feld pro Schicht): hier
zwei Felder zusammen in einer Schicht. Begruendung: der Hinweistext
referenziert seine Quellen ueber [N]-Marker im Fliesstext, die exakt zur
citations-Liste passen muessen (gleiches Prinzip wie "Provenance muss mit
dem Chunk reisen, nicht separat gespeichert werden", RAG-Retrieval-Pfad).
Eine Aufteilung auf Business-/Technical-Schicht wuerde Text und Quelle
trennen und die Referenz-Integritaet dem Frontend ueberlassen.
Platzierung in BusinessSummary statt TechnicalDetail: der Hinweis ist
interne Referenz (entfernt) SS3.1 Punkt 4 zufolge fuer die Fachabteilung/Entscheider gedacht
("DSFA-Indikator: pruefen lassen"), nicht nur Reviewer-Detail.

**5. Kein Request-Body-Override fuer Compliance-Hinweise in /report**
(anders als sharpened_text/proposal_text in ReportRequest). Begruendung:
aus Punkt 4 folgt direkt -- ein frei uebergebener Hinweistext ohne
passende citations-Liste wuerde die [N]-Referenz-Kopplung brechen. Die
einzige korrekte Quelle fuer beide Felder zusammen ist die Persistenz.

## Konsequenzen

Positiv: additiv (keine Breaking Change an bestehenden Routen/Tests
ausserhalb der direkt betroffenen Dateien), Phase-F-Frontend kann /report
ohne erneuten Compliance-Hints-Call die zuletzt generierten Hinweise
anzeigen, generate_compliance_hints() bleibt fachlich unveraendert.

Negativ / Limitation: identische SQLite-Migrations-Limitation wie
ADR-0012 -- eine lokale DB-Datei von vor Tag 58 hat die neue Spalte nicht
und wirft beim naechsten get()/save() einen sqlite3.OperationalError.
Fix: lokale Datei loeschen, wird bei naechstem _init_db() neu angelegt.
Test-DBs sind tmp_path-isoliert, betroffen waere nur eine manuell
angelegte lokale Datei.

Zweite Limitation: kein Override-Mechanismus bedeutet, eine Preview/Test
des Reports mit einem hypothetischen Compliance-Hinweis (ohne vorherigen
echten Call) ist ueber die API nicht moeglich -- bewusst in Kauf genommen,
da der einzige bekannte Anwendungsfall fuer Overrides (Tests/Vorschau ohne
Persist) bei Compliance-Hinweisen die Referenz-Integritaet gefaehrden
wuerde (siehe Entscheidungspunkt 5).

## Offene Punkte

Keiner. Der Tag-57-Folgepunkt ist hiermit geschlossen. Naechste offene
Punkte aus Tag 57 unveraendert: Hybrid Search (BM25 + Vektor + RRF),
macOS-sed-Regex-Eintrag im Fallen-Katalog.
