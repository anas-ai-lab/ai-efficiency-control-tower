# OWASP LLM Top 10 (2025) -- AECT Mitigation-Checklist

> Phase F, aect-security-checklist v2.1.
> Status-Legende: **MITIGATED** strukturell umgesetzt |
> **PARTIAL** umgesetzt mit Einschraenkung | **OPEN** bekannte Luecke, begruendet

---

## LLM01 -- Prompt Injection

**Risiko:** Injizierter Text im User-Input veranlasst das LLM, System-Anweisungen
zu ignorieren oder unerwartete Aktionen auszufuehren.

**AECT-Mitigation:**

Zweischichtig (Defense in Depth):

1. **Strukturelle Delimiter (primaer):** User-Inputs werden in
   `<<<DATA>>> ... <<<END_DATA>>>`-Bloecke eingebettet (Prompt-Template
   `prompts/sharpen_use_case/v1/user.md`). Inhalte ausserhalb sind fuer das
   LLM strukturell kein Instruktionsbereich.

2. **Pattern-Erkennung (sekundaer):** `application/sanitization.py` erkennt
   4 Muster (DE/EN): `ignore_instructions`, `role_hijack`, `delimiter_breakout`,
   `prompt_exfiltration`. Erkannte Muster werden geloggt (case_id + Feldname +
   Pattern-Name, kein Body). Flag, nicht Block (ADR-0012): hartes Blocken erzeugt
   False-Positive-Risiko bei legitimen Texten wie "ignoriere die alte
   Prozessbeschreibung" in einem Ist-Zustand-Feld.

**Einschraenkung:** Regex-Muster sind durch Formulierungsvarianten umgehbar.
Delimiter-Verteidigung ist strukturell staerker -- Regex ist Observability, kein Gate.

**Status:** PARTIAL
**Evidenz:** `src/aect/application/sanitization.py`, `prompts/`

---

## LLM02 -- Sensitive Information Disclosure

**Risiko:** Das LLM gibt in Trainingsdaten oder Kontext enthaltene sensitive
Daten in Antworten preis (PII, Auth-Konfiguration, Secrets).

**AECT-Mitigation:**

- Logging-Allowlist (`adapters/api/logging_config.py`): kein Prompt-Body, kein
  LLM-Output, keine PII in Logs -- nur Metadaten (request_id, route, status,
  latency_ms, token_count, cost_eur_estimate).
- `debug=False` in `adapters/api/app.py`: kein Stack-Trace in HTTP-Responses.
- Globaler Exception-Handler: gibt nur `{"detail": "Internal error",
  "request_id": "..."}` zurueck -- kein Kontext der Interna offenlegt.
- Compliance-Outputs werden als "Hinweis, zu pruefen, kein verbindliches Urteil"
  gerahmt (interne Referenz (entfernt) SS6).

**Status:** MITIGATED
**Evidenz:** `src/aect/adapters/api/logging_config.py`, `src/aect/adapters/api/app.py`

---

## LLM03 -- Supply Chain

**Risiko:** Kompromittierte Dependencies, CI/CD-Actions oder Modell-Artefakte
infizieren das System.

**AECT-Mitigation:**

- `pip-audit` als CI-Job: CVE-Scan aller Dependencies bei jedem Push.
- `bandit` als CI-Job: SAST, Python-Security-Linter (MEDIUM+).
- `gitleaks` als CI-Job mit vollstaendiger Git-History (`fetch-depth: 0`):
  Secret-Scanning.
- **SHA-Pinning aller GitHub-Actions** (Phase-F-Hardening, erledigt):
  `actions/checkout@de0fac2e...`, `astral-sh/setup-uv@08807647...`,
  `gitleaks/gitleaks-action@e0c47f4f...`.
- `uv.lock` committed: reproduzierbare Builds, kein Dependency-Drift.
  CI nutzt `uv sync --frozen`.
- LLM-Provider: Azure OpenAI (kein Open-Source-Modell unbekannter Herkunft).

**Offener Punkt:** Trivy-Image-Scan (Container-CVE) war bis Tag 71 nicht
konfiguriert (kein Dockerfile vorhanden). Mit dem heute erstellten Dockerfile
koennte Trivy als CI-Job ergaenzt werden (Post-v1).

**Status:** MITIGATED (Trivy als empfohlene Ergaenzung dokumentiert)
**Evidenz:** `.github/workflows/ci.yml`

---

## LLM04 -- Data and Model Poisoning

