"""MockLLMAdapter -- deterministischer LLM-Adapter fuer Tests."""

from __future__ import annotations

from aect.application.ports.llm import (
    LLMMessage,
    LLMResponse,
    ToolCall,
    ToolDefinition,
)
from aect.application.structured_output import IdeationDraft, IdeationResult

_MOCK_TOOL_CALL_ID = "mock-tool-call-1"


class MockLLMAdapter:
    """Implementiert LLMPort ohne echten LLM-Call.

    Deterministisch: liefert eine feste, aus dem letzten User-Content
    abgeleitete Antwort. Macht Tests reproduzierbar ohne Netzwerk/Kosten.
    Implementiert LLMPort via strukturellem Subtyping.

    Tool-Call-Simulation (Tag 37, Function-Calling): werden `tools`
    angeboten UND enthaelt die Historie noch keine Tool-Antwort
    (role="tool"), fordert der Mock genau einen Aufruf des ersten
    angebotenen Tools an (Argumente: leeres Dict). Enthaelt die Historie
    bereits eine Tool-Antwort -- oder werden keine `tools` angeboten --
    verhaelt sich der Mock wie zuvor (Echo des letzten User-Contents).

    Bekannte Einschraenkung (siehe ADR-0008): Diese Heuristik bildet nur den
    Standard-Zweischritt "ein Tool, ein Aufruf" nach. Mehrere Tools oder
    mehrere Aufrufe in einer Antwort simuliert der Mock nicht -- ein
    Azure-OpenAI-Adapter kann hier abweichen.
    """

    async def complete(
        self,
        messages: list[LLMMessage],
        tools: list[ToolDefinition] | None = None,
    ) -> LLMResponse:
        if tools and not any(m.role == "tool" for m in messages):
            return LLMResponse(
                content="",
                tool_calls=[
                    ToolCall(id=_MOCK_TOOL_CALL_ID, name=tools[0].name, arguments={})
                ],
            )

        last_user = next(
            (m.content for m in reversed(messages) if m.role == "user"),
            "",
        )
        return LLMResponse(content=f"[mock-response] {last_user}")

    async def generate_ideation(self, problem_description: str) -> IdeationResult:
        """Liefert deterministisch 2 schema-konforme Entwuerfe (Tests, P10).

        Ignoriert den Prompt bewusst (kein echter Call) und baut IdeationResult
        direkt -- die Felder erfuellen die IdeationDraft-Bounds. Keine
        erfundenen Zahlen (D17): quantitative Luecken stehen als offene Fragen.
        """
        return IdeationResult(
            drafts=[
                IdeationDraft(
                    title="[mock] Entwurf A -- Automatisierte Vorpruefung",
                    current_state=(
                        "Der beschriebene Prozess wird heute manuell und ohne "
                        "systematische Unterstuetzung bearbeitet."
                    ),
                    desired_state=(
                        "Ein AI-System uebernimmt die Vorpruefung und legt nur "
                        "Zweifelsfaelle einem Menschen vor."
                    ),
                    example_process=(
                        "Ein einzelner Vorgang wird eingelesen, geprueft und mit "
                        "einer Empfehlung an die Sachbearbeitung uebergeben."
                    ),
                    rationale=(
                        "Passt zum Problem, weil wiederkehrende manuelle Pruefung "
                        "der genannte Engpass ist."
                    ),
                    open_questions=[
                        "Wie viele Vorgaenge fallen pro Jahr an?",
                        "Wie viele Minuten dauert ein Vorgang heute?",
                    ],
                ),
                IdeationDraft(
                    title="[mock] Entwurf B -- Assistenz statt Vollautomatik",
                    current_state=(
                        "Die Bearbeitung erfolgt vollstaendig manuell durch die "
                        "Fachabteilung."
                    ),
                    desired_state=(
                        "Ein Assistenzsystem schlaegt Ergebnisse vor, die "
                        "Entscheidung bleibt beim Menschen."
                    ),
                    example_process=(
                        "Fuer einen Vorgang erzeugt das System einen "
                        "Formulierungsvorschlag, den die Fachkraft freigibt."
                    ),
                    rationale=(
                        "Geringeres Umsetzungsrisiko als Vollautomatik, weil der "
                        "Mensch in der Schleife bleibt."
                    ),
                    open_questions=[
                        "Welche Evidenz gibt es fuer die erwartete Zeitersparnis?",
                    ],
                ),
            ]
        )
