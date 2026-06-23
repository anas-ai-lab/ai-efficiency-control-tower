# ADR-0034 — LLM-Effizienz: kein Semantic Caching, kein Model Routing in v1

**Status:** Accepted
**Datum:** Juni 2026
**Kontext:** Phase F — Dokumentation downgraded Topics (Master-Plan v3.1, interne Referenz (entfernt) §4)

---

## Kontext

AECT ruft Azure OpenAI (gpt-4.1-mini) fuer drei Operationen auf:
Use-Case-Schaerfung, Stack-Loesung (Function-Calling-Loop),
Compliance-Hints. Cost-Logging via cost_logger.py liefert Token-Counts
und EUR-Schaetzung pro Call. Pricing: $0.40 Input / $1.60 Output pro
1M Tokens (Stand Jun 2026). Typischer Case: 800-1200 Input-Tokens +
300-600 Output-Tokens = ~0.003 EUR.

Zwei Effizienz-Mechanismen standen zur Diskussion:
- Semantic Caching: aehnliche Inputs liefern gecachten Output zurueck,
  ohne LLM-Call.
- Model Routing: einfache Aufgaben an guenstiges Modell, komplexe an
  teures Modell.

---

## Alternativen -- Semantic Caching

**A) Kein Cache (umgesetzt)**

Pros: keine zusaetzliche Infra, keine Cache-Invalidierung, kein
Privacy-Overhead.
Cons: jeder Case zahlt volle LLM-Kosten, auch bei aehnlichen
Einreichungen.

**B) Semantic Cache ueber ChromaDB (Design, nicht gebaut)**

Architektur:
- Separate ChromaDB-Collection `llm_response_cache`.
- Pre-LLM-Call: Embedding des System-Prompts + User-Inhalts;
  Similarity-Suche in Cache-Collection.
- Treffer (Score >= 0.92): gecachter LLMResponse zurueck, kein Call.
- Kein Treffer: Call durchfuehren, Ergebnis mit TTL 24h einspeichern.
- Cache-Key: Hash(system_prompt_version + sanitized_input) als ID.
  (system_prompt_version verhindert, dass alte Responses bei
  Prompt-Aenderungen serviert werden.)

Contra B:
1. Use-Case-Einreichungen sind inhaltlich einzigartige
   Geschaeftsvorgaenge mit hoher semantischer Varianz -- niedrige
   Cache-Hit-Rate erwartet, Effizienzgewinn ungesichert.
2. Gecachte LLM-Outputs koennen PII aus vorherigen Einreichungen
   enthalten. Cache-Invalidierung bei Betroffenenrecht-Loeschung
   muss kaskadieren: DB + Embeddings + Cache-Collection.
   DSGVO-Komplexitaet waechst ueberproportional.
3. Falsch-positive Treffer (semantisch aehnlich, inhaltlich verschieden)
   koennen falschen Output liefern -- kein Mechanismus fuer den User
   sichtbar.

---

## Alternativen -- Model Routing

**A) Ein Modell fuer alle Operationen (umgesetzt)**

gpt-4.1-mini fuer Schaerfung, Loesung, Compliance. ~0.003 EUR/Case.
Pros: kein Routing-Layer, konsistente Qualitaet fuer alle Operationen.

**B) Model Router (Design, nicht gebaut)**

Architektur:
- ModelRouter-Klasse zwischen TriageService und ResilientLLMAdapter.
- Routing-Logik nach Operation-Typ:
  sharpen_case (Sprachqualitaet kritisch) -> gpt-4.1
  propose_solution (strukturiert, Function-Calling) -> gpt-4.1-mini
  generate_compliance_hints (Retrieval-augmented, kurz) -> gpt-4.1-mini
- cost_logger.py erhaelt Modellname als zusaetzliches Logging-Feld.

Contra B:
1. gpt-4.1-mini ist bereits das effiziente Modell; Routing ist
   Optimierung ohne bekannte Kostenbasis. Cost-Logger-Daten zeigen
   ob ein Problem existiert -- aktuell nicht.
2. Zwei Adapter-Instanzen, zwei Deployment-Konfigurationen, zwei
   Exception-Uebersetzungspfade.
3. Qualitaets-Schwellwert fuer Routing (wann reicht gpt-4.1-mini,
   wann braucht man gpt-4.1?) ist ohne Eval-Daten eine Annahme.

---

## Entscheidung

Weder Semantic Caching noch Model Routing in v1. Beide: verstanden,
Design oben skizziert, bewusst nicht gebaut.

Gruende:
1. Typischer Case kostet ~0.003 EUR. Bei 100 Cases/Monat: ~0.30 EUR.
   Cost-Logger liefert die Datenbasis um spaeter zu entscheiden, ob
   ein Kostenproblem existiert -- aktuell keins.
2. Cache-Privacy-Komplexitaet (PII in gecachten Outputs, DSGVO-Kaskade)
   ist fuer ein privates Build unverhältnismaessig.
3. Das einzige potenzielle Routing-Anwendungsfeld (AI-vs-Automation) ist
   deterministisch in der Regel-Engine geloest -- kein LLM-Call.

---

## Konsequenzen

- cost_logger.py liefert die Datenbasis fuer eine spaetere
  Routing-/Caching-Entscheidung auf echten Nutzungsdaten.
- Cache und Routing sind die natuerlichen Erweiterungen wenn Volumen
  oder Kosten das rechtfertigen; Einstiegspunkt ist dieser ADR.
- Interview-Position: kein Caching-/Routing-Layer ist eine Entscheidung
  mit Datenbasis (Cost-Logger, 0.003 EUR/Case), keine Wissenslücke.
