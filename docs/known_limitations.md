# Known Limitations — AI Efficiency Control Tower (AECT)

> Limitationen offen benennen ist das staerkste Glaubwuerdigkeits-Asset
> dieses Projekts (Projekt-Prinzip "Grenzen offenlegen"). #1-#14 gelten fuer v1
> (Stand Juni 2026); #15-#17 ergaenzen die v3-Control-Tower-Module und #18-#20
> die v3.1-Assistenz-Features (Juli 2026). #21-#24 ergaenzen die im externen
> Master-Audit H (Juli 2026) bestaetigten ehrlichen Luecken (#24 = offener
> Fix-Kandidat, kein Design-Limit). #25-#32 ergaenzen die V4-Kalibrierungs- und
> Demo-Grenzen (Juli 2026, Demo-Build SDR-0003). #33 dokumentiert den
> Prod-Router-Cache-Workaround im Frontend (Next.js App Router).

---

## 1. Praediktive Validitaet nicht messbar

**Was:** AECT bewertet Use Cases im Vorfeld. Ob die vorhergesagten ROI-Werte
tatsaechlich eintreten, laesst sich im privaten Build nicht messen.

**Warum:** Praediktive Validitaet braeuchte einen geschlossenen Monitoring-Loop:
eingereichter Case -> Bewertung -> Umsetzung -> gemessener Nutzen. Dieser
Loop ist nur im produktiven Einsatz mit abgeschlossenen Cases messbar.

**Konsequenz:** Die Agreement-Rate (AECT vs. Experten-Urteil) misst
*Konsistenz* mit einer Bewertungsrubrik, nicht *Korrektheit* im Sinne
tatsaechlicher Nutzeneintritt.

