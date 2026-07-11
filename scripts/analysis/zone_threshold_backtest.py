"""Backtest: Zonen-Schwellenwert-Kandidaten gegen Autor-Labels (Phase G).

Rechnet fuer alle 60 Eval-Cases (24 gelabelte Golden Cases +
36 unlabeled Synthetic Cases) den predicted_zone unter dem aktuellen
LIKELY_WIN-Composite-Schwellenwert (4) UND unter zwei Kandidaten (5, 6) neu
aus. Antwort auf die in docs/analysis/rule-engine-vs-human-judgment.md
Abschnitt 4 dokumentierte MARGINAL_GAIN-Empfehlung: die dort geprueften
Zahlen muessen aus einem Backtest stammen, nicht aus Einschaetzung.

Nutzt ausschliesslich die bestehende Domain-Pipeline (evaluate_use_case)
und ZoneClassifier.classify() (domain/zones.py) als Funktionsaufruf --
keine Neuimplementierung der Zonen-Logik. Nur der LIKELY_WIN-Composite-
Schwellenwert wird pro Kandidat variiert; alle anderen Schwellen
(Benefit-Minima, CALCULATED_RISK-Obergrenze, Handlungsdruck) bleiben aus
config/zone_thresholds.yaml.

Agreement/Kappa-Formel identisch zu evals/golden/report.json bzw.
evals/golden/inter_annotator_report.md: Raw Agreement = Treffer / gelabelte
Faelle; Cohen's Kappa unweighted ueber die Kategorien {LIKELY_WIN,
CALCULATED_RISK, MARGINAL_GAIN, NONE} (NONE = Vorfilter-Ablehnung, zaehlt
als eigene Kategorie -- reproduziert exakt report.json. Nach der V4-P4-
Remessung (v4-Scoring): 62,5 % / kappa 0,34 (vorher 37,5 % / kappa 0,06).
Der Backtest laedt die ROI-Config mit layer_local=False (reine Platzhalter,
identisch zu run_golden_eval.py), damit die Zahlen CI-reproduzierbar sind und
nicht von der gitignored roi_config.local.toml abhaengen.
Nur die 24 gelabelten Golden Cases fliessen in Agreement/Kappa ein;
Synthetic Cases haben kein Autor-Label und zaehlen nur in Zonen-Verteilung
und MARGINAL_GAIN-Anteil.

Aufruf:
    uv run python scripts/analysis/zone_threshold_backtest.py
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from aect.application.eval import EvalCase, load_eval_cases
from aect.domain import TriageZone, ZoneClassifier, evaluate_use_case, load_roi_config
from aect.domain.pipeline import handlungsdruck_score
from aect.domain.zones import load_zone_classifier

REPO_ROOT = Path(__file__).parents[2]
GOLDEN_CASES_PATH = REPO_ROOT / "evals" / "golden" / "use_cases.jsonl"
SYNTHETIC_CASES_PATH = REPO_ROOT / "evals" / "synthetic" / "use_cases.jsonl"
ROI_CONFIG_PATH = REPO_ROOT / "config" / "roi_config.toml"
GOLDEN_REPORT_PATH = REPO_ROOT / "evals" / "golden" / "report.json"
RESULTS_PATH = (
    REPO_ROOT / "scripts" / "analysis" / "zone_threshold_backtest_results.json"
)

_NONE_LABEL = "NONE"  # Vorfilter-Ablehnung als eigene Kategorie fuer Kappa

# Kandidaten: (Label, likely_win_max_composite). Aktueller Wert zuerst
# (Baseline fuer den Reproduktions-Test und fuer "Zone gewechselt?").
_CANDIDATES: list[tuple[str, int]] = [
    ("aktuell (composite<=4)", 4),
    ("composite<=5", 5),
    ("composite<=6", 6),
]


@dataclass(frozen=True)
class _CaseFacts:
    """Threshold-unabhaengige Fakten eines Case -- einmal pro Case berechnet."""

    case_id: str
    is_golden: bool
    expected_zone: TriageZone | None
    passed_vorfilter: bool
    expected_benefit_eur: Decimal | None
    composite_total: int | None
    handlungsdruck: int | None


def _collect_facts(
    cases: list[EvalCase], roi_config: object, is_golden: bool
) -> list[_CaseFacts]:
    facts = []
    for case in cases:
        triage = evaluate_use_case(case.use_case, roi_config)  # type: ignore[arg-type]
        facts.append(
            _CaseFacts(
                case_id=case.case_id,
                is_golden=is_golden,
                expected_zone=case.expected_zone,
                passed_vorfilter=triage.passed_vorfilter,
                expected_benefit_eur=(
                    triage.roi.expected_benefit_eur if triage.roi is not None else None
                ),
                composite_total=(
                    triage.composite.total if triage.composite is not None else None
                ),
                handlungsdruck=handlungsdruck_score(case.use_case)
                if triage.passed_vorfilter
                else None,
            )
        )
    return facts


def _predict(fact: _CaseFacts, classifier: ZoneClassifier) -> TriageZone | None:
    """Wendet die bestehende ZoneClassifier.classify()-Logik auf die
    threshold-unabhaengigen Fakten eines Case an (kein Re-Implement)."""
    if (
        not fact.passed_vorfilter
        or fact.expected_benefit_eur is None
        or fact.composite_total is None
        or fact.handlungsdruck is None
    ):
        return None
    return classifier.classify(
        expected_benefit_eur=fact.expected_benefit_eur,
        composite_score=fact.composite_total,
        handlungsdruck_score=fact.handlungsdruck,
    ).final_zone


def _raw_agreement(
    predictions: dict[str, TriageZone | None], golden_facts: list[_CaseFacts]
) -> tuple[int, int, float]:
    labeled = [f for f in golden_facts if f.expected_zone is not None]
    agreement = sum(1 for f in labeled if predictions[f.case_id] == f.expected_zone)
    rate = agreement / len(labeled) if labeled else 0.0
    return agreement, len(labeled), rate


def _cohens_kappa(
    predictions: dict[str, TriageZone | None], golden_facts: list[_CaseFacts]
) -> float:
    """Unweighted Cohen's Kappa, NONE als eigene Kategorie fuer Vorfilter-
    Ablehnungen. Identische Formel wie inter_annotator_report.md (verifiziert
    gegen report.json: reproduziert exakt 37,5 % / kappa 0,0625 -> 0,06)."""
    labeled = [f for f in golden_facts if f.expected_zone is not None]
    n = len(labeled)
    if n == 0:
        return 0.0

    def _label(zone: TriageZone | None) -> str:
        return zone.value if zone is not None else _NONE_LABEL

    autor_counts: dict[str, int] = {}
    engine_counts: dict[str, int] = {}
    agree = 0
    for f in labeled:
        autor = _label(f.expected_zone)
        engine = _label(predictions[f.case_id])
        autor_counts[autor] = autor_counts.get(autor, 0) + 1
        engine_counts[engine] = engine_counts.get(engine, 0) + 1
        if autor == engine:
            agree += 1

    categories = set(autor_counts) | set(engine_counts)
    p_o = agree / n
    p_e = sum(autor_counts.get(c, 0) * engine_counts.get(c, 0) for c in categories) / (
        n * n
    )
    if p_e >= 1.0:
        return 0.0
    return (p_o - p_e) / (1 - p_e)


def _run_candidate(
    label: str,
    likely_win_max_composite: int,
    base_classifier: ZoneClassifier,
    all_facts: list[_CaseFacts],
    golden_facts: list[_CaseFacts],
    baseline_predictions: dict[str, TriageZone | None] | None,
) -> dict[str, object]:
    classifier = ZoneClassifier(
        likely_win_min_benefit=base_classifier.likely_win_min_benefit,
        likely_win_max_composite=likely_win_max_composite,
        calculated_risk_min_benefit=base_classifier.calculated_risk_min_benefit,
        calculated_risk_max_composite=base_classifier.calculated_risk_max_composite,
        handlungsdruck_elevation_threshold=(
            base_classifier.handlungsdruck_elevation_threshold
        ),
    )
    predictions = {f.case_id: _predict(f, classifier) for f in all_facts}

    zone_distribution: dict[str, int] = {}
    for zone in predictions.values():
        key = zone.value if zone is not None else _NONE_LABEL
        zone_distribution[key] = zone_distribution.get(key, 0) + 1

    cases_changed = (
        sum(
            1
            for f in all_facts
            if predictions[f.case_id] != baseline_predictions[f.case_id]
        )
        if baseline_predictions is not None
        else 0
    )

    agreement_count, labeled_cases, agreement_rate = _raw_agreement(
        predictions, golden_facts
    )
    kappa = _cohens_kappa(predictions, golden_facts)

    marginal_gain_count = zone_distribution.get(TriageZone.MARGINAL_GAIN.value, 0)
    marginal_gain_share = marginal_gain_count / len(all_facts)

    return {
        "label": label,
        "likely_win_max_composite": likely_win_max_composite,
        "zone_distribution": zone_distribution,
        "cases_changed_vs_baseline": cases_changed,
        "golden_agreement_count": agreement_count,
        "golden_labeled_cases": labeled_cases,
        # Volle Praezision (kein round): muss report.json exakt reproduzieren.
        # agreement_count / labeled_cases ist bitgleich zur Runner-Berechnung
        # (write_report); ein round(., 4) wich bei nicht exakt darstellbaren
        # Raten wie 14/24 vom report.json-Wert ab.
        "golden_raw_agreement_rate": agreement_rate,
        "golden_cohens_kappa": round(kappa, 4),
        "marginal_gain_count": marginal_gain_count,
        "marginal_gain_share": round(marginal_gain_share, 4),
        "_predictions": predictions,  # intern, wird vor dem Schreiben entfernt
    }


def _verify_baseline_reproduces_report(baseline: dict[str, object]) -> None:
    """Harte Gate-Pruefung: Baseline-Kandidat MUSS report.json exakt treffen.

    Bricht mit RuntimeError ab statt die Zahlen still zu akzeptieren --
    ein Mismatch bedeutet einen Logik-Fehler im Backtest-Script, kein
    tolerierbares Rundungsrauschen.
    """
    report = json.loads(GOLDEN_REPORT_PATH.read_text(encoding="utf-8"))
    expected_rate = report["agreement_rate"]
    expected_count = report["agreement_count"]
    expected_labeled = report["labeled_cases"]

    if (
        baseline["golden_agreement_count"] != expected_count
        or baseline["golden_labeled_cases"] != expected_labeled
        or abs(baseline["golden_raw_agreement_rate"] - expected_rate) > 1e-9
    ):
        raise RuntimeError(
            "STOPP -- Logik-Fehler im Backtest-Script: Baseline-Kandidat "
            f"({baseline['golden_agreement_count']}/{baseline['golden_labeled_cases']}"
            f" = {baseline['golden_raw_agreement_rate']}) reproduziert NICHT "
            f"evals/golden/report.json ({expected_count}/{expected_labeled} = "
            f"{expected_rate})."
        )
    # v4-Scoring (V4-P4-Remessung), reine Platzhalter-Config: Baseline-Kappa jetzt
    # 0,34 (vorher 0,06); siehe evals/golden/inter_annotator_report.md.
    expected_kappa_rounded = 0.34
    if round(baseline["golden_cohens_kappa"], 2) != expected_kappa_rounded:
        raise RuntimeError(
            "STOPP -- Logik-Fehler im Backtest-Script: Baseline-Kappa "
            f"{round(baseline['golden_cohens_kappa'], 2)} != erwartete {expected_kappa_rounded} "
            "(vgl. evals/golden/inter_annotator_report.md)."
        )


def main() -> None:
    # layer_local=False: reine Platzhalter-Config (siehe Modul-Docstring) --
    # Baseline muss das committete report.json reproduzieren, das CI ohne
    # roi_config.local.toml erzeugt.
    roi_config = load_roi_config(ROI_CONFIG_PATH, layer_local=False)
    base_classifier = load_zone_classifier()

    golden_cases = [
        c for c in load_eval_cases(GOLDEN_CASES_PATH) if c.expected_zone is not None
    ]
    synthetic_cases = load_eval_cases(SYNTHETIC_CASES_PATH)
    assert len(golden_cases) == 24, (
        f"Erwartet 24 gelabelte Golden Cases, gefunden {len(golden_cases)}"
    )
    assert len(synthetic_cases) == 36, (
        f"Erwartet 36 Synthetic Cases, gefunden {len(synthetic_cases)}"
    )

    golden_facts = _collect_facts(golden_cases, roi_config, is_golden=True)
    synthetic_facts = _collect_facts(synthetic_cases, roi_config, is_golden=False)
    all_facts = golden_facts + synthetic_facts

    candidates: list[dict[str, object]] = []
    baseline_predictions: dict[str, TriageZone | None] | None = None
    for label, lw_max_c in _CANDIDATES:
        result = _run_candidate(
            label,
            lw_max_c,
            base_classifier,
            all_facts,
            golden_facts,
            baseline_predictions,
        )
        if baseline_predictions is None:
            baseline_predictions = result["_predictions"]  # type: ignore[assignment]
        candidates.append(result)

    _verify_baseline_reproduces_report(candidates[0])

    output = {
        "total_cases": len(all_facts),
        "golden_cases": len(golden_facts),
        "synthetic_cases": len(synthetic_facts),
        "candidates": [
            {k: v for k, v in c.items() if k != "_predictions"} for c in candidates
        ],
    }
    RESULTS_PATH.write_text(
        json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"Report geschrieben: {RESULTS_PATH}")
    print(
        f"Baseline reproduziert report.json ({round(candidates[0]['golden_raw_agreement_rate'] * 100, 1)} %, "
        f"kappa {round(candidates[0]['golden_cohens_kappa'], 2)}) -- OK.\n"
    )
    print(
        f"{'Schwellenwert':<25} {'Agreement':>10} {'Kappa':>8} {'MARGINAL_GAIN-Anteil':>22}"
    )
    for c in candidates:
        agreement_pct = f"{c['golden_raw_agreement_rate'] * 100:.1f}%"
        mg_pct = f"{c['marginal_gain_share'] * 100:.1f}%"
        print(
            f"{c['label']:<25} {agreement_pct:>10} {c['golden_cohens_kappa']:>8.2f} {mg_pct:>22}"
        )


if __name__ == "__main__":
    main()
