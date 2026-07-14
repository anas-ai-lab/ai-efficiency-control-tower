"""Deterministische Erklaerbarkeit der Triage-Ergebnisse (V4-P6, SDR-0003).

Ziel: Keine nackte Zahl und kein rohes Enum erreicht den Nutzer. Alles
Regelbasierte wird hier deterministisch in Klartext uebersetzt -- Score-Herkunft,
Konfidenz-Begruendung, Empfehlungs-Satz, Machbarkeits-Definition und die
Contra-Punkte fuer den Entscheider-Report. LLM kommt hier NICHT vor; das ist
bewusst die Regel-Schicht (analog zones._build_reason / application/eval/
breakdown.py).

Sprache (V4.1-S6): Jede build_*-Funktion nimmt ein ``lang``-Argument
(Default ``de``) und zieht ihren Klartext aus den Sprachkatalogen
(domain/i18n). Zahlen/Formeln/Schwellen bleiben unveraendert -- nur der Wortlaut
ist sprachabhaengig. ``de`` reproduziert die frueheren Strings exakt.

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

from aect.domain.formatting import format_number
from aect.domain.i18n import (
    APPROACH_LABEL,
    BASIS_EINSTUFUNG_ERKLAERUNG,
    BELASTBARKEIT_EMPFEHLUNG_GRUND,
    BELASTBARKEIT_ZONE_SATZ,
    BERECHNUNG_LABELS,
    CONFIDENCE_LEVEL_DISPLAY,
    CONTRA_POINTS,
    COST_LABELS,
    DATA_CLASSIFICATION_CLARTEXT,
    DATA_PROTECTION_REASON,
    DEFAULT_LANG,
    EFFORT_ADJEKTIV,
    EFFORT_KLARTEXT,
    EFFORT_LABEL_DISPLAY,
    EMPFEHLUNG_ANSATZ,
    EVIDENCE_FAKTOR_GRUND,
    EXPLAIN_TEXT,
    FEASIBILITY_DEFINITION,
    NUTZEN_FORMEL_WORTE,
    RECOMMENDATION_TEMPLATES,
    SCORE_COMPONENT_LABELS,
    ZONE_LABELS,
    ZU_ENTSCHEIDEN,
    ZU_ENTSCHEIDEN_FAIL,
    Lang,
    localize_vorfilter_criteria,
)
from aect.domain.models import UseCaseInput
from aect.domain.pipeline import TriageResult
from aect.domain.routing import RoutingRecommendation
from aect.domain.scoring import CompositeScore
from aect.domain.types import (
    AdoptionType,
    EvidenceLevel,
    TriageZone,
)
from aect.domain.zones import ZoneClassifier

# ---------------------------------------------------------------------------
# Zentrale numerische Konstanten (Text lebt in domain/i18n)
# ---------------------------------------------------------------------------

#: Composite-Aufwandscore-Obergrenze (V4-Modell, siehe scoring.CompositeScore).
COMPOSITE_MAX_TOTAL = 9


def feasibility_from_composite(composite_total: int) -> int:
    """Machbarkeit aus dem Aufwandscore: 10 - Aufwandscore (Range 1-9)."""
    return 10 - composite_total


#: Zeitgewinn unterhalb dieser Schwelle (Stunden/Vorgang) gilt als "knapp"
#: (~3 Minuten) -- Methodik-Schwelle, keine Firmenzahl.
_KNAPP_HOURS = 0.05

#: Maximale Anzahl Contra-Punkte im Entscheider-Report.
_MAX_CONTRA = 4


# ---------------------------------------------------------------------------
# Ergebnis-Typen
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ScoreComponent:
    """Eine Komponente des Aufwandscores mit deterministischer Begruendung.

    key: stabiler Maschinen-Schluessel (complexity/cost/data_protection).
    label: Anzeige-Label (sprachabhaengig). wert/max: Punktwert und Maximum.
    begruendung: Klartext, aus den Eingaben abgeleitet (sprachabhaengig).
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

    level: "hoch" | "mittel" | "niedrig" (Maschinen-Key, sprachneutral).
    gruende: deterministische Klartext-Begruendungen (Evidenzlage,
    Zonengrenz-Naehe) -- sprachabhaengig.
    """

    level: str
    gruende: tuple[str, ...]


@dataclass(frozen=True)
class ManagementView:
    """Management-taugliche Ergebnis-Ebene (Ebene 1, V4.1-S5).

    Zwei Klartext-Saetze ohne interne Codes, Faktoren oder rohe Scores:
    zonen_satz fasst Nutzen, Aufwand und Belastbarkeit zusammen; empfehlung_satz
    nennt die Empfehlung als ganzen Satz samt Belastbarkeit. Nur fuer bewertete
    Cases gesetzt (sonst None am TriageExplanation).
    """

    zonen_satz: str
    empfehlung_satz: str


@dataclass(frozen=True)
class BerechnungsZeile:
    """Eine Zeile der Berechnungs-Ebene (Ebene 2, "Wie wurde das berechnet?").

    label: Anzeige-Label (z. B. "Erwarteter Nutzen"). wert: der Wert als fertig
    formatierte Zeichenkette (Betrag, Stufe, Score oder Zonen-Label).
    erklaerung: ein Satz Alltagssprache. Zahlenwerte identisch zu den
    bestehenden Feldern -- reine Sprach-Projektion.
    """

    label: str
    wert: str
    erklaerung: str


@dataclass(frozen=True)
class TriageExplanation:
    """Gebuendelte, deterministische Erklaerbarkeit eines TriageResult.

    score_breakdown/confidence/management/berechnung sind None, wenn der
    Vorfilter nicht bestanden wurde (dann sind composite/zone im TriageResult
    None). recommendation_text ist immer gesetzt (auch fuer den Vorfilter-Fail-
    Fall).

    management (Ebene 1) und berechnung (Ebene 2) sind die zweischichtige
    Ergebnisdarstellung (V4.1-S5): management fuer Entscheider ohne interne
    Codes, berechnung als aufklappbare Herkunft je Komponente.
    """

    recommendation_text: str
    score_breakdown: ScoreBreakdown | None
    confidence: ConfidenceReasoning | None
    management: ManagementView | None
    berechnung: tuple[BerechnungsZeile, ...] | None


# ---------------------------------------------------------------------------
# 1. Score-Herkunft
# ---------------------------------------------------------------------------


def build_score_breakdown(
    use_case: UseCaseInput,
    composite: CompositeScore,
    *,
    impl_cost_point_min_eur: float,
    license_cost_point_min_eur: float,
    lang: Lang = DEFAULT_LANG,
) -> ScoreBreakdown:
    """Baut die deterministische Herkunft des Aufwandscores.

    Jede Komponente traegt Wert, Maximum und eine aus den Eingaben generierte
    Begruendung (Umsetzungsansatz, Kostenschwellen, DSGVO-Mapping).
    """
    text = EXPLAIN_TEXT[lang]
    # Ein Score-Breakdown existiert nur fuer bewertete Cases (composite gesetzt);
    # ohne Ansatz gibt es keinen Composite (Vor-Bewertungs-Zustand, ADR-0050).
    assert use_case.implementation_approach is not None
    complexity_reason = text["complexity_reason"].format(
        approach=APPROACH_LABEL[lang][use_case.implementation_approach],
        n=composite.complexity_score,
    )

    cost_labels = COST_LABELS[lang]
    license_reason = _cost_point_reason(
        cost_labels["license"],
        use_case.estimated_license_cost_eur,
        license_cost_point_min_eur,
        suffix=cost_labels["per_year"],
        lang=lang,
    )
    impl_reason = _cost_point_reason(
        cost_labels["impl"],
        use_case.implementation_cost_eur,
        impl_cost_point_min_eur,
        lang=lang,
    )
    cost_reason = f"{license_reason}; {impl_reason}"

    data_reason = DATA_PROTECTION_REASON[lang][use_case.data_classification]

    comp_labels = SCORE_COMPONENT_LABELS[lang]
    components = (
        ScoreComponent(
            key="complexity",
            label=comp_labels["complexity"],
            wert=composite.complexity_score,
            max=5,
            begruendung=complexity_reason,
        ),
        ScoreComponent(
            key="cost",
            label=comp_labels["cost"],
            wert=composite.cost_score,
            max=2,
            begruendung=cost_reason,
        ),
        ScoreComponent(
            key="data_protection",
            label=comp_labels["data_protection"],
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
        total_line=text["total_line"].format(
            total=composite.total,
            max=COMPOSITE_MAX_TOTAL,
            effort=EFFORT_LABEL_DISPLAY[lang][composite.effort_label],
        ),
        feasibility_score=feasibility_from_composite(composite.total),
        feasibility_definition=FEASIBILITY_DEFINITION[lang],
    )


def _cost_point_reason(
    label: str,
    cost_eur: float,
    threshold_eur: float,
    *,
    suffix: str = "",
    lang: Lang = DEFAULT_LANG,
) -> str:
    """Begruendung eines Kostenpunkts: Wert gegen Schwelle, +1 oder kein Punkt."""
    text = EXPLAIN_TEXT[lang]
    key = "cost_point_plus" if cost_eur >= threshold_eur else "cost_point_none"
    return text[key].format(
        label=label,
        cost=format_number(cost_eur, lang, "EUR"),
        suffix=suffix,
        threshold=format_number(threshold_eur, lang, "EUR"),
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
    lang: Lang = DEFAULT_LANG,
) -> ConfidenceReasoning:
    """Konfidenz als {level, gruende} aus deterministischen Regeln.

    - Reine Einschaetzung (pure_estimate) -> Grund + Level hoechstens "mittel".
    - Zonengrenz-Naehe: der kleinere Hebel (Nutzen-% ODER Composite-Punkte, bis
      die Zone kippt) als Satz; Abstand < 10 % oder <= 1 Composite-Punkt ->
      "niedrig".
    - Sonst -> "hoch" mit deutlichem-Abstand-Grund.
    """
    text = EXPLAIN_TEXT[lang]
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
        gruende.append(text["pure_estimate_grund"].format(factor=factor_str))
    if near:
        gruende.append(
            _boundary_sentence(
                benefit_lever, composite_lever, base_zone, benefit_near, lang
            )
        )

    if near:
        level = "niedrig"
    elif is_pure_estimate:
        level = "mittel"
    else:
        level = "hoch"

    if not gruende:
        gruende.append(text["clear_margin_grund"])

    return ConfidenceReasoning(level=level, gruende=tuple(gruende))


# Ein Hebel: (magnitude, richtung, ziel_zone). magnitude ist Prozent (Nutzen)
# bzw. ganzzahlige Composite-Punkte -- interpretiert je nach Hebel-Typ.
# richtung ist ein interner Marker ("weniger"/"mehr"), am Response-Rand
# uebersetzt (siehe _boundary_sentence).
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
    lang: Lang,
) -> str:
    """Formuliert den kleineren (naeheren) Hebel als Kipp-Satz."""
    text = EXPLAIN_TEXT[lang]
    # Normierter Abstand gegen die jeweilige "niedrig"-Schwelle (10 % / 1 Punkt):
    # der kleinere normierte Wert ist der naehere Hebel.
    b_norm = benefit_lever[0] / 10.0 if benefit_lever is not None else float("inf")
    c_norm = composite_lever[0] / 1.0 if composite_lever is not None else float("inf")
    use_benefit = benefit_lever is not None and b_norm <= c_norm
    from_label = ZONE_LABELS[lang][base_zone]
    richtung = {"weniger": text["richtung_less"], "mehr": text["richtung_more"]}

    if use_benefit:
        assert benefit_lever is not None
        magnitude, direction, ziel = benefit_lever
        pct_str = f"{round(magnitude, 1):g}"
        return text["flip_benefit"].format(
            pct=pct_str,
            richtung=richtung[direction],
            from_zone=from_label,
            to_zone=ZONE_LABELS[lang][ziel],
        )
    assert composite_lever is not None
    points, direction, ziel = composite_lever
    n = int(points)
    punkt = text["point_singular"] if n == 1 else text["point_plural"].format(n=n)
    return text["flip_composite"].format(
        points=punkt,
        richtung=richtung[direction],
        from_zone=from_label,
        to_zone=ZONE_LABELS[lang][ziel],
    )


# ---------------------------------------------------------------------------
# 3. Empfehlung als Satz
# ---------------------------------------------------------------------------


def build_recommendation_text(
    result: TriageResult, use_case: UseCaseInput, lang: Lang = DEFAULT_LANG
) -> str:
    """Empfehlung als Satz -- feste Argument-Reihenfolge.

    Reihenfolge: eingesparte Stunden/Jahr -> Netto-Nutzen EUR -> Aufwand ->
    Datenschutzlage. Fuer den Vorfilter-Fail ein eigenes Template mit
    Klartext-Grund (inkl. "kein Zeitgewinn").

    evaluation_pending (ADR-0050): der Case wurde ohne Umsetzungsansatz
    eingereicht -- es gibt weder Routing noch Vorfilter-Ergebnis. Eigener
    Satz vor allen anderen Zweigen (die auf result.routing/result.vorfilter
    zugreifen, die hier None sind).
    """
    text = EXPLAIN_TEXT[lang]
    if result.evaluation_pending:
        return text["eval_pending"]
    # Nicht-pending: routing/vorfilter sind garantiert befuellt (ADR-0050).
    assert result.routing is not None
    assert result.vorfilter is not None
    if (
        result.passed_vorfilter
        and result.roi is not None
        and result.composite is not None
    ):
        template = RECOMMENDATION_TEMPLATES[lang][result.routing.recommendation.value]
        return template.format(
            h=format_number(result.roi.hours_per_year, lang),
            netto=format_number(result.roi.net_expected_benefit_eur, lang),
            x=result.composite.total,
            dp=DATA_CLASSIFICATION_CLARTEXT[lang][use_case.data_classification],
        )
    # Vorfilter-Fail: Klartext-Grund (kein Zeitgewinn hat Vorrang, V4-P3).
    if use_case.time_per_case_hours_with_ai >= use_case.time_per_case_hours_current:
        return text["not_recommended_no_time"]
    criteria = ", ".join(
        localize_vorfilter_criteria(result.vorfilter.failed_criteria, lang)
    )
    return text["not_recommended_prefilter"].format(criteria=criteria)


# ---------------------------------------------------------------------------
# 4. Entscheider-Report-Bausteine (zu_entscheiden, contra_punkte)
# ---------------------------------------------------------------------------


def build_zu_entscheiden(result: TriageResult, lang: Lang = DEFAULT_LANG) -> str:
    """Ein Satz, was das Board konkret freigeben soll (Template je Empfehlung)."""
    if not result.passed_vorfilter:
        return ZU_ENTSCHEIDEN_FAIL[lang]
    # passed_vorfilter True -> bewertet, routing befuellt (ADR-0050).
    assert result.routing is not None
    return ZU_ENTSCHEIDEN[lang][result.routing.recommendation.value]


def build_contra_points(
    result: TriageResult,
    use_case: UseCaseInput,
    *,
    confidence: ConfidenceReasoning | None,
    lang: Lang = DEFAULT_LANG,
) -> tuple[str, ...]:
    """2-4 regelbasierte Contra-Saetze (KEIN LLM).

    Abgeleitet aus Evidenz, Verbindlichkeit, Datenschutz-/Kostenpunkten,
    Konfidenz-Zonennaehe und Zeitdelta. Mindestens 2 immer produzierbar --
    fehlen spezifische Punkte, greifen ehrliche Fallbacks.
    """
    cp = CONTRA_POINTS[lang]
    contra: list[str] = []

    if use_case.evidence_level == EvidenceLevel.PURE_ESTIMATE:
        contra.append(cp["pure_estimate"])
    if use_case.adoption_type == AdoptionType.VOLUNTARY:
        contra.append(cp["voluntary"])

    if result.composite is not None:
        if result.composite.data_protection_score >= 2:
            contra.append(cp["data_sensitive"])
        elif result.composite.data_protection_score >= 1:
            contra.append(cp["data_personal"])
        if result.composite.cost_score >= 1:
            contra.append(cp["cost"])

    if confidence is not None and confidence.level == "niedrig":
        contra.append(cp["boundary"])

    time_delta = (
        use_case.time_per_case_hours_current - use_case.time_per_case_hours_with_ai
    )
    if time_delta <= 0:
        contra.append(cp["no_time"])
    elif time_delta < _KNAPP_HOURS:
        contra.append(cp["little_time"])

    # Mindestens 2 garantieren: mit ehrlichen Fallbacks auffuellen.
    for fallback in (cp["fallback_no_validation"], cp["fallback_ex_ante"]):
        if len(contra) >= 2:
            break
        if fallback not in contra:
            contra.append(fallback)

    return tuple(contra[:_MAX_CONTRA])


# ---------------------------------------------------------------------------
# 5. Management-Ebene (Ebene 1) + Berechnungs-Ebene (Ebene 2) -- V4.1-S5
# ---------------------------------------------------------------------------


def build_management_view(
    *,
    net_expected_benefit_eur: Decimal,
    effort_label: str,
    evidence_level: EvidenceLevel,
    confidence_level: str,
    recommendation: RoutingRecommendation,
    lang: Lang = DEFAULT_LANG,
) -> ManagementView:
    """Baut die Management-Ebene (zwei Klartext-Saetze, keine internen Codes).

    Informationsgehalt: Nutzen (EUR/Jahr), Aufwand (verbal), Belastbarkeit
    (Stufe + Grund) sowie die Empfehlung als ganzer Satz. Alle Zahlen kommen
    unveraendert aus dem bereits berechneten TriageResult -- reine Projektion.
    """
    text = EXPLAIN_TEXT[lang]
    level_display = CONFIDENCE_LEVEL_DISPLAY[lang][confidence_level]
    zonen_satz = text["zonen_satz"].format(
        eur=format_number(net_expected_benefit_eur, lang, "€"),
        adjektiv=EFFORT_ADJEKTIV[lang][effort_label],
        bel_zone=BELASTBARKEIT_ZONE_SATZ[lang][evidence_level],
        level=level_display,
    )
    empfehlung_satz = text["empfehlung_satz"].format(
        ansatz=EMPFEHLUNG_ANSATZ[lang][recommendation.value],
        level=level_display,
        grund=BELASTBARKEIT_EMPFEHLUNG_GRUND[lang][evidence_level],
    )
    return ManagementView(zonen_satz=zonen_satz, empfehlung_satz=empfehlung_satz)


def build_berechnung(
    *,
    net_expected_benefit_eur: Decimal,
    evidence_level: EvidenceLevel,
    evidence_factor: float,
    composite_total: int,
    effort_label: str,
    base_zone: TriageZone,
    confidence: ConfidenceReasoning,
    lang: Lang = DEFAULT_LANG,
) -> tuple[BerechnungsZeile, ...]:
    """Baut die Berechnungs-Ebene: je Komponente eine Zeile in Alltagssprache.

    Vier Zeilen: erwarteter Nutzen (Formel in Worten), Belastbarkeit (Stufe +
    uebersetzter Faktor), Aufwand (Score + verbale Einordnung) und die Basis-
    Einstufung vor der Handlungsdruck-Hochstufung (Zonen-Label statt Code).
    """
    text = EXPLAIN_TEXT[lang]
    labels = BERECHNUNG_LABELS[lang]
    evidence_pct = round(evidence_factor * 100)
    belastbarkeit_erklaerung = text["belastbarkeit_erklaerung"].format(
        pct=evidence_pct,
        grund=EVIDENCE_FAKTOR_GRUND[lang][evidence_level],
    )
    # Zonengrenz-Naehe (falls vorhanden) als Zusatz -- faktorfrei, nennt den
    # kleineren Kipp-Hebel. Wiederverwendung der Konfidenz-Gruende (kein zweiter
    # Rechenweg): der Kipp-Satz enthaelt das sprachweise Marker-Wort ("kippt"/
    # "flips"). confidence wurde in derselben Sprache gebaut -> Marker passt.
    flip = next((g for g in confidence.gruende if text["flip_marker"] in g), None)
    if flip is not None:
        belastbarkeit_erklaerung = f"{belastbarkeit_erklaerung} {flip}"

    return (
        BerechnungsZeile(
            label=labels["benefit"],
            wert=text["benefit_per_year"].format(
                eur=format_number(net_expected_benefit_eur, lang, "€")
            ),
            erklaerung=NUTZEN_FORMEL_WORTE[lang],
        ),
        BerechnungsZeile(
            label=labels["confidence"],
            wert=CONFIDENCE_LEVEL_DISPLAY[lang][confidence.level],
            erklaerung=belastbarkeit_erklaerung,
        ),
        BerechnungsZeile(
            label=labels["effort"],
            wert=f"{composite_total} / {COMPOSITE_MAX_TOTAL}",
            erklaerung=EFFORT_KLARTEXT[lang][effort_label],
        ),
        BerechnungsZeile(
            label=labels["base_zone"],
            wert=ZONE_LABELS[lang][base_zone],
            erklaerung=BASIS_EINSTUFUNG_ERKLAERUNG[lang],
        ),
    )


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
    lang: Lang = DEFAULT_LANG,
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
            lang=lang,
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
            lang=lang,
        )
        if result.zone is not None
        and result.roi is not None
        and result.composite is not None
        else None
    )

    # Ebene 1 + Ebene 2 (V4.1-S5): nur fuer bewertete Cases -- sie brauchen
    # roi/composite/zone/routing und die bereits gebaute Konfidenz-Begruendung.
    management: ManagementView | None = None
    berechnung: tuple[BerechnungsZeile, ...] | None = None
    if (
        confidence is not None
        and result.roi is not None
        and result.composite is not None
        and result.zone is not None
        and result.routing is not None
    ):
        management = build_management_view(
            net_expected_benefit_eur=result.roi.net_expected_benefit_eur,
            effort_label=result.composite.effort_label,
            evidence_level=use_case.evidence_level,
            confidence_level=confidence.level,
            recommendation=result.routing.recommendation,
            lang=lang,
        )
        berechnung = build_berechnung(
            net_expected_benefit_eur=result.roi.net_expected_benefit_eur,
            evidence_level=use_case.evidence_level,
            evidence_factor=result.roi.evidence_factor,
            composite_total=result.composite.total,
            effort_label=result.composite.effort_label,
            base_zone=result.zone.base_zone,
            confidence=confidence,
            lang=lang,
        )

    return TriageExplanation(
        recommendation_text=build_recommendation_text(result, use_case, lang),
        score_breakdown=score_breakdown,
        confidence=confidence,
        management=management,
        berechnung=berechnung,
    )
