# Interview Q&A — AECT

> Vorbereitung fuer AI-Engineer / Solution-Architect Interviews im DACH-Markt.
> Jede Antwort ist aus dem Repo verteidigbar -- Dateiname oder ADR-Nummer
> als Anker, kein auswendig gelerntes Wissen.

---

## Architektur

**Warum Hexagonale Architektur?**

Die Domain-Logik (ROI-Modell, Composite-Score, Zonen) liegt vollstaendig in
`domain/` -- kein Import aus `adapters/`. Das LLM ist ein Adapter hinter
einem Port (`LLMPort`). In Tests: `MockLLMAdapter`. In Produktion:
`AzureOpenAIAdapter`. Adapter-Swap: eine Zeile in `dependencies.py`.
Konkreter Test: "Wie lange dauert ein Wechsel von Azure auf einen anderen
LLM-Provider?" -- ohne Domain-Code zu aendern (ADR-0002).

**Warum SQLite statt PostgreSQL?**

Privates Build, lokal, kein Multi-User. SQLite hat hier keine Nachteile.
Der Repository-Port ist der Ausstiegspunkt: `SQLiteRepository` durch
`PostgreSQLRepository` ersetzen, ohne Domain-Code anzufassen (ADR-007).

**Warum Exceptions statt Result-Type?**

FastAPI-Standard ist Exceptions + globaler Handler. Ein Result-Type waere
ein nicht-additiver Refactor ohne Zielprofil-Nutzen -- explizit entschieden
und dokumentiert (Master-Plan v3.1, entfernt aus session-protocol v3 SS3).

---

## LLM & RAG

**Wie verhindern Sie halluzinierte Artikel-Nummern in Compliance-Hinweisen?**

Citations-before-LLM (ADR-0024): Die Citation-Liste wird deterministisch aus
den Retrieval-Metadaten gebaut, bevor der LLM-Call stattfindet. Das LLM sieht
numerierte DATA-Bloecke [1], [2] und referenziert nur die Nummer im Fliesstext.
Die eigentliche Quellenaufloesung passiert in `_build_compliance_citations()`
in `application/service.py` -- regelbasiert, nicht aus der LLM-Antwort geparst.
Strukturell sicher, nicht nur durch Prompt-Disziplin.

**Warum RAG statt Fine-Tuning?**

Drei Gruende: (1) Regulatorische Texte aendern sich -- ein fine-getuntes
Modell ist statisch, eine kuratierte KB aktualisierbar. (2) RAG ist
nachvollziehbar: jede Aussage hat eine Quellenangabe ([1] = DSGVO Art. 35).
Fine-Tuning ist eine Black Box. (3) Kosten: Fine-Tuning 50--500 USD,
lokal laufende Embeddings (all-MiniLM-L6-v2) = null.

**Was ist Reciprocal Rank Fusion?**

BM25 gibt eine Rang-Liste, Vektor-Retrieval gibt eine andere. RRF kombiniert
beide ohne Gewichtung der absoluten Scores -- nur die Rang-Position zaehlt
(Score = 1/(k + rank), k=60 Standard). Das macht RRF stabil gegen
Skalierungsunterschiede zwischen BM25 und Cosine-Similarity (ADR-0027).

**Warum Cross-Encoder-Reranking nach Hybrid-Search?**

