"""Domain-Modelle für AECT.

Schicht: domain — kein Import aus adapters/, application/ oder externen
Infrastruktur-Libraries (kein FastAPI, kein SQLAlchemy, kein httpx).
Erlaubt: pydantic, Python stdlib, eigene domain-interne Module.
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class EvidenceQuality(StrEnum):
    """Qualität der Zeitersparnis-Schätzung.

    ESTIMATE: Bauchgefühl / grobe Schätzung ohne Messung
    TESTED:   Pilottest oder strukturierte Erhebung vorhanden
    PROVEN:   Mehrere Zyklen gemessen, Datenbasis belastbar
    """

    ESTIMATE = "estimate"
    TESTED = "tested"
    PROVEN = "proven"


class UseCaseInput(BaseModel):
    """Eingabe-Schema für einen AI-Use-Case-Antrag.

    Entspricht den Stammdaten- und Grunddatenfeldern aus dem v5-Bewertungsmodell.
    Pflichtfelder: title, submitter, department, current_state, desired_state,
    example_process. Alle anderen Felder sind optional mit sicheren Defaults.

    Security: extra='forbid' verhindert dass unbekannte Felder (z.B. durch
    Prompt-Injection im JSON-Payload) in die Verarbeitung gelangen (OWASP LLM10).
    max_length-Grenzen schützen vor Token-Flooding bei LLM-Weiterverarbeitung.
    """

    model_config = ConfigDict(
        extra="forbid",  # unbekannte Felder → ValidationError, kein stilles Ignorieren
        str_strip_whitespace=True,  # führende/nachfolgende Leerzeichen entfernen
        frozen=False,  # mutierbar (wird im Application-Layer angereichert)
    )

    # ── Stammdaten ────────────────────────────────────────────────────────────
    title: str = Field(
        min_length=1,
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
        min_length=1,
        max_length=2000,
        description="Beschreibung des aktuellen Prozesses (Ist-Zustand)",
    )
    desired_state: str = Field(
        min_length=1,
        max_length=2000,
        description="Beschreibung des gewünschten Zustands nach AI-Einsatz",
    )
    example_process: str = Field(
        min_length=1,
        max_length=2000,
        description="Konkretes Beispiel eines einzelnen Vorgangs (nicht Gesamtvolumen)",
    )

    # ── Quantitative Felder (optional) ───────────────────────────────────────
    time_savings_hours_per_case: float | None = Field(
        default=None,
        ge=0.0,  # nicht negativ
        description="Geschätzte Zeitersparnis pro Vorgang in Stunden",
    )
    frequency_per_year: int | None = Field(
        default=None,
        ge=0,  # nicht negativ
        description="Anzahl Vorgänge pro Jahr",
    )

    # ── Qualitative Felder (optional) ────────────────────────────────────────
    evidence_quality: EvidenceQuality = Field(
        default=EvidenceQuality.ESTIMATE,
        description="Qualität der Grundlage für Zeitersparnis-Schätzung",
    )
    contains_pii: bool = Field(
        default=False,
        description="Werden personenbezogene Daten verarbeitet?",
    )
