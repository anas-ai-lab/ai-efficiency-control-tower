"""TriageService -- Application Service fuer den Use-Case-Intake-Workflow.

Importiert aus: aect.domain (erlaubt), aect.application.ports (erlaubt).
Importiert NICHT aus: aect.adapters -- das waere eine DI-Verletzung.
"""

from __future__ import annotations

import structlog

from aect.application.cost_logger import log_llm_cost
from aect.application.models import SharpenedUseCase, SolutionProposal, SubmittedCase
from aect.application.ports.clock import ClockPort
from aect.application.ports.id_generator import IdGeneratorPort
from aect.application.ports.llm import LLMMessage, LLMPort
from aect.application.ports.repository import RepositoryPort
from aect.application.prompts import load_prompt
from aect.application.sanitization import detect_injection_patterns
from aect.domain import ROIConfig, UseCaseInput, evaluate_use_case


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
        self, case_id: str, prompt_version: str = "v1"
    ) -> SharpenedUseCase | None:
        """Schaerft die Use-Case-Beschreibung eines persistierten Cases via LLM.

        Original-Felder (title, current_state, desired_state) werden aus dem
        gespeicherten Case uebernommen und nie ueberschrieben -- die
        geschaerfte Version steht daneben (sharpened_text).

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

        return SharpenedUseCase(
            case_id=case.id,
            original_title=case.use_case.title,
            original_current_state=case.use_case.current_state,
            original_desired_state=case.use_case.desired_state,
            sharpened_text=response.content,
            prompt_version=prompt_version,
        )

    async def propose_solution(
        self, case_id: str, prompt_version: str = "v1"
    ) -> SolutionProposal | None:
        """Skizziert einen Loesungsansatz fuer einen persistierten Case via LLM.

        Tag 36, Phase-C-Skeleton: identisches Pattern wie sharpen_case() --
        gleicher Injection-Check, gleiches Messages-/Cost-Logging-Vorgehen,
        andere Prompt-Familie ("propose_solution" statt "sharpen_use_case").

        Returns:
            None wenn case_id nicht existiert (Route mapped das auf 404).

        v1-Prompt nennt bewusst keine konkreten Zielplattformen (siehe
        SolutionProposal-Docstring) -- Stack-Grounding via RAG folgt Phase D.
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
        response = await self._llm.complete(messages)

        log_llm_cost(
            case_id=case.id,
            messages=messages,
            response=response,
            operation="propose_solution",
        )

        return SolutionProposal(
            case_id=case.id,
            proposal_text=response.content,
            prompt_version=prompt_version,
        )
