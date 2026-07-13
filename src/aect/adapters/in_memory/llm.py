"""MockLLMAdapter -- deterministischer LLM-Adapter fuer Tests."""

from __future__ import annotations

from aect.application.ports.llm import (
    LLMMessage,
    LLMResponse,
    ToolCall,
    ToolDefinition,
)
from aect.application.structured_output import (
    ArchitectureSketch,
    CaseField,
    IdeationDraft,
    IdeationResult,
    ImprovementSuggestion,
    SharpenedContentV2,
    SketchEdge,
    SketchNode,
    SketchNodeKind,
    SolutionProposalV2,
)

_MOCK_TOOL_CALL_ID = "mock-tool-call-1"

# Deterministischer, schema-valider zweigeteilter Loesungsvorschlag (V4-P6).
# solution_business ist bewusst FREI von verbotenem Technik-/Architektur-Vokabular
# (domain/solution_guard) -- so verletzt der Mock nie den Vokabular-Guard. Der
# "[mock]"-Marker macht die Herkunft in Assertions sichtbar.
_SOLUTION_MOCK_JSON = SolutionProposalV2(
    solution_business=(
        "[mock] Eingehende Vorgaenge werden kuenftig automatisch vorbereitet und "
        "den Mitarbeitenden strukturiert vorgelegt. Die Fachkraft prueft nur noch "
        "Zweifelsfaelle und gibt frei; die endgueltige Entscheidung bleibt beim "
        "Menschen."
    ),
    solution_technical=(
        "[mock] Ein Dienst liest die benoetigten Felder aus und uebergibt sie an "
        "das Zielsystem; eine Klassifizierung markiert Zweifelsfaelle fuer die "
        "manuelle Pruefung."
    ),
).model_dump_json()

# Deterministische, schema-valide Schaerfung fuer Tests (V4; S4 auf Soll-Felder
# reduziert). Beide Soll-Felder sind bewusst ZAHLENFREI -- so verletzt der Mock
# nie den Zahlen-Guard (domain/sharpening_guard), unabhaengig vom Case. Der
# "[mock]"-Marker macht die Herkunft in Assertions sichtbar.
_SHARPENING_MOCK_JSON = SharpenedContentV2(
    sharpened_desired_state=(
        "[mock] Ein AI-System uebernimmt die wiederkehrende Routine und legt nur "
        "Zweifelsfaelle einem Menschen zur Pruefung vor."
    ),
    sharpened_desired_example_process=(
        "Ein typischer Zielvorgang laeuft weitgehend automatisch; nur eine "
        "unklare Ausnahme geht an eine Fachkraft zur Bestaetigung."
    ),
    improvement_suggestions=[
        ImprovementSuggestion(
            bezugsfeld=CaseField.EVIDENCE_LEVEL,
            vorschlag=(
                "Belege die Zeitersparnis mit einer kurzen Vorher-Nachher-"
                "Messung an echten Vorgaengen."
            ),
            hebel=(
                "Evidenzfaktor steigt, der erwartete Nutzen wird im ROI hoeher "
                "gewichtet."
            ),
        )
    ],
).model_dump_json()


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

        # Schaerfungs-Aufruf erkennen: der sharpen-System-Prompt beschreibt das
        # JSON-Schema und traegt daher "sharpened_desired_state" (S4). Dann
        # liefert der Mock eine schema-valide, zahlenfreie Schaerfung statt eines
        # Echos (der Echo waere kein JSON und wuerde den Fail-loud-Pfad ausloesen).
        if any("sharpened_desired_state" in m.content for m in messages):
            return LLMResponse(content=_SHARPENING_MOCK_JSON)

        # propose_solution v3: der System-Prompt beschreibt das JSON-Schema und
        # traegt daher "solution_business". Dann liefert der Mock einen
        # schema-validen, zweigeteilten Loesungsvorschlag (Business + technisch)
        # statt eines Echos (das waere kein JSON und wuerde den Fail-loud-Pfad
        # ausloesen).
        if any("solution_business" in m.content for m in messages):
            return LLMResponse(content=_SOLUTION_MOCK_JSON)

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

    async def generate_architecture_sketch(
        self,
        case_id: str,
        title: str,
        description: str,
        proposal_text: str,
    ) -> ArchitectureSketch:
        """Liefert deterministisch einen 3-Knoten-Graph (Tests, P11).

        Ignoriert die Eingaben bewusst (kein echter Call) und baut einen festen
        Graphen user -> system -> data_store -- genug fuer den Mock-E2E-Pfad und
        den Mermaid-Builder, ohne Netzwerk/Kosten.
        """
        return ArchitectureSketch(
            nodes=[
                SketchNode(id="user", label="Nutzer", kind=SketchNodeKind.USER),
                SketchNode(
                    id="system",
                    label="[mock] Verarbeitungs-System",
                    kind=SketchNodeKind.SYSTEM,
                ),
                SketchNode(
                    id="data_store",
                    label="Fall-Datenbank",
                    kind=SketchNodeKind.DATA_STORE,
                ),
            ],
            edges=[
                SketchEdge(source="user", target="system", label="reicht ein"),
                SketchEdge(source="system", target="data_store"),
            ],
        )
