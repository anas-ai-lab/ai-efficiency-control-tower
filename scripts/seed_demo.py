"""Legt deterministisch generische Demo-Cases in einer SQLite-DB an (V4-P4).

Zweck: eine reproduzierbare Datenbasis fuer den Demo-Build (interner Vorgesetzter)
-- Portfolio-Read (/cases), Board-Matrix (/board) und Monitoring haben sofort
Inhalt, ohne dass jemand das Intake-Formular neun Mal ausfuellt.

Eigenschaften (bewusst so gewaehlt):
  - 9 GENERISCHE Cases, kein Firmenbezug (IP-Trennung: keine echten Cases,
    Plattform-Namen oder Zahlen -- rein illustrative Prozesse).
  - verteilt ueber Zonen (LIKELY_WIN / CALCULATED_RISK / MARGINAL_GAIN),
    Laender (de/at/ch), Status (submitted/in_review/approved/implemented) und
    Datenschutzklassen (no_personal_data/pseudonymous/personal/sensitive).
  - demo-006 hat ein negatives Zeitdelta (Zeit mit AI > heute) -> der Vorfilter
    lehnt ab, im UI sichtbar als Fall ohne Zone.
  - demo-002 (Composite genau 4) und demo-007 (Composite genau 7) liegen exakt
    auf einer Zonengrenze -- Konfidenz-Score entsprechend niedrig.
  - demo-008 zeigt die Handlungsdruck-Hochstufung (Basis CALCULATED_RISK, durch
    alle drei Druck-Flags nach LIKELY_WIN gehoben).

KEIN Azure-Call: die LLM-Felder (Schaerfung, Loesungsvorschlag, Compliance,
Skizze) bleiben leer -- der Seed nutzt nur die deterministische Regel-Pipeline.

DB-Pfad: --db-path oder Umgebungsvariable AECT_DB_PATH, sonst Repo-Root
`aect_demo.db` (gitignored). Kein Migrations-Framework (Demo-Build): --reset
loescht die DB-Datei vorher (dokumentierter Reset, SDR-0003 / V4-P4).

Aufruf:
    uv run python scripts/seed_demo.py            # anlegen/ergaenzen
    uv run python scripts/seed_demo.py --reset    # DB vorher loeschen
    AECT_DB_PATH=data/demo.db uv run python scripts/seed_demo.py --reset
"""

from __future__ import annotations

import argparse
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from aect.adapters.sqlite.repository import SQLiteRepository
from aect.application.models import SubmittedCase
from aect.domain import (
    AdoptionType,
    CaseStatus,
    Country,
    DataClassification,
    EmployeeCategory,
    EvidenceLevel,
    ImplementationApproach,
    UseCaseInput,
    evaluate_use_case,
    load_roi_config,
)

REPO_ROOT = Path(__file__).parent.parent
_DEFAULT_DB_PATH = REPO_ROOT / "aect_demo.db"

# Fester Ausgangszeitpunkt -> deterministische, reproduzierbare Zeitstempel.
_BASE_TS = datetime(2026, 6, 1, 9, 0, 0, tzinfo=UTC)