Bi-Encoder (Vektor) ist schnell aber ungenau bei semantischen Nuancen.
Cross-Encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`) betrachtet Query +
Kandidat gemeinsam -- deutlich genauer, aber 10--50x langsamer. Deshalb:
Hybrid-Retrieval holt Top-N, Cross-Encoder rerankt auf Top-K. Qualitaet
des Cross-Encoders bei Latenz des Bi-Encoders (ADR-0028).

---

## Evaluation

**Was misst die Agreement-Rate -- und was nicht?**

Sie misst Inter-Rater-Agreement: stimmt AECTs Vorbewertung mit einem
unabhaengigen menschlichen Urteil auf denselben Cases ueberein?
Sie misst NICHT, ob der vorhergesagte ROI tatsaechlich eintritt (praediktive
Validitaet). Dafuer braeuchte man abgeschlossene, ausgewertete Cases im
produktiven Betrieb (Limitation 1 in `docs/known_limitations.md`).

**Warum sind synthetische Cases unlabeled?**

Self-Labeling: Pipeline generiert Ergebnis -> wird als expected_zone gesetzt
-> Pipeline wird gegen eigenen Output evaluiert. Agreement-Rate 36/36.
Aussagewert: null. Zirkulaere Validierung misst nur Konsistenz, nicht
Korrektheit (ADR-0029/0030). Synthetic Cases testen ausschliesslich
Crash-Freiheit und Determinismus.

**Was ist "Hard-Threshold-Brittleness"?**

Zonengrenzen sind harte Zahlenschwellen in YAML. Ein Use Case mit 99.999 EUR
Nutzen bei einer LIKELY_WIN-Schwelle von 100.000 EUR bekommt eine andere Zone
als derselbe Case mit 100.001 EUR. golden-001 und golden-003 liegen off-by-one
zur Experten-Einschaetzung -- kein Berechnungsfehler, sondern eine Eigenschaft
harter Grenzen auf kontinuierlichen Werten.

---

## Security

**Wie schuetzen Sie gegen Prompt Injection? (OWASP LLM01)**

Vierlagig: (1) `sanitization.py`: Regex auf bekannte Patterns (DE/EN),
Flagging vor Blocking, loggt case_id + Feldname (nie Body). (2) System-/
User-Prompt als getrennte `LLMMessage`-Objekte, kein String-Concat.
(3) User-Input in abgegrenztem Block mit Delimiter-Markierung. (4) LLM-Output
gegen Pydantic-Schema validiert, als untrusted behandelt -- nie direkt in SQL.
Red-Team-Tests in `tests/adapters/llm/`. OWASP-Status in `docs/owasp-llm-checklist.md`.

**Wie verwalten Sie Secrets?**

`pydantic-settings` (`BaseSettings`) liest aus `.env` -- nie committed
(`.gitignore`). `gitleaks` in CI scannt jeden Push. Keine Secrets in Logs
(Allowlist: request_id, route, status, latency, token_count). Kein Secret
im System-Prompt, keine Hard-Kodierung.

**EU AI Act -- welche Risikoklasse ist AECT?**

Limited Risk (Art. 50 Transparenzpflicht). Begruendung: AECT bewertet
Use Cases/Projekte, nicht Personen. Kein Annex-III-Tatbestand (biometrische
Identifikation, kritische Infrastruktur etc.). Art. 50 greift ab 2. Aug 2026:
"Diese Analyse nutzt ein KI-System" -- im Frontend zu zeigen (Phase F).
Herleitung dokumentiert in ADR-0020, nicht behauptet.

---

## Trade-offs

**Was wuerden Sie beim naechsten Mal anders machen?**

Drei Punkte: (1) Zonen als kontinuierliche Scores statt diskreter Grenzen --
vermeidet Hard-Threshold-Brittleness. (2) Embedding-Modell frueher auf
juristische Fachtexte testen -- all-MiniLM ist General-Purpose, kein
Legal-Domain-Modell. (3) Expert-Labeling parallel zum Build starten --
wir haben erst in Phase E damit begonnen, obwohl die Cases ab Phase D klar waren.

**Wo endet AECT und faengt menschliche Verantwortung an?**

AECT liefert Entscheidungsunterstuetzung, keine Entscheidungen. Der Mensch
bleibt Entscheider. Jede Compliance-Ausgabe ist als "zu pruefen, kein Urteil"
markiert. Das ist bewusst: ein System ohne Human-in-the-Loop, das
Use-Case-Prioritaeten falsch setzt, kostet reale Budgets. Verteidigt als Projekt-Prinzip Human-in-the-Loop ("Menschen fuer Verantwortung").

---

## Control-Tower (v3)

**Warum append-only fuer die Monitoring-Zeitleiste?**

Zwei Gruende, beide strukturell. Erstens Lost-Update: eine JSON-Liste am Case,
an die man Eintraege anhaengt, muesste man lesen -> ergaenzen -> zurueckschreiben.
Zwei parallele Notizen (oder eine Notiz parallel zu einem LLM-Feld-Write, der die
ganze Zeile via `save()` ersetzt) lesen denselben Ausgangsstand; der langsamere
Write gewinnt und verschluckt den anderen Eintrag. Genau das Muster, das schon
die per-Feld-UPDATEs motiviert hat (F-011). Ein eigener INSERT je Eintrag hat das
Problem strukturell nicht -- Zeilen kollidieren nicht. Zweitens Audit-Charakter:
der Zweck der Zeitleiste IST die Historie. Ein ueberschreibbares Feld beantwortet
"wie ist der Stand jetzt", nicht "was ist wann passiert". Es gibt bewusst keine
UPDATE- und keine Einzel-DELETE-Methode -- ein Eintrag ist damit nicht
faelschbar. Append-only ist hier das Feature, nicht eine Einschraenkung
(ADR-0046). Die einzige Loeschung ist die DSGVO-Art.-17-Kaskade beim Loeschen
des ganzen Case.

**Warum recharts statt einer selbstgebauten SVG-Matrix?**

Build-vs-Buy. Ein Scatter mit skalierten Achsen, invertierter y-Domain,
Bubble-Groesse, Tooltip-Hit-Testing, responsivem Reflow und Klick-Navigation ist
genau die Menge Arbeit, die eine Chart-Lib loest. Selbstbau haette Achsen-Ticks,
Domain-Padding, Hover-Treffererkennung und Resize-Logik reproduziert -- viel
fehleranfaelliger Code fuer null Differenzierung. D3 waere imperativ und
React-fremd, Plotly gross und ueberdimensioniert; recharts ist deklarativ und
React-nativ. Der Nettonutzen einer Portfolio-Ansicht liegt in der Aussage, nicht
in einer handgeschriebenen Rendering-Engine -- dieselbe Abwaegung wie bei zod
oder shadcn/ui. Eine dokumentierte Reibung: recharts loest `var(--token)` im
SVG-`fill` nicht auf, darum werden die Zonen-Farben via `getComputedStyle` gelesen
und bei Dark-Mode-Wechsel per MutationObserver neu aufgeloest (ADR-0047).

**Warum ein Status-Enum mit Decision-Kopplung statt einem einzigen System?**

Es sind zwei orthogonale Achsen. `reviewer_decision` (ADR-0043) beantwortet
"ist der Case freigegeben?" (PENDING/APPROVED/REJECTED). `CaseStatus` (ADR-0045)
beantwortet "wo im Bearbeitungsfluss steht er?" (SUBMITTED, IN_REVIEW, INTEGRATED,
IMPLEMENTED ...). Ein Case kann freigegeben UND noch nicht integriert sein --
beide Achsen zusammen in ein Enum zu ziehen braeuchte ein Kreuzprodukt der Werte.
Getrennte Felder halten beide Achsen unabhaengig les- und setzbar. Die Kopplung
ist gezielt und einseitig: `record_decision()` setzt zusaetzlich den
Lifecycle-Status (APPROVED/REJECTED), damit der Lifecycle nie im Widerspruch zur
fachlichen Freigabe steht -- die Freigabe gewinnt und darf einen manuell
gesetzten Status ueberschreiben. Bewusst KEINE Transitions-Matrix: der
Single-User-Inhaber des API-Keys ist die Autoritaet ueber den Stand, eine
erzwungene Matrix wuerde nur legitime Korrekturen blockieren (ADR-0045).

---

## Haertere Reviewer-Fragen (Senior-Challenge)

**Ist Hexagonal fuer ein Single-User-Tool nicht Over-Engineering?**

Berechtigte Frage -- die ehrliche Antwort ist: teils ja, und das ist bewusst. Der
Nutzen ist nicht die theoretische Austauschbarkeit, sondern dass die Domain ohne
laufende Infrastruktur testbar ist (449 Tests, kein Azure/Chroma noetig, MockLLM/
MockRetriever per DI) und dass der LLM-Provider-Wechsel eine Adapter-Zeile ist.
Der Preis sind Ports/Protocols, die bei einem Wegwerf-Skript Overhead waeren. Fuer
ein Portfolio-Projekt, das Architektur-Kompetenz zeigen soll, ist genau diese
Trennung der Punkt -- und sie hat sich beim Mock-First-Testen real ausgezahlt.
Bei einem echten Wegwerf-Tool haette ich es nicht gemacht (ADR-004).

**97% Coverage -- aber sind die Tests gut, oder testen sie nur Implementierung?**

Coverage misst Quantitaet, nicht Qualitaet. Deshalb gibt es Property-Tests
(hypothesis) auf dem ROI-/Zonen-Kern, die Verhalten gegen Invarianten pruefen,
nicht Zeilen abhaken. Mutation-Testing (mutmut) auf dem Domain-Kern ist als
naechster Schritt dokumentiert (peak-optimization-roadmap.md) -- ueberlebende
Mutanten zeigen, wo ein Test gruen bleibt, obwohl die Logik kaputt ist. Das ist
das ehrliche Mass; 97% ist nur die Eintrittskarte.

**Warum kein Semantic Caching oder Model Routing?**

Datenbasis statt Bauchgefuehl: der Cost-Logger zeigt ~0,003 EUR/Case bei
gpt-4.1-mini. Bei dem Volumen ist Caching Optimierung ohne Problem -- und
Cache-PII-Invalidierung (DSGVO-Kaskade) waere neue Komplexitaet ohne Gegenwert.
Model Routing braeuchte Eval-Daten, die zeigen, dass ein guenstigeres Modell
reicht; die habe ich nicht. Beide Designs sind in ADR-0034 skizziert und bewusst
nicht gebaut -- eine Entscheidung mit Datenbasis, keine Wissensluecke.

---

## Vor echten Interviews vertiefen (ehrliche Lern-Luecken, G-S6 Tag 81)

Die Antworten oben sind aus dem Repo verteidigbar. Bei tiefer Nachfrage wird
folgendes Wissen duenn -- vor echten Gespraechen auffrischen, nicht erst im Raum:

- **RRF-Sensitivitaet:** Warum k=60 und nicht 10 oder 100? Literaturwert
  (Cormack 2009), aber die Wirkung von k auf die Fusion eigenstaendig erklaeren
  koennen, nicht nur zitieren.
- **Cross-Encoder-Mechanik:** Warum betrachtet ein Cross-Encoder Query+Dokument
  gemeinsam genauer als zwei getrennte Embeddings? Attention ueber das Paar --
  konkreter als "10-50x langsamer".
- **EU AI Act aktuell:** Art.-50-Zeitleiste, GPAI-Regeln, Stand nach Digital
  Omnibus. Das Gesetz bewegt sich; ADR-0020 ist ein Zeitpunkt-Stand.
- **v5-ROI-Herleitung:** Warum die Faktoren adoption_factor/evidence_factor
  multiplikativ? Die Modell-Logik aus ADR-001 frei herleiten koennen.
- **Production-Hardening-Pfad:** ChromaDB-Auth, RBAC, Reverse-Proxy -- die
  Server-Deploy-Punkte aus threat-model.md (O-01/O-03/S-03) als Plan erklaeren.
