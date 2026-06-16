# Phase C — Review

**Datum:** Juni 2026
**Tests bei Review:** 323 (Budget-Sentinel-Live-Test heute erstmals echt gelaufen statt skipped)
**Gate-Status:** Bestanden — Budget-Sentinel verifiziert, cost_eur_estimate=0.000005 EUR < 0,01 EUR (echter Call gegen Deployment gpt-4.1-mini, Region Sweden Central, 16.06.2026).

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
| `tests/adapters/llm/test_azure_openai_live.py` | Budget-Sentinel — echter Call, Kosten < 0,01 € (Tag 44 gebaut, Tag 45 scharf). |
| `docs/adr/0005–0013` | LLM-Port, Prompt-Loader/Schärfung, Resilience, Function-Calling (Tool-Layer + Loop), Azure-Adapter, Report-Renderer, Sharpened-Proposal-Persistenz, Structured-Output-Schema. |

---

## Was ich heute anders designen würde

**1. `resilient.py`-Docstring ist stale.** Beschreibt die Retry-Exception-Typen
(`TimeoutError`/`ConnectionError`) noch als "generischer Platzhalter, muss
erweitert werden, sobald ein Azure-Adapter existiert". `azure_openai.py`
übersetzt seit Tag ~35 exakt in diese beiden Typen — der ADR-0007-Punkt ist
erledigt, nur nicht nachgezogen. Kleiner Doku-Fix, weiterhin offen.

**2. Zwei ADR-Serien (`000X` / `ADR-00X`) koexistieren weiterhin** — bereits
als Phase-F-Review-Punkt dokumentiert, kein neuer Fund.

**3. `case_id` bei Cost-Logging wird pro Call-Site manuell durchgereicht.**
Funktioniert (siehe Budget-Sentinel-Test), aber bei mehr LLM-Operationen pro
Request (Phase D: Retrieval + Generation) wird das Durchreichen unübersichtlich.
Kein Redesign jetzt — Beobachtung für Phase D, falls sich das Muster wiederholt.

**4. Modell-Annahme war nicht versions-stabil.** `cost_logger.py` und der
Master-Plan hatten "gpt-4o-mini" als fixen Default angenommen, ohne den
Azure-Modell-Lifecycle einzuplanen. Das Modell war zum Zeitpunkt des ersten
echten Calls (16.06.2026) bei Azure für Neukunden bereits eingeschraenkt/
ausgemustert — reine Aussenwelt-Aenderung, kein eigener Fehler. Der LLMPort-
Schnitt hat das schadlos abgefangen (Modellname ist Config, kein Code).
Lehre: Modellnamen in Doku/Config als "Stand <Datum>, vor Re-Deploy
re-verifizieren" markieren, nicht als feste Annahme.

---

## Offene technische Schulden

| Punkt | Priorität | Wann adressieren |
|---|---|---|
| `resilient.py`-Docstring stale (siehe oben) | Niedrig | vor erstem RAG-Code |
| Microsoft-DPA für AECT-Kontext (Art. 28) noch nicht dokumentiert (Security-Checklist Phase C) | Niedrig | Phase F (Doku-Bündel) — kein v1-Blocker, da privates Build |
| Budget-Sentinel | — | erledigt (16.06.2026) |

---

## Vertrauen ins Phase-C-Design (1–10)

**LLM-Port/Adapter-Austausch:** 9 — drei Adapter (Mock → Resilient → Azure)
hintereinander, `TriageService` unverändert. Heute zusaetzlich bestaetigt:
auch ein Modellwechsel beim Provider (siehe Punkt 4 oben) blieb ein reiner
Config-Vorgang, kein Code-Eingriff.
**Resilience:** 8 — Exception-Translation + Retry-Policy greifen nahtlos
zusammen (siehe Punkt 1 oben — funktioniert, nur Doku hinkt nach).
**Cost-Tracking:** 9 — Budget-Sentinel heute bestaetigt (16.06.2026),
provider-agnostisch (Mock liefert dieselben Metriken wie Azure). Pricing-
Konstanten muessen bei jedem Modellwechsel manuell nachgezogen werden —
das ist der einzige manuelle Schritt in der Kette.
**Function-Calling / Structured Output:** 8 — Graceful Degradation getestet
(Mock liefert nie valides JSON → immer Rohpfad), echter Strukturpfad erst mit
echter KI ab Phase D verifizierbar.

---

## Midpoint-Reflexion (§7, nach Phase C)

**Mechanisch ohne Verständnis gearbeitet?** Ja — bewusst. Anas liest den
Code nicht; Ziel ist Verständnis der Prinzipien (was wird gebaut, wie
greift es zusammen), nicht Code-Recall. Das ist der designte Modus dieses
Projekts (session-protocol v3 §3), kein Risiko-Signal.

**Welche ADR würdest du heute anders entscheiden?** ADR-0010 (Azure-Adapter):
die Exception-Translation-Tabelle (APITimeoutError/APIConnectionError/
RateLimitError -> TimeoutError/ConnectionError) ist der Vertrag, auf dem
ResilientLLMAdapters Retry-Policy aufbaut — aktuell steht diese Korrespondenz
nur implizit in zwei Dateien (azure_openai.py, resilient.py), nicht explizit
im ADR-Text als Tabelle. Würde ich heute als expliziten Abschnitt in
ADR-0010 nachtragen, kein Architektur-Redesign.

**Vertrauen ins Hexagonal-Pattern (1-10)?** 9. Beleg: drei Adapter
(Mock -> Resilient -> Azure) ausgetauscht, TriageService unveraendert.
Abzug von 10: Persistenz-Schicht (SQLite) hat noch den dokumentierten
Boilerplate-Punkt aus phase-b-review.md (getrennte Pydantic-/
Dataclass-Serialisierung).

---

## Offene Punkte für Phase D (Stand Tag 45)

1. EU-AI-Act-Re-Check (§4-Vorab-Check) — erledigt (16.06.2026): Digital-
   Omnibus-Trilog-Einigung vom 7. Mai 2026 weiterhin nur politische Einigung,
   Amtsblatt-Veroeffentlichung laut aktueller Berichterstattung fuer Juni/Juli
   2026 erwartet (vor 2. August 2026). Verschiebungstermine unveraendert:
   Annex III (eigenstaendige Hochrisiko-Systeme) 2. Dezember 2027, Annex I
   (eingebettete Produkte) 2. August 2028. Art. 50 (Transparenzpflicht) bleibt
   unveraendert bei 2. August 2026 — nicht von der Verschiebung erfasst.
   Fuer AECTs Limited-Risk-Einordnung aendert sich dadurch nichts. Quelle:
   oeffentliche Berichterstattung Stand 16.06.2026, vor formaler
   Amtsblatt-Veroeffentlichung — bei Phase-D-Start erneut pruefen, falls die
   Veroeffentlichung bis dahin erfolgt ist.
2. Budget-Sentinel nachgeholt (16.06.2026) — erledigt, siehe Gate-Status oben.
3. `resilient.py`-Docstring-Fix (siehe „Was ich heute anders designen würde") —
   weiterhin offen, vor erstem RAG-Code.
4. Modellverfuegbarkeit re-pruefen, falls Phase D zusaetzliche Deployments
   braucht (Embeddings-Modell) — die Lifecycle-Realitaet von heute (Punkt 4
   oben) gilt genauso fuer Embedding-Modelle.
