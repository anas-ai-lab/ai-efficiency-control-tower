"""Deterministic zone classification for AECT use-case triage.

Implements the 3-zone logic (MARGINAL_GAIN / CALCULATED_RISK / LIKELY_WIN)
and optional Handlungsdruck elevation.

Design notes:
- No LLM, no I/O — purely arithmetic comparisons.
- ZoneClassifier accepts numbers, not UseCaseInput. This keeps the domain
  layer loosely coupled: ZoneClassifier does not need to know field names.
  The Application Service (Phase B) will connect ROIResult + CompositeScore
  to this classifier.
- Thresholds are injected via constructor (config-driven, not hardcoded).
  IP separation: threshold *values* live in config/zone_thresholds.yaml;
  the *logic* here is generic and shareable (interne Referenz (entfernt) §5).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, ClassVar

import yaml

from aect.domain.types import TriageZone


@dataclass(frozen=True)
class ZoneResult:
    """Immutable result of zone classification.

    Attributes:
        base_zone: Zone before Handlungsdruck adjustment.
        final_zone: Zone after adjustment — the operative verdict.
        handlungsdruck_elevated: True only when the zone actually changed.
        reason: German-language rationale string (included in triage report).
    """

    base_zone: TriageZone
    final_zone: TriageZone
    handlungsdruck_elevated: bool
    reason: str


class ZoneClassifier:
    """Classifies a use case into a triage zone.

    All thresholds are injected — never hardcoded here.
    Use load_zone_classifier() to create an instance from config.

    Args:
        likely_win_min_benefit: Minimum expected benefit (EUR) for LIKELY_WIN.
        likely_win_max_composite: Maximum composite score for LIKELY_WIN.
        calculated_risk_min_benefit: Minimum expected benefit for CALCULATED_RISK.
        calculated_risk_max_composite: Maximum composite score for CALCULATED_RISK.
        handlungsdruck_elevation_threshold: Score (1-5) at or above which
            the base zone is elevated by one step.
    """

    _ELEVATION: ClassVar[dict[TriageZone, TriageZone]] = {
        TriageZone.MARGINAL_GAIN: TriageZone.CALCULATED_RISK,
        TriageZone.CALCULATED_RISK: TriageZone.LIKELY_WIN,
        TriageZone.LIKELY_WIN: TriageZone.LIKELY_WIN,  # already maximum
    }

    def __init__(
        self,
        likely_win_min_benefit: Decimal,
        likely_win_max_composite: int,
        calculated_risk_min_benefit: Decimal,
        calculated_risk_max_composite: int,
        handlungsdruck_elevation_threshold: int,
    ) -> None:
        self._lw_min = likely_win_min_benefit
        self._lw_max_c = likely_win_max_composite
        self._cr_min = calculated_risk_min_benefit
        self._cr_max_c = calculated_risk_max_composite
        self._hd_threshold = handlungsdruck_elevation_threshold

    def classify(
        self,
        expected_benefit_eur: Decimal,
        composite_score: int,
        handlungsdruck_score: int,
    ) -> ZoneResult:
        """Classify a use case and apply Handlungsdruck elevation.

        Args:
            expected_benefit_eur: Expected annual net benefit (from ROI engine).
            composite_score: Composite effort/risk score (from composite scorer).
            handlungsdruck_score: Urgency on a 1-5 integer scale.

        Returns:
            ZoneResult with base zone, final zone, elevation flag, and reason.
        """
        base = self._base_zone(expected_benefit_eur, composite_score)
        elevated, final = self._apply_handlungsdruck(base, handlungsdruck_score)
        reason = _build_reason(
            base=base,
            final=final,
            elevated=elevated,
            benefit=expected_benefit_eur,
            composite=composite_score,
            handlungsdruck=handlungsdruck_score,
        )
        return ZoneResult(
            base_zone=base,
            final_zone=final,
            handlungsdruck_elevated=elevated,
            reason=reason,
        )

    def _base_zone(self, benefit: Decimal, composite: int) -> TriageZone:
        if benefit >= self._lw_min and composite <= self._lw_max_c:
            return TriageZone.LIKELY_WIN
        if benefit >= self._cr_min and composite <= self._cr_max_c:
            return TriageZone.CALCULATED_RISK
        return TriageZone.MARGINAL_GAIN

    def _apply_handlungsdruck(
        self, base: TriageZone, score: int
    ) -> tuple[bool, TriageZone]:
        if score < self._hd_threshold:
            return False, base
        elevated = self._ELEVATION[base]
        return elevated != base, elevated


def _build_reason(
    base: TriageZone,
    final: TriageZone,
    elevated: bool,
    benefit: Decimal,
    composite: int,
    handlungsdruck: int,
) -> str:
    parts = [
        f"Erwarteter Nutzen: {benefit:,.0f} EUR.",
        f"Composite-Score: {composite}.",
        f"Basis-Zone: {base.value}.",
    ]
    if elevated:
        parts.append(
            f"Handlungsdruck {handlungsdruck}/5 → Zone hochgestuft: "
            f"{base.value} → {final.value}."
        )
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Config loader
# Phase A: convenience factory that reads YAML.
# Phase B: the Application Service will inject config explicitly.
# ---------------------------------------------------------------------------

_DEFAULT_CONFIG_PATH: Path = (
    Path(__file__).parents[3] / "config" / "zone_thresholds.yaml"
)


def load_zone_classifier(
    config_path: Path = _DEFAULT_CONFIG_PATH,
) -> ZoneClassifier:
    """Create a ZoneClassifier from a YAML config file.

    Args:
        config_path: Path to zone_thresholds.yaml.
                     Defaults to <project_root>/config/zone_thresholds.yaml.

    Returns:
        Configured ZoneClassifier instance.

    Raises:
        FileNotFoundError: Config file not found.
        KeyError: Required key missing from config.
    """
    with config_path.open(encoding="utf-8") as f:
        cfg: dict[str, Any] = yaml.safe_load(f)

    zone = cfg["zone"]
    hd = cfg["handlungsdruck"]

    return ZoneClassifier(
        likely_win_min_benefit=Decimal(
            str(zone["likely_win"]["min_expected_benefit_eur"])
        ),
        likely_win_max_composite=int(zone["likely_win"]["max_composite_score"]),
        calculated_risk_min_benefit=Decimal(
            str(zone["calculated_risk"]["min_expected_benefit_eur"])
        ),
        calculated_risk_max_composite=int(
            zone["calculated_risk"]["max_composite_score"]
        ),
        handlungsdruck_elevation_threshold=int(hd["elevation_threshold"]),
    )
