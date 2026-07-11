"""Deterministische Erklaerbarkeit der Triage-Ergebnisse (V4-P6, SDR-0003).

Ziel: Keine nackte Zahl und kein rohes Enum erreicht den Nutzer. Alles
Regelbasierte wird hier deterministisch in deutschen Klartext uebersetzt --
Score-Herkunft, Konfidenz-Begruendung, Empfehlungs-Satz, Machbarkeits-Definition
und die Contra-Punkte fuer den Entscheider-Report. LLM kommt hier NICHT vor;
das ist bewusst die Regel-Schicht (analog zones._build_reason /
application/eval/breakdown.py).

Schicht: domain -- importiert nur aus aect.domain.*. Reine Projektion ueber
bereits berechneten Werten (TriageResult), kein I/O, kein State. Die Ergebnisse
werden NICHT am TriageResult persistiert (die SQLite-Reserialisierung
rekonstruiert TriageResult feldweise) -- sie sind eine Read-Time-Projektion, die
die Adapter/Application-Schicht bei der Response-Serialisierung aufbaut.

Formatierung bewusst konsistent mit zones.py/breakdown.py: Betraege
``{wert:,.0f} EUR``, Pfeil ``->``, Vergleiche ``>=``/``<`` (ASCII, RUF001-sicher).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from aect.domain.formatting import format_de
from aect.domain.models import UseCaseInput
from aect.domain.pipeline import TriageResult
from aect.domain.routing import RoutingRecommendation
from aect.domain.scoring import CompositeScore
from aect.domain.types import (
    AdoptionType,
    DataClassification,
    EvidenceLevel,
    ImplementationApproach,
    TriageZone,
)
from aect.domain.zones import ZoneClassifier

# ---------------------------------------------------------------------------
# Zentrale Label-/Definitions-Konstanten (einmal definiert, ueberall referenziert)
# ---------------------------------------------------------------------------

#: Composite-Aufwandscore-Obergrenze (V4-Modell, siehe scoring.CompositeScore).
COMPOSITE_MAX_TOTAL = 9

#: Deutsche Zonen-Labels fuer Entscheider (SDR-0003 / V4-P6). Zentrale Quelle --
#: die Kennzahlen-Zeile im Entscheider-Report und die Konfidenz-Kipp-Saetze
#: referenzieren dieselbe Map, kein zweiter Ort mit abweichenden Woertern.
ZONE_LABELS: dict[TriageZone, str] = {
    TriageZone.LIKELY_WIN: "Klarer Gewinn",
    TriageZone.CALCULATED_RISK: "Kalkuliertes Risiko",
    TriageZone.MARGINAL_GAIN: "Geringer Nutzen",
}

#: Machbarkeit = 10 - Aufwandscore. Bei Aufwandscore 1-9 (V4-Range, Step 0)
#: ergibt das einen Machbarkeits-Bereich 1-9 -- verifiziert, nicht angenommen:
#: total=1 -> 9 (leicht), total=9 -> 1 (schwer). Zentrale Definition + Formel,
#: ueberall (Score-Breakdown, Board-Daten) referenziert.
FEASIBILITY_DEFINITION = (
    "Machbarkeit = 10 - Aufwandscore; hoher Wert = leichter umsetzbar."
)


def feasibility_from_composite(composite_total: int) -> int:
    """Machbarkeit aus dem Aufwandscore: 10 - Aufwandscore (Range 1-9)."""
    return 10 - composite_total


_APPROACH_LABEL: dict[ImplementationApproach, str] = {
    ImplementationApproach.SIMPLE_INTEGRATION: "Einfache Integration in Bestand",
    ImplementationApproach.DEVELOPMENT_ON_EXISTING: "Entwicklung auf Bestehendem",
    ImplementationApproach.API_INTEGRATION: "API-Anbindung an Bestehendes",
    ImplementationApproach.CUSTOM_DEVELOPMENT: "Eigene Entwicklung",
    ImplementationApproach.NEW_TOOL: "Einfuehrung eines neuen Tools",
}

#: Datenschutz-Klartext fuer Empfehlungssatz + Contra-Punkte + Datenlage.
DATA_CLASSIFICATION_CLARTEXT: dict[DataClassification, str] = {
    DataClassification.NO_PERSONAL_DATA: "keine personenbezogenen Daten",
    DataClassification.PSEUDONYMOUS: (
        "pseudonyme Daten (bleiben personenbezogen, Art. 4 Nr. 5 DSGVO)"
    ),
    DataClassification.PERSONAL: "personenbezogene Daten (Art. 4 DSGVO)",
    DataClassification.SENSITIVE_PERSONAL: (
        "besondere Kategorien personenbezogener Daten (Art. 9 DSGVO)"
    ),
}

#: Evidenz-Labels (deutsche Klartext-Fassung der EvidenceLevel-Stufen).
EVIDENCE_LABELS: dict[EvidenceLevel, str] = {
    EvidenceLevel.PURE_ESTIMATE: "reine Einschaetzung",
    EvidenceLevel.SIMILAR_PROJECT: "eigene Erfahrung / Analogieprojekt",
    EvidenceLevel.TESTED_PILOTED: "mit realen Beispielen getestet",
}

#: Verbindlichkeits-Labels (deutsche Klartext-Fassung der AdoptionType-Stufen).
ADOPTION_LABELS: dict[AdoptionType, str] = {
    AdoptionType.VOLUNTARY: "freiwillige Nutzung",
    AdoptionType.RECOMMENDED_STANDARD: "empfohlener Teamstandard",
    AdoptionType.FIXED_PROCESS_STEP: "fester Prozessschritt",
}

#: Datenschutz-Begruendung je Klassifizierung fuer die Score-Herkunft.
_DATA_PROTECTION_REASON: dict[DataClassification, str] = {
    DataClassification.NO_PERSONAL_DATA: "Keine personenbezogenen Daten -> 0 Punkte",
    DataClassification.PSEUDONYMOUS: (
        "Pseudonyme Daten (bleiben personenbezogen, Art. 4 Nr. 5 DSGVO) -> +1"
    ),
    DataClassification.PERSONAL: "Personenbezogene Daten (Art. 4 DSGVO) -> +1",
    DataClassification.SENSITIVE_PERSONAL: (
        "Besondere Kategorien personenbezogener Daten (Art. 9 DSGVO) -> +2"
    ),
}

#: Zeitgewinn unterhalb dieser Schwelle (Stunden/Vorgang) gilt als "knapp"
#: (~3 Minuten) -- Methodik-Schwelle, keine Firmenzahl.
_KNAPP_HOURS = 0.05


# ---------------------------------------------------------------------------
# Ergebnis-Typen
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ScoreComponent:
    """Eine Komponente des Aufwandscores mit deterministischer Begruendung.

    key: stabiler Maschinen-Schluessel (complexity/cost/data_protection).
    label: deutsches Anzeige-Label. wert/max: der Punktwert und sein Maximum.
    begruendung: deutscher Klartext, aus den Eingaben abgeleitet.
    """

    key: str
    label: str
    wert: int
    max: int
    begruendung: str


@dataclass(frozen=True)
class ScoreBreakdown:
    """Herkunft des Aufwandscores -- Komponenten + Gesamtzeile + Machbarkeit."""

    components: tuple[ScoreComponent, ...]
    total: int
    max_total: int
    effort_label: str
    total_line: str
    feasibility_score: int
    feasibility_definition: str


@dataclass(frozen=True)
class ConfidenceReasoning:
    """Konfidenz als Begruendung statt Zahl (V4-P6).

    level: "hoch" | "mittel" | "niedrig". gruende: deterministische
    Klartext-Begruendungen (Evidenzlage, Zonengrenz-Naehe).
    """

    level: str
    gruende: tuple[str, ...]


@dataclass(frozen=True)
class TriageExplanation:
    """Gebuendelte, deterministische Erklaerbarkeit eines TriageResult.

    score_breakdown/confidence sind None, wenn der Vorfilter nicht bestanden
    wurde (dann sind composite/zone im TriageResult None). recommendation_text
    ist immer gesetzt (auch fuer den Vorfilter-Fail-Fall).
    """

    recommendation_text: str
    score_breakdown: ScoreBreakdown | None
    confidence: ConfidenceReasoning | None


# ---------------------------------------------------------------------------
# 1. Score-Herkunft
# ---------------------------------------------------------------------------


def build_score_breakdown(
    use_case: UseCaseInput,
    composite: CompositeScore,
    *,
    impl_cost_point_min_eur: float,
    license_cost_point_min_eur: float,
) -> ScoreBreakdown:
    """Baut die deterministische Herkunft des Aufwandscores.

    Jede Komponente traegt Wert, Maximum und eine aus den Eingaben generierte
    deutsche Begruendung (Umsetzungsansatz, Kostenschwellen, DSGVO-Mapping).
    """
    complexity_reason = (
        f"{_APPROACH_LABEL[use_case.implementation_approach]} "
        f"-> Komplexitaet {composite.complexity_score} von 5"
    )

    license_reason = _cost_point_reason(
        "Lizenzkosten",
        use_case.estimated_license_cost_eur,
        license_cost_point_min_eur,
        suffix="/Jahr",
    )
    impl_reason = _cost_point_reason(
        "Implementierungskosten",
        use_case.implementation_cost_eur,
        impl_cost_point_min_eur,
    )
    cost_reason = f"{license_reason}; {impl_reason}"

    data_reason = _DATA_PROTECTION_REASON[use_case.data_classification]

    components = (
        ScoreComponent(
            key="complexity",
            label="Komplexitaet",
            wert=composite.complexity_score,
            max=5,
            begruendung=complexity_reason,
        ),
        ScoreComponent(
            key="cost",
            label="Kosten",
            wert=composite.cost_score,
            max=2,
            begruendung=cost_reason,
        ),
        ScoreComponent(
            key="data_protection",
            label="Datenschutz",
            wert=composite.data_protection_score,
            max=2,
            begruendung=data_reason,
        ),
    )

    return ScoreBreakdown(
        components=components,
        total=composite.total,
        max_total=COMPOSITE_MAX_TOTAL,
        effort_label=composite.effort_label,
        total_line=(
            f"Aufwandscore {composite.total} von {COMPOSITE_MAX_TOTAL} "
            f"-> {composite.effort_label}"
        ),
        feasibility_score=feasibility_from_composite(composite.total),
        feasibility_definition=FEASIBILITY_DEFINITION,
    )


def _cost_point_reason(
    label: str, cost_eur: float, threshold_eur: float, *, suffix: str = ""
) -> str:
    """Begruendung eines Kostenpunkts: Wert gegen Schwelle, +1 oder kein Punkt."""
    if cost_eur >= threshold_eur:
        return (
            f"{label} {format_de(cost_eur, 'EUR')}{suffix} "
            f">= {format_de(threshold_eur, 'EUR')} -> +1 Kostenpunkt"
        )
    return (
        f"{label} {format_de(cost_eur, 'EUR')}{suffix} "
        f"< {format_de(threshold_eur, 'EUR')} -> kein Punkt"
    )


# ---------------------------------------------------------------------------
# 2. Konfidenz: von Zahl zu Begruendung
# ---------------------------------------------------------------------------


def build_confidence_reasoning(
    *,
    evidence_level: EvidenceLevel,
    evidence_factor: float,
    expected_benefit_eur: Decimal,
    composite_total: int,
    base_zone: TriageZone,
    classifier: ZoneClassifier,
) -> ConfidenceReasoning:
    """Konfidenz als {level, gruende} aus deterministischen Regeln.

    - Reine Einschaetzung (pure_estimate) -> Grund + Level hoechstens "mittel".
    - Zonengrenz-Naehe: der kleinere Hebel (Nutzen-% ODER Composite-Punkte, bis
      die Zone kippt) als Satz; Abstand < 10 % oder <= 1 Composite-Punkt ->
      "niedrig".
    - Sonst -> "hoch" mit deutlichem-Abstand-Grund.
    """
    is_pure_estimate = evidence_level == EvidenceLevel.PURE_ESTIMATE

    benefit_lever, composite_lever = _zone_flip_levers(
        benefit=float(expected_benefit_eur),
        composite=composite_total,
        base_zone=base_zone,
        classifier=classifier,
    )

    benefit_near = benefit_lever is not None and benefit_lever[0] < 10.0
    composite_near = composite_lever is not None and composite_lever[0] <= 1
    near = benefit_near or composite_near

    gruende: list[str] = []
    if is_pure_estimate:
        factor_str = f"{evidence_factor:.2f}".replace(".", ",")
        gruende.append(
            f"Nutzen basiert auf reiner Einschaetzung (Faktor {factor_str})."
        )
    if near:
        gruende.append(
            _boundary_sentence(benefit_lever, composite_lever, base_zone, benefit_near)
        )

    if near:
        level = "niedrig"
    elif is_pure_estimate:
        level = "mittel"
    else:
        level = "hoch"

    if not gruende:
        gruende.append("Evidenz gemessen und deutlicher Abstand zu allen Zonengrenzen.")

    return ConfidenceReasoning(level=level, gruende=tuple(gruende))


# Ein Hebel: (magnitude, richtung, ziel_zone). magnitude ist Prozent (Nutzen)
# bzw. ganzzahlige Composite-Punkte -- interpretiert je nach Hebel-Typ.
_Lever = tuple[float, str, TriageZone]


def _zone_flip_levers(
    *,
    benefit: float,
    composite: int,
    base_zone: TriageZone,
    classifier: ZoneClassifier,
) -> tuple[_Lever | None, _Lever | None]:
    """Naechster Nutzen-Hebel (%) und naechster Composite-Hebel (Punkte).

    Fuer beide Achsen der jeweils kleinste Ein-Hebel-Schritt, der die Basis-Zone
    kippt. Ein Hebel ist None, wenn auf dieser Achse kein Ein-Schritt-Kippen
    moeglich ist (z. B. MARGINAL_GAIN, wenn beide Achsen gleichzeitig blockieren).
    """
    lw_min = float(classifier.likely_win_min_benefit)
    lw_max_c = classifier.likely_win_max_composite
    cr_min = float(classifier.calculated_risk_min_benefit)
    cr_max_c = classifier.calculated_risk_max_composite

    benefit_cands: list[_Lever] = []
    composite_cands: list[_Lever] = []

    def pct(gap: float) -> float:
        return abs(gap) / benefit * 100.0 if benefit > 0 else float("inf")

    if base_zone == TriageZone.LIKELY_WIN:
        benefit_cands.append(
            (pct(benefit - lw_min), "weniger", TriageZone.CALCULATED_RISK)
        )
        composite_cands.append(
            (float(lw_max_c - composite + 1), "mehr", TriageZone.CALCULATED_RISK)
        )
    elif base_zone == TriageZone.CALCULATED_RISK:
        # Abstufung nach MARGINAL_GAIN (immer moeglich).
        benefit_cands.append(
            (pct(benefit - cr_min), "weniger", TriageZone.MARGINAL_GAIN)
        )
        composite_cands.append(
            (float(cr_max_c - composite + 1), "mehr", TriageZone.MARGINAL_GAIN)
        )
        # Hochstufung nach LIKELY_WIN -- nur wenn die jeweils andere Achse schon
        # qualifiziert.
        if composite <= lw_max_c:
            benefit_cands.append((pct(lw_min - benefit), "mehr", TriageZone.LIKELY_WIN))
        if benefit >= lw_min:
            composite_cands.append(
                (float(composite - lw_max_c), "weniger", TriageZone.LIKELY_WIN)
            )
    else:  # MARGINAL_GAIN -> Hochstufung nach CALCULATED_RISK
        if composite <= cr_max_c:
            benefit_cands.append(
                (pct(cr_min - benefit), "mehr", TriageZone.CALCULATED_RISK)
            )
        if benefit >= cr_min:
            composite_cands.append(
                (float(composite - cr_max_c), "weniger", TriageZone.CALCULATED_RISK)
            )

    benefit_lever = min(benefit_cands, key=lambda c: c[0]) if benefit_cands else None
    composite_lever = (
        min(composite_cands, key=lambda c: c[0]) if composite_cands else None
    )
    return benefit_lever, composite_lever


def _boundary_sentence(
    benefit_lever: _Lever | None,
    composite_lever: _Lever | None,
    base_zone: TriageZone,
    benefit_near: bool,
) -> str:
    """Formuliert den kleineren (naeheren) Hebel als Kipp-Satz."""
    # Normierter Abstand gegen die jeweilige "niedrig"-Schwelle (10 % / 1 Punkt):
    # der kleinere normierte Wert ist der naehere Hebel.
    b_norm = benefit_lever[0] / 10.0 if benefit_lever is not None else float("inf")
    c_norm = composite_lever[0] / 1.0 if composite_lever is not None else float("inf")
    use_benefit = benefit_lever is not None and b_norm <= c_norm
    from_label = ZONE_LABELS[base_zone]

    if use_benefit:
        assert benefit_lever is not None
        magnitude, richtung, ziel = benefit_lever
        pct_str = f"{round(magnitude, 1):g}"
        return (
            f"Mit {pct_str} % {richtung} erwartetem Nutzen kippt der Case von "
            f"{from_label} nach {ZONE_LABELS[ziel]}."
        )
    assert composite_lever is not None
    points, richtung, ziel = composite_lever
    n = int(points)
    punkt = "einem Aufwandspunkt" if n == 1 else f"{n} Aufwandspunkten"
    return (
        f"Mit {punkt} {richtung} kippt der Case von {from_label} "
        f"nach {ZONE_LABELS[ziel]}."
    )


# ---------------------------------------------------------------------------
# 3. Empfehlung als Satz
# ---------------------------------------------------------------------------

_RECOMMENDATION_TEMPLATES: dict[RoutingRecommendation, str] = {
    RoutingRecommendation.AUTOMATION_RECOMMENDED: (
        "Automatisierung empfohlen: rechnerisch {h} eingesparte Stunden pro Jahr "
        "({netto} EUR Netto-Nutzen) bei Aufwand {x} von 9 und {dp}."
    ),
    RoutingRecommendation.AI_RECOMMENDED: (
        "AI-Einsatz empfohlen: rechnerisch {h} eingesparte Stunden pro Jahr "
        "({netto} EUR Netto-Nutzen) bei Aufwand {x} von 9 und {dp}."
    ),
    RoutingRecommendation.HUMAN_REVIEW_REQUIRED: (
        "Vor Umsetzung fachliche Pruefung erforderlich: {h} eingesparte Stunden "
        "pro Jahr ({netto} EUR Netto-Nutzen) bei Aufwand {x} von 9 und {dp}."
    ),
    RoutingRecommendation.BORDERLINE: (
        "Mischsignale, Einzelfallpruefung empfohlen: {h} eingesparte Stunden pro "
        "Jahr ({netto} EUR Netto-Nutzen) bei Aufwand {x} von 9 und {dp}."
    ),
}


def build_recommendation_text(result: TriageResult, use_case: UseCaseInput) -> str:
    """Empfehlung als deutscher Satz -- feste Argument-Reihenfolge.

    Reihenfolge: eingesparte Stunden/Jahr -> Netto-Nutzen EUR -> Aufwand ->
    Datenschutzlage. Fuer den Vorfilter-Fail ein eigenes Template mit
    Klartext-Grund (inkl. "kein Zeitgewinn").
    """
    if (
        result.passed_vorfilter
        and result.roi is not None
        and result.composite is not None
    ):
        template = _RECOMMENDATION_TEMPLATES[result.routing.recommendation]
        return template.format(
            h=format_de(result.roi.hours_per_year),
            netto=format_de(result.roi.net_expected_benefit_eur),
            x=result.composite.total,
            dp=DATA_CLASSIFICATION_CLARTEXT[use_case.data_classification],
        )
    # Vorfilter-Fail: Klartext-Grund (kein Zeitgewinn hat Vorrang, V4-P3).
    if use_case.time_per_case_hours_with_ai >= use_case.time_per_case_hours_current:
        return (
            "Nicht zur Umsetzung empfohlen: der Vorgang mit KI ist nicht schneller "
            "als heute -- kein Zeitgewinn."
        )
    return (
        "Nicht zur Umsetzung empfohlen: Vorfilter nicht bestanden "
        f"({', '.join(result.vorfilter.failed_criteria)})."
    )


# ---------------------------------------------------------------------------
# 4. Entscheider-Report-Bausteine (zu_entscheiden, contra_punkte)
# ---------------------------------------------------------------------------

_ZU_ENTSCHEIDEN: dict[RoutingRecommendation, str] = {
    RoutingRecommendation.AUTOMATION_RECOMMENDED: (
        "Freigabe zur Umsetzung als klassische Automatisierung (ohne AI-Komponente)."
    ),
    RoutingRecommendation.AI_RECOMMENDED: ("Freigabe zur Umsetzung mit AI-Komponente."),
    RoutingRecommendation.HUMAN_REVIEW_REQUIRED: (
        "Freigabe einer vertieften fachlichen und datenschutzrechtlichen Pruefung "
        "vor der Umsetzung."
    ),
    RoutingRecommendation.BORDERLINE: (
        "Entscheidung ueber eine Einzelfallpruefung -- die Signale sind gemischt."
    ),
}

_ZU_ENTSCHEIDEN_FAIL = (
    "Keine Freigabe -- der Case erfuellt die Mindestkriterien des Vorfilters nicht."
)

# Immer verfuegbare, ehrliche Contra-Punkte (Fallback, wenn keine spezifischen
# greifen -- garantiert mindestens 2 produzierbare Punkte).
_CONTRA_FALLBACKS = (
    "Bewertung beruht vollstaendig auf Angaben des Einreichers; keine unabhaengige "
    "Validierung.",
    "Die Bewertung ist eine Ex-ante-Schaetzung -- der tatsaechliche Nutzen zeigt "
    "sich erst nach der Umsetzung.",
)

_MAX_CONTRA = 4


def build_zu_entscheiden(result: TriageResult) -> str:
    """Ein Satz, was das Board konkret freigeben soll (Template je Empfehlung)."""
    if not result.passed_vorfilter:
        return _ZU_ENTSCHEIDEN_FAIL
    return _ZU_ENTSCHEIDEN[result.routing.recommendation]


def build_contra_points(
    result: TriageResult,
    use_case: UseCaseInput,
    *,
    confidence: ConfidenceReasoning | None,
) -> tuple[str, ...]:
    """2-4 regelbasierte Contra-Saetze (KEIN LLM).

    Abgeleitet aus Evidenz, Verbindlichkeit, Datenschutz-/Kostenpunkten,
    Konfidenz-Zonennaehe und Zeitdelta. Mindestens 2 immer produzierbar --
    fehlen spezifische Punkte, greifen ehrliche Fallbacks.
    """
    contra: list[str] = []

    if use_case.evidence_level == EvidenceLevel.PURE_ESTIMATE:
        contra.append(
            "Der erwartete Nutzen beruht auf einer reinen Einschaetzung -- keine "
            "gemessene Grundlage."
        )
    if use_case.adoption_type == AdoptionType.VOLUNTARY:
        contra.append(
            "Die Nutzung ist freiwillig -- ohne Verbindlichkeit bleibt die "
            "tatsaechliche Adoption unsicher."
        )

    if result.composite is not None:
        if result.composite.data_protection_score >= 2:
            contra.append(
                "Besondere Kategorien personenbezogener Daten (Art. 9 DSGVO) -- "
                "Datenschutz-Folgenabschaetzung erforderlich."
            )
        elif result.composite.data_protection_score >= 1:
            contra.append(
                "Es werden personenbezogene Daten verarbeitet -- Datenschutzaufwand "
                "einplanen."
            )
        if result.composite.cost_score >= 1:
            contra.append(
                "Der Aufwandscore traegt Kostenpunkte (Lizenz- und/oder "
                "Implementierungskosten oberhalb der Schwelle)."
            )

    if confidence is not None and confidence.level == "niedrig":
        contra.append(
            "Der Case liegt nahe an einer Zonengrenze -- kleine Aenderungen an "
            "Nutzen oder Aufwand kippen die Einstufung."
        )

    time_delta = (
        use_case.time_per_case_hours_current - use_case.time_per_case_hours_with_ai
    )
    if time_delta <= 0:
        contra.append(
            "Der Vorgang spart mit KI keine Zeit -- der wirtschaftliche Nutzen ist "
            "fraglich."
        )
    elif time_delta < _KNAPP_HOURS:
        contra.append(
            "Die Zeitersparnis pro Vorgang ist mit unter 3 Minuten knapp -- der "
            "Nutzen haengt stark am Volumen."
        )

    # Mindestens 2 garantieren: mit ehrlichen Fallbacks auffuellen.
    for fallback in _CONTRA_FALLBACKS:
        if len(contra) >= 2:
            break
        if fallback not in contra:
            contra.append(fallback)

    return tuple(contra[:_MAX_CONTRA])


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def explain_triage(
    use_case: UseCaseInput,
    result: TriageResult,
    *,
    impl_cost_point_min_eur: float,
    license_cost_point_min_eur: float,
    classifier: ZoneClassifier,
) -> TriageExplanation:
    """Baut die vollstaendige Erklaerbarkeit eines TriageResult.

    score_breakdown/confidence sind None, wenn der Vorfilter nicht bestanden
    wurde (composite/zone None). recommendation_text ist immer gesetzt.
    """
    score_breakdown = (
        build_score_breakdown(
            use_case,
            result.composite,
            impl_cost_point_min_eur=impl_cost_point_min_eur,
            license_cost_point_min_eur=license_cost_point_min_eur,
        )
        if result.composite is not None
        else None
    )

    confidence = (
        build_confidence_reasoning(
            evidence_level=use_case.evidence_level,
            evidence_factor=result.roi.evidence_factor,
            expected_benefit_eur=result.roi.expected_benefit_eur,
            composite_total=result.composite.total,
            base_zone=result.zone.base_zone,
            classifier=classifier,
        )
        if result.zone is not None
        and result.roi is not None
        and result.composite is not None
        else None
    )

    return TriageExplanation(
        recommendation_text=build_recommendation_text(result, use_case),
        score_breakdown=score_breakdown,
        confidence=confidence,
    )
