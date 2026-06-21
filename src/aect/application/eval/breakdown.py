"""Score-Breakdown-Diagnostik fuer Eval-Cases (Tag 65, Master-Plan v3.1 Phase E,
ADR-0031, baut auf ADR-0029/0030 auf).

Beantwortet "warum bekommt dieser Fall genau diese Bewertung?" (Eval-Runner-
Comprehension-Gate-Thema, session-protocol v3 SS3) strukturiert: zeigt
Composite-Score-Komponenten, Handlungsdruck-Score und die konfigurierten
Zonen-Schwellen nebeneinander, plus eine deterministisch generierte,
menschenlesbare Erklaerung der Zonen-Entscheidung.

Bewusst getrennt von EvalCaseResult/run_eval() (runner.py): run_eval() ist
bereits Gate-getestet (Phase D->E) und bleibt unveraendert. Score-Breakdown
ist zusaetzliche Diagnostik on top, kein Ersatz (ADR-0031).

Schicht: application -- importiert aus aect.domain (erlaubt), nicht aus
aect.adapters. Importiert EvalCase aus .models statt aus dem eval-Package
selbst (Vermeidung Circular Import: eval/__init__.py importiert breakdown.py).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import structlog

from aect.application.eval.models import EvalCase
from aect.domain import (
    ROIConfig,
    TriageZone,
    ZoneClassifier,
    evaluate_use_case,
    handlungsdruck_score,
)

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class ScoreBreakdown:
    """Diagnostischer Breakdown eines einzelnen Eval-Case.

    composite_*, base_zone, final_zone sind None wenn passed_vorfilter False
    ist -- analog zu TriageResult (domain/pipeline.py). expected_benefit_eur
    ist roi.expected_benefit_eur (vor Lizenzkosten) -- dasselbe Feld, das
    ZoneClassifier.classify() fuer die Zonen-Einstufung verwendet, bewusst
    nicht net_expected_benefit_eur (siehe domain/pipeline.py evaluate_use_case()).
    """

    case_id: str
    passed_vorfilter: bool
    predicted_zone: TriageZone | None
    expected_zone: TriageZone | None
    is_match: bool | None
    expected_benefit_eur: float | None
    composite_total: int | None
    composite_complexity: int | None
    composite_cost: int | None
    composite_data_protection: int | None
    handlungsdruck_score: int
    base_zone: TriageZone | None
    final_zone: TriageZone | None
    handlungsdruck_elevated: bool
    likely_win_min_benefit_eur: float
    likely_win_max_composite: int
    calculated_risk_min_benefit_eur: float
    calculated_risk_max_composite: int
    handlungsdruck_elevation_threshold: int
    explanation: str


def _base_zone_explanation(
    benefit: Decimal, composite: int, classifier: ZoneClassifier
) -> tuple[TriageZone, str]:
    """Rekonstruiert ZoneClassifier._base_zone() mit lesbarer Begruendung.

    Spiegelt die Vergleichsreihenfolge aus domain/zones.py exakt: LIKELY_WIN
    zuerst pruefen, dann CALCULATED_RISK, sonst MARGINAL_GAIN. Bekannte
    technische Schuld (ADR-0031): muss bei Aenderungen an
    ZoneClassifier._base_zone() manuell synchron gehalten werden.
    """
    if benefit >= classifier.likely_win_min_benefit and (
        composite <= classifier.likely_win_max_composite
    ):
        return TriageZone.LIKELY_WIN, (
            f"Nutzen {benefit:,.0f} EUR >= LIKELY_WIN-Schwelle "
            f"{classifier.likely_win_min_benefit:,.0f} EUR UND Composite "
            f"{composite} <= {classifier.likely_win_max_composite} "
            f"-> Basis-Zone LIKELY_WIN."
        )
    if benefit >= classifier.calculated_risk_min_benefit and (
        composite <= classifier.calculated_risk_max_composite
    ):
        misses: list[str] = []
        if composite > classifier.likely_win_max_composite:
            misses.append(
                f"Composite {composite} > LIKELY_WIN-Obergrenze "
                f"{classifier.likely_win_max_composite}"
            )
        if benefit < classifier.likely_win_min_benefit:
            misses.append(
                f"Nutzen {benefit:,.0f} EUR < LIKELY_WIN-Schwelle "
                f"{classifier.likely_win_min_benefit:,.0f} EUR"
            )
        return TriageZone.CALCULATED_RISK, (
            f"{' UND '.join(misses)}, aber Nutzen {benefit:,.0f} EUR >= "
            f"{classifier.calculated_risk_min_benefit:,.0f} EUR UND Composite "
            f"{composite} <= {classifier.calculated_risk_max_composite} "
            f"-> Basis-Zone CALCULATED_RISK."
        )
    reasons: list[str] = []
    if benefit < classifier.calculated_risk_min_benefit:
        reasons.append(
            f"Nutzen {benefit:,.0f} EUR < CALCULATED_RISK-Schwelle "
            f"{classifier.calculated_risk_min_benefit:,.0f} EUR"
        )
    if composite > classifier.calculated_risk_max_composite:
        reasons.append(
            f"Composite {composite} > CALCULATED_RISK-Obergrenze "
            f"{classifier.calculated_risk_max_composite}"
        )
    return (
        TriageZone.MARGINAL_GAIN,
        " UND ".join(reasons) + " -> Basis-Zone MARGINAL_GAIN.",
    )


def _elevation_explanation(
    base: TriageZone, final: TriageZone, hd_score: int, classifier: ZoneClassifier
) -> str:
    """Rekonstruiert ZoneClassifier._apply_handlungsdruck() mit lesbarer Begruendung."""
    if hd_score < classifier.handlungsdruck_elevation_threshold:
        gap = classifier.handlungsdruck_elevation_threshold - hd_score
        return (
            f"Handlungsdruck {hd_score} < Schwelle "
            f"{classifier.handlungsdruck_elevation_threshold} (fehlt {gap}) "
            f"-> keine Hochstufung."
        )
    if base == final:
        return (
            f"Handlungsdruck {hd_score} >= Schwelle "
            f"{classifier.handlungsdruck_elevation_threshold}, Basis-Zone war "
            f"bereits LIKELY_WIN -> keine Aenderung."
        )
    return (
        f"Handlungsdruck {hd_score} >= Schwelle "
        f"{classifier.handlungsdruck_elevation_threshold} -> Hochstufung "
        f"{base.value} -> {final.value}."
    )


def build_score_breakdown(
    case: EvalCase,
    roi_config: ROIConfig,
    classifier: ZoneClassifier,
    country: str = "DE",
) -> ScoreBreakdown:
    """Fuehrt einen EvalCase durch die Pipeline und baut den diagnostischen Breakdown.

    Ruft evaluate_use_case() erneut auf (wie run_eval()) statt TriageResult zu
    teilen -- reine Berechnung ohne I/O, kein Performance-Problem bei der
    heutigen Case-Anzahl. Bewusst kein assert fuer die Optional-Narrowing nach
    dem Vorfilter-Check (Bandit B101) -- stattdessen ein expliziter Guard.
    """
    triage = evaluate_use_case(case.use_case, roi_config, country=country)
    hd_score = handlungsdruck_score(case.use_case)
    predicted = triage.zone.final_zone if triage.zone is not None else None
    is_match = None if case.expected_zone is None else predicted == case.expected_zone

    if not triage.passed_vorfilter:
        return ScoreBreakdown(
            case_id=case.case_id,
            passed_vorfilter=False,
            predicted_zone=None,
            expected_zone=case.expected_zone,
            is_match=None,
            expected_benefit_eur=None,
            composite_total=None,
            composite_complexity=None,
            composite_cost=None,
            composite_data_protection=None,
            handlungsdruck_score=hd_score,
            base_zone=None,
            final_zone=None,
            handlungsdruck_elevated=False,
            likely_win_min_benefit_eur=float(classifier.likely_win_min_benefit),
            likely_win_max_composite=classifier.likely_win_max_composite,
            calculated_risk_min_benefit_eur=float(
                classifier.calculated_risk_min_benefit
            ),
            calculated_risk_max_composite=classifier.calculated_risk_max_composite,
            handlungsdruck_elevation_threshold=(
                classifier.handlungsdruck_elevation_threshold
            ),
            explanation=(
                f"Vorfilter nicht bestanden "
                f"({', '.join(triage.vorfilter.failed_criteria)}). "
                f"Keine Zonen-Bewertung moeglich."
            ),
        )

    if triage.roi is None or triage.composite is None or triage.zone is None:
        raise RuntimeError(
            "Inkonsistenter Pipeline-Zustand: passed_vorfilter=True aber "
            "roi/composite/zone ist None (TriageResult-Invariante verletzt, "
            "siehe domain/pipeline.py)."
        )

    base_zone, base_explanation = _base_zone_explanation(
        triage.roi.expected_benefit_eur, triage.composite.total, classifier
    )
    elevation_explanation = _elevation_explanation(
        base_zone, triage.zone.final_zone, hd_score, classifier
    )

    return ScoreBreakdown(
        case_id=case.case_id,
        passed_vorfilter=True,
        predicted_zone=predicted,
        expected_zone=case.expected_zone,
        is_match=is_match,
        expected_benefit_eur=float(triage.roi.expected_benefit_eur),
        composite_total=triage.composite.total,
        composite_complexity=triage.composite.complexity_score,
        composite_cost=triage.composite.cost_score,
        composite_data_protection=triage.composite.data_protection_score,
        handlungsdruck_score=hd_score,
        base_zone=triage.zone.base_zone,
        final_zone=triage.zone.final_zone,
        handlungsdruck_elevated=triage.zone.handlungsdruck_elevated,
        likely_win_min_benefit_eur=float(classifier.likely_win_min_benefit),
        likely_win_max_composite=classifier.likely_win_max_composite,
        calculated_risk_min_benefit_eur=float(classifier.calculated_risk_min_benefit),
        calculated_risk_max_composite=classifier.calculated_risk_max_composite,
        handlungsdruck_elevation_threshold=(
            classifier.handlungsdruck_elevation_threshold
        ),
        explanation=f"{base_explanation} {elevation_explanation}",
    )


def write_breakdown_report(breakdowns: list[ScoreBreakdown], path: Path) -> None:
    """Schreibt eine JSON-Zusammenfassung der Score-Breakdowns nach path.

    Analog write_report() (runner.py) -- nur Zahlenwerte + generierte
    Erklaerung, kein use_case-Inhalt (Logging-Allowlist,
    aect-security-checklist v2.1).
    """
    report = {
        "total_cases": len(breakdowns),
        "results": [_breakdown_to_dict(b) for b in breakdowns],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(
        "score_breakdown_report_written", path=str(path), total_cases=len(breakdowns)
    )


def _breakdown_to_dict(b: ScoreBreakdown) -> dict[str, object]:
    return {
        "case_id": b.case_id,
        "passed_vorfilter": b.passed_vorfilter,
        "predicted_zone": (
            b.predicted_zone.value if b.predicted_zone is not None else None
        ),
        "expected_zone": (
            b.expected_zone.value if b.expected_zone is not None else None
        ),
        "is_match": b.is_match,
        "expected_benefit_eur": b.expected_benefit_eur,
        "composite_total": b.composite_total,
        "composite_complexity": b.composite_complexity,
        "composite_cost": b.composite_cost,
        "composite_data_protection": b.composite_data_protection,
        "handlungsdruck_score": b.handlungsdruck_score,
        "base_zone": b.base_zone.value if b.base_zone is not None else None,
        "final_zone": b.final_zone.value if b.final_zone is not None else None,
        "handlungsdruck_elevated": b.handlungsdruck_elevated,
        "thresholds": {
            "likely_win_min_benefit_eur": b.likely_win_min_benefit_eur,
            "likely_win_max_composite": b.likely_win_max_composite,
            "calculated_risk_min_benefit_eur": b.calculated_risk_min_benefit_eur,
            "calculated_risk_max_composite": b.calculated_risk_max_composite,
            "handlungsdruck_elevation_threshold": (
                b.handlungsdruck_elevation_threshold
            ),
        },
        "explanation": b.explanation,
    }
