"""TriageService -- Application Service fuer den Use-Case-Intake-Workflow.

Importiert aus: aect.domain (erlaubt), aect.application.ports (erlaubt).
Importiert NICHT aus: aect.adapters -- das waere eine DI-Verletzung.
"""

from __future__ import annotations

import json
from typing import Any

import structlog

from aect.application.cost_logger import log_llm_cost
from aect.application.models import (
    BusinessSummary,
    ReportResult,
    SharpenedUseCase,
    SolutionProposal,
    SubmittedCase,
    TechnicalDetail,
)
from aect.application.ports.clock import ClockPort
from aect.application.ports.id_generator import IdGeneratorPort
from aect.application.ports.llm import LLMMessage, LLMPort
from aect.application.ports.repository import RepositoryPort
from aect.application.prompts import load_prompt
from aect.application.sanitization import detect_injection_patterns
from aect.application.structured_output import (
    InvalidLLMOutputError,
    SharpenedContentV2,
    parse_structured_llm_output,
)
from aect.application.tools import (
    TOOL_DEFINITIONS,
    UnknownToolError,
    dispatch_tool_call,
)
from aect.domain import ROIConfig, TriageResult, UseCaseInput, evaluate_use_case


def _render_sharpened_content(content_json: str | None) -> str | None:
    """Rendert den persistierten Schaerfungs-Inhalt zu lesbarem Text.

    Reine Regel-Schicht (ADR-0011: kein LLM-Call). content_json ist entweder
    None (sharpen_case() lief nie fuer diesen Case), ein Graceful-
    Degradation-JSON (raw_text gesetzt, ADR-0013 Teil 2) oder ein valides
    SharpenedContentV2-JSON (strukturierte Felder gesetzt).
    """
    if content_json is None:
        return None
    data = json.loads(content_json)
    if data.get("raw_text") is not None:
        return str(data["raw_text"])
    lines = [
        f"Titel: {data['sharpened_title']}",
        f"Ist-Zustand: {data['sharpened_current_state']}",
        f"Soll-Zustand: {data['sharpened_desired_state']}",
        "Verbesserungsvorschlaege:",
    ]
    lines += [f"- {s}" for s in data["improvement_suggestions"]]
    return "\n".join(lines)


def _build_business_summary(
    result: TriageResult, sharpened_text: str | None
) -> BusinessSummary:
    """Leitet die Entscheider-Schicht deterministisch aus TriageResult ab.

    result.zone ist None genau dann, wenn der Vorfilter nicht bestanden wurde
    (domain/pipeline.py) -- in diesem Fall auch result.roi None.
    """
    if result.zone is not None:
        zone_value: str | None = result.zone.final_zone.value
        expected_benefit: float | None = (
            float(result.roi.expected_benefit_eur) if result.roi is not None else None
        )
        summary_text = (
            f"'{result.title}': Zone {zone_value}, "
            f"Empfehlung {result.routing.recommendation.value}. "
            f"{result.zone.reason}"
        )
    else:
        zone_value = None
        expected_benefit = None
        summary_text = (
            f"'{result.title}' erfuellt die Vorfilter-Kriterien nicht "
            f"({', '.join(result.vorfilter.failed_criteria)}). "
            f"Empfehlung {result.routing.recommendation.value}."
        )

    return BusinessSummary(
        title=result.title,
        zone=zone_value,
        is_actionable=result.is_actionable,
        recommendation=result.routing.recommendation.value,
        expected_benefit_eur=expected_benefit,
        summary_text=summary_text,
        sharpened_text=sharpened_text,
    )


def _build_technical_detail(
    result: TriageResult, proposal_text: str | None
) -> TechnicalDetail:
    """Leitet die Reviewer-Schicht deterministisch aus TriageResult ab.

    composite/roi sind None wenn passed_vorfilter False ist (siehe
    domain/pipeline.py) -- entsprechende Felder werden dann None.
    """
    return TechnicalDetail(
        passed_vorfilter=result.passed_vorfilter,
        vorfilter_failed_criteria=list(result.vorfilter.failed_criteria),
        composite_total=(
            result.composite.total if result.composite is not None else None
        ),
        composite_effort_label=(
            result.composite.effort_label if result.composite is not None else None
        ),
        feasibility_flags=[f.value for f in result.feasibility.flags],
        feasibility_recommendation=result.feasibility.recommendation,
        automation_signals=list(result.routing.automation_signals),
        ai_signals=list(result.routing.ai_signals),
        risk_flags=list(result.routing.risk_flags),
        requires_human_review=result.routing.requires_human_review,
        roi_theoretical_potential_eur=(
            float(result.roi.theoretical_potential_eur)
            if result.roi is not None
            else None
        ),
        roi_net_expected_benefit_eur=(
            float(result.roi.net_expected_benefit_eur)
            if result.roi is not None
            else None
        ),
        proposal_text=proposal_text,
    )


