# Phase C — Review

**Datum:** Juni 2026
**Tests bei Review:** 323 (vorher 322, +1 Budget-Sentinel-Live-Test)
**Gate-Status:** <VARIANTE A: "Bestanden — Budget-Sentinel verifiziert, cost_eur_estimate=<WERT> < 0,01 €"
                  VARIANTE B: "Bestanden mit 1 offenem Punkt — Budget-Sentinel ausstehend (Azure-Credentials nicht konfiguriert), nachgeholt vor Phase-D-Start (Tag 45)">

---

## Gebaute Artefakte

| Datei | Inhalt (1 Satz) |
|---|---|
| `application/ports/llm.py` | LLMPort-Protokoll, LLMMessage/LLMResponse, ToolCall/ToolDefinition (Function-Calling). |
| `adapters/in_memory/llm.py` | MockLLMAdapter — deterministischer Echo-Responder für Tests/Dev. |
| `adapters/llm/resilient.py` | ResilientLLMAdapter — Retry/Backoff/Timeout via tenacity, Decorator um beliebigen LLMPort. |
| `adapters/llm/azure_openai.py` | AzureOpenAIAdapter — echter Azure-Call, Exception-Translation, Tool-Call-Deserialisierung. |
| `application/prompts.py` | Prompt-Loader mit Versionierung (`prompts/<name>/<version>/<role>.md`). |
| `application/sanitization.py` | Injection-Pattern-Detection (DE/EN, flag-not-block) vor LLM-Calls. |
| `application/cost_logger.py` | tiktoken-basierte Token-/Kostenschätzung, structlog-Allowlist-Logging. |
| `application/tools.py` | Function-Calling-Tool `lookup_stack_options`. |
| `application/structured_output.py` | SharpenedContentV2-Schema + generischer Validator + InvalidLLMOutputError. |
| `application/service.py` | `sharpen_case()`, `propose_solution()`, `generate_report()` — Graceful Degradation bei LLM-Ausfall. |
| `tests/adapters/llm/test_azure_openai_live.py` | Budget-Sentinel — echter Call, Kosten < 0,01 € (Tag 44). |
| `docs/adr/0005–0013` | LLM-Port, Prompt-Loader/Schärfung, Resilience, Function-Calling (Tool-Layer + Loop), Azure-Adapter, Report-Renderer, Sharpened-Proposal-Persistenz, Structured-Output-Schema. |

---

## Was ich heute anders designen würde

**1. `resilient.py`-Docstring ist stale.** Beschreibt die Retry-Exception-Typen
(`TimeoutError`/`ConnectionError`) noch als "generischer Platzhalter, muss
erweitert werden, sobald ein Azure-Adapter existiert". `azure_openai.py`
übersetzt seit Tag ~35 exakt in diese beiden Typen — der ADR-0007-Punkt ist
erledigt, nur nicht nachgezogen. Kleiner Doku-Fix, Kandidat für Tag 45
(Micro-Task vor Phase-D-Start, kein eigener Tag wert).

**2. Zwei ADR-Serien (`000X` / `ADR-00X`) koexistieren weiterhin** — bereits
in §6.13 als Phase-F-Review-Punkt dokumentiert, kein neuer Fund.

**3. `case_id` bei Cost-Logging wird pro Call-Site manuell durchgereicht.**
Funktioniert (siehe Budget-Sentinel-Test), aber bei mehr LLM-Operationen pro
Request (Phase D: Retrieval + Generation) wird das Durchreichen unübersichtlich.
Kein Redesign jetzt — Beobachtung für Phase D, falls sich das Muster wiederholt.

---

## Offene technische Schulden

| Punkt | Priorität | Wann adressieren |
|---|---|---|
| `resilient.py`-Docstring stale (siehe oben) | Niedrig | Tag 45, vor erstem RAG-Code |
| Microsoft-DPA für AECT-Kontext (Art. 28) noch nicht dokumentiert (Security-Checklist Phase C) | Niedrig | Phase F (Doku-Bündel) — kein v1-Blocker, da privates Build |
| Budget-Sentinel <VARIANTE B: "noch ausstehend — Azure-Credentials fehlen"> | <VARIANTE B: "Mittel — vor Phase-D-Start (Tag 45)" / VARIANTE A: "—"> | <VARIANTE B: "Tag 45" / VARIANTE A: "erledigt"> |

---

## Vertrauen ins Phase-C-Design (1–10)

**LLM-Port/Adapter-Austausch:** 9 — drei Adapter (Mock → Resilient → Azure)
hintereinander, `TriageService` unverändert. Stärkster empirischer Beleg für
Hexagonal in diesem Projekt bisher.
**Resilience:** 8 — Exception-Translation + Retry-Policy greifen nahtlos
zusammen (siehe Punkt 1 oben — funktioniert, nur Doku hinkt nach).
**Cost-Tracking:** 8 — Budget-Sentinel heute <bestätigt / noch offen>,
provider-agnostisch (Mock liefert dieselben Metriken wie Azure).
**Function-Calling / Structured Output:** 8 — Graceful Degradation getestet
(Mock liefert nie valides JSON → immer Rohpfad), echter Strukturpfad erst mit
echter KI ab Phase D verifizierbar.

---

## Midpoint-Reflexion (§7, nach Phase C)

**Mechanisch ohne Verständnis gearbeitet?** Ja — bewusst. Anas liest den
Code nicht; Ziel ist Verständnis der Prinzipien (was wird gebaut, wie
greift es zusammen), nicht Code-Recall. Das ist der designte Modus dieses
Projekts (session-protocol v3 §3), kein Risiko-Signal.

**Welche ADR würdest du heute anders entscheiden?** (Antwort delegiert an
Claude als Tech Lead.) ADR-0010 (Azure-Adapter): die Exception-Translation-
Tabelle (APITimeoutError/APIConnectionError/RateLimitError ->
TimeoutError/ConnectionError) ist der Vertrag, auf dem ResilientLLMAdapters
Retry-Policy aufbaut — aktuell steht diese Korrespondenz nur implizit in
zwei Dateien (azure_openai.py, resilient.py), nicht explizit im ADR-Text
als Tabelle. Würde ich heute als expliziten Abschnitt in ADR-0010
nachtragen, kein Architektur-Redesign.

**Vertrauen ins Hexagonal-Pattern (1-10)?** (Antwort delegiert an Claude.)
9. Beleg: drei Adapter (Mock -> Resilient -> Azure) ausgetauscht,
TriageService unveraendert. Abzug von 10: Persistenz-Schicht (SQLite)
hat noch den dokumentierten Boilerplate-Punkt aus phase-b-review.md
(getrennte Pydantic-/Dataclass-Serialisierung).

---

## Offene Punkte für Phase D (Stand Tag 44)

1. EU-AI-Act-Re-Check (§4-Vorab-Check) vor erstem RAG-Code — Tag 45.
2. <VARIANTE B: "Budget-Sentinel nachholen (Azure-Credentials + Budget-Alerts einrichten), vor erstem RAG-Embedding-Call." />
3. `resilient.py`-Docstring-Fix (siehe „Was ich heute anders designen würde").
