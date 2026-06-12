# ADR-0005: LLM-Port mit Messages-API-Pattern

**Status:** Accepted
**Datum:** Juni 2026

## Kontext

Phase C braucht einen LLM-Port, der Mock- und Azure-OpenAI-Adapter gleich
behandelt (aect-security-checklist v2.1, Phase C: "Messages-API, kein
String-Concat, System/User getrennt").

## Entscheidung

`LLMMessage(role, content)` mit `role: Literal["system", "user", "assistant"]`
als strukturelle Trennung. `LLMPort.complete(messages: list[LLMMessage]) ->
LLMResponse` ist async, da der Azure-Adapter (Phase C, spaeter) echte
HTTP-Calls macht.

## Konsequenzen

- Kein Adapter kann System- und User-Content versehentlich zusammen-
  konkatenieren — die Trennung ist im Typ erzwungen, nicht nur Konvention.
- MockLLMAdapter ist deterministisch (letzter User-Content wird echo-t),
  daher reproduzierbare Tests ohne Netzwerk/Kosten.
- Cost-Logging (tiktoken), Resilience (tenacity) und Output-Validation
  folgen als eigene Artefakte in spaeteren Tagen — bewusst nicht heute.
