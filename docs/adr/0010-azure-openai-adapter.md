# ADR-0010: Azure-OpenAI-Adapter (LLMPort-Implementierung, Phase C)

**Status:** Accepted
**Datum:** Juni 2026

## Kontext

Phase C braucht neben MockLLMAdapter einen realen LLMPort fuer echte
Azure-OpenAI-Calls. ADR-0003 legt Provider (Azure OpenAI), Region
(swedencentral/westeurope), Modell (gpt-4o-mini) und PII-Schutz fest.
ADR-0007 definiert Resilience via ResilientLLMAdapter (Retry/Backoff/Timeout).

## Entscheidungen

**1. Constructor-DI fuer AsyncAzureOpenAI-Client.**
`AzureOpenAIAdapter` bekommt den Client von aussen. `get_llm_adapter()`
in `dependencies.py` baut den Client und uebergibt ihn. Tests brauchen
kein `patch()` -- konsistent mit Hexagonal-Pattern (ADR-0002).

**2. EU-Region-Validierung im Code: nicht moeglich.**
Azure-Endpoint-URLs (`<resource>.openai.azure.com`) enthalten die Region
nicht -- sie liegt im Azure-Resource-Deployment. Validierung ist
Deployment-Zeit-Pflicht (ADR-0003), kein Code-Gate. Dokumentiert,
nicht versteckt.

**3. Exception-Translation.**
- `APITimeoutError`    -> `TimeoutError`    (Retry in ResilientLLMAdapter)
- `APIConnectionError` -> `ConnectionError` (Retry in ResilientLLMAdapter)
- `RateLimitError`     -> `ConnectionError` (vereinfacht: Rate-Limit wie
  transiente Verbindungsstoerung. Kein Retry-After-Header-Backoff --
  bekannte Vereinfachung, eigener Folge-Tag bei Bedarf.)
Alle anderen Exceptions propagieren unveraendert.

**4. max_tokens-Cap (Default 1000).**
Harter Cap gegen LLM10 Unbounded Consumption
(aect-security-checklist v2.1, Phase C).

**5. Env-Var-Prefix AECT_.**
`AECT_AZURE_OPENAI_ENDPOINT`, `_API_KEY`, `_DEPLOYMENT`, `_API_VERSION`.
Konsistent mit `AECT_API_KEY` / `AECT_DB_PATH`.

**6. api_version Default `2024-10-21`.**
GA-Version zum Zeitpunkt des Builds. Muss gegen das tatsaechliche
Azure-Resource-Setup verifiziert werden sobald Credentials verfuegbar
sind (Budget-Sentinel-Tag).

## Konsequenzen

`get_llm_adapter()` in `dependencies.py` ist die einzige Stelle die weiss,
ob Mock oder Azure laeuft. TriageService aendert sich nicht -- Dependency
Inversion (ADR-0002) in der Praxis.

## Offene Punkte

- **PII-Redaction vor LLM-Call** (Permanent-Regel 4, Checklist):
  eigenstaendiger Scope, nicht Teil dieses Adapters. Folgt als separater Tag.
- **RateLimitError-Backoff mit Retry-After**: aktuell vereinfacht.
  Eigener Folge-Tag + ADR wenn dedizierter Backoff benoetigt wird.
- **Erster echter Azure-Call + Budget-Sentinel**: folgt als Mini-Tag,
  sobald AECT_AZURE_OPENAI_* Keys in `.env` gesetzt sind.