class TriageService:
    """Orchestriert Use-Case-Einreichung: ID -> Zeitstempel -> Domain -> Persistenz.

    Alle Abhaengigkeiten werden von aussen injiziert (Constructor DI).
    Die Domain-Logik liegt vollstaendig in evaluate_use_case() -- der Service
    ist ausschliesslich fuer Orchestrierung und Persistenz zustaendig.

    llm: LLMPort -- Phase C, fuer sharpen_case(). Pflicht-Parameter, kein
    Default: ein Default auf MockLLMAdapter() wuerde aus aect.adapters
    importieren und die Dependency-Inversion-Grenze verletzen (siehe
    Modul-Docstring).
    """

    def __init__(
        self,
        repository: RepositoryPort,
        clock: ClockPort,
        id_generator: IdGeneratorPort,
        roi_config: ROIConfig,
        llm: LLMPort,
        country: str = "DE",
    ) -> None:
        self._repository = repository
        self._clock = clock
        self._id_generator = id_generator
        self._roi_config = roi_config
        self._llm = llm
        self._country = country

    def submit_use_case(self, use_case: UseCaseInput) -> SubmittedCase:
        """Bewertet einen Use Case und persistiert das Ergebnis.

        Reihenfolge: ID generieren -> Zeitstempel -> Domain-Evaluate -> Speichern.
        Exceptions aus evaluate_use_case() (z. B. ungueltige Config-Keys) propagieren.
        """
        case_id = self._id_generator.generate()
        submitted_at = self._clock.now()
        result = evaluate_use_case(use_case, self._roi_config, self._country)
        case = SubmittedCase(
            id=case_id,
            submitted_at=submitted_at,
            use_case=use_case,
            result=result,
        )
        self._repository.save(case)
        return case

    def get_case(self, case_id: str) -> SubmittedCase | None:
        """Gibt einen gespeicherten Case zurueck oder None wenn nicht gefunden."""
        return self._repository.get(case_id)

    def list_cases(self) -> list[SubmittedCase]:
        """Alle bisher eingereichten Cases."""
        return self._repository.list_all()

    async def sharpen_case(
        self, case_id: str, prompt_version: str = "v2"
    ) -> SharpenedUseCase | None:
        """Schaerft die Use-Case-Beschreibung eines persistierten Cases via LLM.

        Original-Felder (title, current_state, desired_state) werden aus dem
        gespeicherten Case uebernommen und nie ueberschrieben -- die
        geschaerfte Version steht daneben (sharpened_title/current_state/
        desired_state + improvement_suggestions).

        Strukturierte Ausgabe + Graceful Degradation (ADR-0013 Teil 2):
        response.content wird gegen SharpenedContentV2 validiert
        (parse_structured_llm_output). Erfolg -> strukturierte Felder
        gesetzt, raw_text=None. InvalidLLMOutputError -> alle strukturierten
        Felder None/leer, raw_text=response.content, Warnung
        "structured_output_validation_failed" geloggt (case_id, operation,
        error), kein Abbruch.

        Persistenz (Tag 42 ADR-0012, erweitert ADR-0013 Teil 2): das
        Ergebnis wird als JSON auf case.sharpened_content_json gespeichert
        (self._repository.save()). generate_report() rendert daraus den
        sichtbaren Text (_render_sharpened_content) -- /report-Schema bleibt
        unveraendert.

        Returns:
            None wenn case_id nicht existiert (Route mapped das auf 404).

        Messages-API (aect-security-checklist v2.1, Phase C): System- und
        User-Prompt bleiben getrennte LLMMessage-Eintraege, kein String-Concat.

        Injection-Pattern-Check (OWASP LLM01, Tag 32): Freitextfelder werden vor
        dem LLM-Call auf bekannte Injection-Muster geprueft. Treffer werden
        geloggt (case_id + Feldname + Pattern-Namen, kein Body), der Call laeuft
        trotzdem weiter -- Flaggen, nicht Blocken (siehe sanitization.py).
        """
        case = self._repository.get(case_id)
        if case is None:
            return None

        fields_to_check = {
            "title": case.use_case.title,
            "current_state": case.use_case.current_state,
            "desired_state": case.use_case.desired_state,
            "example_process": case.use_case.example_process,
        }
        detected: dict[str, list[str]] = {
            field_name: patterns
            for field_name, field_value in fields_to_check.items()
            if (patterns := detect_injection_patterns(field_value))
        }
        if detected:
            logger = structlog.get_logger()
            logger.warning(
                "injection_pattern_detected",
                case_id=case.id,
                fields=detected,
            )

        system_prompt = load_prompt("sharpen_use_case", "system", prompt_version)
        user_template = load_prompt("sharpen_use_case", "user", prompt_version)
        user_content = user_template.format(
            title=case.use_case.title,
            current_state=case.use_case.current_state,
            desired_state=case.use_case.desired_state,
            example_process=case.use_case.example_process,
        )

        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_content),
        ]
        response = await self._llm.complete(messages)

        log_llm_cost(
            case_id=case.id,
            messages=messages,
            response=response,
            operation="sharpen_case",
        )

        try:
            parsed = parse_structured_llm_output(response.content, SharpenedContentV2)
        except InvalidLLMOutputError as exc:
            logger = structlog.get_logger()
            logger.warning(
                "structured_output_validation_failed",
                case_id=case.id,
                operation="sharpen_case",
                error=str(exc),
            )
            sharpened_title: str | None = None
            sharpened_current_state: str | None = None
            sharpened_desired_state: str | None = None
            improvement_suggestions: tuple[str, ...] = ()
            raw_text: str | None = response.content
        else:
            sharpened_title = parsed.sharpened_title
            sharpened_current_state = parsed.sharpened_current_state
            sharpened_desired_state = parsed.sharpened_desired_state
            improvement_suggestions = tuple(parsed.improvement_suggestions)
            raw_text = None

        case.sharpened_content_json = json.dumps(
            {
                "sharpened_title": sharpened_title,
                "sharpened_current_state": sharpened_current_state,
                "sharpened_desired_state": sharpened_desired_state,
                "improvement_suggestions": list(improvement_suggestions),
                "raw_text": raw_text,
            }
        )
        self._repository.save(case)

        return SharpenedUseCase(
            case_id=case.id,
            original_title=case.use_case.title,
            original_current_state=case.use_case.current_state,
            original_desired_state=case.use_case.desired_state,
            sharpened_title=sharpened_title,
            sharpened_current_state=sharpened_current_state,
            sharpened_desired_state=sharpened_desired_state,
            improvement_suggestions=improvement_suggestions,
            raw_text=raw_text,
            prompt_version=prompt_version,
        )

    async def propose_solution(
        self, case_id: str, prompt_version: str = "v2"
    ) -> SolutionProposal | None:
        """Skizziert einen Loesungsansatz fuer einen persistierten Case via LLM.

        Function-Calling-Loop (Tag 38, ADR-0009): propose_solution() bietet
        TOOL_DEFINITIONS an. Fordert das LLM einen Tool-Call an
        (response.tool_calls nicht leer), wird jeder Aufruf via
        dispatch_tool_call() ausgefuehrt, das Ergebnis als role="tool"-
        Nachricht angehaengt und complete() ein zweites Mal aufgerufen.
        Kein while-Loop -- maximal zwei complete()-Aufrufe pro Call
        (LLM10 Unbounded Consumption, siehe ADR-0009).

        LLM06 Excessive Agency: dispatch_tool_call() wirft UnknownToolError
        fuer nicht registrierte Tool-Namen. Der Fehler wird als
        Tool-Ergebnis ({"error": ...}) an das LLM zurueckgegeben statt die
        Anfrage abzubrechen -- Graceful Degradation.

        Persistenz (Tag 42, ADR-0012): die finale response.content (nach
        einem etwaigen Tool-Call-Loop) wird zusaetzlich auf
        case.proposal_text gespeichert (self._repository.save()), damit
        generate_report() es ohne erneuten Request-Body-Transport anzeigen
        kann.

        Returns:
            None wenn case_id nicht existiert (Route mapped das auf 404).

        v2-Prompt (prompts/propose_solution/v2/) weist das LLM auf
        lookup_stack_options hin und markiert die Plattform-Beschreibungen
        als vorlaeufig/unbelegt (RAG-Grounding folgt Phase D). v1 bleibt
        unveraendert erhalten (Versionierung, application/prompts.py).
        """
        case = self._repository.get(case_id)
        if case is None:
            return None

        fields_to_check = {
            "title": case.use_case.title,
            "current_state": case.use_case.current_state,
            "desired_state": case.use_case.desired_state,
            "example_process": case.use_case.example_process,
        }
        detected: dict[str, list[str]] = {
            field_name: patterns
            for field_name, field_value in fields_to_check.items()
            if (patterns := detect_injection_patterns(field_value))
        }
        if detected:
            logger = structlog.get_logger()
            logger.warning(
                "injection_pattern_detected",
                case_id=case.id,
                fields=detected,
            )

        system_prompt = load_prompt("propose_solution", "system", prompt_version)
        user_template = load_prompt("propose_solution", "user", prompt_version)
        user_content = user_template.format(
            title=case.use_case.title,
            current_state=case.use_case.current_state,
            desired_state=case.use_case.desired_state,
            example_process=case.use_case.example_process,
        )

        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_content),
        ]
        response = await self._llm.complete(messages, tools=TOOL_DEFINITIONS)

        log_llm_cost(
            case_id=case.id,
            messages=messages,
            response=response,
            operation="propose_solution",
        )

        if response.tool_calls:
            messages.append(
                LLMMessage(
                    role="assistant",
                    content=response.content,
                    tool_calls=response.tool_calls,
                )
            )
            for tool_call in response.tool_calls:
                tool_result: dict[str, Any]
                try:
                    tool_result = dispatch_tool_call(tool_call)
                except UnknownToolError as exc:
                    tool_result = {"error": str(exc)}
                messages.append(
                    LLMMessage(
                        role="tool",
                        content=json.dumps(tool_result),
                        tool_call_id=tool_call.id,
                    )
                )

            response = await self._llm.complete(messages, tools=TOOL_DEFINITIONS)

            log_llm_cost(
                case_id=case.id,
                messages=messages,
                response=response,
                operation="propose_solution",
            )

        case.proposal_text = response.content
        self._repository.save(case)

        return SolutionProposal(
            case_id=case.id,
            proposal_text=response.content,
            prompt_version=prompt_version,
        )

    def generate_report(
        self,
        case_id: str,
        sharpened_text: str | None = None,
        proposal_text: str | None = None,
    ) -> ReportResult | None:
        """Erstellt den zweischichtigen Report (Business + Technisch) fuer einen Case.

        Reine Regel-Schicht (Master-Plan v3.1, Phase C: "Zweischichtiger
        Report-Renderer", ADR-0011): kombiniert das deterministische
        TriageResult mit optionalen LLM-Narrativen aus sharpen_case() /
        propose_solution().

        Persistenz (Tag 42, ADR-0012): sharpened_text/proposal_text werden
        standardmaessig aus dem persistierten SubmittedCase gelesen (sofern
        sharpen_case()/propose_solution() fuer diesen Case bereits liefen).
        Ein hier uebergebener Wert ueberschreibt den persistierten -- z. B.
        fuer Tests oder eine Vorschau ohne erneuten Persist.

        sharpened_text/proposal_text fliessen unveraendert als untrusted
        LLM-Output durch (aect-security-checklist v2.1: "LLM-Output immer
        als untrusted behandeln") -- sie wirken nicht auf Berechnungen,
        nur auf die Anzeige.

        Returns:
            None wenn case_id nicht existiert (Route mapped das auf 404).
        """
        case = self._repository.get(case_id)
        if case is None:
            return None

        effective_sharpened_text = (
            sharpened_text
            if sharpened_text is not None
            else _render_sharpened_content(case.sharpened_content_json)
        )
        effective_proposal_text = (
            proposal_text if proposal_text is not None else case.proposal_text
        )

        return ReportResult(
            case_id=case.id,
            business_summary=_build_business_summary(
                case.result, effective_sharpened_text
            ),
            technical_detail=_build_technical_detail(
                case.result, effective_proposal_text
            ),
        )
