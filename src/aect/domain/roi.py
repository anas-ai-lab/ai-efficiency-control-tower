"""ROI / Value-Engine — deterministisch, ohne LLM-Calls.

Implementiert das v5-Bewertungsmodell:
  Theoretisches Potenzial  = Stundenwert × Zeit_pro_Vorgang × Jahres-Multiplikator
                             × Mitarbeiterzahl
  Erwarteter Nutzen        = Potenzial × Nutzungsfaktor × Evidenzfaktor
  Netto-Nutzen             = Erwarteter Nutzen − Lizenzkosten
  Vorfilter                = 3 Schwellenwerte (Potenzial, Stunden, Netto-Nutzen)

Alle firmenspezifischen Parameter kommen per ROIConfig rein (interne Referenz (entfernt) §5).
Kein Hardcoding von Stundensätzen oder Schwellen im Code.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from aect.domain.models import UseCaseInput

# ---------------------------------------------------------------------------
# Frequenz → Jahres-Multiplikator
# Keys = FrequencyUnit.value aus src/aect/domain/types.py
# Nach Schritt 0: prüfen ob die Enum-Werte stimmen, ggf. Keys anpassen.
# ---------------------------------------------------------------------------
_FREQUENCY_TO_ANNUAL: Final[dict[str, int]] = {
    "DAILY": 250,  # Arbeitstage pro Jahr
    "WEEKLY": 52,
    "BIWEEKLY": 26,
    "MONTHLY": 12,
    "QUARTERLY": 4,
    "ANNUALLY": 1,
}

_TWO_PLACES: Final[Decimal] = Decimal("0.01")


# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ROIConfig:
    """Alle numerischen Parameter des ROI-Modells.

    Wird per load_roi_config() befüllt — nie inline konstruieren (außer in Tests).
    IP-Trennung: Stundensätze und Schwellen in TOML, nie im Code (interne Referenz (entfernt) §5).

    hourly_rates:     {"DE": {"PROFESSIONAL": Decimal("65"), ...}, ...}
    evidence_factors: {"HIGH": 1.0, "MEDIUM": 0.75, ...}  — Keys = EvidenceLevel.value
    adoption_factors: {"HIGH": 1.0, "MEDIUM": 0.60, ...}  — Keys = AdoptionType.value
    """

    hourly_rates: dict[str, dict[str, Decimal]]
    evidence_factors: dict[str, float]
    adoption_factors: dict[str, float]
    min_potential_eur: Decimal
    min_hours_per_year: float
    min_expected_benefit_eur: Decimal


def load_roi_config(path: Path | None = None) -> ROIConfig:
    """Lädt ROIConfig aus config/roi_config.toml (Repo-Root).

    Sucht standardmäßig 3 Ebenen über diesem Modul (src/aect/domain/ → Repo-Root).
    Für Tests ROIConfig direkt konstruieren — kein Dateisystem-Zugriff nötig.
    """
    if path is None:
        # src/aect/domain/roi.py → parents[0]=domain, [1]=aect, [2]=src, [3]=repo_root
        repo_root = Path(__file__).resolve().parents[3]
        path = repo_root / "config" / "roi_config.toml"

    with path.open("rb") as f:
        raw = tomllib.load(f)

    return ROIConfig(
        hourly_rates={
            country: {lvl: Decimal(str(rate)) for lvl, rate in rates.items()}
            for country, rates in raw["hourly_rates"].items()
        },
        evidence_factors={k: float(v) for k, v in raw["evidence_factors"].items()},
        adoption_factors={k: float(v) for k, v in raw["adoption_factors"].items()},
        min_potential_eur=Decimal(str(raw["thresholds"]["min_potential_eur"])),
        min_hours_per_year=float(raw["thresholds"]["min_hours_per_year"]),
        min_expected_benefit_eur=Decimal(
            str(raw["thresholds"]["min_expected_benefit_eur"])
        ),
    )


# ---------------------------------------------------------------------------
# Ergebnis
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ROIResult:
    """Unveränderliches Berechnungsergebnis.

    Alle monetären Werte in EUR, auf 2 Dezimalstellen gerundet.
    Invariante (property-based getestet): expected_benefit_eur <= theoretical_potential_eur.
    hours_per_year = Gesamtstunden Organisation (Einzelersparnis × Mitarbeiterzahl).
    """

    theoretical_potential_eur: Decimal  # Stundenwert × Gesamtstunden
    usage_factor: float  # Nutzungsfaktor (aus AdoptionType)
    evidence_factor: float  # Evidenzfaktor (aus EvidenceLevel)
    expected_benefit_eur: Decimal  # Potenzial × Nutzung × Evidenz (vor Lizenz)
    license_cost_annual_eur: Decimal  # Jährliche Lizenzkosten
    net_expected_benefit_eur: Decimal  # expected − license (kann negativ sein)
    hours_per_year: float  # Gesamtstunden Organisation pro Jahr
    passes_prefilter: bool
    prefilter_fail_reason: str | None  # None wenn passes_prefilter is True


# ---------------------------------------------------------------------------
# Hilfsfunktionen — direkt testbar, ohne UseCaseInput
# ---------------------------------------------------------------------------


def _to_annual_hours(
    time_per_occurrence: float,
    occurrences_per_period: float,
    frequency_unit_value: str,
) -> float:
    """Rechnet Häufigkeit in jährliche Stunden (pro Person) um.

    Args:
        time_per_occurrence: Zeitersparnis pro Vorgang in Stunden.
        occurrences_per_period: Vorgänge pro Periode (z. B. pro Woche).
        frequency_unit_value: FrequencyUnit.value (z. B. "WEEKLY").

    Raises:
        ValueError: Bei unbekanntem frequency_unit_value.
    """
    multiplier = _FREQUENCY_TO_ANNUAL.get(frequency_unit_value)
    if multiplier is None:
        msg = (
            f"Unbekannte FrequencyUnit: {frequency_unit_value!r}. "
            f"Gültige Werte: {sorted(_FREQUENCY_TO_ANNUAL)}"
        )
        raise ValueError(msg)
    return time_per_occurrence * occurrences_per_period * multiplier


def _check_prefilter(
    theoretical_potential: Decimal,
    hours_per_year: float,
    net_expected_benefit: Decimal,
    config: ROIConfig,
) -> tuple[bool, str | None]:
    """Prüft die drei Vorfilter-Bedingungen in fester Reihenfolge.

    Reihenfolge: Potenzial → Stunden → Netto-Nutzen. Erster Fail gewinnt.
    Returns: (passes, fail_reason) — reason ist None wenn passes=True.
    """
    if theoretical_potential < config.min_potential_eur:
        return False, (
            f"Theoretisches Potenzial {theoretical_potential} EUR "
            f"< Schwelle {config.min_potential_eur} EUR"
        )
    if hours_per_year < config.min_hours_per_year:
        return False, (
            f"Jährliche Stunden {hours_per_year:.1f} "
            f"< Schwelle {config.min_hours_per_year:.1f}"
        )
    if net_expected_benefit < config.min_expected_benefit_eur:
        return False, (
            f"Netto-Nutzen {net_expected_benefit} EUR "
            f"< Schwelle {config.min_expected_benefit_eur} EUR"
        )
    return True, None


def _calculate_roi_values(
    *,
    employee_country: str,
    employee_category_value: str,
    time_saved_per_occurrence_hours: float,
    occurrences_per_period: float,
    frequency_unit_value: str,
    employees_affected: int,
    license_cost_annual_eur: float,
    adoption_type_value: str,
    evidence_level_value: str,
    config: ROIConfig,
) -> ROIResult:
    """Kernberechnung — seiteneffektfrei, deterministisch.

    Alle Argumente keyword-only (verhindert Positionsfehler bei vielen Parametern).
    Testbar ohne UseCaseInput — Tests rufen diese Funktion direkt auf.

    Unbekanntes Land oder Level → Stundensatz 0 → Potenzial 0 → Vorfilter schlägt fehl.
    Unbekannter Faktor-Key → Faktor 0.0 → Nutzen 0 → Vorfilter schlägt fehl.
    """
    # 1. Stundensatz-Lookup (fehlendes Land/Level → 0, defensives Default)
    rate: Decimal = config.hourly_rates.get(employee_country, {}).get(
        employee_category_value, Decimal("0")
    )

    # 2. Jährliche Stunden pro Person
    hours_per_person = _to_annual_hours(
        time_per_occurrence=time_saved_per_occurrence_hours,
        occurrences_per_period=occurrences_per_period,
        frequency_unit_value=frequency_unit_value,
    )

    # 3. Gesamtstunden Organisation (für Potenzial und Vorfilter)
    total_hours = hours_per_person * employees_affected

    # 4. Theoretisches Potenzial
    potential = (Decimal(str(total_hours)) * rate).quantize(
        _TWO_PLACES, rounding=ROUND_HALF_UP
    )

    # 5. Nutzungs- und Evidenzfaktor
    usage = config.adoption_factors.get(adoption_type_value, 0.0)
    evidence = config.evidence_factors.get(evidence_level_value, 0.0)

    # 6. Erwarteter Nutzen (vor Lizenzkosten)
    expected = (potential * Decimal(str(usage)) * Decimal(str(evidence))).quantize(
        _TWO_PLACES, rounding=ROUND_HALF_UP
    )

    # 7. Lizenzkosten + Netto
    license_cost = Decimal(str(license_cost_annual_eur)).quantize(
        _TWO_PLACES, rounding=ROUND_HALF_UP
    )
    net = (expected - license_cost).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)

    # 8. Vorfilter
    passes, reason = _check_prefilter(
        theoretical_potential=potential,
        hours_per_year=total_hours,
        net_expected_benefit=net,
        config=config,
    )

    return ROIResult(
        theoretical_potential_eur=potential,
        usage_factor=usage,
        evidence_factor=evidence,
        expected_benefit_eur=expected,
        license_cost_annual_eur=license_cost,
        net_expected_benefit_eur=net,
        hours_per_year=total_hours,
        passes_prefilter=passes,
        prefilter_fail_reason=reason,
    )


# ---------------------------------------------------------------------------
# Öffentliche API
# ---------------------------------------------------------------------------


def calculate_roi(input: UseCaseInput, config: ROIConfig) -> ROIResult:
    """Öffentlicher Einstiegspunkt: UseCaseInput → ROIResult.

    TODO: Adapter-Implementierung nach Schritt 0 (Feldnamen aus models.py verifizieren).
    Erwartete Felder: employee_country, employee_category, time_saved_per_occurrence_hours,
    occurrences_per_period, frequency_unit, employees_affected, license_cost_annual_eur,
    adoption_type, evidence_level.
    NotImplementedError entfernen und Feldnamen eintragen sobald verifiziert.
    """
    raise NotImplementedError(
        "calculate_roi-Adapter: Feldnamen aus models.py in Schritt 0 prüfen, "
        "dann _calculate_roi_values(...) mit den echten Feldnamen aufrufen."
    )
