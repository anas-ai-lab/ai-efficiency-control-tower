"""Generiert synthetische Eval-Cases fuer den Volumen-/Crash-Test des
Eval-Runners (Master-Plan v3.1 Phase E, Gate E->F: >= 30 Cases ohne Crash).

Bewusst unlabeled (expected_zone=None fuer alle Cases): der Experten-Abgleich
laeuft ueber die von Hand kuratierten Golden-Cases (Tag 64); diese
Synthetic-Cases testen Schema-Abdeckung, Wertebereich-Grenzen und
Konsistenz-Verhalten der Pipeline ueber ein breiteres Eingabe-Spektrum, nicht
Korrektheit gegen menschliches Urteil. Die Pipeline-eigene Vorhersage als
"Soll-Wert" einzutragen waere zirkulaer und wuerde nichts pruefen
(EvalCase.expected_zone-Docstring, ADR-0029).

30 Cases aus einem 5x6-Raster (5 Domaenen-Templates x 6 quantitative
Varianten, die jeweils auf einen anderen Bereich der Vorfilter-/Zonen-Logik
zielen), plus 6 explizite Grenzwert-Cases (Min/Max der numerischen Felder,
Text-Laengen-Grenze, MIXED-Kategorie) -- insgesamt 36 Cases.

V4-Eingabemodell (SDR-0003): person-basierte Zeit-Semantik
(time_per_case_hours_current/-with_ai, occurrences_per_employee_per_year) und
implementation_approach (5 Stufen, Komplexitaet daraus abgeleitet -- kein
separates implementation_complexity-Feld mehr).

Aufruf:
    uv run python scripts/generate_synthetic_cases.py
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aect.application.eval import EvalCase
from aect.domain import UseCaseInput
from aect.domain.types import (
    AdoptionType,
    Country,
    DataClassification,
    EmployeeCategory,
    EvidenceLevel,
    ImplementationApproach,
)

REPO_ROOT = Path(__file__).parent.parent
OUTPUT_PATH = REPO_ROOT / "evals" / "synthetic" / "use_cases.jsonl"

# ---------------------------------------------------------------------------
# 5 Domaenen-Templates -- liefern Stammdaten + Prozessbeschreibung.
# Quantitative Werte und Enums kommen aus den VARIANTS (Raster-Multiplikation).
# ---------------------------------------------------------------------------
TEMPLATES: list[dict[str, str]] = [
    {
        "key": "hr",
        "department": "Personalwesen",
        "title": "Bewerbungsunterlagen-Vorpruefung automatisieren",
        "current_state": (
            "HR-Sachbearbeiter sichten eingehende Bewerbungsunterlagen manuell "
            "auf Vollstaendigkeit und gleichen sie gegen die Stellenanforderungen ab."
        ),
        "desired_state": (
            "Ein System prueft Bewerbungsunterlagen automatisch auf Vollstaendigkeit "
            "und markiert die Passung zu den Stellenanforderungen vor."
        ),
        "example_process": (
            "Eine Bewerbung mit Anschreiben, Lebenslauf und Zeugnissen wird "
            "gegen die Anforderungen der Stellenausschreibung abgeglichen."
        ),
    },
    {
        "key": "it",
        "department": "IT-Betrieb",
        "title": "Logfile-Anomalien automatisiert markieren",
        "current_state": (
            "IT-Mitarbeiter sichten taeglich Systemlogs manuell, um ungewoehnliche "
            "Muster oder Fehlerhaeufungen zu erkennen, bevor sie eskalieren."
        ),
        "desired_state": (
            "Ein System markiert auffaellige Logfile-Muster automatisch und "
            "liefert eine priorisierte Liste statt der vollstaendigen Logs."
        ),
        "example_process": (
            "Die taeglichen Logs eines Produktionsservers werden gesichtet, "
            "eine Haeufung von Timeout-Fehlern wird markiert."
        ),
    },
    {
        "key": "finance",
        "department": "Finanzen",
        "title": "Spesenabrechnungen automatisiert pruefen",
        "current_state": (
            "Mitarbeiter der Buchhaltung pruefen eingereichte Spesenabrechnungen "
            "manuell gegen die Reisekostenrichtlinie und Belegvorgaben."
        ),
        "desired_state": (
            "Ein System prueft Spesenabrechnungen automatisch gegen die Richtlinie "
            "und markiert Abweichungen fuer die manuelle Nachpruefung."
        ),
        "example_process": (
            "Eine Spesenabrechnung mit drei Belegen wird gegen die "
            "Reisekostenrichtlinie abgeglichen, ein Beleg ueberschreitet das Limit."
        ),
    },
    {
        "key": "legal",
        "department": "Rechtsabteilung",
        "title": "Vertragsfristen automatisiert ueberwachen",
        "current_state": (
            "Juristen pflegen Vertragsfristen manuell in einer Tabelle und "
            "pruefen woechentlich, welche Fristen in den naechsten 30 Tagen ablaufen."
        ),
        "desired_state": (
            "Ein System extrahiert Fristen aus Vertragsdokumenten automatisch "
            "und erinnert rechtzeitig vor Ablauf."
        ),
        "example_process": (
            "Ein neuer Liefervertrag wird hochgeladen, die Kuendigungsfrist "
            "wird erkannt und im Fristenkalender hinterlegt."
        ),
    },
    {
        "key": "procurement",
        "department": "Einkauf",
        "title": "Bestellanforderungen automatisiert kategorisieren",
        "current_state": (
            "Einkaeufer lesen eingehende Bestellanforderungen manuell und ordnen "
            "sie einer von acht Warengruppen fuer die weitere Bearbeitung zu."
        ),
        "desired_state": (
            "Ein System kategorisiert Bestellanforderungen automatisch nach "
            "Warengruppe und leitet sie an den zustaendigen Einkaeufer weiter."
        ),
        "example_process": (
            "Eine Anforderung fuer 50 Buerostuehle wird gelesen und der "
            "Warengruppe Bueromoebel zugeordnet."
        ),
    },
]

# ---------------------------------------------------------------------------
# 6 quantitative/Enum-Varianten -- jede zielt auf einen anderen Bereich der
# Vorfilter-/Zonen-/Handlungsdruck-Logik (config/zone_thresholds.yaml,
# config/roi_config.toml). Kein Soll-Zone-Wert -- siehe Modul-Docstring.
#
# V4: time_per_case_hours_current ist der Aufwand heute, time_per_case_hours_
# with_ai der Restaufwand mit AI (Ersparnis = Differenz). occurrences_per_
# employee_per_year zaehlt person-basiert. implementation_approach ersetzt das
# alte implementation_complexity-Feld (Komplexitaet daraus abgeleitet).
# ---------------------------------------------------------------------------
VARIANTS: list[dict[str, Any]] = [
    {
        "suffix": "Mini-Volumen",
        "time_per_case_hours_current": 0.2,
        "time_per_case_hours_with_ai": 0.0,
        "occurrences_per_employee_per_year": 20,
        "affected_employees_count": 1,
        "employee_category": EmployeeCategory.JUNIOR,
        "evidence_level": EvidenceLevel.PURE_ESTIMATE,
        "adoption_type": AdoptionType.VOLUNTARY,
        "implementation_approach": ImplementationApproach.SIMPLE_INTEGRATION,
        "estimated_license_cost_eur": 0.0,
        "contains_pii": False,
        "data_classification": DataClassification.NO_PERSONAL_DATA,
        "regulatory_pressure": False,
        "competitive_pressure": False,
        "strategic_priority": False,
        "notes": "Zielt klar unter alle Vorfilter-Schwellen (Stunden/Jahr, Potenzial).",
    },
    {
        "suffix": "Marginal-Profil",
        "time_per_case_hours_current": 1.0,
        "time_per_case_hours_with_ai": 0.0,
        "occurrences_per_employee_per_year": 150,
        "affected_employees_count": 2,
        "employee_category": EmployeeCategory.JUNIOR,
        "evidence_level": EvidenceLevel.PURE_ESTIMATE,
        "adoption_type": AdoptionType.VOLUNTARY,
        "implementation_approach": ImplementationApproach.CUSTOM_DEVELOPMENT,
        "estimated_license_cost_eur": 5000.0,
        "contains_pii": True,
        "data_classification": DataClassification.PERSONAL,
        "regulatory_pressure": False,
        "competitive_pressure": False,
        "strategic_priority": False,
        "notes": "Besteht Vorfilter knapp, hohe Komplexitaet haelt Composite-Score oben.",
    },
    {
        "suffix": "Basis-Risiko",
        "time_per_case_hours_current": 2.0,
        "time_per_case_hours_with_ai": 0.0,
        "occurrences_per_employee_per_year": 500,
        "affected_employees_count": 5,
        "employee_category": EmployeeCategory.PROFESSIONAL,
        "evidence_level": EvidenceLevel.SIMILAR_PROJECT,
        "adoption_type": AdoptionType.FIXED_PROCESS_STEP,
        "implementation_approach": ImplementationApproach.API_INTEGRATION,
        "estimated_license_cost_eur": 10000.0,
        "contains_pii": False,
        "data_classification": DataClassification.PSEUDONYMOUS,
        "regulatory_pressure": False,
        "competitive_pressure": False,
        "strategic_priority": False,
        "notes": "Mittleres Profil ohne Handlungsdruck-Flags -- Basis-Zonen-Pfad.",
    },
    {
        "suffix": "Hochstufung-Test",
        "time_per_case_hours_current": 1.5,
        "time_per_case_hours_with_ai": 0.0,
        "occurrences_per_employee_per_year": 400,
        "affected_employees_count": 4,
        "employee_category": EmployeeCategory.SENIOR,
        "evidence_level": EvidenceLevel.PURE_ESTIMATE,
        "adoption_type": AdoptionType.VOLUNTARY,
        "implementation_approach": ImplementationApproach.CUSTOM_DEVELOPMENT,
        "estimated_license_cost_eur": 0.0,
        "contains_pii": True,
        "data_classification": DataClassification.SENSITIVE_PERSONAL,
        "regulatory_pressure": True,
        "competitive_pressure": True,
        "strategic_priority": True,
        "notes": "Alle drei Handlungsdruck-Flags gesetzt -- testet die Zonen-Hochstufung.",
    },
    {
        "suffix": "Solide-Win",
        "time_per_case_hours_current": 4.0,
        "time_per_case_hours_with_ai": 0.0,
        "occurrences_per_employee_per_year": 800,
        "affected_employees_count": 8,
        "employee_category": EmployeeCategory.PROFESSIONAL,
        "evidence_level": EvidenceLevel.TESTED_PILOTED,
        "adoption_type": AdoptionType.FIXED_PROCESS_STEP,
        "implementation_approach": ImplementationApproach.DEVELOPMENT_ON_EXISTING,
        "estimated_license_cost_eur": 8000.0,
        "contains_pii": False,
        "data_classification": DataClassification.NO_PERSONAL_DATA,
        "regulatory_pressure": False,
        "competitive_pressure": False,
        "strategic_priority": False,
        "notes": "Hoher Nutzen, niedrige Komplexitaet -- klarer Basis-Win-Pfad.",
    },
    {
        "suffix": "Hochvolumen-Win",
        "time_per_case_hours_current": 0.15,
        "time_per_case_hours_with_ai": 0.0,
        "occurrences_per_employee_per_year": 60000,
        "affected_employees_count": 20,
        "employee_category": EmployeeCategory.JUNIOR,
        "evidence_level": EvidenceLevel.TESTED_PILOTED,
        "adoption_type": AdoptionType.FIXED_PROCESS_STEP,
        "implementation_approach": ImplementationApproach.DEVELOPMENT_ON_EXISTING,
        "estimated_license_cost_eur": 15000.0,
        "contains_pii": False,
        "data_classification": DataClassification.NO_PERSONAL_DATA,
        "regulatory_pressure": False,
        "competitive_pressure": True,
        "strategic_priority": False,
        "notes": "Sehr hohe Frequenz bei winziger Zeitersparnis/Fall -- Hochrechnungs-Pfad.",
    },
]


def _build_grid_cases() -> list[EvalCase]:
    cases: list[EvalCase] = []
    idx = 1
    for template in TEMPLATES:
        for variant in VARIANTS:
            use_case = UseCaseInput(
                title=f"{template['title']} ({variant['suffix']})",
                submitter="Synthetic Case Generator",
                department=template["department"],
                country=Country.DE,
                current_state=template["current_state"],
                desired_state=template["desired_state"],
                example_process=template["example_process"],
                time_per_case_hours_current=variant["time_per_case_hours_current"],
                time_per_case_hours_with_ai=variant["time_per_case_hours_with_ai"],
                occurrences_per_employee_per_year=variant[
                    "occurrences_per_employee_per_year"
                ],
                affected_employees_count=variant["affected_employees_count"],
                employee_category=variant["employee_category"],
                evidence_level=variant["evidence_level"],
                adoption_type=variant["adoption_type"],
                implementation_approach=variant["implementation_approach"],
                estimated_license_cost_eur=variant["estimated_license_cost_eur"],
                contains_pii=variant["contains_pii"],
                data_classification=variant["data_classification"],
                regulatory_pressure=variant["regulatory_pressure"],
                competitive_pressure=variant["competitive_pressure"],
                strategic_priority=variant["strategic_priority"],
            )
            cases.append(
                EvalCase(
                    case_id=f"synthetic-{idx:03d}",
                    use_case=use_case,
                    expected_zone=None,
                    notes=f"{template['key']}/{variant['suffix']}: {variant['notes']}",
                )
            )
            idx += 1
    return cases


def _build_edge_cases() -> list[EvalCase]:
    """6 explizite Grenzwert-Cases -- Min/Max der numerischen Felder und
    Text-Laengen-Grenzen. Nutzt das HR-Template als neutrale Basis."""
    base = TEMPLATES[0]
    edge_specs: list[dict[str, Any]] = [
        {
            "suffix": "Max-Werte",
            "time_per_case_hours_current": 8.0,
            "time_per_case_hours_with_ai": 0.0,
            "occurrences_per_employee_per_year": 1_000_000,
            "affected_employees_count": 50_000,
            "employee_category": EmployeeCategory.PROFESSIONAL,
            "evidence_level": EvidenceLevel.TESTED_PILOTED,
            "adoption_type": AdoptionType.FIXED_PROCESS_STEP,
            "implementation_approach": ImplementationApproach.NEW_TOOL,
            "estimated_license_cost_eur": 10_000_000.0,
            "contains_pii": True,
            "data_classification": DataClassification.SENSITIVE_PERSONAL,
            "regulatory_pressure": True,
            "competitive_pressure": True,
            "strategic_priority": True,
            "notes": "Obergrenze aller numerischen Felder gleichzeitig.",
        },
        {
            "suffix": "Min-Werte",
            "time_per_case_hours_current": 0.01,
            "time_per_case_hours_with_ai": 0.0,
            "occurrences_per_employee_per_year": 1,
            "affected_employees_count": 1,
            "employee_category": EmployeeCategory.JUNIOR,
            "evidence_level": EvidenceLevel.PURE_ESTIMATE,
            "adoption_type": AdoptionType.VOLUNTARY,
            "implementation_approach": ImplementationApproach.SIMPLE_INTEGRATION,
            "estimated_license_cost_eur": 0.0,
            "contains_pii": False,
            "data_classification": DataClassification.NO_PERSONAL_DATA,
            "regulatory_pressure": False,
            "competitive_pressure": False,
            "strategic_priority": False,
            "notes": "Untergrenze aller numerischen Felder gleichzeitig.",
        },
        {
            "suffix": "Mixed-Kategorie",
            "time_per_case_hours_current": 3.0,
            "time_per_case_hours_with_ai": 0.0,
            "occurrences_per_employee_per_year": 1000,
            "affected_employees_count": 12,
            "employee_category": EmployeeCategory.PROFESSIONAL,
            "evidence_level": EvidenceLevel.SIMILAR_PROJECT,
            "adoption_type": AdoptionType.FIXED_PROCESS_STEP,
            "implementation_approach": ImplementationApproach.API_INTEGRATION,
            "estimated_license_cost_eur": 20000.0,
            "contains_pii": False,
            "data_classification": DataClassification.PSEUDONYMOUS,
            "regulatory_pressure": False,
            "competitive_pressure": False,
            "strategic_priority": False,
            "notes": "MIXED-Kategorie wird in keiner Raster-Variante abgedeckt.",
        },
        {
            "suffix": "Kurztitel",
            "time_per_case_hours_current": 2.5,
            "time_per_case_hours_with_ai": 0.0,
            "occurrences_per_employee_per_year": 300,
            "affected_employees_count": 3,
            "employee_category": EmployeeCategory.PROFESSIONAL,
            "evidence_level": EvidenceLevel.PURE_ESTIMATE,
            "adoption_type": AdoptionType.VOLUNTARY,
            "implementation_approach": ImplementationApproach.DEVELOPMENT_ON_EXISTING,
            "estimated_license_cost_eur": 0.0,
            "contains_pii": False,
            "data_classification": DataClassification.NO_PERSONAL_DATA,
            "regulatory_pressure": False,
            "competitive_pressure": False,
            "strategic_priority": False,
            "notes": "Titel an der min_length=5-Grenze.",
            "title_override": "HR-KI",
        },
        {
            "suffix": "Kostenloser-Vendor",
            "time_per_case_hours_current": 1.2,
            "time_per_case_hours_with_ai": 0.0,
            "occurrences_per_employee_per_year": 250,
            "affected_employees_count": 3,
            "employee_category": EmployeeCategory.PROFESSIONAL,
            "evidence_level": EvidenceLevel.SIMILAR_PROJECT,
            "adoption_type": AdoptionType.FIXED_PROCESS_STEP,
            "implementation_approach": ImplementationApproach.DEVELOPMENT_ON_EXISTING,
            "estimated_license_cost_eur": 0.0,
            "contains_pii": False,
            "data_classification": DataClassification.NO_PERSONAL_DATA,
            "regulatory_pressure": False,
            "competitive_pressure": False,
            "strategic_priority": False,
            "notes": "Zugekaufte Loesung mit Lizenzkosten = 0 (z.B. Open-Source).",
        },
        {
            "suffix": "Druck-trotz-Mini",
            "time_per_case_hours_current": 0.3,
            "time_per_case_hours_with_ai": 0.0,
            "occurrences_per_employee_per_year": 30,
            "affected_employees_count": 1,
            "employee_category": EmployeeCategory.JUNIOR,
            "evidence_level": EvidenceLevel.PURE_ESTIMATE,
            "adoption_type": AdoptionType.VOLUNTARY,
            "implementation_approach": ImplementationApproach.SIMPLE_INTEGRATION,
            "estimated_license_cost_eur": 0.0,
            "contains_pii": False,
            "data_classification": DataClassification.NO_PERSONAL_DATA,
            "regulatory_pressure": True,
            "competitive_pressure": True,
            "strategic_priority": True,
            "notes": (
                "Alle Handlungsdruck-Flags trotz Mini-Volumen -- prueft, dass "
                "Handlungsdruck einen gescheiterten Vorfilter nicht uebersteuert."
            ),
        },
    ]

    cases: list[EvalCase] = []
    for i, spec in enumerate(edge_specs, start=31):
        use_case = UseCaseInput(
            title=spec.get("title_override", f"{base['title']} ({spec['suffix']})"),
            submitter="Synthetic Case Generator",
            department=base["department"],
            country=Country.DE,
            current_state=base["current_state"],
            desired_state=base["desired_state"],
            example_process=base["example_process"],
            time_per_case_hours_current=spec["time_per_case_hours_current"],
            time_per_case_hours_with_ai=spec["time_per_case_hours_with_ai"],
            occurrences_per_employee_per_year=spec["occurrences_per_employee_per_year"],
            affected_employees_count=spec["affected_employees_count"],
            employee_category=spec["employee_category"],
            evidence_level=spec["evidence_level"],
            adoption_type=spec["adoption_type"],
            implementation_approach=spec["implementation_approach"],
            estimated_license_cost_eur=spec["estimated_license_cost_eur"],
            contains_pii=spec["contains_pii"],
            data_classification=spec["data_classification"],
            regulatory_pressure=spec["regulatory_pressure"],
            competitive_pressure=spec["competitive_pressure"],
            strategic_priority=spec["strategic_priority"],
        )
        cases.append(
            EvalCase(
                case_id=f"synthetic-{i:03d}",
                use_case=use_case,
                expected_zone=None,
                notes=f"edge/{spec['suffix']}: {spec['notes']}",
            )
        )
    return cases


def main() -> None:
    cases = _build_grid_cases() + _build_edge_cases()

    case_ids = [c.case_id for c in cases]
    assert len(case_ids) == len(set(case_ids)), "case_id-Kollision im Generator"

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        for case in cases:
            f.write(case.model_dump_json())
            f.write("\n")

    print(f"{len(cases)} synthetische Cases geschrieben: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
