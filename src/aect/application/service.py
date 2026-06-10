"""TriageService -- Application Service fuer den Use-Case-Intake-Workflow.

Importiert aus: aect.domain (erlaubt), aect.application.ports (erlaubt).
Importiert NICHT aus: aect.adapters -- das waere eine DI-Verletzung.
"""

from __future__ import annotations

from aect.application.models import SubmittedCase
from aect.application.ports.clock import ClockPort
from aect.application.ports.id_generator import IdGeneratorPort
from aect.application.ports.repository import RepositoryPort
from aect.domain import ROIConfig, UseCaseInput, evaluate_use_case


class TriageService:
    """Orchestriert Use-Case-Einreichung: ID -> Zeitstempel -> Domain -> Persistenz.

    Alle Abhaengigkeiten werden von aussen injiziert (Constructor DI).
    Die Domain-Logik liegt vollstaendig in evaluate_use_case() -- der Service
    ist ausschliesslich fuer Orchestrierung und Persistenz zustaendig.
    """

    def __init__(
        self,
        repository: RepositoryPort,
        clock: ClockPort,
        id_generator: IdGeneratorPort,
        roi_config: ROIConfig,
        country: str = "DE",
    ) -> None:
        self._repository = repository
        self._clock = clock
        self._id_generator = id_generator
        self._roi_config = roi_config
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