# ---------------------------------------------------------------------------
# Case-Spezifikationen -- generisch, kein Firmenbezug.
# status: Ziel-Lifecycle-Status (submitted braucht kein update_status).
# ---------------------------------------------------------------------------
_SPECS: list[dict[str, Any]] = [
    {
        "id": "demo-001",
        "status": CaseStatus.APPROVED,
        "use_case": {
            "title": "Eingangsrechnungen automatisch vorpruefen",
            "submitter": "Demo Einreicher",
            "department": "Finanzbuchhaltung",
            "country": Country.DE,
            "current_state": (
                "Sachbearbeiter pruefen eingehende Rechnungen manuell auf "
                "Vollstaendigkeit und gleichen Betraege gegen die Bestellung ab."
            ),
            "desired_state": (
                "Ein System liest Rechnungen aus, prueft Pflichtfelder und "
                "markiert nur Abweichungen fuer die manuelle Nachbearbeitung."
            ),
            "example_process": (
                "Eine Rechnung wird geoeffnet, Betrag und Lieferant gegen die "
                "Bestellung geprueft und das Ergebnis erfasst."
            ),
            "time_per_case_hours_current": 0.5,
            "time_per_case_hours_with_ai": 0.1,
            "occurrences_per_employee_per_year": 400,
            "affected_employees_count": 12,
            "employee_category": EmployeeCategory.PROFESSIONAL,
            "evidence_level": EvidenceLevel.TESTED_PILOTED,
            "adoption_type": AdoptionType.FIXED_PROCESS_STEP,
            "implementation_approach": ImplementationApproach.SIMPLE_INTEGRATION,
            "estimated_license_cost_eur": 5000.0,
            "data_classification": DataClassification.NO_PERSONAL_DATA,
        },
    },
    {
        "id": "demo-002",  # Composite genau 4 -> Grenze LIKELY_WIN/CALCULATED_RISK
        "status": CaseStatus.IMPLEMENTED,
        "use_case": {
            "title": "Support-Tickets automatisch kategorisieren",
            "submitter": "Demo Einreicher",
            "department": "IT-Support",
            "country": Country.AT,
            "current_state": (
                "Mitarbeiter lesen jedes eingehende Ticket und ordnen es manuell "
                "einer Kategorie zu, bevor es an das Fachteam weitergeleitet wird."
            ),
            "desired_state": (
                "Ein System kategorisiert Tickets automatisch und leitet sie "
                "weiter; Mitarbeiter pruefen nur noch Grenzfaelle."
            ),
            "example_process": (
                "Ein Ticket wird gelesen, der Kategorie Hardware zugeordnet und "
                "an das zustaendige Team weitergeleitet."
            ),
            "time_per_case_hours_current": 0.2,
            "time_per_case_hours_with_ai": 0.05,
            "occurrences_per_employee_per_year": 3000,
            "affected_employees_count": 20,
            "employee_category": EmployeeCategory.JUNIOR,
            "evidence_level": EvidenceLevel.TESTED_PILOTED,
            "adoption_type": AdoptionType.FIXED_PROCESS_STEP,
            "implementation_approach": ImplementationApproach.DEVELOPMENT_ON_EXISTING,
            "estimated_license_cost_eur": 14000.0,
            "data_classification": DataClassification.PERSONAL,
        },
    },
    {
        "id": "demo-003",
        "status": CaseStatus.IN_REVIEW,
        "use_case": {
            "title": "Vertragsklauseln gegen die Standardvorlage pruefen",
            "submitter": "Demo Einreicher",
            "department": "Rechtsabteilung",
            "country": Country.CH,
            "current_state": (
                "Juristen lesen jeden Vertrag vollstaendig und markieren manuell "
                "Klauseln, die von der internen Standardvorlage abweichen."
            ),
            "desired_state": (
                "Ein System markiert Abweichungen automatisch und liefert eine "
                "priorisierte Pruefliste statt des vollstaendigen Dokuments."
            ),
            "example_process": (
                "Ein Vertrag wird hochgeladen, eine abweichende Haftungsklausel "
                "wird erkannt und zur Pruefung markiert."
            ),
            "time_per_case_hours_current": 3.0,
            "time_per_case_hours_with_ai": 0.5,
            "occurrences_per_employee_per_year": 200,
            "affected_employees_count": 4,
            "employee_category": EmployeeCategory.SENIOR,
            "evidence_level": EvidenceLevel.PURE_ESTIMATE,
            "adoption_type": AdoptionType.VOLUNTARY,
            "implementation_approach": ImplementationApproach.CUSTOM_DEVELOPMENT,
            "estimated_license_cost_eur": 0.0,
            "data_classification": DataClassification.SENSITIVE_PERSONAL,
            "regulatory_pressure": True,
        },
    },
    {
        "id": "demo-004",
        "status": CaseStatus.SUBMITTED,
        "use_case": {
            "title": "Angebotstexte aus Anforderungen entwerfen",
            "submitter": "Demo Einreicher",
            "department": "Vertrieb",
            "country": Country.DE,
            "current_state": (
                "Mitarbeiter formulieren fuer jedes Angebot die beschreibenden "
                "Textbausteine manuell auf Basis der Anforderungen."
            ),
            "desired_state": (
                "Ein System erzeugt Textentwuerfe, die der Vertrieb nur noch "
                "finalisiert."
            ),
            "example_process": (
                "Aus den Eckdaten einer Anfrage wird ein Entwurf der "
                "Leistungsbeschreibung erzeugt."
            ),
            "time_per_case_hours_current": 1.0,
            "time_per_case_hours_with_ai": 0.4,
            "occurrences_per_employee_per_year": 300,
            "affected_employees_count": 3,
            "employee_category": EmployeeCategory.PROFESSIONAL,
            "evidence_level": EvidenceLevel.SIMILAR_PROJECT,
            "adoption_type": AdoptionType.VOLUNTARY,
            "implementation_approach": ImplementationApproach.API_INTEGRATION,
            "estimated_license_cost_eur": 3000.0,
            "data_classification": DataClassification.NO_PERSONAL_DATA,
        },
    },
    {
        "id": "demo-005",  # Composite 9 -> MARGINAL_GAIN trotz gutem Nutzen
        "status": CaseStatus.SUBMITTED,
        "use_case": {
            "title": "Neues KI-Tool fuer die Wissensrecherche einfuehren",
            "submitter": "Demo Einreicher",
            "department": "Forschung",
            "country": Country.DE,
            "current_state": (
                "Fachkraefte recherchieren relevante Informationen manuell in "
                "verstreuten internen Quellen, bevor sie eine Analyse beginnen."
            ),
            "desired_state": (
                "Ein neu eingefuehrtes KI-Tool durchsucht die Quellen und liefert "
                "eine belegte Zusammenfassung als Ausgangspunkt."
            ),
            "example_process": (
                "Zu einer Fragestellung werden mehrere Dokumente gesichtet und zu "
                "einer belegten Kurzfassung verdichtet."
            ),
            "time_per_case_hours_current": 2.0,
            "time_per_case_hours_with_ai": 0.3,
            "occurrences_per_employee_per_year": 500,
            "affected_employees_count": 6,
            "employee_category": EmployeeCategory.CONSULTANT,
            "evidence_level": EvidenceLevel.SIMILAR_PROJECT,
            "adoption_type": AdoptionType.VOLUNTARY,
            "implementation_approach": ImplementationApproach.NEW_TOOL,
            "estimated_license_cost_eur": 20000.0,
            "implementation_cost_eur": 15000.0,
            "data_classification": DataClassification.SENSITIVE_PERSONAL,
        },
    },
    {
        "id": "demo-006",  # negatives Zeitdelta -> Vorfilter lehnt ab
        "status": CaseStatus.SUBMITTED,
        "use_case": {
            "title": "Monatsbericht aus Protokollen zusammenfassen",
            "submitter": "Demo Einreicher",
            "department": "Facility Management",
            "country": Country.AT,
            "current_state": (
                "Ein Mitarbeiter fasst monatlich die Wartungsprotokolle mehrerer "
                "Standorte manuell in einem Bericht zusammen."
            ),
            "desired_state": (
                "Ein System erstellt die Zusammenfassung, die anschliessend "
                "aufwendig gegengelesen und korrigiert werden muss."
            ),
            "example_process": (
                "Protokolle mehrerer Standorte werden gesichtet und zu einem "
                "Fliesstext zusammengefasst."
            ),
            "time_per_case_hours_current": 0.5,
            "time_per_case_hours_with_ai": 0.8,  # langsamer als heute -> Delta < 0
            "occurrences_per_employee_per_year": 12,
            "affected_employees_count": 1,
            "employee_category": EmployeeCategory.PROFESSIONAL,
            "evidence_level": EvidenceLevel.PURE_ESTIMATE,
            "adoption_type": AdoptionType.VOLUNTARY,
            "implementation_approach": ImplementationApproach.SIMPLE_INTEGRATION,
            "estimated_license_cost_eur": 2000.0,
            "data_classification": DataClassification.NO_PERSONAL_DATA,
        },
    },
    {
        "id": "demo-007",  # Composite genau 7 -> Grenze CALCULATED_RISK/MARGINAL_GAIN
        "status": CaseStatus.APPROVED,
        "use_case": {
            "title": "Reklamationen nach Fehlerart einordnen",
            "submitter": "Demo Einreicher",
            "department": "Qualitaetsmanagement",
            "country": Country.CH,
            "current_state": (
                "Mitarbeiter lesen jede Reklamation und ordnen sie manuell einer "
                "Fehlerkategorie zu, bevor die Ursachenanalyse startet."
            ),
            "desired_state": (
                "Ein System schlaegt die Fehlerkategorie vor und leitet den Fall "
                "an die zustaendige Analyse weiter."
            ),
            "example_process": (
                "Eine Reklamation ueber eine beschaedigte Lieferung wird der "
                "Kategorie Transportschaden zugeordnet."
            ),
            "time_per_case_hours_current": 1.5,
            "time_per_case_hours_with_ai": 0.5,
            "occurrences_per_employee_per_year": 400,
            "affected_employees_count": 5,
            "employee_category": EmployeeCategory.PROFESSIONAL,
            "evidence_level": EvidenceLevel.SIMILAR_PROJECT,
            "adoption_type": AdoptionType.RECOMMENDED_STANDARD,
            "implementation_approach": ImplementationApproach.CUSTOM_DEVELOPMENT,
            "estimated_license_cost_eur": 12000.0,
            "implementation_cost_eur": 12000.0,
            "data_classification": DataClassification.PSEUDONYMOUS,
        },
    },
    {
        "id": "demo-008",  # Handlungsdruck hebt CALCULATED_RISK -> LIKELY_WIN
        "status": CaseStatus.IN_REVIEW,
        "use_case": {
            "title": "Verdachtsmuster in Transaktionen vorsortieren",
            "submitter": "Demo Einreicher",
            "department": "Compliance",
            "country": Country.AT,
            "current_state": (
                "Mitarbeiter pruefen Transaktionen manuell auf Auffaelligkeiten, "
                "um moegliche Verdachtsfaelle zu identifizieren."
            ),
            "desired_state": (
                "Ein System sortiert auffaellige Muster vor und legt sie zur "
                "abschliessenden Bewertung vor."
            ),
            "example_process": (
                "Eine ungewoehnliche Folge von Ueberweisungen wird als Muster "
                "markiert und zur Pruefung vorgelegt."
            ),
            "time_per_case_hours_current": 0.8,
            "time_per_case_hours_with_ai": 0.2,
            "occurrences_per_employee_per_year": 250,
            "affected_employees_count": 4,
            "employee_category": EmployeeCategory.PROFESSIONAL,
            "evidence_level": EvidenceLevel.SIMILAR_PROJECT,
            "adoption_type": AdoptionType.RECOMMENDED_STANDARD,
            "implementation_approach": ImplementationApproach.API_INTEGRATION,
            "estimated_license_cost_eur": 8000.0,
            "data_classification": DataClassification.PERSONAL,
            "regulatory_pressure": True,
            "competitive_pressure": True,
            "strategic_priority": True,
        },
    },
    {
        "id": "demo-009",
        "status": CaseStatus.IMPLEMENTED,
        "use_case": {
            "title": "Log-Anomalien fuer die Security-Analyse markieren",
            "submitter": "Demo Einreicher",
            "department": "IT-Security",
            "country": Country.DE,
            "current_state": (
                "Analysten sichten Systemprotokolle manuell, um ungewoehnliche "
                "Zugriffs- und Aktivitaetsmuster als moegliche Vorfaelle zu erkennen."
            ),
            "desired_state": (
                "Ein System markiert Anomalien automatisch und legt verdaechtige "
                "Muster den Analysten zur Bewertung vor."
            ),
            "example_process": (
                "Eine Haeufung fehlgeschlagener Logins ausserhalb der "
                "Geschaeftszeiten wird als Anomalie markiert."
            ),
            "time_per_case_hours_current": 2.0,
            "time_per_case_hours_with_ai": 0.5,
            "occurrences_per_employee_per_year": 300,
            "affected_employees_count": 8,
            "employee_category": EmployeeCategory.SENIOR,
            "evidence_level": EvidenceLevel.TESTED_PILOTED,
            "adoption_type": AdoptionType.FIXED_PROCESS_STEP,
            "implementation_approach": ImplementationApproach.DEVELOPMENT_ON_EXISTING,
            "estimated_license_cost_eur": 0.0,
            "data_classification": DataClassification.NO_PERSONAL_DATA,
        },
    },
]


