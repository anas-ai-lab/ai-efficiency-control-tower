"""AI-vs-Automation-Router — deterministisch, Phase A.

Klassifiziert Use-Case-Einreichungen nach technischer Eignung:
  AI_RECOMMENDED          -- ambigue, kontextabhaengig, sprachbasiert.
  AUTOMATION_RECOMMENDED  -- regelbasiert, deterministisch, hohe Frequenz.
  HUMAN_REVIEW_REQUIRED   -- Datenschutz-Risikoflags, mind. 2 aktive Flags.
  BORDERLINE              -- Mischsignale; Phase-C-LLM bewertet Freitext nach.

Architektur: reine Funktion, seiteneffektfrei, kein Dateisystem, kein Netzwerk.
Phase-C-Erweiterung: BORDERLINE-Cases werden per LLM-Analyse verfeinert.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from aect.domain.models import UseCaseInput
from aect.domain.scoring import COMPLEXITY_BY_APPROACH
from aect.domain.types import (
    AdoptionType,
    DataClassification,
    EvidenceLevel,
)

# ---------------------------------------------------------------------------
# Schwellen (Methodik-Parameter -- keine Firmenwerte, IP-sauber)
# ---------------------------------------------------------------------------
_SIMPLE_TASK_MAX_COMPLEXITY: int = 2  # Komplexitaet <= -> Automation-Signal
_COMPLEX_TASK_MIN_COMPLEXITY: int = 4  # Komplexitaet >= -> AI-Signal
# Vorgaenge pro Mitarbeiter und Jahr >= -> Automation-Signal: eine hohe
# Wiederholfrequenz amortisiert den Automatisierungsaufwand. Seit dem V4-Rename
# (SDR-0003) ist die Haeufigkeit person-basiert, die Schwelle wurde aber nicht
# nachgezogen -- der alte Wert 2000 war fuer das organisationsweite Gesamtvolumen
# kalibriert und ist pro Mitarbeiter praktisch nie erreichbar (~8 Vorgaenge je
# Arbeitstag), das Signal war tot.
# Herleitung (250): die Golden-Cases trennen hier nicht -- die Autor-Zonenlabels
# haengen an Nutzen/Composite/Handlungsdruck, nicht an der Frequenz (bei
# 500-600 Vorgaengen/Jahr stehen LIKELY_WIN und CALCULATED_RISK nebeneinander).
# Daher eine nachvollziehbare Alltagsannahme statt einer Datenschwelle:
# ~220 Arbeitstage/Jahr, ein mindestens (nahezu) taeglich wiederkehrender Vorgang
# erreicht >= 250/Jahr; ein woechentlicher (~50/Jahr) bleibt bewusst darunter.
_HIGH_VOLUME_MIN_ANNUAL: int = 250
_AMBIGUOUS_DESC_MIN_LEN: int = 300  # Zeichen in desired_state >= -> AI-Signal


# ---------------------------------------------------------------------------
# Ergebnis-Typen
# ---------------------------------------------------------------------------


class RoutingRecommendation(StrEnum):
    """Routing-Empfehlung des AI-vs-Automation-Routers."""

    AI_RECOMMENDED = "AI_RECOMMENDED"
    AUTOMATION_RECOMMENDED = "AUTOMATION_RECOMMENDED"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    BORDERLINE = "BORDERLINE"


@dataclass(frozen=True)
class RoutingResult:
    """Unveraenderliches Ergebnis des AI-vs-Automation-Routings.

    automation_signals: Argumente fuer klassische Automatisierung.
    ai_signals:         Argumente fuer AI/LLM-Einsatz.
    risk_flags:         Datenschutz-/Eskalationshinweise.
    confidence:         Konfidenzgrad der Empfehlung: HIGH / MEDIUM / LOW.
    """

    recommendation: RoutingRecommendation
    confidence: str  # "HIGH" | "MEDIUM" | "LOW"
    automation_signals: tuple[str, ...]
    ai_signals: tuple[str, ...]
    risk_flags: tuple[str, ...]

    @property
    def requires_human_review(self) -> bool:
        """True wenn Human Review empfohlen -- entweder via Empfehlung oder Risikoflags."""
        return (
            self.recommendation == RoutingRecommendation.HUMAN_REVIEW_REQUIRED
            or bool(self.risk_flags)
        )


# ---------------------------------------------------------------------------
# Signal-Sammlung (seiteneffektfrei, einzeln testbar)
# ---------------------------------------------------------------------------


def _collect_automation_signals(use_case: UseCaseInput) -> list[str]:
    """Argumente fuer klassische Automatisierung.

    Die Komplexitaet wird seit V4 aus dem Umsetzungsansatz abgeleitet
    (COMPLEXITY_BY_APPROACH) -- ein separates Ansatz-Signal entfaellt, es waere
    eine Doppelzaehlung derselben Groesse.
    """
    signals: list[str] = []
    # route_use_case laeuft nur fuer bewertete Cases: evaluate_use_case faengt
    # den fehlenden Ansatz vorher als Vor-Bewertungs-Zustand ab (ADR-0050).
    assert use_case.implementation_approach is not None
    complexity = COMPLEXITY_BY_APPROACH[use_case.implementation_approach]
    if complexity <= _SIMPLE_TASK_MAX_COMPLEXITY:
        signals.append(
            f"Komplexitaet {complexity}"
            f" <= {_SIMPLE_TASK_MAX_COMPLEXITY} -- einfacher, regelbasierter Ablauf"
        )
    if use_case.occurrences_per_employee_per_year >= _HIGH_VOLUME_MIN_ANNUAL:
        signals.append(
            f"Volumen {use_case.occurrences_per_employee_per_year}/Jahr je MA"
            f" >= {_HIGH_VOLUME_MIN_ANNUAL} -- hoher Automatisierungs-ROI"
        )
    if use_case.adoption_type == AdoptionType.FIXED_PROCESS_STEP:
        signals.append(
            "Fester Prozessschritt"
            " -- konsistentes Nutzungsverhalten begunstigt Automatisierung"
        )
    return signals


def _collect_ai_signals(use_case: UseCaseInput) -> list[str]:
    """Argumente fuer AI/LLM-Einsatz.

    Die Komplexitaet wird seit V4 aus dem Umsetzungsansatz abgeleitet
    (COMPLEXITY_BY_APPROACH) -- ein separates Ansatz-Signal entfaellt.
    """
    signals: list[str] = []
    # route_use_case laeuft nur fuer bewertete Cases (ADR-0050, siehe oben).
    assert use_case.implementation_approach is not None
    complexity = COMPLEXITY_BY_APPROACH[use_case.implementation_approach]
    if complexity >= _COMPLEX_TASK_MIN_COMPLEXITY:
        signals.append(
            f"Komplexitaet {complexity}"
            f" >= {_COMPLEX_TASK_MIN_COMPLEXITY} -- kontextabhaengige, ambigue Aufgabe"
        )
    if use_case.evidence_level == EvidenceLevel.PURE_ESTIMATE:
        signals.append(
            "Schaetzqualitaet gering (pure_estimate)"
            " -- AI fuer explorativen, unsicheren Anwendungsfall geeignet"
        )
    if len(use_case.desired_state) >= _AMBIGUOUS_DESC_MIN_LEN:
        signals.append(
            f"Soll-Beschreibung {len(use_case.desired_state)} Zeichen"
            " -- mehrdimensionale Anforderung deutet auf AI-Bedarf hin"
        )
    return signals


def _collect_risk_flags(use_case: UseCaseInput) -> list[str]:
    """Datenschutz- und Eskalationshinweise."""
    flags: list[str] = []
    if use_case.data_classification == DataClassification.SENSITIVE_PERSONAL:
        flags.append(
            "Sensible Personendaten (Art. 9 DSGVO)"
            " -- DSFA-Pruefung und Human Review vor Umsetzung erforderlich"
        )
    if use_case.regulatory_pressure and use_case.contains_pii:
        flags.append(
            "Regulatorischer Druck + PII-Verarbeitung"
            " -- Human Review und Datenschutzfolgenabschaetzung empfohlen"
        )
    return flags


# ---------------------------------------------------------------------------
# Entscheidungsmatrix
# ---------------------------------------------------------------------------


def _decide(
    automation_count: int,
    ai_count: int,
    risk_count: int,
) -> tuple[RoutingRecommendation, str]:
    """Signal-Zaehler -> Empfehlung + Konfidenz.

    Reihenfolge: Risiko-Eskalation > eindeutige Mehrheit > gemischte Signale.
    HUMAN_REVIEW_REQUIRED nur bei mind. 2 Risikoflags (1 Flag: requires_human_review=True,
    aber Routing-Empfehlung bleibt signalbasiert).
    """
    if risk_count >= 2:
        return RoutingRecommendation.HUMAN_REVIEW_REQUIRED, "HIGH"

    # Eindeutige Automation-Mehrheit
    if automation_count >= 2 and ai_count == 0:
        return RoutingRecommendation.AUTOMATION_RECOMMENDED, "HIGH"
    if automation_count >= 1 and ai_count == 0:
        return RoutingRecommendation.AUTOMATION_RECOMMENDED, "MEDIUM"

    # Eindeutige AI-Mehrheit
    if ai_count >= 2 and automation_count == 0:
        return RoutingRecommendation.AI_RECOMMENDED, "HIGH"
    if ai_count >= 1 and automation_count == 0:
        return RoutingRecommendation.AI_RECOMMENDED, "MEDIUM"

    # Gemischte Signale -- Mehrheit gewinnt mit Konfidenz LOW
    net = automation_count - ai_count
    if net > 0:
        return RoutingRecommendation.AUTOMATION_RECOMMENDED, "LOW"
    if net < 0:
        return RoutingRecommendation.AI_RECOMMENDED, "LOW"

    # Gleichstand oder keine Signale -- Phase-C-LLM entscheidet
    return RoutingRecommendation.BORDERLINE, "LOW"


# ---------------------------------------------------------------------------
# Oeffentliche API
# ---------------------------------------------------------------------------


def route_use_case(use_case: UseCaseInput) -> RoutingResult:
    """Hauptfunktion: UseCaseInput -> RoutingResult.

    Seiteneffektfrei, deterministisch, ohne LLM-Call (Phase A).
    BORDERLINE-Cases werden in Phase C per LLM-Analyse verfeinert.
    """
    automation_signals = _collect_automation_signals(use_case)
    ai_signals = _collect_ai_signals(use_case)
    risk_flags = _collect_risk_flags(use_case)

    recommendation, confidence = _decide(
        automation_count=len(automation_signals),
        ai_count=len(ai_signals),
        risk_count=len(risk_flags),
    )

    return RoutingResult(
        recommendation=recommendation,
        confidence=confidence,
        automation_signals=tuple(automation_signals),
        ai_signals=tuple(ai_signals),
        risk_flags=tuple(risk_flags),
    )
