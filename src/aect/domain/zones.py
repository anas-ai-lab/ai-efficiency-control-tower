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
  the *logic* here is generic and shareable (contractual IP separation).
- Read-only properties (Tag 65) expose the injected thresholds for
  diagnostic consumers (application/eval/breakdown.py) without changing
  behavior — classify() is untouched.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, ClassVar

import yaml

from aect.domain.types import TriageZone

# Composite-Score-Wertebereich (siehe scoring.CompositeScore: Summe 2-10).
# Strukturelle Grenze der Skala, kein IP-/Business-Wert -> hier konstant,
# nicht in config. Wird nur fuer die Konfidenz-Normierung der offenen
# Randzonen (LIKELY_WIN / MARGINAL_GAIN) gebraucht.
_COMPOSITE_MIN = 2
_COMPOSITE_MAX = 10


def _confidence_label(score: float) -> str:
    """Mappt confidence_score auf ein dreistufiges Label."""
    if score >= 0.85:
        return "hoch"
    if score >= 0.70:
        return "mittel"
    return "niedrig"


@dataclass(frozen=True)
class ZoneResult:
    """Immutable result of zone classification.

    Attributes:
        base_zone: Zone before Handlungsdruck adjustment.
        final_zone: Zone after adjustment — the operative verdict.
        handlungsdruck_elevated: True only when the zone actually changed.
        reason: German-language rationale string (included in triage report).
        confidence_score: Vertrauen in die composite-basierte Einstufung,
            [0.5, 1.0]. 0.5 = direkt auf einer Zonengrenze (maximale
            Unsicherheit), 1.0 = in der Zonenmitte (maximale Sicherheit).
            Additiv -- aendert weder base_zone/final_zone noch Downstream-Logik
            (ADR-0036, known_limitations #2).
        confidence_label: "hoch" (>= 0.85) | "mittel" (>= 0.70) | "niedrig".
    """

    base_zone: TriageZone
    final_zone: TriageZone
    handlungsdruck_elevated: bool
    reason: str
    confidence_score: float
    confidence_label: str


class ZoneClassifier:
    """Classifies a use case into a triage zone.

    All thresholds are injected — never hardcoded here.
    Use load_zone_classifier() to create an instance from config.

    Args:
        likely_win_min_benefit: Minimum expected benefit (EUR) for LIKELY_WIN.
        likely_win_max_composite: Maximum composite score for LIKELY_WIN.
        calculated_risk_min_benefit: Minimum expected benefit for CALCULATED_RISK.
        calculated_risk_max_composite: Maximum composite score for CALCULATED_RISK.
        handlungsdruck_elevation_threshold: Score (1-4) at or above which
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

    @property
    def likely_win_min_benefit(self) -> Decimal:
        """Minimum expected benefit (EUR) required for LIKELY_WIN."""
        return self._lw_min

    @property
    def likely_win_max_composite(self) -> int:
        """Maximum composite score allowed for LIKELY_WIN."""
        return self._lw_max_c

    @property
    def calculated_risk_min_benefit(self) -> Decimal:
        """Minimum expected benefit (EUR) required for CALCULATED_RISK."""
        return self._cr_min

    @property
    def calculated_risk_max_composite(self) -> int:
        """Maximum composite score allowed for CALCULATED_RISK."""
        return self._cr_max_c

    @property
    def handlungsdruck_elevation_threshold(self) -> int:
        """Handlungsdruck score (1-4) at or above which elevation triggers."""
        return self._hd_threshold

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
            handlungsdruck_score: Urgency on a 1-4 integer scale.

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
        score, label = self._confidence(base, composite_score)
        return ZoneResult(
            base_zone=base,
            final_zone=final,
            handlungsdruck_elevated=elevated,
            reason=reason,
            confidence_score=score,
            confidence_label=label,
        )

    def _confidence(self, base: TriageZone, composite: int) -> tuple[float, str]:
        """Konfidenz der composite-basierten Zonen-Einstufung in [0.5, 1.0].

        Misst den Abstand des composite_score zur naechsten Zonengrenze auf der
        Composite-Achse, normiert auf die halbe Zonenbreite:

            score = 0.5 + min(distance / half_width, 1.0) * 0.5

        Grenzwerte: 0.5 direkt auf der Grenze (maximale Unsicherheit), 1.0 in
        der Zonenmitte. distance wird auf >= 0 geklemmt -- so bleibt der Score
        auch dann in [0.5, 1.0], wenn die Zone NICHT vom composite, sondern vom
        expected_benefit bestimmt wurde (dann liegt composite ausserhalb des
        zonen-typischen Bandes -> distance < 0 -> Score 0.5 = unsicher).

        Bewusst eindimensional (nur composite): adressiert die Off-by-one-
        Brittleness an den Composite-Grenzen. Die Benefit-Achse bleibt offen --
        siehe ADR-0036 und known_limitations #2.

        Die Konfidenz bezieht sich auf base_zone (reine benefit/composite-
        Einstufung). Die Handlungsdruck-Hochstufung ist ein separates,
        deterministisches Signal (handlungsdruck_elevated).
        """
        b1 = self._lw_max_c  # Grenze LIKELY_WIN | CALCULATED_RISK
        b2 = self._cr_max_c  # Grenze CALCULATED_RISK | MARGINAL_GAIN
        if base == TriageZone.LIKELY_WIN:
            distance = float(b1 - composite)
            half_width = (b1 - _COMPOSITE_MIN) / 2
        elif base == TriageZone.CALCULATED_RISK:
            distance = float(min(composite - b1, b2 - composite))
            half_width = (b2 - b1) / 2
        else:  # MARGINAL_GAIN
            distance = float(composite - b2)
            half_width = (_COMPOSITE_MAX - b2) / 2

        ratio = 0.0 if half_width <= 0 else min(max(distance, 0.0) / half_width, 1.0)
        score = round(0.5 + ratio * 0.5, 2)
        return score, _confidence_label(score)

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
            f"Handlungsdruck {handlungsdruck}/4 → Zone hochgestuft: "
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
