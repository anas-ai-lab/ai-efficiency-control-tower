"""ROI / Value-Engine — deterministisch, ohne LLM-Calls (V4-Modell, SDR-0003).

Person-basierte Nutzenformel (fixierte Semantik):
  Ersparnis pro Vorgang = Zeit_ist - Zeit_ai          (darf <= 0 sein)
  Roh-Nutzen/Jahr        = Ersparnis x Vorgaenge_pro_Mitarbeiter_und_Jahr
                           x Mitarbeiterzahl x Stundensatz(Land, Level)
  Erwarteter Nutzen      = Roh-Nutzen x Verbindlichkeitsfaktor x Evidenzfaktor
  Netto-Nutzen           = Erwarteter Nutzen - jaehrliche Lizenzkosten
  Vorfilter              = Kein-Zeitgewinn-Check, dann 3 Schwellenwerte

Alle firmenspezifischen Parameter kommen per ROIConfig rein (vertraglich bedingte IP-Trennung).
Kein Hardcoding von Stundensätzen oder Schwellen im Code.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

if TYPE_CHECKING:
    from aect.domain.models import UseCaseInput

_TWO_PLACES: Final[Decimal] = Decimal("0.01")


# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ROIConfig:
    """Alle numerischen Parameter des ROI-Modells.

    Wird per load_roi_config() befüllt — nie inline konstruieren (außer in Tests).
    IP-Trennung: Stundensätze und Schwellen in TOML, nie im Code (vertraglich bedingte IP-Trennung).

    hourly_rates:     {"de": {"professional": Decimal("65"), ...}, ...}  — Keys = Country.value / EmployeeCategory.value
    evidence_factors: {"pure_estimate": 0.40, "similar_project": 0.55, "tested_piloted": 0.90}  — Keys = EvidenceLevel.value
    adoption_factors: {"voluntary": 0.50, "recommended_standard": 0.70, "fixed_process_step": 0.90}  — Keys = AdoptionType.value
    impl_cost_point_min_eur / license_cost_point_min_eur: Schwellen für die zwei
        Kostenpunkte des Composite-Aufwand-Scores ([effort_cost_points]).
    """

    hourly_rates: dict[str, dict[str, Decimal]]
    evidence_factors: dict[str, float]
    adoption_factors: dict[str, float]
    min_potential_eur: Decimal
    min_hours_per_year: float
    min_expected_benefit_eur: Decimal
    impl_cost_point_min_eur: float
    license_cost_point_min_eur: float


def _merge_config(base: dict[str, Any], overlay: dict[str, Any]) -> None:
    """Merged overlay in-place über base (Config-Layering, V4 SDR-0003 Abschnitt 5).

    Pro Top-Level-Section: sind beide Werte dicts, werden die Keys der overlay-
    Section in die base-Section gemischt (shallow) -- so ergänzen/überschreiben
    hourly_rates länderweise (Country → Levels) und Faktoren/Schwellen keyweise.
    Ansonsten ersetzt overlay den base-Wert. Fehlende Sections in overlay bleiben
    unangetastet (Platzhalter gelten weiter).
    """
    for section, value in overlay.items():
        current = base.get(section)
        if isinstance(current, dict) and isinstance(value, dict):
            current.update(value)
        else:
            base[section] = value


def load_roi_config(path: Path | None = None) -> ROIConfig:
    """Lädt ROIConfig aus config/roi_config.toml (Repo-Root), mit Config-Layering.

    Sucht standardmäßig 3 Ebenen über diesem Modul (src/aect/domain/ → Repo-Root).
    Existiert neben der Basis-Datei ein `roi_config.local.toml` (gitignored, echte
    Raten je Land x Level), wird es DARÜBER gemerged: hourly_rates länderweise,
    andere Sections optional keyweise (siehe _merge_config). Fehlt local, gelten
    die getrackten Platzhalter — das Repo bleibt aus sich heraus lauffähig.
    Für Tests ROIConfig direkt konstruieren — kein Dateisystem-Zugriff nötig.
    """
    if path is None:
        # src/aect/domain/roi.py → parents[0]=domain, [1]=aect, [2]=src, [3]=repo_root
        repo_root = Path(__file__).resolve().parents[3]
        path = repo_root / "config" / "roi_config.toml"

    with path.open("rb") as f:
        raw = tomllib.load(f)

    local_path = path.with_name("roi_config.local.toml")
    if local_path.exists():
        with local_path.open("rb") as f:
            local_raw = tomllib.load(f)
        _merge_config(raw, local_raw)

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
        # KeyError bei fehlender [effort_cost_points]-Section ist gewollt (lauter
        # Fehler statt stillem Fallback -- Lehre aus F-001).
        impl_cost_point_min_eur=float(
            raw["effort_cost_points"]["impl_cost_point_min_eur"]
        ),
        license_cost_point_min_eur=float(
            raw["effort_cost_points"]["license_cost_point_min_eur"]
        ),
    )


# ---------------------------------------------------------------------------
# Ergebnis
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ROIResult:
    """Unveränderliches Berechnungsergebnis.

    Alle monetären Werte in EUR, auf 2 Dezimalstellen gerundet.
    Invariante (property-based getestet für Ersparnis >= 0):
    expected_benefit_eur <= theoretical_potential_eur.
    hours_per_year = Gesamtstunden Organisation (Einzelersparnis × Mitarbeiterzahl).
    time_saved_per_case_hours = Zeit_ist - Zeit_ai (auch negativ möglich).
    """

    theoretical_potential_eur: Decimal  # Stundenwert × Gesamtstunden
    usage_factor: float  # Nutzungsfaktor (aus AdoptionType)
    evidence_factor: float  # Evidenzfaktor (aus EvidenceLevel)
    expected_benefit_eur: Decimal  # Potenzial × Nutzung × Evidenz (vor Lizenz)
    license_cost_annual_eur: Decimal  # Jährliche Lizenzkosten
    net_expected_benefit_eur: Decimal  # expected − license (kann negativ sein)
    hours_per_year: float  # Gesamtstunden Organisation pro Jahr
    time_saved_per_case_hours: float  # Zeit_ist − Zeit_ai (auch negativ)
    passes_prefilter: bool
    prefilter_fail_reason: str | None  # None wenn passes_prefilter is True


# ---------------------------------------------------------------------------
# Hilfsfunktionen — direkt testbar, ohne UseCaseInput
# ---------------------------------------------------------------------------


def _check_prefilter(
    theoretical_potential: Decimal,
    hours_per_year: float,
    net_expected_benefit: Decimal,
    config: ROIConfig,
) -> tuple[bool, str | None]:
    """Prüft die drei Vorfilter-Schwellen in fester Reihenfolge.

    Reihenfolge: Potenzial → Stunden → Netto-Nutzen. Erster Fail gewinnt.
    Der Kein-Zeitgewinn-Check (Ersparnis <= 0) läuft VORHER in
    _calculate_roi_values und hat Vorrang vor diesen Schwellen.
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
    time_per_case_current_hours: float,
    time_per_case_with_ai_hours: float,
    occurrences_per_employee_per_year: float,
    employees_affected: int,
    license_cost_annual_eur: float,
    adoption_type_value: str,
    evidence_level_value: str,
    config: ROIConfig,
) -> ROIResult:
    """Kernberechnung — seiteneffektfrei, deterministisch.

    Alle Argumente keyword-only (verhindert Positionsfehler bei vielen Parametern).
    Testbar ohne UseCaseInput — Tests rufen diese Funktion direkt auf.

    Ersparnis pro Vorgang = current - with_ai. Ist sie <= 0, schlägt der Vorfilter
    mit Klartext-Grund fehl (kein stilles Clamping auf 0). Unbekanntes Land oder
    Level → Stundensatz 0 → Potenzial 0 → Vorfilter schlägt fehl. Unbekannter
    Faktor-Key → Faktor 0.0 → Nutzen 0 → Vorfilter schlägt fehl.
    """
    # 0. Ersparnis pro Vorgang (darf <= 0 sein)
    saved_per_case = time_per_case_current_hours - time_per_case_with_ai_hours

    # 1. Stundensatz-Lookup (fehlendes Land/Level → 0, defensives Default)
    rate: Decimal = config.hourly_rates.get(employee_country, {}).get(
        employee_category_value, Decimal("0")
    )

    # 2. Jährliche Stunden pro Person und Gesamtstunden Organisation
    hours_per_person = saved_per_case * occurrences_per_employee_per_year
    total_hours = hours_per_person * employees_affected

    # 3. Theoretisches Potenzial (kann negativ sein, wenn saved_per_case < 0)
    potential = (Decimal(str(total_hours)) * rate).quantize(
        _TWO_PLACES, rounding=ROUND_HALF_UP
    )

    # 4. Nutzungs- und Evidenzfaktor
    usage = config.adoption_factors.get(adoption_type_value, 0.0)
    evidence = config.evidence_factors.get(evidence_level_value, 0.0)

    # 5. Erwarteter Nutzen (vor Lizenzkosten)
    expected = (potential * Decimal(str(usage)) * Decimal(str(evidence))).quantize(
        _TWO_PLACES, rounding=ROUND_HALF_UP
    )

    # 6. Lizenzkosten + Netto
    license_cost = Decimal(str(license_cost_annual_eur)).quantize(
        _TWO_PLACES, rounding=ROUND_HALF_UP
    )
    net = (expected - license_cost).quantize(_TWO_PLACES, rounding=ROUND_HALF_UP)

    # 7. Vorfilter -- Kein-Zeitgewinn-Check zuerst (Vorrang vor den Schwellen)
    passes: bool
    reason: str | None
    if saved_per_case <= 0:
        passes = False
        reason = (
            f"Kein Zeitgewinn: Vorgang mit KI ({time_per_case_with_ai_hours} h) "
            f"ist nicht schneller als heute ({time_per_case_current_hours} h)."
        )
    else:
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
        time_saved_per_case_hours=saved_per_case,
        passes_prefilter=passes,
        prefilter_fail_reason=reason,
    )


