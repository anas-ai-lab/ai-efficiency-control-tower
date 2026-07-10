"""Domain-Typen für AECT — kontrollierte Vokabular-Enums.

Alle Enum-Werte sind snake_case (StrEnum — direktes Parsen aus JSON/Form-Daten,
kein manuelles .value-Mapping nötig).

IP-Trennung (vertraglich bedingt): Faktor-Mappings (Stundensätze, Score-Gewichte,
Vorfilter-Schwellen) liegen in config/roi_config.toml — nicht hier.
"""

from __future__ import annotations

from enum import StrEnum


class EvidenceLevel(StrEnum):
    """Qualität der Zeitersparnis-Schätzung.

    Beeinflusst den Evidenzfaktor im ROI-Modell (aufsteigend nach Verlässlichkeit).
    Konkretes Faktor-Mapping (V4: 0.40 / 0.55 / 0.90) liegt in config/roi_config.toml.

    Deutsche Labels (V4, SDR-0003 Entscheidung 3):
      pure_estimate   -- reine Einschaetzung (Bauchgefuehl ohne Datenbasis)
      similar_project -- eigene Erfahrung bzw. Analogieprojekt
      tested_piloted  -- mit mehreren realen Beispielen getestet oder gemessen
    """

    PURE_ESTIMATE = "pure_estimate"  # reine Einschaetzung ohne Datenbasis
    SIMILAR_PROJECT = "similar_project"  # eigene Erfahrung / Analogieprojekt
    TESTED_PILOTED = "tested_piloted"  # mit realen Beispielen getestet oder gemessen


class AdoptionType(StrEnum):
    """Verbindlichkeit der Nutzung — beeinflusst den Nutzungsfaktor im ROI-Modell.

    Deutsche Labels (V4, SDR-0003 Entscheidung 3): aufsteigend nach Verbindlichkeit.
    Faktor-Mapping (0.50 / 0.70 / 0.90) liegt in config/roi_config.toml.
    """

    VOLUNTARY = "voluntary"  # freiwillige Nutzung (opt-in)
    RECOMMENDED_STANDARD = "recommended_standard"  # empfohlener Teamstandard
    FIXED_PROCESS_STEP = "fixed_process_step"  # fester Prozessschritt


class ImplementationApproach(StrEnum):
    """Geplanter Umsetzungsansatz — ordinal, aufsteigende Komplexitaet (V4).

    Der Ansatz ersetzt das fruehere freie Komplexitaets-Eingabefeld: die
    Komplexitaet (1-5) wird deterministisch aus dem Ansatz abgeleitet
    (COMPLEXITY_BY_APPROACH in domain/scoring.py, SDR-0003 Entscheidung 4).

    Deutsche Labels:
      simple_integration      -- einfache Implementierung in bestehende Umgebung
      development_on_existing -- Entwicklung auf bestehender Umgebung
      api_integration         -- API-Anbindung in bestehende Umgebung
      custom_development       -- eigene Entwicklung
      new_tool                -- Einfuehrung neues Tool
    """

    SIMPLE_INTEGRATION = "simple_integration"  # einfache Implementierung, Bestand
    DEVELOPMENT_ON_EXISTING = "development_on_existing"  # Entwicklung auf Bestand
    API_INTEGRATION = "api_integration"  # API-Anbindung in bestehende Umgebung
    CUSTOM_DEVELOPMENT = "custom_development"  # eigene Entwicklung
    NEW_TOOL = "new_tool"  # Einfuehrung neues Tool


class DataClassification(StrEnum):
    """Datenschutz-Einstufung der verarbeiteten Daten.

    Beeinflusst den Datenschutz-Anteil im Composite-Aufwand-Score (aufsteigend).
    Score-Mapping (V4): NO_PERSONAL_DATA=0, PSEUDONYMOUS=1, PERSONAL=1,
    SENSITIVE_PERSONAL=2. Pseudonymisierte Daten bleiben personenbezogen i. S. d.
    DSGVO (Art. 4 Nr. 5), daher gleicher Score wie PERSONAL. Mapping liegt in
    domain/scoring.py, nicht hier.
    """

    NO_PERSONAL_DATA = "no_personal_data"  # Rein operative / anonyme Daten
    PSEUDONYMOUS = "pseudonymous"  # Pseudonymisiert (Art. 4 Nr. 5 DSGVO)
    PERSONAL = "personal"  # Personenbezogen (Art. 4 Nr. 1 DSGVO)
    SENSITIVE_PERSONAL = "sensitive_personal"  # Besondere Kategorien (Art. 9 DSGVO)