def _resolve_db_path(cli_path: str | None) -> Path:
    """CLI-Argument > AECT_DB_PATH > Repo-Root/aect_demo.db."""
    if cli_path:
        return Path(cli_path)
    env_path = os.environ.get("AECT_DB_PATH")
    if env_path:
        return Path(env_path)
    return _DEFAULT_DB_PATH


def seed(db_path: Path, *, reset: bool) -> list[tuple[str, str, str]]:
    """Legt die Demo-Cases in db_path an. Gibt (id, zone, status) je Case zurueck."""
    if reset and db_path.exists():
        db_path.unlink()
        print(f"DB geloescht: {db_path}")

    db_path.parent.mkdir(parents=True, exist_ok=True)
    repository = SQLiteRepository(db_path)
    roi_config = load_roi_config()

    summary: list[tuple[str, str, str]] = []
    for offset, spec in enumerate(_SPECS):
        use_case = UseCaseInput(**spec["use_case"])
        submitted_at = _BASE_TS + timedelta(days=offset)
        result = evaluate_use_case(use_case, roi_config)
        case = SubmittedCase(
            id=spec["id"],
            submitted_at=submitted_at,
            use_case=use_case,
            result=result,
        )
        repository.save(case)

        status: CaseStatus = spec["status"]
        if status is not CaseStatus.SUBMITTED:
            # +1 Tag als Zeitstempel des Statuswechsels (deterministisch).
            repository.update_status(spec["id"], status, submitted_at + timedelta(days=1))

        zone = (
            result.zone.final_zone.value
            if result.zone is not None
            else "-- (Vorfilter)"
        )
        summary.append((spec["id"], zone, status.value))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Legt generische Demo-Cases an.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="DB-Datei vor dem Anlegen loeschen (dokumentierter Demo-Reset).",
    )
    parser.add_argument(
        "--db-path",
        default=None,
        help="Ziel-DB-Pfad (Default: AECT_DB_PATH oder Repo-Root/aect_demo.db).",
    )
    args = parser.parse_args()

    db_path = _resolve_db_path(args.db_path)
    summary = seed(db_path, reset=args.reset)

    print(f"{len(summary)} Demo-Cases geschrieben: {db_path}")
    print(f"{'ID':<10} {'Zone':<18} Status")
    for case_id, zone, status in summary:
        print(f"{case_id:<10} {zone:<18} {status}")
    print(
        "\nAPI mit dieser DB starten:\n"
        f"    AECT_DB_PATH={db_path} uv run uvicorn aect.adapters.api.app:app --port 8000"
    )


if __name__ == "__main__":
    main()