# ---------------------------------------------------------------------------
# Öffentliche API
# ---------------------------------------------------------------------------


def calculate_roi(
    input: UseCaseInput,
    config: ROIConfig,
) -> ROIResult:
    """Öffentlicher Einstiegspunkt: UseCaseInput → ROIResult.

    Mappt UseCaseInput-Felder auf _calculate_roi_values().

    occurrences_per_employee_per_year zählt, wie oft EIN Mitarbeiter den Vorgang
    pro Jahr ausführt (person-basiert, nicht Gesamtvolumen) — das Gesamtvolumen
    entsteht erst durch × affected_employees_count.

    Das Land kommt aus input.country (Country-StrEnum, lowercase) — der Wert muss
    als [hourly_rates.<land>]-Section in roi_config.toml (oder .local.toml)
    existieren. Unbekanntes Land → theoretical_potential=0 → Vorfilter-Fail.

    implementation_cost_eur fliesst hier bewusst NICHT ein: einmalige Setup-Kosten
    sind kein jaehrlicher Abzug und wuerden die Jahres-ROI-Logik verfaelschen. Sie
    werden im Composite-Aufwand-Score als Kostenpunkt beruecksichtigt (scoring).
    """
    return _calculate_roi_values(
        employee_country=input.country.value,
        employee_category_value=input.employee_category.value,
        time_per_case_current_hours=input.time_per_case_hours_current,
        time_per_case_with_ai_hours=input.time_per_case_hours_with_ai,
        occurrences_per_employee_per_year=float(
            input.occurrences_per_employee_per_year
        ),
        employees_affected=input.affected_employees_count,
        license_cost_annual_eur=input.estimated_license_cost_eur,
        adoption_type_value=input.adoption_type.value,
        evidence_level_value=input.evidence_level.value,
        config=config,
    )
