# Known Limitations — AI Efficiency Control Tower (AECT)

> Limitationen offen benennen ist das staerkste Glaubwuerdigkeits-Asset
> dieses Projekts (Projekt-Prinzip "Grenzen offenlegen"). #1-#14 gelten fuer v1
> (Stand Juni 2026); #15-#17 ergaenzen die v3-Control-Tower-Module und #18-#20
> die v3.1-Assistenz-Features (Juli 2026).

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
golden-004 bewusst unlabeled) — Agreement 9 von 24 (37,5 %). Die Divergenz ist
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
unlabeled, Vorfilter-Grenzfall). Agreement-Rate: 9/24 (37,5 %). Das Sample
wurde von urspruenglich 3 gelabelten Cases (Tag 64, Agreement 1/3) auf 24
erweitert.

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
heutiger KB-Groesse (< 20 Dokumente) selten -- wae chst die KB, haeufiger.

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

*Letzte Aktualisierung: 2026-07-06 -- v3.1.0 (Assistenz-Layer-Closeout, #18-#20
ergaenzt). Phase-G-Triage der urspruenglichen 14 Punkte (bewusstes Design /
v1-Grenze + v2-Roadmap) in `docs/reviews/phase-g-review.md` SS3.*
