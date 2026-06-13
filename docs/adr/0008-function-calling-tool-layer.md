# ADR-0008: Function-Calling-Vorbereitung -- Tool-Typen, Mock-Simulation, Tool-Registry

**Status:** Accepted
**Datum:** Juni 2026
**Kontext:** Phase C, AECT

## Entscheidung

`LLMPort.complete()` bekommt einen optionalen Parameter `tools:
list[ToolDefinition] | None = None` (Default `None`, rueckwaertskompatibel --
`sharpen_case()`/`propose_solution()` aendern sich nicht). Neue Typen in
`application/ports/llm.py`: `ToolDefinition` (name, description,
parameters-JSON-Schema), `ToolCall` (id, name, arguments). `LLMMessage`
bekommt `role: Literal[..., "tool"]`, `tool_call_id` und `tool_calls` als
optionale Felder; `LLMResponse` bekommt `tool_calls`.

`MockLLMAdapter` simuliert genau einen Tool-Call, wenn `tools` angeboten
werden und die Historie noch keine `role="tool"`-Antwort enthaelt --
danach faellt er auf das bisherige Echo-Verhalten zurueck.
`ResilientLLMAdapter` reicht `tools` unveraendert durch (reiner
Passthrough, keine Retry-/Timeout-Aenderung).

Neues Modul `application/tools.py`: `TOOL_DEFINITIONS` (Registry),
`lookup_stack_options()`, `dispatch_tool_call()`, `UnknownToolError`. Erstes
Tool: `lookup_stack_options` -- parameterlos, liest Plattform-Optionen
(Open WebUI, Copilot Studio, Foundry, SAP BTP, Andere) aus neuer Datei
`config/stack_options.toml`.

## Begruendung

| Alternative | Warum verworfen |
|---|---|
| Plattform-Liste direkt im System-Prompt von `propose_solution` | Verstoesst gegen "Regeln vor LLM" -- die Liste ist eine deterministische Fakten-Quelle, kein Sprachproblem. Aenderung der Plattform-Liste wuerde Prompt-Edits statt Config-Edits erfordern (IP-Trennung, interne Referenz (entfernt) §5). |
| Tool-Layer + Loop-Verdrahtung an einem Tag | Zu gross fuer 8-15h/Woche; Risiko, die Loop-Architektur-Entscheidung (Service vs. eigener Adapter) unter Zeitdruck zu treffen. Aufgeteilt: Tag 37 Fundament, Tag 38 Verdrahtung + Tool-Fail-Test (Gate-Thema "Function-Calling-Loop", session-protocol v3 §3). |
| `arguments: str` (roher JSON-String, providertypisch) | `dict[str, Any]` ist fuer Mock und `lookup_stack_options` (parameterlos) einfacher; Parsing/Serialisierung gehoert in einen spaeteren Azure-Adapter, nicht in den providerunabhaengigen Port. |

## Konsequenzen

**Positiv:**
- Rueckwaertskompatibel: alle 262 bestehenden Tests bleiben unveraendert
  gruen, `tools=None` ist der bisherige Pfad.
- Plattform-Namen liegen ab heute in `config/stack_options.toml` --
  IP-Trennung (interne Referenz (entfernt) §5), bevor `propose_solution` sie nutzt.
- `dispatch_tool_call()` zentralisiert das Dispatch und whitelisted Tool-
  Namen (LLM06 Excessive Agency) -- Tag 38 muss nur noch die Schleife
  verdrahten, nicht das Dispatch entwerfen.

**Negativ / Trade-offs:**
- Mock-Heuristik ("ein Tool, ein Aufruf, dann Echo") ist eine grobe
  Vereinfachung. Reale Provider koennen mehrere Tools in einer Antwort
  anfordern oder nach einem Tool-Ergebnis erneut ein Tool aufrufen
  (verschachtelte Loops). Tag-38-Loop muss mindestens "ein Aufruf" korrekt
  behandeln; Mehrfach-Aufrufe sind ein dokumentierter, noch nicht geloester
  Fall.
- `ToolDefinition`/`ToolCall` sind `frozen=True` mit `dict`-Feldern --
  `__eq__` funktioniert (dict-Vergleich), `__hash__` wuerde bei `dict`-
  Inhalten zur Laufzeit fehlschlagen. Da keine Stelle diese Typen hasht,
  ist das aktuell folgenlos.

**Neutral / Folgeentscheidungen:**
- `lookup_stack_options()` ist Tag-37-bewusst noch ohne RAG-Beleg
  (Platzhalter-Beschreibungen in `config/stack_options.toml`).
  Stack-Grounding mit zitierten Quellen folgt Phase D (Master-Plan v3.1) --
  die Funktionssignatur bleibt voraussichtlich stabil, nur die Datenquelle
  wechselt.

## Offener Punkt (Tag 38)

Wo lebt die Function-Calling-Loop? Optionen: (a)
`TriageService.propose_solution()` direkt (zwei `complete()`-Aufrufe
inline), oder (b) ein eigener `ToolCallingLLMAdapter` (Decorator analog
`ResilientLLMAdapter`, kapselt die Schleife hinter `LLMPort`). (b) haelt
`TriageService` unveraendert, (a) macht den Kontrollfluss im Service
sichtbarer. Entscheidung Tag 38, mit `cat` auf `service.py` und
`dependencies.py` vor dem Schreiben (session-protocol v3 §1 Schritt 4).
