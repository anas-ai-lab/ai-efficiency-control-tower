# ADR-0009: Function-Calling-Loop -- Architektur (Aufloesung ADR-0008)

**Status:** Accepted
**Datum:** Juni 2026
**Kontext:** Phase C, AECT -- loest den offenen Punkt aus ADR-0008.

## Entscheidung

Die Function-Calling-Loop lebt **inline in `TriageService.propose_solution()`**,
nicht in einem eigenen `ToolCallingLLMAdapter`.

Ablauf:
1. Erster `complete(messages, tools=TOOL_DEFINITIONS)`-Call.
2. Falls `response.tool_calls` nicht leer ist: fuer jeden Tool-Call
   `dispatch_tool_call()` aufrufen, Ergebnis als `role="tool"`-Nachricht
   anhaengen (`tool_call_id` referenziert den Aufruf).
3. Zweiter `complete()`-Call mit der erweiterten Historie -> finale Antwort.
4. Kein `while`-Loop -- maximal zwei `complete()`-Aufrufe pro
   `propose_solution()`-Call, unabhaengig davon, ob/wie viele Tool-Calls
   angefordert wurden.

`sharpen_case()` bleibt unveraendert (kein `tools`-Parameter).

## Begruendung

| Alternative | Warum verworfen |
|---|---|
| Eigener `ToolCallingLLMAdapter` (Decorator, analog `ResilientLLMAdapter`) | Zusaetzliche Indirektion fuer genau 1 Tool und genau 1 garantierten Round-Trip (Mock-Heuristik, ADR-0008). `TriageService` muesste trotzdem wissen, *dass* ein Tool-Call passiert ist, um beide `complete()`-Aufrufe korrekt zu loggen (Cost-Logger) -- der Decorator wuerde das verstecken, nicht vereinfachen. |
| `while`-Loop (mehrere Tool-Call-Runden) | Kein Anwendungsfall heute (1 Tool, parameterlos). Ungebremster Loop bei einem realen Provider waere ein LLM10-Risiko (Unbounded Consumption). Wird erst designt, wenn ein zweiter Tool-Aufruf-Bedarf entsteht. |

## Konsequenzen

**Positiv:**
- Zwei `complete()`-Aufrufe = zwei `log_llm_cost`-Eintraege (operation=
  "propose_solution") -- Kosten eines Tool-Use-Roundtrips sind direkt
  sichtbar, kein versteckter zweiter Call in einem Adapter.
- Die `for`-Schleife ueber `response.tool_calls` behandelt korrekt auch
  mehrere Tool-Calls in einer Antwort, falls ein spaeterer Provider das tut
  (Mock liefert heute nur einen) -- ADR-0008 dokumentierte das als offen,
  ist mit dieser Schleifenform bereits abgedeckt.
- LLM06 (Excessive Agency): `dispatch_tool_call()` wirft `UnknownToolError`
  fuer nicht registrierte Tool-Namen. Statt die Anfrage abzubrechen, wird
  der Fehler als Tool-Ergebnis (`{"error": ...}`) an das LLM zurueckgegeben
  -- Graceful Degradation, der Service liefert trotzdem eine Antwort.

**Negativ / Trade-offs:**
- Harte Begrenzung auf zwei `complete()`-Aufrufe ist fuer das heutige
  Mock-Verhalten korrekt, aber eine Designentscheidung, kein Naturgesetz:
  fordert ein realer Provider nach einem Tool-Ergebnis ein *weiteres* Tool
  an, wird dieser zweite Tool-Call ignoriert (response.content der zweiten
  Antwort wird als final behandelt, auch wenn `tool_calls` erneut gesetzt
  waere). Dokumentierte Grenze, kein Bug -- Erweiterung erst bei Bedarf
  (zweites Tool oder echter Azure-Call mit beobachtetem Verhalten).
- `lookup_stack_options()` liest `config/stack_options.toml` synchron
  (`tomllib`) innerhalb eines `async`-Pfads. Blockierend, aber Datei ist
  klein und lokal -- kein messbarer Effekt. Nicht optimiert
  ("Simplest solution first"); relevant erst wenn IO durch RAG-Quellen
  (Phase D) ersetzt wird.

## Prompt-Versionierung (Folge dieser Entscheidung)

`propose_solution()` bietet ab heute `TOOL_DEFINITIONS` an -- das LLM muss
wissen, dass das Werkzeug existiert und dass dessen Daten unbelegt sind
(Tag-37-Platzhalter). Das ist eine inhaltliche Aenderung des System-Prompts,
keine Korrektur -> neue Version `prompts/propose_solution/v2/`. v1 bleibt
unveraendert erhalten. Default von `propose_solution()` wechselt auf `"v2"`.