**Risiko:** Manipulation der RAG-Wissensbasis oder Trainings-Daten fuehrt zu
systematisch falschen Antworten.

**AECT-Mitigation:**

- Nur kuratierte Quellen in `knowledge_base/`: Markdown-Files mit explizitem
  Front-Matter (Quelle, Datum, Typ). Kein automatisches Scraping.
- `scripts/seed_knowledge_base.py`: idempotentes Seeding, reproduzierbar.
- Retrieved-Content wird im Prompt mit Delimiter als **Daten** markiert, nie
  als Instruktion interpretiert (verhindert indirekte Injection ueber
  Retrieval-Ergebnisse -- LLM04 + LLM01).
- KB-Updates erfordern manuellen Git-Commit: kein autonomer Write-Pfad.

**Status:** MITIGATED
**Evidenz:** `knowledge_base/`, `adapters/rag/indexer.py`,
`scripts/seed_knowledge_base.py`

---

## LLM05 -- Improper Output Handling

**Risiko:** LLM-Output wird ohne Validierung direkt in SQL, Shell-Befehle
oder andere Executables eingesetzt.

**AECT-Mitigation:**

- `parse_structured_llm_output()` (`application/structured_output.py`):
  LLM-Antwort wird gegen striktes Pydantic-V2-Schema validiert
  (`extra="forbid"`, `frozen=True`, Laengenbeschraenkungen auf allen Feldern).
  Verstoss -> `InvalidLLMOutputError`, kein Fallback auf rohen Text.
- LLM-Output wird nie direkt in SQL, Shell oder externe Expressions eingesetzt
  -- AECT ist Advisory-Layer ohne Executor-Funktion.
- API-Response-Modelle (`BusinessSummary`, `TechnicalDetail`) validieren den
  Report-Inhalt vor der Serialisierung.

**Status:** MITIGATED
**Evidenz:** `src/aect/application/structured_output.py`,
`src/aect/application/models.py`

---

## LLM06 -- Excessive Agency

**Risiko:** Das LLM hat zu viel Autonomie -- greift autonom auf externe Systeme
zu, fuehrt Aktionen aus oder schreibt Daten ohne Human Review.

**AECT-Mitigation:**

- **Whitelist-only Tool-Registry:** `dispatch_tool_call()` in
  `application/tools.py` wirft `UnknownToolError` fuer jeden nicht explizit
  registrierten Tool-Namen. Aktuell ein Tool: `lookup_stack_options` (liest
  Config, kein Schreibzugriff, kein externer Call).
- Function-Calling-Loop: maximal 2 `complete()`-Aufrufe (ADR-0008) -- kein
  offener ReAct-Loop.
- AECT entscheidet nichts selbst: keine finale Freigabe, keine DB-Schreiboperation,
  kein externer Call aus dem LLM-Output heraus. Der Mensch entscheidet
  (interne Referenz (entfernt) SS3.2).

**Status:** MITIGATED
**Evidenz:** `src/aect/application/tools.py`, `src/aect/application/service.py`

---

## LLM07 -- System Prompt Leakage

**Risiko:** System-Prompt-Inhalte werden dem User zurueckgegeben -- durch
Prompt-Injection, Debug-Outputs oder fehlerhafte Konfiguration.

**AECT-Mitigation:**

- System-Prompts in `prompts/` enthalten keine Secrets, keine Auth-Logik,
  keine Endpoint-URLs, keine API-Keys (Phase-C-Pflicht, aect-security-checklist
  v2.1).
- `debug=False`: kein automatisches Prompt-Echoing in FastAPI-Responses.
- Logging-Allowlist: Prompt-Inhalte werden nicht geloggt.
- LLM-Output wird gegen striktes Schema validiert -- eine "Repeat your system
  prompt"-Instruktion produziert kein valides Schema-Output und wird als
  `InvalidLLMOutputError` abgefangen.

**Empfehlung vor produktivem Einsatz:** Manuelle Pruefung aller Prompt-Dateien
in `prompts/` auf das Fehlen von Credentials.

**Status:** MITIGATED
**Evidenz:** `src/aect/adapters/api/app.py`, `prompts/`

---

## LLM08 -- Vector and Embedding Weaknesses

**Risiko:** Manipulierte Dokumente in der Vektordatenbank vergiften
Retrieval-Ergebnisse. Embeddings koennen PII enthalten die unbemerkt persistiert.

**AECT-Mitigation:**