class EmployeeCategory(StrEnum):
    """Grobe Seniorität der betroffenen Mitarbeiter (aufsteigend nach Seniorität).

    Konkretes Stundensatz-Mapping (je Land x Stufe) liegt in config/roi_config.toml.
    Dieses Enum ist der IP-saubere Anker — keine Firmenzahlen im Code.
    """

    JUNIOR = "junior"  # Einsteiger / Analyst / Junior Developer
    PROFESSIONAL = "professional"  # Erfahrener Sachbearbeiter / Fachkraft
    CONSULTANT = "consultant"  # Berater / Spezialist mit Projektverantwortung
    SENIOR = "senior"  # Senior / Principal Expert
    MANAGEMENT = "management"  # Fuehrungsebene / Bereichsleitung


class Country(StrEnum):
    """Land der betroffenen Mitarbeiter — steuert den Stundensatz-Lookup.

    Werte sind generische ISO-3166-alpha-2-Kuerzel (lowercase). Konkrete
    Stundensaetze je Land x Level liegen in config, nie im Code (IP-Trennung):
    generische DACH-Platzhalter in config/roi_config.toml, echte Saetze und
    weitere Laender in config/roi_config.local.toml (gitignored).

    Erweiterbar: ein neuer Wert hier braucht eine passende [hourly_rates.<wert>]-
    Section mit allen 5 Leveln, sonst stiller ROI=0 (TOML/StrEnum-Invariante).
    """

    DE = "de"
    AT = "at"
    CH = "ch"
    NO = "no"
    GB = "gb"
    ES = "es"
    IT = "it"
    TR = "tr"
    RO = "ro"
    PL = "pl"
    EG = "eg"
    IN = "in"


class TriageZone(StrEnum):
    """Outcome zone for AECT use-case triage.

    MARGINAL_GAIN: insufficient benefit or excessive complexity.
    CALCULATED_RISK: viable with caveats — proceed with caution.
    LIKELY_WIN: high benefit, manageable complexity.
    """

    MARGINAL_GAIN = "MARGINAL_GAIN"
    CALCULATED_RISK = "CALCULATED_RISK"
    LIKELY_WIN = "LIKELY_WIN"


class ReviewerDecision(StrEnum):
    """Human-in-the-Loop-Entscheidung zu einem Case (minimaler Decision-Record,
    ADR-0043 -- bewusst kein Multi-User-Reviewer-Workflow mit Rollen).

    PENDING ist der Default direkt nach Einreichung. APPROVED/REJECTED werden
    ausschliesslich ueber POST /cases/{id}/decision gesetzt (TriageService.
    record_decision()) -- derselbe API-Key-Auth-Mechanismus wie alle anderen
    Routen, kein eigenes Auth-/Rollen-Konzept.
    """

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class CaseStatus(StrEnum):
    """Lifecycle-Status eines Case -- wo im Bearbeitungsfluss er steht.

    APPROVED/REJECTED werden zusaetzlich durch record_decision() gesetzt
    (Kopplung an ReviewerDecision, ADR-0043 -- der Freigabe-Akt bewegt den
    Case auch im Lifecycle). Die uebrigen Zustaende werden ausschliesslich
    ueber POST /cases/{id}/status gesetzt.

    SUBMITTED ist der Default direkt nach Einreichung. Es gibt bewusst keine
    Transitions-Matrix -- jeder Zustand ist aus jedem setzbar (menschliche
    Autoritaet in einem Single-User-Build, siehe Lifecycle-ADR).
    """

    SUBMITTED = "submitted"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    ALREADY_EXISTS = "already_exists"
    INTEGRATED = "integrated"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"
