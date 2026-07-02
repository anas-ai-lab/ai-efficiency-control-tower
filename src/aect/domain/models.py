"""Domain-Modelle für AECT.

Schicht: domain — kein Import aus adapters/, application/ oder externen
Infrastruktur-Libraries (kein FastAPI, kein SQLAlchemy, kein httpx).
Erlaubt: pydantic, Python stdlib, eigene domain-interne Module.

Security by Design:
  extra='forbid'          → kein unerwarteter Input umgeht die Validierung (OWASP LLM10)
  max_length auf ALLEN Freitextfeldern → Schutz gegen Token-Flooding in Phase C
  frozen=True             → Domain-Eingabeobjekte sind nach Erstellung unveränderlich

Anreicherung durch den Application-Layer passiert in separaten Ausgabeobjekten
(TriageResult — wird in Phase B/C eingeführt), nicht durch Mutation dieses Objekts.

IP-Trennung (interne Referenz (entfernt) §5): Stundensätze, Faktor-Mappings, Vorfilter-Schwellen
liegen in config/roi_config.toml — nie in diesem Modell.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from aect.domain.types import (
    AdoptionType,
    DataClassification,
    EmployeeCategory,
    EvidenceLevel,
    ImplementationApproach,
)


class UseCaseInput(BaseModel):
    """Eingabe-Schema für einen AI-Use-Case-Antrag.

    Entspricht den Feldern des v5-Bewertungsmodells:
    Stammdaten / Ist-Soll / Mengen / Zeit / Evidenz / Verbindlichkeit /
    Kosten / Datenschutz / Handlungsdruck.

    Alle Freitextfelder: min_length + max_length (Substanz + Token-Budget).
    Alle Enum-Felder: StrEnum — parst direkt aus JSON-Strings.
    Die Rule Engine (Phase A) liest ausschließlich dieses Objekt.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        frozen=True,
    )

    # ── Stammdaten ────────────────────────────────────────────────────────────
    title: str = Field(
        min_length=5,
        max_length=200,
        description="Kurzer, sprechender Name des Use Case",
    )
    submitter: str = Field(
        min_length=1,
        max_length=100,
        description="Name der einreichenden Person",
    )
    department: str = Field(
        min_length=1,
        max_length=100,
        description="Abteilung / Organisationseinheit",
    )

    # ── Ist / Soll / Beispiel ─────────────────────────────────────────────────
    current_state: str = Field(
        min_length=30,
        max_length=2000,
        description="Beschreibung des aktuellen Prozesses (Ist-Zustand)",
    )
    desired_state: str = Field(
        min_length=30,
        max_length=2000,
        description="Beschreibung des gewünschten Zustands nach AI-Einsatz",
    )
    example_process: str = Field(
        min_length=20,
        max_length=2000,
        description="Konkretes Beispiel eines einzelnen Vorgangs (nicht Gesamtvolumen)",
    )

    # ── Quantitative Felder (required — ohne diese keine ROI-Berechnung) ─────
    time_savings_hours_per_case: float = Field(
        gt=0.0,
        le=8.0,
        description="Geschätzte Zeitersparnis pro Vorgang in Stunden (max = 8 h)",
    )
    frequency_per_year: int = Field(
        gt=0,
        le=1_000_000,
        description="Anzahl Vorgänge pro Jahr",
    )
    affected_employees_count: int = Field(
        gt=0,
        le=50_000,
        description="Anzahl Mitarbeiter, die diesen Prozess heute manuell durchführen",
    )
    employee_category: EmployeeCategory = Field(
        description="Grobe Seniorität der betroffenen Mitarbeiter (→ Stundensatz aus Config)",
    )

    # ── Evidenz & Verbindlichkeit ─────────────────────────────────────────────
    evidence_level: EvidenceLevel = Field(
        default=EvidenceLevel.PURE_ESTIMATE,
        description="Qualität der Grundlage für die Zeitersparnis-Schätzung",
    )
    adoption_type: AdoptionType = Field(
        description="Pflicht- oder Freiwillignutzung (beeinflusst Nutzungsfaktor)",
    )
    implementation_approach: ImplementationApproach = Field(
        description="Geplante Umsetzungsstrategie",
    )

    # ── Kosten ────────────────────────────────────────────────────────────────
    estimated_license_cost_eur: float = Field(
        default=0.0,
        ge=0.0,
        le=10_000_000.0,
        description="Geschätzte Lizenzkosten p.a. in EUR (0 = open-source oder intern gebaut)",
    )
    implementation_complexity: int = Field(
        ge=1,
        le=5,
        description="Technische Komplexität: 1 = trivial, 3 = mittel, 5 = sehr hoch",
    )

    # ── Datenschutz ───────────────────────────────────────────────────────────
    contains_pii: bool = Field(
        default=False,
        description="Werden personenbezogene Daten verarbeitet? (Schnellcheck)",
    )
    data_classification: DataClassification = Field(
        description=(
            "Datenschutz-Einstufung der verarbeiteten Daten. "
            "SENSITIVE_PERSONAL → Datenschutz-Score 2 im Composite-Aufwand-Score."
        ),
    )

    # ── Handlungsdruck (für Zonen-Hochstufung) ───────────────────────────────
    regulatory_pressure: bool = Field(
        default=False,
        description="Regulatorischer Druck (Compliance-Anforderung, Audit-Finding)?",
    )
    competitive_pressure: bool = Field(
        default=False,
        description="Wettbewerbsdruck (Branche setzt AI bereits ein)?",
    )
    strategic_priority: bool = Field(
        default=False,
        description="Explizit strategische Priorität von Vorstand oder Management?",
    )