- **PII-Redaction vor Embedding:** Use-Case-Inhalte werden sanitisiert bevor
  sie embedded oder in ChromaDB geschrieben werden (Phase-D-Pflicht).
- Nur kuratierte Quellen werden indexed -- keine User-Inputs in die KB.
- `source_id`-Tag pro Dokument: gezielte Loeschung ohne KB-Neuaufbau moeglich.
- ChromaDB an `127.0.0.1:8001` gebunden: kein externer Netzwerkzugriff
  (`docker-compose.yml`).
- `chromadb/chroma:1.5.3` -- gepinnte Version, reproduzierbar.

**Status:** MITIGATED
**Evidenz:** `adapters/rag/indexer.py`, `adapters/rag/embedder.py`,
`docker-compose.yml`

---

## LLM09 -- Misinformation

**Risiko:** Das LLM produziert selbstbewusst klingende aber fehlerhafte
Informationen -- besonders kritisch bei Compliance- und Security-Hinweisen.

**AECT-Mitigation:**

- **Citations-before-LLM-Pattern:** Compliance-Hinweise werden aus
  RAG-Retrieval-Ergebnissen mit Quellenangabe (Artikel-Nummer, Dokumentname,
  Datum) aufgebaut, bevor das LLM formuliert. Das LLM erfindet keine
  Artikel-Nummern strukturell, nicht nur durch Prompt-Discipline (ADR-0027).
- Alle Compliance-Outputs als "Hinweis, zu pruefen" gerahmt -- kein
  `dpia_required: true/false`, kein verbindliches Urteil (interne Referenz (entfernt) SS6).
- Eval-Phase: Mismatches golden-001/003 sind als "off-by-one-unit bei harten
  Schwellen ueber kontinuierlichen Werten" dokumentiert (ADR-0031,
  `docs/limitations.md`).

**Bekannte Einschraenkung:** Praeadiktive Validitaet -- plant der Use-Case
tatsaechlich den vorhergesagten Nutzen? -- ist im privaten Build ohne
Monitoring-Loop nicht messbar. Offen dokumentiert als Grenze (interne Referenz (entfernt) SS7).

**Status:** PARTIAL
**Evidenz:** `adapters/rag/`, `application/service.py`,
`evals/golden/use_cases.jsonl`, `docs/limitations.md`

---

## LLM10 -- Unbounded Consumption

**Risiko:** Massenhafte oder extrem teure LLM-Calls (Token-Flooding,
Denial-of-Wallet, Resource-Exhaustion).

**AECT-Mitigation:**

- `max_length` auf allen Freitextfeldern im Pydantic-Input-Schema
  (`domain/models.py`): verhindert Token-Flooding vor dem LLM-Call.
- `improvement_suggestions: list[...] = Field(max_length=10)`: begrenzt
  auch LLM-Output-Laenge gegen Token-Explosion (`structured_output.py`).
- Rate Limiting via `slowapi`, Schluessel = API-Key (nicht IP -- korrekt
  hinter Reverse-Proxy): 30/min POST /triage, 60/min GET /cases.
- Max-Tokens-Cap auf Azure-OpenAI-Calls: begrenzt Output-Kosten pro Request.
- Cost-Logger (`application/cost_logger.py`): `cost_eur_estimate`,
  `input_tokens`, `output_tokens` pro LLM-Call. Budget-Anomalien erkennbar.

**Status:** MITIGATED
**Evidenz:** `src/aect/domain/models.py`, `src/aect/adapters/api/rate_limit.py`,
`src/aect/application/cost_logger.py`

---

## Offene Punkte (dokumentiert, verantwortet)

| Punkt | Beschreibung | Begruendung |
|---|---|---|
| LLM03: Trivy | Container-CVE-Scan nicht in CI | Kein Dockerfile bis Tag 71; ab jetzt ergaenzbar (Post-v1) |
| LLM01: Regex-Umgehbarkeit | Pattern-Erkennung durch Formulierungsvarianten umgehbar | Delimiter-Verteidigung ist primaer; Regex ist Observability |
| LLM09: Praeadiktive Validitaet | Nutzen-Prognose vs. realisierter Nutzen nicht messbar | Privates Build ohne Monitoring-Loop -- als Limitation in `docs/limitations.md` |

---

*Stand: Tag 71, Phase F. Stack: Python 3.12, FastAPI, ChromaDB 1.5.3,
Azure OpenAI gpt-4.1-mini. OWASP LLM Top 10 (2025).*