**Stand:** Experten-Abgleich auf 24 gelabelten Golden-Cases (golden-001..025,
golden-004 bewusst unlabeled) — unter dem V4-Bewertungsmodell Agreement 15 von 24
(62,5 %, Kappa 0,34; Remessung 2026-07-10, Details in #26); die v3-Basis lag bei
9 von 24 (37,5 %). Die Divergenz ist
das Eval-Ergebnis, nicht ein zu behebender Fehler: Labels sind unabhaengige
Experten-Ground-Truth und werden nicht an die Engine angeglichen. Detail in
`evals/golden/report.json`, Begruendung je Case in `evals/golden/score_breakdown.json`.

---

## 2. Hard-Threshold-Brittleness

**Was:** Die drei Zonen (MARGINAL_GAIN / CALCULATED_RISK / LIKELY_WIN) werden
durch harte Zahlenschwellen in `config/zone_thresholds.yaml` getrennt.
Werte knapp unterhalb einer Schwelle landen in der niedrigeren Zone,
obwohl der Unterschied wirtschaftlich minimal ist.

**Evidenz:** golden-001 und golden-003: beide predicted zones liegen je
eine Zone neben der Experten-Einschaetzung (off-by-one). Score-Breakdown
zeigt, dass die Abweichung aus kleinen Differenzen beim `expected_benefit_eur`
oder `composite_total` resultiert -- keine falsche Berechnung, sondern
eine Eigenschaft harter Grenzen auf kontinuierlichen Werten.

**Konsequenz:** Ein Use Case mit 99.999 EUR Nutzen bei einer
LIKELY_WIN-Schwelle von 100.000 EUR erhaelt eine andere Zone als der
identische Case mit 100.001 EUR -- trotz wirtschaftlicher Aequivalenz.

**Teilweise behoben (v2, ADR-0036):** `ZoneResult` liefert jetzt einen additiven
`confidence_score` [0.5, 1.0] + `confidence_label` (hoch/mittel/niedrig). Der
Score misst den Abstand des `composite_score` zur naechsten Zonengrenze --
Grenzfaelle erhalten ~0.5, Kernfaelle ~1.0. Die Zonen-Entscheidung bleibt
deterministisch und unveraendert; der Score macht die Brittleness nur sichtbar.

**Offen:** Der Score ist eindimensional (nur composite-Achse). Die oben
beschriebene Brittleness auf der `expected_benefit`-Achse (99.999 vs. 100.001)
ist damit noch NICHT abgedeckt -- eine Zone, die durch knappen Benefit-Abstand
entsteht, wird vom composite-basierten Score nicht erfasst.

**v2-Kandidat (Rest):** 2D-Konfidenz, die zusaetzlich den Abstand zu den
Benefit-Schwellen einbezieht.

**Vertiefung:** Fallbasierte Analyse der Divergenz-Muster (dominantes
composite-5-7-Muster, Zweitannotator-Einordnung, MARGINAL_GAIN feuert
praktisch nie) mit expliziter Empfehlung 2 Zonen + numerischer Score statt
Schwellen-Nachjustierung in `docs/analysis/rule-engine-vs-human-judgment.md`.

---

## 3. Expert-Agreement auf kleinem Sample

**Was:** 24 von 25 Golden-Cases sind gelabelt (golden-004 bleibt bewusst
unlabeled, Vorfilter-Grenzfall). Agreement-Rate unter dem V4-Modell: 15/24
(62,5 %, Kappa 0,34; siehe #26). Die im Folgenden analysierte v3-Basis lag bei
9/24 (37,5 %). Das Sample wurde von urspruenglich 3 gelabelten Cases (Tag 64,
Agreement 1/3) auf 24 erweitert.

**Konsequenz:** Bei n=24 ist die Rate aussagekraeftiger als bei n=3, aber
weiterhin kein Signifikanztest. Wichtiger als die Zahl ist das Muster: Die
Mehrheit der Mismatches entsteht, weil die Engine LIKELY_WIN eng definiert
(`composite_total <= 4`), waehrend das Experten-Urteil "klarer High-Value-Fall"
breiter ist -- Composite 5-7 landet als CALCULATED_RISK. Ein groesseres Sample
mit dokumentierten Divergenzen ist ein staerkeres Asset als ein kleines mit
hoher Scheinuebereinstimmung.

**Naechster Schritt (Post-v1):** Cross-Rater-Agreement (zweiter unabhaengiger
Labeler) messen; pruefen, ob die LIKELY_WIN-Composite-Schwelle an das
Experten-Urteil angepasst werden sollte (Schwellen-Kalibrierung, nicht
Label-Korrektur). Teilweise eingeloest (Juli 2026): ein LLM-Zweitannotator im
Blind-Protokoll -- ausdruecklich kein menschlicher Experte -- erreicht Kappa 0,33
gegen die Autor-Labels und nutzt anders als der Autor auch MARGINAL_GAIN
(`evals/golden/inter_annotator_report.md`); menschliche Inter-Rater-Reliabilitaet
bleibt offen.

---

## 4. Synthetische Cases absichtlich unlabeled

**Was:** 36 synthetische Cases in `evals/synthetic/use_cases.jsonl` sind
bewusst `expected_zone: null` (ADR-0029).

**Warum:** Self-Labeling (Pipeline generiert Ergebnis -> Ergebnis wird als
expected_zone gesetzt -> Pipeline wird dagegen evaluiert) ist zirkulaere
Validierung ohne Aussagewert. Synthetic Cases testen ausschliesslich
Konsistenz (kein Crash, deterministisch) -- nicht inhaltliche Korrektheit.

---

## 5. Statische Wissensbasis

**Was:** `knowledge_base/` enthaelt kuratierte Markdown-Dateien.
Kein Live-Update aus EU-Amtsblatt, BSI oder anderen regulatorischen Quellen.

**Konsequenz:** Nach Rechtsaenderungen (z. B. Digital Omnibus in Kraft)
muessen KB-Dateien manuell aktualisiert werden. AECT prueft nicht,
ob seine Compliance-Hinweise noch dem aktuellen Rechtsstand entsprechen.

**v2-Kandidat:** Versioniertes KB-Update-Verfahren mit `last_reviewed`-Datum
und automatisiertem Staleness-Alert (> 90 Tage ohne Review).

**Konkrete Abdeckungsluecken v1:** Die Wissensbasis enthaelt aktuell DSGVO Art. 35
(DSFA-Trigger) und EU AI Act Art. 50 (Transparenzpflicht). Nicht abgedeckt sind
u. a. DSGVO Art. 28 (AVV), DSGVO Art. 6 (Rechtsgrundlage), EU AI Act Art. 4
(AI Literacy), EU AI Act Art. 5 (verbotene Praktiken) und die Doku der
konfigurierten Zielplattformen (stack_options). Die RAG-/Citation-Kette
funktioniert strukturell; die Qualitaet der Compliance-Hinweise bleibt aber
proportional zum Umfang der kuratierten Wissensbasis. Erweiterung: v2-Backlog.

---

## 6. Fehlende Deduplizierung in Compliance-Hints

**Was:** `generate_compliance_hints()` stellt bis zu zwei Retrieval-Queries
(`_TRANSPARENCY_QUERY` + `_DSFA_QUERY`). Wenn beide Queries denselben Chunk
zurueckgeben, erscheint er doppelt in der Citation-Liste.

**Konsequenz:** Hinweistext kann doppelte [N]-Referenzen enthalten. Bei
heutiger KB-Groesse (< 20 Dokumente) selten -- waechst die KB, haeufiger.

**Workaround:** Chunk-IDs vor dem Citation-Bau auf Set-Basis deduplizieren.
Dokumentiert in `application/service.py` generate_compliance_hints() Docstring.

---

## 7. PII-Erkennung: Regex, kein NER

**Was:** `sanitization.py` prueft Freitextfelder mit 4 Regex-Patterns auf
Injection-Muster (DE/EN). Kein Named-Entity-Recognition fuer echte PII
(Namen, IBAN, Geburtsdaten).

**Konsequenz:** Ein Text mit "Max Mustermann" wird nicht erkannt und
ungefiltert an den LLM-Call weitergereicht. PII-Schutz liegt beim Einreicher.

**v2-Kandidat:** spaCy-NER als optionaler Pre-Processor vor LLM-Calls.

---

## 8. LLM-Output: Graceful Degradation, nicht Qualitaetspruefung

**Was:** Bei strukturierten LLM-Outputs (Use-Case-Schaerfung) validiert AECT
gegen ein Pydantic-Schema (ADR-0013). Validierungsfehler -> `raw_text` statt
strukturierter Felder. Keine inhaltliche Qualitaetspruefung.

**Konsequenz:** Eine sachlich falsche, aber schema-konforme Schaerfung wird
akzeptiert. Human Review vor Freigabe ist nicht optional -- AECT unterstuetzt,
ersetzt kein Urteil.

---

## 9. Compliance-Hinweise: Advisory, kein Rechtsurteil

**Was:** Compliance-Hinweise sind belegte Hinweise mit Quellenangabe, immer
als "zu pruefen" markiert (Projekt-Prinzip "Hinweis, kein Urteil"). Kein juristisches Urteil,
kein `dpia_required: true`.

**Konsequenz:** Ein Hinweis "DSFA-Pruefung empfohlen" ersetzt keine
Rechtsberatung und keine tatsaechliche DSFA.

---

## 10. Embedding-Modell: Nicht domain-spezifisch

**Was:** `all-MiniLM-L6-v2` ist ein General-Purpose-Modell.
Kein Fine-Tuning auf DSGVO/EU-AI-Act-Fachterminologie.

**Konsequenz:** Semantische Aehnlichkeit bei Rechtsbegriffen ist approximiert.
Cross-Encoder-Reranking kompensiert teilweise (ADR-0028), loest das Problem
aber nicht vollstaendig.

---

## 11. Kein Produktivbetrieb

**Was:** AECT ist ein privates Portfolio-Projekt (Projekt-Zielsetzung).
Kein Clustering, kein HA, kein automatisiertes Backup, kein Monitoring
(Alerting-Konzept dokumentiert, nicht implementiert).

**Konsequenz:** Kein SLA. Nicht fuer Kundendaten geeignet ohne
Security-Hardening-Pass und IP-Klaerung (vertraglich bedingt).

**Vertiefung (ADR-0040):** "Kein Clustering" konkretisiert -- die
F-010/F-011-Concurrency-Fixes verifizieren nur parallele Requests EINES
Nutzers auf denselben Case, nicht viele gleichzeitige Nutzer. SQLite ist
Single-Writer (kein horizontaler Scaling-Pfad), ChromaDB laeuft als
Einzelinstanz (kein Multi-Instance-Deploy ohne Umbau). Migrationstrigger
dort konkret benannt (z. B. mehr als ein gleichzeitiger Reviewer).

---

## 12. Frontend: lokal laufend, kein Cloud-Deploy

**Was:** Das Next.js 16 Frontend (App Router, shadcn/ui) ist fertig und laeuft
lokal auf Port 3000. Triage-Flow (Intake -> Triage -> Sharpen -> Solution ->
Compliance -> Report) plus die v3-Control-Tower-Module (Ideenliste, Board,
Monitoring).

**Konsequenz:** Demo erfordert zwei laufende Prozesse (uvicorn + npm run dev)
und Docker fuer ChromaDB. Kein öffentlicher URL -- privates Portfolio-Build
(privates Projekt, vertragliche IP-Klaerung ausstehend).

**Produktivbetrieb-Anforderungen:** Reverse-Proxy (NGINX/Caddy) vor beiden
Services, HTTPS-Terminierung, Dockerfile fuer Frontend. Dokumentiert als
Post-v1-Punkt (ADR-0035).

---

## 13. ADR-Doppelserie (Technische Schuld)

**Was:** Zwei koexistierende ADR-Serien: `ADR-00X` (Phase A/B) und `0XXX`
(Phase C+). Historisch gewachsen (session-protocol v3 SS6 Punkt 13).

**Konsequenz:** Neue ADRs muessen `ls docs/adr/` pruefen statt eine Serie
anzunehmen.

**Entscheidung (G-S6, Tag 81):** Bewusst als dokumentierte Schuld belassen, NICHT
konsolidiert. Ein Rename aller 41 ADRs plus Nachziehen jeder Quer-Referenz (README,
CLAUDE.md, Code-Docstrings, andere ADRs) ist hohe Churn mit Null funktionalem
Gewinn und realem Bruch-Risiko fuer Links. Die `ls docs/adr/`-Regel (CLAUDE.md)
ist der guenstigere Workaround. Re-Evaluierung nur falls eine dritte Serie droht.

---

## 15. Monitoring ist manuell -- praediktive Validitaet bleibt unmessbar

**Was:** Die Monitoring-Zeitleiste (v3, ADR-0046) fuellt sich ausschliesslich
durch manuelle Notizen. Es gibt keinen automatischen Abgleich zwischen dem bei
der Triage vorhergesagten Nutzen (Plan) und einem tatsaechlich realisierten
Nutzen (Ist).

**Konsequenz:** Das Monitoring dokumentiert den Bearbeitungsverlauf, schliesst
aber NICHT den Plan-vs-Ist-Loop, der praediktive Validitaet messbar machen
wuerde. Es ist dieselbe Grenze wie Limitation #1 -- die Zeitleiste macht den
Verlauf nachvollziehbar, liefert aber keine gemessene Nutzen-Korrektheit. Ein
Eintrag "Nutzen liegt unter Prognose" ist eine Notiz, kein strukturiertes
Messsignal, das gegen die Bewertung zurueckfliesst.

**v2-Kandidat:** siehe Limitation #1 -- ein geschlossener Monitoring-Loop mit
strukturierten Ist-Werten je Case setzt produktiven Einsatz mit abgeschlossenen
Cases voraus.

---

## 16. Status-Historie: nur Snapshots im Frontend sichtbar

**Was:** Jeder Statuswechsel loggt ein `case_status_changed`-Event in structlog
(vollstaendiges Audit-Log, ADR-0045). Im Frontend ist die Status-Historie
jedoch NICHT als vollstaendiges Audit-Log sichtbar -- nur der aktuelle Status
(Case-Detail) und die `status_snapshot`-Momentaufnahmen in den
Monitoring-Eintraegen (ADR-0046) zeigen den Verlauf indirekt.

**Konsequenz:** Wer im Frontend rekonstruieren will, wann ein Case von IN_REVIEW
nach APPROVED wechselte, sieht das nur, wenn zu diesem Zeitpunkt zufaellig eine
Monitoring-Notiz mit passendem Snapshot angelegt wurde. Der lueckenlose
Statusverlauf existiert nur in den structlog-Events, nicht in einer abfragbaren
Frontend-Ansicht.

**v2-Kandidat:** eine eigene Status-Change-Tabelle (append-only, analog
`monitoring_entries`) mit Frontend-Historie, falls ein lueckenloser
Statusverlauf gebraucht wird.

---

## 17. Board-Quadranten-Linien sind Platzhalter, keine Schwellen

**Was:** Die Board-Matrix (v3, ADR-0047) zeigt zwei gestrichelte
Quadranten-Linien (x = 50.000 EUR, y = 6) und vier Ecklabels ("Quick Wins",
"Nice to have", "Strategische Wetten", "Vermeiden"). Diese Werte sind statisch im
Frontend hartcodiert (`board-matrix.tsx`, `QUADRANT_X`/`QUADRANT_Y`), NICHT aus
`config/zone_thresholds.yaml` gelesen.

**Konsequenz:** Die Linien sind eine visuelle Lese-Hilfe zur groben Gruppierung,
KEINE Geschaeftsregel. Die tatsaechliche Triage-Zone transportiert die
Punktfarbe -- nicht die Position relativ zur Linie. Das Backend exponiert die
echten Schwellen bewusst nicht (IP-Trennung), darum kann die Board-Ansicht sie
nicht spiegeln. Ein Punkt links der 50.000-Linie ist nicht automatisch
MARGINAL_GAIN.

**Bewusst so:** Eine aus der Config gelesene Schwellen-Linie wuerde den
Eindruck einer zweiten, eventuell abweichenden Klassifikation erzeugen. Die
Farbe ist die einzige Wahrheit; die Linien sind Dekoration mit Orientierungswert.

---

## 18. Generative Features nicht durch die Golden-Eval abgedeckt

**Was:** Die zwei generativen v3.1-Features -- der Ideen-Assistent (`/ideation`,
ADR-0048) und die Architektur-Skizze (`/cases/{id}/architecture-sketch`,
ADR-0049) -- sind NICHT Teil der Golden-Eval. Die 25 Golden-Cases messen die
deterministische Bewertung (Zone, ROI); es gibt keine gelabelten Referenz-
Entwuerfe oder Referenz-Skizzen, gegen die eine generierte Ausgabe verglichen
wird.

**Warum:** Beide Ausgaben sind offen (freie Sprache bzw. ein Graph aus einer
grossen Moeglichkeitsmenge). Eine belastbare Qualitaets-Metrik braeuchte
menschlich gelabelte Referenzen ODER einen LLM-Judge mit eigener Validitaets-
frage -- beides ist im privaten Build nicht aufgebaut. Self-Labeling (Ausgabe
wird zur eigenen Ground-Truth) waere zirkulaer, dieselbe Falle wie bei den
synthetischen Cases (#4).

**Konsequenz:** Die Qualitaet der generativen Ausgaben ist NICHT metrisch
belegt. Gesichert ist nur die *Form*, nicht der *Inhalt*: (1) Schema-Zwang --
Ideation validiert gegen `IdeationResult`, die Skizze gegen `ArchitectureSketch`
(Referenz-Integritaet per Model-Validator); eine schema-verletzende Antwort
wird auf 502 gemappt, nicht ausgeliefert. (2) Menschliche Pruefung -- der
Entwurf ist eine Arbeitsvorlage (Zahlen liefert der Mensch, ADR-0048), die
Skizze ein "zu pruefen"-Artefakt. Eine sachlich schwache, aber schema-konforme
Ausgabe wird akzeptiert -- dieselbe Grenze wie bei der Use-Case-Schaerfung (#8).

**v2-Kandidat (Backlog "Eval-Abdeckung generative Features"):** eine kleine
Referenz-Menge (Problembeschreibung -> erwartete Entwurfs-Merkmale;
Loesungsvorschlag -> erwartete Knoten/Kanten) plus ein LLM-Judge mit
dokumentierter Validitaetsgrenze -- analog zum Inter-Annotator-Ansatz bei den
Golden-Cases (#3).

---

## 19. Dedup-Sicht rechnet O(n^2) beim Lesen

**Was:** `GET /cases/similarity-pairs` (v3.1) vergleicht alle Cases mit Embedding
paarweise -- der Aufwand waechst quadratisch mit der Case-Zahl. Der Vergleich
laeuft bei jedem Aufruf neu (on-read), es gibt keinen vorberechneten
Aehnlichkeits-Index.

**Warum bewusst:** AECT ist ein privater Portfolio-Build ohne Pagination-Scope
(SDR-0002 Paragraph 12), die Portfolio-Datenmenge bleibt klein. Bei wenigen
Dutzend Cases ist die Matrix schlicht der einfachere, testbarere Code als ein
Approximate-Nearest-Neighbor-Index (z. B. HNSW), der Index-Rebuild bei jedem
Intake und Konsistenz Index-vs-DB als Betriebskomplexitaet einfuehren wuerde --
Aufwand fuer eine Last, die es in diesem Build nie gibt.

**Grenze:** Ab einigen Tausend Cases wird der Vollscan spuerbar; dann waere ein
ANN-Index ueber den bestehenden Vektor-Store die richtige Antwort. Dokumentiert
als Code-Kommentar in `list_similarity_pairs()` und in `notes/daily`
(Tag 86) -- bewusst kein ADR, weil kein Architekturbruch.

---

## 20. Aehnlichkeit misst Text-Naehe, kein inhaltliches Urteil

**Was:** Die Dedup-Sicht (#19) und die Intake-Warnung beruhen auf Cosinus-
Aehnlichkeit von Embeddings (`all-MiniLM-L6-v2`) ueber Titel/Beschreibung. Ein
hoher Score bedeutet Text-Naehe, nicht dass zwei Cases wirklich dieselbe
fachliche Loesung meinen.

**Konsequenz:** Zwei sprachlich aehnliche, fachlich verschiedene Cases koennen
als Paar erscheinen (False Positive); zwei fachlich gleiche, aber anders
formulierte Cases koennen unter der Schwelle bleiben (False Negative). Die Sicht
ist deshalb eine *Vorschlagsliste* fuer eine menschliche Zusammenlege-
Entscheidung ("N aehnlich" / "Zusammenlegen pruefen"), kein automatisches
Dedup-Urteil -- dieselbe Human-in-the-Loop-Linie wie ueberall. Verstaerkt durch
#10 (Embedding-Modell ist General-Purpose, nicht domain-spezifisch).

---

## 21. Prompt-Injection-Erkennung ist Best-Effort-Observability, kein Schutz

**Was:** `sanitization.py` prueft Freitext mit vier Regex-Patterns (DE/EN) und
FLAGGT Treffer (Log), blockt aber nicht (`flag-not-block`, bewusst). Ein externer
Audit-Lauf (Master-Audit H-017, S2) hat gezeigt: fuenf von fuenf einfachen
Obfuskations-Varianten (Zero-Width-Space, Leetspeak `1gn0re`, Synonyme `skip the
rules`, Newline-Split, Sprach-Mix) umgehen ALLE vier Patterns. Der als "primaere
Verteidigung" bezeichnete `<<<DATA>>>`-Delimiter ist zudem vom Nutzer-Input
brechbar, weil der Freitext roh (ohne Delimiter-Neutralisierung) in den Prompt
gesetzt wird (H-018). Auf zwei der fuenf LLM-Pfade (compliance-hints, sketch) laeuft
die Erkennung gar nicht (H-030).

**Konsequenz:** Der Wert der Injection-Erkennung ist ausschliesslich Observability
(eine Log-Zeile), und diese ist mit trivialen Tricks stumm zu schalten. Sie ist
KEIN Control. Der real begrenzte Blast-Radius ist strukturell bedingt, nicht durch
die Regex: kein Secret im System-Prompt, Single-User, parameterloses Tool, Ausgabe
ist Advisory-Text. Die Formulierung "vierlagiger Schutz" ueberschaetzt die Regex-
Lage; strukturell tragen nur die getrennten `LLMMessage`-Rollen und die
Pydantic-Output-Validierung.

**v2-Kandidat:** Unicode-Normalisierung (NFKC + Zero-Width strippen) vor dem Match,
Delimiter-Tokens im Feldwert neutralisieren, und die Erkennung auf allen LLM-Pfaden
aufrufen -- ODER die Erkennung ehrlich nur als Logging deklarieren und die
Verteidigung strukturell fuehren.

---

## 22. Country-Coverage: 3 von 12 Enum-Laendern konfiguriert

**Was:** Das `Country`-Enum bietet 12 Laender an (de/at/ch/no/gb/es/it/tr/ro/pl/
eg/in); die committete `config/roi_config.toml` traegt Stundensaetze nur fuer
`de/at/ch`. Die uebrigen neun Laender liegen in der gitignorierten
`roi_config.local.toml` (IP-Trennung) und fehlen im Fresh Clone.

**Konsequenz:** Ein API-/Frontend-valides `country` ausserhalb DACH fuehrt zu
Stundensatz 0 → Potenzial 0 → Vorfilter-Fail. Der Vorfilter meldet dann
"Theoretisches Potenzial 0 EUR < Schwelle" statt "kein Stundensatz fuer Land X
konfiguriert" -- eine inhaltlich falsch begruendete, still aussehende Ablehnung
(Master-Audit H-011, S1). Im Docstring vermerkt, zur Laufzeit aber still.

**v2-Kandidat:** Fail-fast bei fehlendem Land (expliziter Fehler statt stillem 0),
oder das Enum/Frontend auf die tatsaechlich konfigurierten Laender beschraenken,
oder mindestens den Vorfilter-Grund den wahren Ursprung nennen lassen.

---

## 23. Zonen-Einstufung nutzt den Brutto-Nutzen (vor Lizenzabzug)

**Was:** Die Benefit-Achse der Zonen-Einstufung erhaelt `expected_benefit_eur`
(Nutzen VOR Lizenzabzug); die Lizenzkosten wirken nur ueber den Composite-Kosten-
Tier (Aufwand-Achse), nicht auf der Benefit-Achse (Master-Audit H-009, S1).

**Konsequenz:** Ein Case mit hohem Brutto-Potenzial, aber duennem Netto-Nutzen nach
Lizenz (z. B. 325.000 EUR Potenzial, 320.000 EUR Lizenz → 5.000 EUR netto) kann als
LIKELY_WIN erscheinen, obwohl der reale Jahres-Nettonutzen minimal ist. Das steht in
Spannung zu ADR-002, dessen Formulierung die untere Zonen-Schwelle mit dem
Netto-Nutzen-Vorfilter gleichsetzt. Der Vorfilter selbst rechnet netto und faengt
die extremsten Faelle ab; die Zonen-EINSTUFUNG darueber bleibt brutto.

**v2-Kandidat:** Zone bewusst auf `net_expected_benefit_eur` umstellen ODER die
Brutto-Semantik in ADR-002 + `zone_thresholds.yaml` explizit machen und begruenden,
warum die Lizenz nur auf der Aufwand-Achse zaehlt.

---

## 24. CSV-Export ohne Formel-Injection-Schutz (Fix-Kandidat, kein Design-Limit)

**Was:** Der client-seitige CSV-Export (`frontend/src/lib/csv.ts`) neutralisiert
fuehrende Formel-Zeichen (`=`, `+`, `-`, `@`) in Feldwerten nicht (Master-Audit
H-038, S6). Oeffnet ein Nutzer die exportierte Datei in Excel/LibreOffice, kann ein
Case-Titel wie `=HYPERLINK(...)` oder `=cmd|...` als Formel ausgewertet werden
(CSV/Formula Injection).

**Konsequenz:** Ein per Intake eingeschleuster Titel wird beim Export zu einer
potenziell aktiven Zelle. Im privaten Single-User-Build mit selbst eingegebenen
Daten ist das Risiko klein, aber der Export ist die einzige Stelle, an der
Case-Text die vertrauenswuerdige App-Grenze in eine fremde Anwendung verlaesst.

**Anders als #1-#23 ist das kein bewusstes Design-Limit, sondern ein offener
Fix-Kandidat (P1):** fuehrende `= + - @ \t \r` je Feld mit einem `'` praefixen
(gaengige Anti-CSV-Injection-Konvention). Als Limitation gefuehrt, bis der Code-Fix
gemacht ist.

---

---

## 25. Composite-Range 1-9 mit unveraenderten Zonen-Schwellen (Kalibrierungsstand)

**Was:** V4 rechnet den Aufwandscore neu (Range **1-9**: Komplexitaet 1-5 aus dem
Implementierungsansatz + Kostenpunkte 0-2 + Datenschutz 0-2, SDR-0003 Entscheidung
4). Die Zonen-Schwellen in `config/zone_thresholds.yaml` blieben dabei bewusst
**unveraendert** (SDR-0003 Entscheidung 5) -- LIKELY_WIN feuert weiter bei
`composite_total <= 4`.

**Backtest-Befund:** Der Zonen-Schwellen-Backtest
(`scripts/analysis/zone_threshold_backtest.py`) misst das Golden-Agreement fuer
verschiedene LIKELY_WIN-Composite-Schwellen und findet das Optimum bei
`composite <= 5`, nicht beim aktuell gesetzten `<= 4` (Peak `composite<=5` = 0,667,
danach nicht-monoton: `composite<=6` faellt wieder auf 0,625).

**Konsequenz / Entscheidung:** Das Backtest-Optimum wird **bewusst NICHT
automatisch uebernommen** -- Produktentscheidung. Eine Schwelle an ein
24-Case-Sample zu fitten waere Overfitting auf ein kleines Set ohne
Signifikanztest (#3); stabile Schwellen halten die Zonen-Semantik ueber die
Versionen vergleichbar. Der Backtest ist ein dokumentierter Kalibrierungs-Hinweis,
keine Auto-Tuning-Schleife. Verwandt mit #2 (Hard-Threshold-Brittleness) und #26.

---

## 26. Golden-Agreement unter V4: 62,5 % (15/24), v3-Basis 37,5 %

**Was:** Unter dem V4-Nutzenmodell (person-basierte Formel) stieg das Raw
Agreement der Engine gegen die Autor-Labels auf **15/24 (62,5 %, Cohen's Kappa
0,34)**, gemessen **2026-07-10** (V4-P4). Die v3-Basis (altes Modell) lag bei
**9/24 (37,5 %, Kappa 0,06)** -- der historische Vergleichswert, auf den sich #1
und #3 urspruenglich bezogen.

**Warum die Verschiebung:** Die person-basierte Formel (Zeitersparnis x Vorgaenge
je MA x Anzahl MA x Stundensatz) inflationiert Cases mit vielen betroffenen
Mitarbeitern -> mehr LIKELY_WIN, was besser zu den optimistischen Autor-Labels
passt. Zugleich fallen drei Ein-Personen-Cases (golden-005/006/016) jetzt knapp
durch den Vorfilter (Potenzial < 20k). Die Labels selbst blieben unangetastet
(kein Anpassen der Ground Truth an das Modell, SDR-0003 Entscheidung 5).

**Konsequenz:** Kappa 0,34 ist "fair" -- die Zahl misst weiter *Konsistenz* mit
einer Rubrik, nicht *Korrektheit* (#1), auf einem 24-Case-Sample ohne
Signifikanztest. Details und Grenzen in `evals/golden/inter_annotator_report.md`
(V4-P4-Abschnitt), Rohdaten in `evals/golden/report.json`.

---

## 27. Zahlen-Validator: Ziffern + einfache Zahlwoerter, keine komplexen Faelle

**Was:** Der Schaerfungs-Guard (`domain/sharpening_guard.py`, SDR-0003 Entscheidung
6) verhindert deterministisch (Regel VOR dem LLM), dass eine geschaerfte
Beschreibung Zahlen enthaelt, die nicht aus der Eingabe stammen. `extract_numbers`
erkennt Ziffern (dt. Formate: `4.200` -> 4200, `1.000,50` -> 1000.5) und einfache
ausgeschriebene Zahlwoerter (`eins` .. `tausend`).

**Grenze:** Komplexe zusammengesetzte Zahlwoerter ("zweihundertfuenfzigtausend"),
Einheiten-Umrechnungen (Stunden <-> Minuten, Prozent <-> Faktor) und implizite
Rechnungen werden **nicht** erkannt. Aufzaehlungsmarker (`1.`/`2)`/`3:`) und
Jahreszahlen sind bewusst ausgenommen. Der Guard laeuft nur ueber
`sharpened_title` / `current_state` / `desired_state`, **nicht** ueber die
Vorschlags-`hebel` (die duerfen Faktoren beziffern, z. B. "Evidenzfaktor 0,40 ->
0,90").

**Konsequenz:** Eine erfundene Zahl in einem nicht abgedeckten Format kann
durchrutschen. Der Guard ist eine deterministische erste Verteidigung, keine
vollstaendige numerische Faktenpruefung -- der eigentliche Schutz bleibt die
menschliche Pruefung des Drafts vor dem Accept (Draft/Accept-Flow). Verwandt mit
#8 (LLM-Output: Graceful Degradation, keine Qualitaetspruefung).

---

## 28. Auth ist ein Single-Admin-Demo-Modell

**Was:** V4 fuehrt zwei Zugriffsstufen ein (anonym / Admin) ueber ein **einziges**
Admin-Passwort (scrypt-Hash in `AECT_ADMIN_PASSWORD_HASH`) + Session-Cookie
(SDR-0003 Entscheidung 7). Kein Multi-User, keine Nutzerverwaltung, keine Rollen
jenseits anonym/Admin, kein JWT/OAuth, keine Passwort-Zuruecksetzung, kein
Login-Audit je Person.

**Konsequenz:** "Admin" ist eine Betriebs**stufe**, keine Identitaet -- alle
Admin-Aktionen sind ununterscheidbar (ein geteilter `session`-Token-Budget-Bucket,
V4-P-Auth). Der `/login` ist zwar rate-limitiert (10/Minute), aber es gibt keinen
Account-Lockout und keine Zwei-Faktor-Stufe. Fuer den Demo-Build (ein
Vorfuehrender) ist das ausreichend und bewusst minimal; Mehrbenutzer-Betrieb
braeuchte ein echtes Identity-Modell. Hebt die "API-Key only"-Grenze aus SDR-0002
Paragraph 12a kontrolliert auf (weiterhin kein Multi-User).

---

## 29. Stundensaetze NO/GB/ES/IT/RO/IN sind unverifizierte Schaetzwerte

**Was:** Die gitignorierte `config/roi_config.local.toml` traegt Stundensaetze fuer
12 Laender x 5 Level (Config-Layering ueber die getrackte Platzhalter-Config). Fuer
`de/at/ch` sind die Werte belastbarer; die Saetze fuer `no/gb/es/it/ro/in` sind
**lokale Schaetzwerte** ("vor Demo pruefen"), nicht gegen eine externe Quelle
verifiziert.

**Konsequenz:** ROI-Zahlen fuer Cases in diesen Laendern sind
groessenordnungs-, nicht punktgenau -- ein systematischer Fehler in einem Satz
wirkt linear auf Roh-Nutzen und Netto-Nutzen durch. Verstaerkt #22: im getrackten
`config/roi_config.toml` sind ohnehin nur `de/at/ch` konfiguriert, die uebrigen
neun Laender fehlen im Fresh Clone ganz (dort Stundensatz 0 -> Vorfilter-Fail).

---

## 30. Die Bewertung ist Admin-Material -- Nicht-Admins sehen nur die Entscheidung

**Was:** `GET /cases` (Liste) und `GET /cases/{id}` (Detail) antworten mit
**zwei verschiedenen Schemas**. Nicht-Admins bekommen `PublicCaseSummary` bzw.
`PublicCaseDetailResponse`: Grunddaten des Einreichens, Lifecycle-Status und --
im Detail -- die Board-Entscheidung samt Begruendung. Zone, Nettonutzen, Scores,
Machbarkeit, Analyse/Empfehlung, Loesungsvorschlag, Compliance und Report stehen
in diesen Antworten **nicht** -- auch nicht als `null`. Admins (Session ODER
X-API-Key) bekommen unveraendert die vollen Schemas.

**Warum:** zweite **Korrektur derselben Stelle**. V4-P7 (`2c1d440`/`5dfc58e`)
machte die Bewertung sofort anonym sichtbar; die erste Korrektur koppelte sie an
`reviewer_decision != PENDING` -- nach der Entscheidung war der volle Score also
weiterhin anonym lesbar, inkl. `assessment_visible` als Verraeter der verborgenen
Groessen. Das Rollenmodell aus SDR-0003 (Entscheidung 7) will, dass der
Einreicher **das Ergebnis** kennt, nicht dessen Herleitung: die Bewertung ist
Entscheidungsgrundlage des Boards, kein Feedback an den Einreicher.

**Konsequenz:** Ein Bewertungs-Leak ueber diese Routen ist nicht mehr eine Frage
der Bedingung, sondern strukturell ausgeschlossen -- die Public-Klassen fuehren
die Felder nicht, `extra="forbid"` laesst ein versehentlich durchgereichtes Feld
laut scheitern. Kehrseite: der Einreicher erfaehrt nie, *warum* sein Case
abgelehnt wurde, ausser das Board schreibt es in die Begruendung
(`reviewer_note`). Die Qualitaet dieser Freitext-Begruendung traegt damit die
gesamte Rueckmeldung -- im Demo-Build gewollt, im Self-Service-Betrieb waere ein
strukturierteres Feedback die naechste Frage.

---

## 31. `_HIGH_VOLUME_MIN_ANNUAL = 250`/Jahr ist eine Alltagsannahme

**Was:** Das AI-vs-Automation-Routing (`domain/routing.py`) wertet ein hohes
Vorgangsvolumen als Automatisierungs-Signal, ab `_HIGH_VOLUME_MIN_ANNUAL = 250`
Vorgaengen je Mitarbeiter/Jahr. Der Wert wurde bei der V4-Umstellung auf
person-basierte Semantik neu gesetzt (vorher 2000, kalibriert fuer das
Gesamtvolumen der Organisation).

**Grenze:** 250 ist eine plausible **Alltagsannahme** (~ein Vorgang je
Arbeitstag), **nicht** aus den Golden-Cases abgeleitet -- dort ist das
Volumen-Signal nicht trennscharf genug fuer eine datengetriebene Schwelle.

**Konsequenz:** Ein Case knapp ueber/unter 250 gewinnt oder verliert das
Volumen-Signal, ohne dass die Grenze empirisch fundiert ist -- dieselbe
Hard-Threshold-Natur wie bei den Zonen (#2), nur auf der Routing-Achse. Der Wert
ist eine bewusste, dokumentierte Setzung, kein gemessenes Optimum.

---

## 32. Board-Ecklabels und Diff-Split nur strukturell verifiziert (kein Browser-Tool)

**Was:** Zwei rein visuelle V4-Frontend-Punkte sind **strukturell**, aber nicht
per Screenshot verifiziert: die Board-Ecklabel-Positionen (`board-matrix.tsx`,
Pixel-Naeherungen relativ zu den Quadranten) und die churn-abhaengige
Diff-Split-Ansicht (`sharpening-review.tsx`, Umschaltschwelle churn 0,5). Die
Build-Umgebung hat kein Browser-Tool (Playwright/Puppeteer).

**Verifikationsstand:** Board-Achsen-Ueberlappung per Layout-Argument
ausgeschlossen (Achsentitel in eigenen HTML-Gutter-Boxen, disjunkt zu den
Tick-Labels); y-Achsen-Domain gegen den 1-9-Composite gerechnet; die
churn-Umschaltung (inline < 0,5 < split) per Skript belegt. **Nicht** verifiziert:
die pixelgenaue Ecklabel-Position und die visuelle Lesbarkeit des Splits bei
einem echten starken Rewrite.

**Konsequenz:** Kein Funktions-, sondern ein **Verifikations-Vorbehalt** -- diese
beiden Punkte vor der echten Demo einmal im Browser gegenpruefen
(`docs/demo-script.md` Abschnitt 3.3). Verwandt mit #17 (die Quadranten-Linien
sind Lese-Hilfe, keine Schwellen).

---

## 33. Prod-Router-Cache: harter Reload statt `router.refresh()`

**Was:** Auf der Case-Detailseite (`/cases/[id]`) greift `router.refresh()` im
**Prod-Build** nicht durch -- der client-seitige RSC-Router-Cache liefert die
alte Server-Component-Nutzlast weiter. Eine gerade persistierte Admin-Aktion
(Schaerfen-Uebernehmen, Loesung, Compliance, Board-Entscheidung, Ansatz-Nachtrag)
erscheint dann nicht in der UI, obwohl der Backend-/RSC-Endpoint frisch ist
(`no-store`, `force-dynamic`, 200 vom Backend).

**Workaround:** Ein zentraler harter Reload statt Soft-Refresh --
`hardRefresh()` (`frontend/src/lib/reload.ts`, `window.location.reload()`) an
allen mutierenden Detail-Aktionen zieht den frischen SSR-Stand zuverlaessig
(Fix `86791c3`).

**Warum so:** Die serverseitige Cache-Invalidierung per `revalidatePath`
(`actions.ts`) und ein `staleTimes: 0` loesten den **client-seitigen**
Router-Cache nicht auf -- der Soft-Refresh blieb stale. Das ist **kein
AECT-spezifischer Bug**, sondern bekanntes Next.js-App-Router-Verhalten (der
RSC-Router-Cache im Prod-Build, im Dev-Build nicht sichtbar). Der harte Reload
ist die pragmatische, robuste Antwort fuer den Single-User-Demo-Build; ein
feineres Soft-Refresh-Muster ist ein Post-v4-Punkt.

---

## 14. Vorfilter-Schwellen: Zwei Quellen (BEHOBEN, F-001)

**Was (historisch):** Die Vorfilter-Schwellen existierten doppelt: als
Python-Defaults in `src/aect/domain/filters.py` UND als Config-Werte in
`config/roi_config.toml`. `evaluate_use_case()` nutzte die Python-Defaults --
Aenderungen an den TOML-Schwellen waren fuer die Pipeline ein stiller No-op.

**Status:** Behoben (Phase-2-Fix F-001, Juli 2026). `apply_prefilter()` hat
keine eigenen Defaults mehr; `evaluate_use_case()` reicht die
ROIConfig-Schwellen verpflichtend durch. `vorfilter.passes` (Pipeline) und
`roi.passes_prefilter` (ROI-Engine) urteilen gegen dieselbe Quelle.
Regressionstest: `tests/domain/test_pipeline.py`
(`test_prefilter_uses_config_thresholds_not_module_defaults`).

---

## 15. i18n (Deutsch/Englisch): Grenzen der Lokalisierung (V4.1-S6)

**Was:** AECT ist zweisprachig (Deutsch = Default, Englisch per Header-Umschalter,
Cookie-basiert ohne Locale-URL-Prefix). Backend-seitig sind alle deterministisch
erzeugten Texte katalogisiert (Score-Erklaerungen, Report/Contra-Punkte,
Routing-Signale, Vorfilter-/Machbarkeits-Texte, darstellbare 4xx/5xx-Details) und
folgen dem `lang`-Query-Parameter (Default `de`, ungueltig -> 422).

**Bewusste Grenzen:**

1. **Nutzereingaben werden nie uebersetzt.** Case-Titel, Ist-/Soll-Beschreibungen,
   Beispielprozesse und Monitoring-Notizen erscheinen in der Sprache, in der sie
   erfasst wurden -- unabhaengig von der aktiven UI-Sprache. Das System uebersetzt
   keine Freitext-Eingaben (kein zusaetzlicher LLM-Call, keine erfundene Semantik).

2. **Bestands-LLM-Inhalte bleiben in ihrer Erstellungssprache.** Schaerfungen,
   Loesungsvorschlaege und Ideen-Entwuerfe, die vor bzw. in einer anderen Sprache
   erzeugt wurden, werden nicht rueckuebersetzt. Neue LLM-Calls (Schaerfen, Loesung,
   Ideation) erhalten bei `lang=en` eine Sprachinstruktion; bereits gespeicherte
   Ergebnisse bleiben unveraendert.

3. **Sharpening-Guard-Zahlwoerter sind deutsch.** Der Zahlen-Validator vergleicht
   sprachunabhaengig Ziffern; die zusaetzliche Wort->Ziffer-Normalisierung
   ("fuenf" -> "5") deckt nur deutsche Zahlwoerter ab. Im EN-Modus erzwingt die
   LLM-Sprachinstruktion daher Ziffern ("keep all numeric values as digits") --
   englische Zahlwoerter wuerden vom Guard nicht als Zahl erkannt.

4. **Zahl-Gruppierung in Backend-Fliesstext folgt Deutsch.** Frontend-seitig
   formatierte Zahlen/Betraege/Daten folgen der aktiven Locale (next-intl
   `useFormatter`, EUR-Symbol fix). Zahlen, die das Backend deterministisch IN
   einen Satz einbettet (z. B. der Empfehlungs-Satz "... about 10.000 hours
   saved ... (259.200 EUR net benefit) ..."), nutzen weiterhin die deutsche
   Tausender-Gruppierung (`domain/formatting.format_de`). Das ist eine reine
   Gruppierungs-Konvention, kein deutsches Wort; eine Locale-abhaengige
   Backend-Zahlformatierung ist bewusst nicht gebaut (waere ein Query-Wert quer
   durch die Erklaerbarkeits-Schicht).

Die Frontend-Lokalisierung ist vollstaendig: alle Seiten (Startseite, Einreichen
inkl. Validierungsfehler, Ideenliste, Fall-Detail mit allen drei Bereichen,
Board, Monitoring, Ideen-Assistent, Admin-Login) und die geteilten Kataloge
(Enums, Status, Zonen, Navigation, Footer, Fehlermeldungen) sind in de/en. Ein
CI-faehiger Paritaets-Check (`npm run i18n:check`) stellt sicher, dass
`de.json`/`en.json` keine divergierenden Schluessel haben. Der Sprachwechsel
laedt hart neu (`window.location.reload`), damit der Next.js-Router-Cache -- der
NICHT nach Cookie variiert -- keinen Rest der Vorsprache auf vorgeladenen Routen
zeigt (dieselbe App-Router-Cache-Grenze wie #33). Ein offener Intake-Wizard
verliert dabei seinen Zwischenstand -- bewusster Kompromiss zugunsten
konsistenter Sprache.

---

*Letzte Aktualisierung: 2026-07-14 -- #15 auf vollstaendige Frontend-Lokalisierung
aktualisiert (V4.1-S6 Phase 2 abgeschlossen: alle Seiten de/en, Zahl-Gruppierung
in Backend-Fliesstext bleibt deutsch, Hard-Reload beim Sprachwechsel). Vorher
2026-07-14 -- #15 ergaenzt (i18n de/en, Grenzen). Vorher 2026-07-13 -- Pre-S5-Nacharbeit: #33 ergaenzt
(Prod-Router-Cache-Workaround, harter Reload statt `router.refresh()`; bekanntes
Next.js-App-Router-Verhalten, kein AECT-Bug). Vorher 2026-07-11 -- V4-Release
(v4.0.0): #25-#32 ergaenzt
(Composite-Range 1-9 bei stabilen Zonen-Schwellen, Golden-Agreement-Remessung
62,5 %, Zahlen-Validator-Grenze, Single-Admin-Auth, unverifizierte
Nicht-DACH-Stundensaetze, decision-gekoppelte Sichtbarkeit, Routing-Volumen-
Schwelle, strukturelle Frontend-Verifikation); #1/#3 auf die V4-Agreement-Rate
nachgezogen. Vorstand: 2026-07-06 -- v3.1.0 + Master-Audit-H-Konsolidierung
(#21-#24 aus H-009/H-011/H-017/H-018/H-030/H-038, siehe
`docs/reviews/master-audit-h-summary.md`). Phase-G-Triage der urspruenglichen 14
Punkte (bewusstes Design / v1-Grenze + v2-Roadmap) in
`docs/reviews/phase-g-review.md` SS3.*
