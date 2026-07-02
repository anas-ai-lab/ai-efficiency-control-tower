"""Eval-Runner -- fuehrt EvalCases durch die Phase-A-Pipeline und vergleicht
das Ergebnis mit einem optionalen Experten-Label (Master-Plan v3.1 Phase E,
ADR-0030).

Zwei Eval-Arten aus der Projekt-Methodik, beide ueber denselben Lauf erreichbar:
  - Konsistenz-Eval: predicted_zone ist deterministisch (gleicher Use Case ->
    gleiches Ergebnis, siehe tests/domain/test_pipeline.py::test_pipeline_is_deterministic).
  - Experten-Abgleich: is_match vergleicht predicted_zone gegen expected_zone,
    wo ein Experten-Label vorliegt. is_match ist None, wenn kein Label vorliegt --
    das ist kein Sonderfall, sondern der Normalfall fuer unlabeled Cases.

Schicht: application -- importiert aus aect.domain (Pipeline) und
aect.application.eval (Case-Schema), nicht aus aect.adapters.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import structlog

from aect.application.eval.models import EvalCase
from aect.domain import ROIConfig, TriageZone, evaluate_use_case

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class EvalCaseResult:
    """Ergebnis eines einzelnen EvalCase nach dem Lauf durch die Pipeline.

    is_match ist None, wenn kein Experten-Label (expected_zone) vorliegt --
    explizit verschieden von False (vgl. ADR-0030). Nur is_match in {True, False}
    zaehlt fuer den Experten-Abgleich; is_match=None wird bei der Agreement-Rate
    ausgeschlossen, nicht als Mismatch gewertet.
    """

    case_id: str
    passed_vorfilter: bool
    predicted_zone: TriageZone | None
    expected_zone: TriageZone | None
    is_match: bool | None


def run_eval(
    cases: list[EvalCase],
    roi_config: ROIConfig,
    country: str = "DE",
) -> list[EvalCaseResult]:
    """Fuehrt jeden EvalCase durch die Phase-A-Pipeline und vergleicht das
    Ergebnis mit einem evtl. vorhandenen Experten-Label.

    Args:
        cases:      Liste validierter EvalCase (z. B. aus load_eval_cases()).
        roi_config: ROI-Konfiguration aus load_roi_config().
        country:    ISO-Laendercode fuer Stundensatz-Lookup (Default: DE).

    Returns:
        Eine EvalCaseResult pro Case, in derselben Reihenfolge wie cases.
    """
    results: list[EvalCaseResult] = []
    for case in cases:
        triage = evaluate_use_case(case.use_case, roi_config, country=country)
        predicted_zone = triage.zone.final_zone if triage.zone is not None else None
        expected_zone = case.expected_zone

        is_match: bool | None = (
            None if expected_zone is None else predicted_zone == expected_zone
        )

        results.append(
            EvalCaseResult(
                case_id=case.case_id,
                passed_vorfilter=triage.passed_vorfilter,
                predicted_zone=predicted_zone,
                expected_zone=expected_zone,
                is_match=is_match,
            )
        )
    return results


def write_report(results: list[EvalCaseResult], path: Path) -> None:
    """Schreibt eine JSON-Zusammenfassung der Eval-Ergebnisse nach path.

    Enthaelt nur case_id + Zonen-Werte -- keinen use_case-Inhalt (Logging-
    Allowlist-Prinzip, aect-security-checklist v2.1, vgl. ADR-0030).

    Args:
        results: Ausgabe von run_eval().
        path:    Zielpfad fuer die JSON-Datei. Elternverzeichnisse werden
                 bei Bedarf angelegt.
    """
    labeled = [r for r in results if r.expected_zone is not None]
    agreement_count = sum(1 for r in labeled if r.is_match)
    agreement_rate = agreement_count / len(labeled) if labeled else None

    report = {
        "total_cases": len(results),
        "labeled_cases": len(labeled),
        "agreement_count": agreement_count,
        "agreement_rate": agreement_rate,
        "results": [
            {
                "case_id": r.case_id,
                "passed_vorfilter": r.passed_vorfilter,
                "predicted_zone": (
                    r.predicted_zone.value if r.predicted_zone is not None else None
                ),
                "expected_zone": (
                    r.expected_zone.value if r.expected_zone is not None else None
                ),
                "is_match": r.is_match,
            }
            for r in results
        ],
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    # Allowlist-konform: nur Pfad + Zaehlwerte, kein Payload-Inhalt
    logger.info(
        "eval_report_written",
        path=str(path),
        total_cases=len(results),
        labeled_cases=len(labeled),
    )
