"""DSGVO Art. 5(1)(e) Retention-Enforcement (Phase G Privacy-Haertung).

Loescht Cases aelter als AECT_RETENTION_DAYS ueber den BESTEHENDEN,
beim Audit bereits verifizierten Art.-17-Loeschpfad
(TriageService.delete_case(), ADR-0038) -- keine zweite Loeschlogik. Das
ist derselbe Aufruf, den DELETE /cases/{case_id} intern nutzt
(adapters/api/routes/cases.py); eine eigene Loeschimplementierung haette
riskiert, dass beide Pfade auseinanderlaufen.

Feldname-Praezisierung: SubmittedCase hat KEIN `created_at`-Feld -- der
Zeitstempel heisst `submitted_at` (application/models.py, per Clock-Port
bei submit_use_case() gesetzt).

Fuer Cron-Betrieb gedacht (Azure Container Apps Scheduled Job, Design in
docs/adr/0042-retention-scheduled-job.md): Default OHNE --dry-run loescht
tatsaechlich, kein interaktives Bestaetigen.

Aufruf:
    uv run python scripts/enforce_retention.py            # loescht tatsaechlich
    uv run python scripts/enforce_retention.py --dry-run  # listet nur auf
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import timedelta

import structlog

from aect.adapters.api.dependencies import (
    get_llm_adapter,
    get_triage_service,
    resolve_retriever,
)
from aect.adapters.api.settings import Settings
from aect.adapters.in_memory.clock import SystemClock
from aect.application.models import SubmittedCase
from aect.application.ports.clock import ClockPort
from aect.application.service import TriageService


def find_expired_case_ids(
    cases: list[SubmittedCase], clock: ClockPort, retention_days: int
) -> list[str]:
    """Reine Funktion (kein I/O) -- welche Case-IDs sind aelter als
    retention_days, bezogen auf submitted_at? Eigenstaendig testbar ohne
    Repository-/Service-Aufbau.

    "Aelter als N Tage" = strikt kleiner als der Cutoff -- ein Case, der
    exakt N Tage alt ist, gilt noch nicht als abgelaufen.
    """
    cutoff = clock.now() - timedelta(days=retention_days)
    return [case.id for case in cases if case.submitted_at < cutoff]


async def enforce_retention(
    service: TriageService,
    clock: ClockPort,
    retention_days: int,
    dry_run: bool,
) -> list[str]:
    """Fuehrt einen Retention-Lauf aus.

    dry_run=True: listet nur auf, loescht nichts.
    dry_run=False: ruft fuer jeden abgelaufenen Case service.delete_case()
    auf -- derselbe kaskadierte Pfad (Repository + Vektor-Store +
    Audit-Log) wie DELETE /cases/{case_id}.

    Returns:
        Case-IDs, die abgelaufen sind (bei dry_run: die WUERDEN geloescht
        werden; sonst: die WURDEN geloescht).
    """
    logger = structlog.get_logger()
    expired = find_expired_case_ids(service.list_cases(), clock, retention_days)

    if dry_run:
        logger.info("retention_dry_run", case_count=len(expired), case_ids=expired)
        return expired

    for case_id in expired:
        await service.delete_case(case_id)
    logger.info("retention_enforced", case_count=len(expired), case_ids=expired)
    return expired


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "DSGVO Art. 5(1)(e) Retention-Enforcement -- loescht Cases "
            "aelter als AECT_RETENTION_DAYS."
        )
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Nur betroffene Case-IDs auflisten, nichts loeschen "
            "(Default ohne dieses Flag: tatsaechlich loeschen -- fuer Cron-Betrieb)."
        ),
    )
    args = parser.parse_args()

    settings = Settings()
    # Wiederverwendet exakt die Produktions-DI-Verdrahtung aus
    # dependencies.py (get_llm_adapter/resolve_retriever sind normale
    # Python-Funktionen, direkt aufrufbar ohne FastAPI-Request-Kontext,
    # analog dem bestehenden Muster in tests/adapters/api/test_dependencies.py).
    service = get_triage_service(
        settings=settings,
        llm=get_llm_adapter(settings=settings),
        retriever=resolve_retriever(settings),
    )
    asyncio.run(
        enforce_retention(service, SystemClock(), settings.retention_days, args.dry_run)
    )


if __name__ == "__main__":
    main()
