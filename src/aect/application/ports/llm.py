"""LLMPort -- testbarer Kontrakt fuer LLM-Provider (Mock, Azure OpenAI, ...)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol

from aect.application.structured_output import IdeationResult

Role = Literal["system", "user", "assistant", "tool"]


@dataclass(frozen=True)
class ToolDefinition:
    """Beschreibt ein Tool, das das LLM aufrufen kann (Function-Calling).

    `parameters` ist ein JSON-Schema-Dict (OpenAI-Function-Calling-Format).
    Tag 37: erstes Tool ist `lookup_stack_options` (application/tools.py),
    parameterlos -- `parameters` ist dafuer ein leeres Objekt-Schema.
    """

    name: str
    description: str
    parameters: dict[str, Any]


@dataclass(frozen=True)
class ToolCall:
    """Ein vom LLM angeforderter Tool-Aufruf (Teil einer LLMResponse).

    `id` identifiziert den Aufruf -- die Antwort darauf (LLMMessage mit
    role="tool") referenziert ihn ueber `tool_call_id`, damit bei mehreren
    parallelen Tool-Calls die Zuordnung eindeutig bleibt.

    `arguments`: vom LLM gelieferte Argumente. Wie jede LLM-Ausgabe als
    untrusted behandeln (aect-security-checklist v2.1, Phase C).
    Tag 38 / ADR-0009: lookup_stack_options ist parameterlos --
    dispatch_tool_call() liest `arguments` nicht, daher entsteht heute keine
    Validierungsluecke. Bei zukuenftigen Tools mit Parametern: Validierung
    von `arguments` gegen ein erwartetes Schema vor dem Dispatch nachruesten.
    """

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class LLMMessage:
    """Eine Nachricht im Messages-API-Format (System/User/Assistant/Tool getrennt).

    Kein String-Concat (aect-security-checklist v2.1, Phase C): System- und
    User-Anteile bleiben strukturell getrennt, damit kein Adapter sie
    versehentlich vermischt.

    Tag 37 (Function-Calling): role="tool" traegt das Ergebnis eines
    Tool-Aufrufs zurueck, `tool_call_id` referenziert den ToolCall aus der
    vorherigen LLMResponse. `tool_calls` traegt auf einer Assistant-Nachricht
    die vom LLM angeforderten Aufrufe (Wiederholung der Historie beim
    zweiten complete()-Call).
    """

    role: Role
    content: str
    tool_call_id: str | None = None
    tool_calls: list[ToolCall] | None = None


@dataclass(frozen=True)
class LLMResponse:
    """Antwort eines LLM-Providers.

    `tool_calls`: None oder leer -> normale Text-Antwort (`content` ist die
    Nutzlast). Nicht-leer -> das LLM fordert Tool-Aufrufe an; `content` kann
    in diesem Fall leer sein (provider-abhaengig).
    """

    content: str
    tool_calls: list[ToolCall] | None = None


class LLMPort(Protocol):
    """Kontrakt fuer LLM-Provider.

    Warum ein Port? Schaerfung, Loesungsvorschlag und Report (Phase C)
    duerfen nicht von einem konkreten Provider abhaengen. MockLLMAdapter
    liefert deterministische Antworten fuer Tests; ein spaeterer
    Azure-OpenAI-Adapter implementiert denselben Kontrakt mit echten Calls.

    `tools`: optionale Liste verfuegbarer Tools (Function-Calling, Tag 37).
    None (Default) -> Adapter bietet keine Tools an, Verhalten unveraendert
    gegenueber Tag 36 (sharpen_case/propose_solution rufen complete() ohne
    `tools` auf).
    """

    async def complete(
        self, messages: list[LLMMessage], tools: list[ToolDefinition] | None = None
    ) -> LLMResponse: ...

    async def generate_ideation(self, problem_description: str) -> IdeationResult:
        """Erzeugt 1-3 AI-Use-Case-Entwuerfe aus einer Problembeschreibung (P10).

        Hoehere Faehigkeit als complete(): der Adapter laedt den versionierten
        ideation-Prompt (System/User getrennt, Delimiter-Block gegen LLM01),
        fuehrt den Call aus, loggt die Kosten und validiert die rohe Antwort
        gegen IdeationResult (Output als untrusted, ADR-0013). Kein
        Function-Calling (bewusst simpel -- tools.py bleibt unangetastet).

        Raises:
            InvalidLLMOutputError: rohe Antwort ist kein valides JSON oder
                verletzt IdeationResult -- vom Aufrufer (Route) auf einen
                sauberen HTTP-Fehler gemappt, kein 500-Stack-Trace.
            ConnectionError/TimeoutError: LLM nicht erreichbar (nach Retries) --
                vom Aufrufer auf 503 gemappt.
        """
        ...
