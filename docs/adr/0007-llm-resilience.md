# ADR-000<N+1>: Resilience-Decorator fuer LLMPort (Retry/Backoff/Timeout)

**Status:** Accepted
**Datum:** Juni 2026
**Kontext:** Phase C, AECT

## Entscheidung

`ResilientLLMAdapter` (in `src/aect/adapters/llm/resilient.py`) wrapt einen
beliebigen `LLMPort` als Decorator. `TriageService` haengt weiterhin nur von
`LLMPort` ab (Dependency Inversion bleibt intakt) -- ob der konkrete Adapter
direkt oder resilience-gewrappt ist, entscheidet die Dependency-Injection
(`dependencies.py`), nicht der Service.

Policy: bis zu `max_attempts` (Default 3) Versuche, exponentieller Backoff
(`tenacity.wait_exponential`, Default 1-8s), harter Timeout pro Versuch
(`asyncio.wait_for`, Default 30s). Retry nur bei `TimeoutError` und
`ConnectionError`, alle anderen Exceptions propagieren sofort. Nach
Erschoepfen der Versuche wird die urspruengliche Exception erneut geworfen
(`reraise=True`), kein `RetryError`-Wrapper.

## Begruendung

- Deckt aect-security-checklist v2.1 Phase C: "Circuit Breaker (tenacity):
  Retry + Backoff + harter Timeout".
- Decorator statt Inline-Retry in `TriageService.sharpen_case()`: derselbe
  Wrapper gilt spaeter auch fuer den Loesungsvorschlag-Call (Phase C/D), ohne
  Duplikation.
- `reraise=True` statt `RetryError`: Aufrufer (Route-Layer, Exception-Handler)
  sehen den urspruenglichen Fehlertyp und koennen ihn gezielt behandeln (z. B.
  503 bei `ConnectionError`/`TimeoutError`).

## Offener Punkt

Die Retry-Exception-Typen (`TimeoutError`, `ConnectionError`) sind ein
generischer Platzhalter fuer den MockLLMAdapter. Ein spaeterer
Azure-OpenAI-Adapter wirft providerspezifische Exceptions (z. B.
`openai.APIConnectionError`, `openai.APITimeoutError`,
`openai.RateLimitError`). Die Retry-Bedingung muss dann erweitert werden --
zu klaeren, sobald der Azure-Adapter existiert und sein Quelltext per
`cat` vorliegt (session-protocol v3 SS1 Schritt 4).

## Nicht entschieden (bewusst verschoben)

- DI-Wiring (`dependencies.py`): wann/ob `TriageService` immer mit
  resilience-gewrapptem LLM laeuft -- naechster Tag.
- Verhalten von `sharpen_case()` nach Retry-Exhaustion auf API-Ebene
  (welcher HTTP-Status, welche Fehlermeldung) -- Teil des globalen
  Exception-Handlers, Phase B/C-Schnittstelle.
