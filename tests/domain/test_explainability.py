"""Tests fuer die deterministische Erklaerbarkeit (V4-P6, domain/explainability).

Deckt Score-Herkunft (parametrisiert inkl. 1-9-Grenzfaelle), Konfidenz-Regeln,
Empfehlungs-Templates aller Auspraegungen, Contra-Ableitung und die
Machbarkeits-Formel ab.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from aect.domain.explainability import (
    FEASIBILITY_DEFINITION,
    ZONE_LABELS,
    build_berechnung,
    build_confidence_reasoning,
    build_contra_points,
    build_management_view,
    build_recommendation_text,
    build_routing_begruendung,
    build_score_breakdown,
    build_zu_entscheiden,
    feasibility_from_composite,
)
from aect.domain.feasibility import FeasibilityResult
from aect.domain.filters import FilterResult
from aect.domain.models import UseCaseInput
from aect.domain.pipeline import TriageResult
from aect.domain.roi import ROIResult
from aect.domain.routing import RoutingRecommendation, RoutingResult
from aect.domain.scoring import CompositeScore, compute_composite_score
from aect.domain.types import (
    AdoptionType,
    Country,
    DataClassification,
    EmployeeCategory,
    EvidenceLevel,
    ImplementationApproach,
    TriageZone,
)
from aect.domain.zones import ZoneClassifier, ZoneResult

# Feste Zonen-Schwellen (identisch zu config/zone_thresholds.yaml).
_LW_MIN = Decimal("50000")
_LW_MAX_C = 4
_CR_MIN = Decimal("5000")
_CR_MAX_C = 7


@pytest.fixture
def clf() -> ZoneClassifier:
    return ZoneClassifier(
        likely_win_min_benefit=_LW_MIN,
        likely_win_max_composite=_LW_MAX_C,
        calculated_risk_min_benefit=_CR_MIN,
        calculated_risk_max_composite=_CR_MAX_C,
        handlungsdruck_elevation_threshold=4,
    )


def _uc(**overrides: object) -> UseCaseInput:
    defaults: dict[str, object] = {
        "title": "Erklaerbarkeits-Testfall",
        "submitter": "Tester",
        "department": "IT",
        "country": Country.DE,
        "current_state": (
            "Aktuell wird der Vorgang manuell bearbeitet und bindet viel Zeit im "
            "Team ohne technische Unterstuetzung."
        ),
        "desired_state": (
            "Ein AI-System uebernimmt die Routine und legt nur Zweifelsfaelle vor."
        ),
        "example_process": "Ein einzelner Vorgang dauert rund 12 Minuten.",
        "time_per_case_hours_current": 0.2,
        "time_per_case_hours_with_ai": 0.0,
        "occurrences_per_employee_per_year": 5000,
        "affected_employees_count": 10,
        "employee_category": EmployeeCategory.PROFESSIONAL,
        "evidence_level": EvidenceLevel.TESTED_PILOTED,
        "adoption_type": AdoptionType.FIXED_PROCESS_STEP,
        "implementation_approach": ImplementationApproach.CUSTOM_DEVELOPMENT,
        "estimated_license_cost_eur": 0.0,
        "implementation_cost_eur": 0.0,
        "data_classification": DataClassification.NO_PERSONAL_DATA,
    }
    defaults.update(overrides)
    return UseCaseInput.model_validate(defaults)


# ---------------------------------------------------------------------------
# Machbarkeit (Formel-Verifikation)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("composite_total", "expected"),
    [(1, 9), (4, 6), (6, 4), (9, 1)],
)
def test_feasibility_formula_range_1_to_9(composite_total: int, expected: int) -> None:
    # 10 - Aufwandscore: bei Aufwandscore 1-9 (Step-0-Range) liegt Machbarkeit
    # ebenfalls in 1-9 -- verifiziert, nicht angenommen.
    assert feasibility_from_composite(composite_total) == expected


def test_feasibility_definition_states_formula() -> None:
    assert "10 - Aufwandscore" in FEASIBILITY_DEFINITION["de"]


# ---------------------------------------------------------------------------
# Score-Herkunft (parametrisiert)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("approach", "complexity"),
    [
        (ImplementationApproach.SIMPLE_INTEGRATION, 1),
        (ImplementationApproach.DEVELOPMENT_ON_EXISTING, 2),
        (ImplementationApproach.API_INTEGRATION, 3),
        (ImplementationApproach.CUSTOM_DEVELOPMENT, 4),
        (ImplementationApproach.NEW_TOOL, 5),
    ],
)
def test_complexity_component_reason(
    approach: ImplementationApproach, complexity: int
) -> None:
    composite = compute_composite_score(
        approach, 0.0, 0.0, DataClassification.NO_PERSONAL_DATA
    )
    breakdown = build_score_breakdown(
        _uc(implementation_approach=approach),
        composite,
        impl_cost_point_min_eur=10_000.0,
        license_cost_point_min_eur=10_000.0,
    )
    complexity_comp = breakdown.components[0]
    assert complexity_comp.key == "complexity"
    assert complexity_comp.wert == complexity
    assert complexity_comp.max == 5
    assert f"Komplexität {complexity} von 5" in complexity_comp.begruendung


@pytest.mark.parametrize(
    ("license_cost", "expected_text"),
    [
        # Nur Lizenzkosten ueber der Schwelle -> ein Satz, der genau das sagt.
        (
            10_000.0,
            "Lizenzkosten ab 10.000 EUR -- +1 Aufwandspunkt; "
            "Implementierungskosten darunter.",
        ),
        (
            14_000.0,
            "Lizenzkosten ab 10.000 EUR -- +1 Aufwandspunkt; "
            "Implementierungskosten darunter.",
        ),
        # Beide darunter -> ein kompakter Satz statt zweier Vergleichsketten.
        (
            9_999.99,
            "Lizenz- und Implementierungskosten unter 10.000 EUR -- keine Aufwandspunkte.",
        ),
        (
            0.0,
            "Lizenz- und Implementierungskosten unter 10.000 EUR -- keine Aufwandspunkte.",
        ),
    ],
)
def test_cost_component_threshold_boundary(
    license_cost: float, expected_text: str
) -> None:
    """V4.1-S9: die Kostenbegruendung ist EIN Satz je Ausgang.

    Die Schwellen-Grenze bleibt exakt wie in compute_composite_score (>= gibt
    den Punkt, 9_999.99 nicht) -- geprueft ueber den Wortlaut UND den Punktwert.
    """
    composite = compute_composite_score(
        ImplementationApproach.CUSTOM_DEVELOPMENT,
        0.0,
        license_cost,
        DataClassification.NO_PERSONAL_DATA,
    )
    breakdown = build_score_breakdown(
        _uc(estimated_license_cost_eur=license_cost),
        composite,
        impl_cost_point_min_eur=10_000.0,
        license_cost_point_min_eur=10_000.0,
    )
    cost_comp = breakdown.components[1]
    assert cost_comp.key == "cost"
    assert cost_comp.begruendung == expected_text
    # Der Text folgt dem Punktwert, er behauptet nichts Eigenes.
    assert cost_comp.wert == (1 if license_cost >= 10_000.0 else 0)
    # Die frueheren Vergleichsketten sind weg (Erfolgskriterium Punkt 3).
    assert "->" not in cost_comp.begruendung
    assert "kein Punkt" not in cost_comp.begruendung


def test_cost_reason_names_both_thresholds_when_they_differ() -> None:
    """Die zwei Kostenschwellen sind getrennte Config-Keys. Weichen sie ab, muss
    der kompakte Satz beide nennen -- sonst waere er schlicht falsch."""
    composite = compute_composite_score(
        ImplementationApproach.CUSTOM_DEVELOPMENT,
        0.0,
        0.0,
        DataClassification.NO_PERSONAL_DATA,
        impl_cost_point_min_eur=5_000.0,
        license_cost_point_min_eur=10_000.0,
    )
    breakdown = build_score_breakdown(
        _uc(estimated_license_cost_eur=0.0, implementation_cost_eur=0.0),
        composite,
        impl_cost_point_min_eur=5_000.0,
        license_cost_point_min_eur=10_000.0,
    )
    begruendung = breakdown.components[1].begruendung
    assert "10.000 EUR" in begruendung
    assert "5.000 EUR" in begruendung


@pytest.mark.parametrize(
    ("classification", "score", "fragment"),
    [
        (DataClassification.NO_PERSONAL_DATA, 0, "Keine personenbezogenen Daten"),
        (DataClassification.PSEUDONYMOUS, 1, "Pseudonyme Daten"),
        (DataClassification.PERSONAL, 1, "Art. 4 DSGVO"),
        (DataClassification.SENSITIVE_PERSONAL, 2, "Art. 9 DSGVO"),
    ],
)
def test_data_protection_component_reason(
    classification: DataClassification, score: int, fragment: str
) -> None:
    composite = compute_composite_score(
        ImplementationApproach.CUSTOM_DEVELOPMENT, 0.0, 0.0, classification
    )
    breakdown = build_score_breakdown(
        _uc(data_classification=classification),
        composite,
        impl_cost_point_min_eur=10_000.0,
        license_cost_point_min_eur=10_000.0,
    )
    data_comp = breakdown.components[2]
    assert data_comp.key == "data_protection"
    assert data_comp.wert == score
    assert fragment in data_comp.begruendung


@pytest.mark.parametrize(
    ("approach", "impl", "lic", "classification", "total", "label"),
    [
        # Untere Grenze der 1-9-Range.
        (
            ImplementationApproach.SIMPLE_INTEGRATION,
            0.0,
            0.0,
            DataClassification.NO_PERSONAL_DATA,
            1,
            "NIEDRIG",
        ),
        # Obere Grenze der 1-9-Range.
        (
            ImplementationApproach.NEW_TOOL,
            10_000.0,
            10_000.0,
            DataClassification.SENSITIVE_PERSONAL,
            9,
            "HOCH",
        ),
    ],
)
def test_total_line_and_feasibility_at_range_bounds(
    approach: ImplementationApproach,
    impl: float,
    lic: float,
    classification: DataClassification,
    total: int,
    label: str,
) -> None:
    composite = compute_composite_score(approach, impl, lic, classification)
    breakdown = build_score_breakdown(
        _uc(
            implementation_approach=approach,
            implementation_cost_eur=impl,
            estimated_license_cost_eur=lic,
            data_classification=classification,
        ),
        composite,
        impl_cost_point_min_eur=10_000.0,
        license_cost_point_min_eur=10_000.0,
    )
    assert breakdown.total == total
    assert breakdown.max_total == 9
    assert breakdown.total_line == f"Aufwandscore {total} von 9 -> {label}"
    assert breakdown.feasibility_score == 10 - total
    assert breakdown.feasibility_definition == FEASIBILITY_DEFINITION["de"]


# ---------------------------------------------------------------------------
# Konfidenz-Regeln
# ---------------------------------------------------------------------------


def test_confidence_pure_estimate_caps_at_mittel(clf: ZoneClassifier) -> None:
    # Tief im Band (kein Grenzfall), aber reine Einschaetzung -> hoechstens mittel.
    conf = build_confidence_reasoning(
        evidence_level=EvidenceLevel.PURE_ESTIMATE,
        evidence_factor=0.40,
        expected_benefit_eur=Decimal("200000"),
        composite_total=2,
        base_zone=TriageZone.LIKELY_WIN,
        classifier=clf,
    )
    assert conf.level == "mittel"
    assert any("reiner Einschätzung" in g and "0,40" in g for g in conf.gruende)


def test_confidence_high_when_measured_and_far(clf: ZoneClassifier) -> None:
    conf = build_confidence_reasoning(
        evidence_level=EvidenceLevel.TESTED_PILOTED,
        evidence_factor=0.90,
        expected_benefit_eur=Decimal("200000"),
        composite_total=2,
        base_zone=TriageZone.LIKELY_WIN,
        classifier=clf,
    )
    assert conf.level == "hoch"
    assert any("deutlicher Abstand" in g for g in conf.gruende)


def test_confidence_low_near_composite_boundary(clf: ZoneClassifier) -> None:
    # composite == cr_max_c (7): genau 1 Punkt bis MARGINAL_GAIN -> niedrig.
    conf = build_confidence_reasoning(
        evidence_level=EvidenceLevel.TESTED_PILOTED,
        evidence_factor=0.90,
        expected_benefit_eur=Decimal("20000"),
        composite_total=7,
        base_zone=TriageZone.CALCULATED_RISK,
        classifier=clf,
    )
    assert conf.level == "niedrig"
    grund = " ".join(conf.gruende)
    assert "Aufwandspunkt" in grund
    assert ZONE_LABELS["de"][TriageZone.CALCULATED_RISK] in grund
    assert ZONE_LABELS["de"][TriageZone.MARGINAL_GAIN] in grund


def test_confidence_low_near_benefit_boundary(clf: ZoneClassifier) -> None:
    # Nur knapp ueber der LIKELY_WIN-Nutzenschwelle -> < 10 % -> niedrig,
    # Nutzen-Hebel als Satz.
    conf = build_confidence_reasoning(
        evidence_level=EvidenceLevel.TESTED_PILOTED,
        evidence_factor=0.90,
        expected_benefit_eur=Decimal("52000"),
        composite_total=2,
        base_zone=TriageZone.LIKELY_WIN,
        classifier=clf,
    )
    assert conf.level == "niedrig"
    grund = " ".join(conf.gruende)
    assert "%" in grund
    assert "weniger erwartetem Nutzen" in grund
    assert ZONE_LABELS["de"][TriageZone.LIKELY_WIN] in grund


def test_confidence_level_always_valid(clf: ZoneClassifier) -> None:
    for zone in TriageZone:
        conf = build_confidence_reasoning(
            evidence_level=EvidenceLevel.SIMILAR_PROJECT,
            evidence_factor=0.55,
            expected_benefit_eur=Decimal("30000"),
            composite_total=5,
            base_zone=zone,
            classifier=clf,
        )
        assert conf.level in {"hoch", "mittel", "niedrig"}
        assert len(conf.gruende) >= 1


# ---------------------------------------------------------------------------
# Empfehlung als Satz (alle Auspraegungen)
# ---------------------------------------------------------------------------


def _passing_result(
    recommendation: RoutingRecommendation,
    *,
    hours: float = 1000.0,
    netto: Decimal = Decimal("120000"),
) -> TriageResult:
    roi = ROIResult(
        theoretical_potential_eur=Decimal("300000"),
        usage_factor=0.9,
        evidence_factor=0.9,
        expected_benefit_eur=Decimal("200000"),
        license_cost_annual_eur=Decimal("0"),
        net_expected_benefit_eur=netto,
        hours_per_year=hours,
        time_saved_per_case_hours=0.2,
        passes_prefilter=True,
        prefilter_fail_reason=None,
    )
    # Aufwandscore 5 (Komplexitaet 3 + Kosten 1 + Datenschutz 1); Tests, die einen
    # anderen Composite brauchen, ueberschreiben ihn via object.__setattr__.
    composite = CompositeScore(
        complexity_score=3, cost_score=1, data_protection_score=1, total=5
    )
    zone = ZoneResult(
        base_zone=TriageZone.CALCULATED_RISK,
        final_zone=TriageZone.CALCULATED_RISK,
        handlungsdruck_elevated=False,
        reason="",
        confidence_score=0.83,
        confidence_label="mittel",
    )
    routing = RoutingResult(
        recommendation=recommendation,
        confidence="HIGH",
        automation_signals=(),
        ai_signals=(),
        risk_flags=(),
    )
    return TriageResult(
        title="T",
        passed_vorfilter=True,
        vorfilter=FilterResult(passes=True, failed_criteria=[], details={}),
        routing=routing,
        feasibility=FeasibilityResult(is_feasible=True, flags=(), recommendation=None),
        roi=roi,
        composite=composite,
        zone=zone,
    )


@pytest.mark.parametrize(
    ("recommendation", "prefix"),
    [
        (RoutingRecommendation.AUTOMATION_RECOMMENDED, "Automatisierung empfohlen"),
        (RoutingRecommendation.AI_RECOMMENDED, "AI-Einsatz empfohlen"),
        (
            RoutingRecommendation.HUMAN_REVIEW_REQUIRED,
            "Vor Umsetzung fachliche Prüfung erforderlich",
        ),
        (RoutingRecommendation.BORDERLINE, "Mischsignale"),
    ],
)
def test_recommendation_templates_all_variants(
    recommendation: RoutingRecommendation, prefix: str
) -> None:
    result = _passing_result(recommendation)
    text = build_recommendation_text(result, _uc())
    assert text.startswith(prefix)
    # Feste Argument-Reihenfolge: Stunden -> Netto -> Aufwand -> Datenschutz.
    assert "eingesparte Stunden pro Jahr" in text
    assert "Netto-Nutzen" in text
    assert "Aufwand 5 von 9" in text
    assert "keine personenbezogenen Daten" in text


def test_recommendation_prefilter_fail_names_reason() -> None:
    # Winziger Case -> Vorfilter-Fail -> Klartext-Grund.
    tiny = _uc(
        occurrences_per_employee_per_year=5,
        affected_employees_count=1,
        time_per_case_hours_current=0.01,
    )
    from aect.domain import evaluate_use_case
    from aect.domain.roi import load_roi_config

    result = evaluate_use_case(tiny, load_roi_config())
    text = build_recommendation_text(result, tiny)
    assert text.startswith("Nicht zur Umsetzung empfohlen: Vorfilter nicht bestanden")


def test_recommendation_no_time_gain() -> None:
    # with_ai == current -> kein Zeitgewinn (V4-P3).
    no_gain = _uc(time_per_case_hours_current=0.2, time_per_case_hours_with_ai=0.2)
    from aect.domain import evaluate_use_case
    from aect.domain.roi import load_roi_config

    result = evaluate_use_case(no_gain, load_roi_config())
    text = build_recommendation_text(result, no_gain)
    assert "kein Zeitgewinn" in text


# ---------------------------------------------------------------------------
# Contra-Ableitung + zu_entscheiden
# ---------------------------------------------------------------------------


def test_contra_points_derive_specific_reasons(clf: ZoneClassifier) -> None:
    result = _passing_result(RoutingRecommendation.BORDERLINE)
    use_case = _uc(
        evidence_level=EvidenceLevel.PURE_ESTIMATE,
        adoption_type=AdoptionType.VOLUNTARY,
    )
    conf = build_confidence_reasoning(
        evidence_level=EvidenceLevel.PURE_ESTIMATE,
        evidence_factor=0.40,
        expected_benefit_eur=Decimal("200000"),
        composite_total=2,
        base_zone=TriageZone.LIKELY_WIN,
        classifier=clf,
    )
    contra = build_contra_points(result, use_case, confidence=conf)
    joined = " ".join(contra)
    assert "reinen Einschätzung" in joined
    assert "freiwillig" in joined
    assert 2 <= len(contra) <= 4


def test_contra_points_always_at_least_two_with_fallback() -> None:
    # "Perfekter" Case: gemessen, verbindlich, keine PII, keine Kosten -> keine
    # spezifischen Contras -> ehrliche Fallbacks fuellen auf mindestens 2 auf.
    result = _passing_result(RoutingRecommendation.AUTOMATION_RECOMMENDED)
    object.__setattr__(
        result,
        "composite",
        CompositeScore(
            complexity_score=1, cost_score=0, data_protection_score=0, total=1
        ),
    )
    use_case = _uc(
        evidence_level=EvidenceLevel.TESTED_PILOTED,
        adoption_type=AdoptionType.FIXED_PROCESS_STEP,
    )
    contra = build_contra_points(result, use_case, confidence=None)
    assert len(contra) >= 2
    assert any("Angaben des Einreichers" in c for c in contra)


def test_contra_points_sensitive_data() -> None:
    result = _passing_result(RoutingRecommendation.HUMAN_REVIEW_REQUIRED)
    object.__setattr__(
        result,
        "composite",
        CompositeScore(
            complexity_score=3, cost_score=1, data_protection_score=2, total=6
        ),
    )
    contra = build_contra_points(
        result,
        _uc(data_classification=DataClassification.SENSITIVE_PERSONAL),
        confidence=None,
    )
    assert any("Art. 9 DSGVO" in c for c in contra)


@pytest.mark.parametrize(
    ("recommendation", "fragment"),
    [
        (RoutingRecommendation.AUTOMATION_RECOMMENDED, "klassische Automatisierung"),
        (RoutingRecommendation.AI_RECOMMENDED, "mit AI-Komponente"),
        (RoutingRecommendation.HUMAN_REVIEW_REQUIRED, "Prüfung"),
        (RoutingRecommendation.BORDERLINE, "Einzelfallprüfung"),
    ],
)
def test_zu_entscheiden_per_recommendation(
    recommendation: RoutingRecommendation, fragment: str
) -> None:
    result = _passing_result(recommendation)
    assert fragment in build_zu_entscheiden(result)


# ---------------------------------------------------------------------------
# Management-Ebene (Ebene 1) + Berechnungs-Ebene (Ebene 2) -- V4.1-S5
# ---------------------------------------------------------------------------

# Ebene-1-Verbote (Task A): keine internen Codes/Faktoren/Scores duerfen in den
# Management-Saetzen erscheinen.
_EBENE1_VERBOTE = (
    "LIKELY_WIN",
    "CALCULATED_RISK",
    "MARGINAL_GAIN",
    "Faktor",
    "von 9",
    "Basis-Zone",
    "Composite",
    "composite",
)


def test_management_view_summarises_without_internal_codes() -> None:
    mv = build_management_view(
        net_expected_benefit_eur=Decimal("164929"),
        effort_label="NIEDRIG",
        evidence_level=EvidenceLevel.PURE_ESTIMATE,
        recommendation=RoutingRecommendation.AUTOMATION_RECOMMENDED,
    )
    # Nutzen (EUR/Jahr) und Aufwand (verbal) im Satz -- die Datenlage in
    # Alltagssprache dahinter.
    assert "164.929 €" in mv.zonen_satz
    assert "niedrigem Umsetzungsaufwand" in mv.zonen_satz
    assert "Einschätzungen ohne Belege" in mv.zonen_satz
    # Empfehlung als ganzer Satz -- die Begruendung liefert routing.begruendung.
    assert mv.empfehlung_satz == "Empfehlung: Automatisierung (regelbasiert, ohne KI)."
    for banned in _EBENE1_VERBOTE:
        assert banned not in mv.zonen_satz
        assert banned not in mv.empfehlung_satz


def test_management_view_never_shows_belastbarkeit_level() -> None:
    """Erfolgskriterium Punkt 1: kein "Belastbarkeit <Stufe>" mehr -- fuer JEDE
    Kombination aus Evidenzlage und Empfehlung, nicht nur die geprueften."""
    for evidence in EvidenceLevel:
        for recommendation in RoutingRecommendation:
            mv = build_management_view(
                net_expected_benefit_eur=Decimal("50000"),
                effort_label="MITTEL",
                evidence_level=evidence,
                recommendation=recommendation,
                lang="de",
            )
            assert "Belastbarkeit" not in mv.zonen_satz
            assert "Belastbarkeit" not in mv.empfehlung_satz
            mv_en = build_management_view(
                net_expected_benefit_eur=Decimal("50000"),
                effort_label="MITTEL",
                evidence_level=evidence,
                recommendation=recommendation,
                lang="en",
            )
            assert "onfidence" not in mv_en.zonen_satz
            assert "onfidence" not in mv_en.empfehlung_satz


@pytest.mark.parametrize(
    ("effort_label", "adjektiv"),
    [("NIEDRIG", "niedrigem"), ("MITTEL", "mittlerem"), ("HOCH", "hohem")],
)
def test_management_view_effort_adjektiv(effort_label: str, adjektiv: str) -> None:
    mv = build_management_view(
        net_expected_benefit_eur=Decimal("120000"),
        effort_label=effort_label,
        evidence_level=EvidenceLevel.TESTED_PILOTED,
        recommendation=RoutingRecommendation.AI_RECOMMENDED,
    )
    assert f"bei {adjektiv} Umsetzungsaufwand" in mv.zonen_satz


def test_berechnung_three_rows_translate_code(clf: ZoneClassifier) -> None:
    """V4.1-S9: die Belastbarkeits-Zeile (Stufe + "40 % des theoretischen
    Potenzials") ist raus -- drei Zeilen bleiben."""
    conf = build_confidence_reasoning(
        evidence_level=EvidenceLevel.PURE_ESTIMATE,
        evidence_factor=0.40,
        expected_benefit_eur=Decimal("200000"),
        composite_total=2,
        base_zone=TriageZone.LIKELY_WIN,
        classifier=clf,
    )
    rows = build_berechnung(
        net_expected_benefit_eur=Decimal("164929"),
        composite_total=3,
        effort_label="NIEDRIG",
        base_zone=TriageZone.LIKELY_WIN,
        confidence=conf,
    )
    by = {r.label: r for r in rows}
    assert [r.label for r in rows] == [
        "Erwarteter Nutzen",
        "Aufwand",
        "Basis-Einstufung vor Dämpfung",
    ]
    assert "164.929 €" in by["Erwarteter Nutzen"].wert
    assert "Minuten pro Vorgang" in by["Erwarteter Nutzen"].erklaerung
    assert by["Aufwand"].wert == "3 / 9"
    assert by["Aufwand"].erklaerung == "niedrig -- kurzfristig umsetzbar"
    # Deutsches Label statt Enum-Code (zentrale ZONE_LABELS-Map).
    assert (
        by["Basis-Einstufung vor Dämpfung"].wert
        == ZONE_LABELS["de"][TriageZone.LIKELY_WIN]
    )
    joined = " ".join(r.wert + r.erklaerung for r in rows)
    for banned in ("LIKELY_WIN", "CALCULATED_RISK", "MARGINAL_GAIN"):
        assert banned not in joined
    # Erfolgskriterium Punkt 1: weder Label noch der 40-%-Erklaersatz.
    assert "Belastbarkeit" not in joined
    assert "des theoretischen Potenzials" not in joined


def test_berechnung_base_zone_row_carries_boundary_flip(clf: ZoneClassifier) -> None:
    """Der Kipp-Hinweis ueberlebt den Wegfall der Belastbarkeits-Zeile: er haengt
    jetzt an der Basis-Einstufung -- er beschreibt genau deren Kippen."""
    # Genau 1 Composite-Punkt bis MARGINAL_GAIN -> Konfidenz niedrig, Kipp-Satz.
    conf = build_confidence_reasoning(
        evidence_level=EvidenceLevel.TESTED_PILOTED,
        evidence_factor=0.90,
        expected_benefit_eur=Decimal("20000"),
        composite_total=7,
        base_zone=TriageZone.CALCULATED_RISK,
        classifier=clf,
    )
    rows = build_berechnung(
        net_expected_benefit_eur=Decimal("20000"),
        composite_total=7,
        effort_label="HOCH",
        base_zone=TriageZone.CALCULATED_RISK,
        confidence=conf,
    )
    base_zone_row = next(r for r in rows if r.label == "Basis-Einstufung vor Dämpfung")
    assert "kippt" in base_zone_row.erklaerung
    # Die Faktor-Prozentzahl bleibt draussen.
    assert "des theoretischen Potenzials" not in base_zone_row.erklaerung


# ---------------------------------------------------------------------------
# Routing-Begruendung (V4.1-S9, Punkt 5)
# ---------------------------------------------------------------------------


def test_routing_begruendung_names_the_decisive_criteria() -> None:
    """Erfolgskriterium Punkt 5: die Empfehlung traegt IMMER eine fallspezifische
    Begruendung -- kein generischer Satz. Der eindeutige Automation-Fall nennt
    die erkannten Automation-Kriterien und sagt, dass fuer KI keines sprach."""
    begruendung = build_routing_begruendung(
        recommendation=RoutingRecommendation.AUTOMATION_RECOMMENDED,
        automation_signals=(
            "Komplexität 2 <= 2 -- einfacher Ablauf",
            "Fester Prozessschritt",
        ),
        ai_signals=(),
        risk_flags=(),
    )
    assert "kein Kriterium sprach für KI" in begruendung
    assert "Komplexität 2 <= 2 -- einfacher Ablauf" in begruendung
    assert "Fester Prozessschritt" in begruendung


def test_routing_begruendung_mixed_signals_says_majority_decided() -> None:
    """Gemischte Signale (beide Seiten haben Kriterien): der Text darf NICHT
    behaupten, die Gegenseite habe nichts vorzuweisen."""
    begruendung = build_routing_begruendung(
        recommendation=RoutingRecommendation.AUTOMATION_RECOMMENDED,
        automation_signals=("A1", "A2"),
        ai_signals=("KI1",),
        risk_flags=(),
    )
    assert "für Automatisierung sprachen mehr" in begruendung
    assert "kein Kriterium" not in begruendung


def test_routing_begruendung_human_review_names_the_risk_flags() -> None:
    begruendung = build_routing_begruendung(
        recommendation=RoutingRecommendation.HUMAN_REVIEW_REQUIRED,
        automation_signals=("A1",),
        ai_signals=("KI1",),
        risk_flags=(
            "Sensible Personendaten (Art. 9 DSGVO)",
            "Regulatorischer Druck + PII",
        ),
    )
    assert "Sensible Personendaten (Art. 9 DSGVO)" in begruendung
    assert "Regulatorischer Druck + PII" in begruendung
    assert "fachliche Prüfung" in begruendung


def test_routing_begruendung_borderline_without_any_signal_is_honest() -> None:
    """BORDERLINE ohne jedes Signal: es gibt keine Kriterien zu nennen -- der
    Text sagt genau das, statt eine leere Aufzaehlung zu drucken."""
    begruendung = build_routing_begruendung(
        recommendation=RoutingRecommendation.BORDERLINE,
        automation_signals=(),
        ai_signals=(),
        risk_flags=(),
    )
    assert "weder für Automatisierung noch für KI" in begruendung
    assert begruendung.strip().endswith(".")


def test_routing_begruendung_exists_for_every_recommendation_in_both_langs() -> None:
    """Kein Zweig ohne Begruendung -- in beiden Sprachen. Faellt eine Empfehlung
    durch die Zuordnung, waere die Anzeige wieder ohne Begruendung."""
    for lang in ("de", "en"):
        for recommendation in RoutingRecommendation:
            begruendung = build_routing_begruendung(
                recommendation=recommendation,
                automation_signals=("A1",),
                ai_signals=("KI1",),
                risk_flags=("R1", "R2"),
                lang=lang,  # type: ignore[arg-type]
            )
            assert begruendung.strip() != ""
            assert "{" not in begruendung  # kein ungefuelltes Template
