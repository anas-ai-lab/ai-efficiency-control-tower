"""Regressionstest: Backtest-Baseline muss evals/golden/report.json exakt
reproduzieren (Phase G, docs/analysis/rule-engine-vs-human-judgment.md).

scripts/ liegt bewusst ausserhalb von src/aect (Einmal-/Analyse-Skripte,
kein Package auf pythonpath) -- Laden per importlib ueber den Dateipfad,
keine Aenderung an pyproject.toml [tool.pytest.ini_options] pythonpath.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "analysis" / "zone_threshold_backtest.py"
_MODULE_NAME = "zone_threshold_backtest"


def _load_backtest_module():
    spec = importlib.util.spec_from_file_location(_MODULE_NAME, SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # dataclass()-Feldaufloesung braucht das Modul in sys.modules (siehe
    # dataclasses._process_class -> sys.modules.get(cls.__module__)), sonst
    # AttributeError bei @dataclass(frozen=True) in _CaseFacts.
    sys.modules[_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


def test_baseline_reproduces_golden_report_exactly() -> None:
    """composite<=4 (aktueller Wert) MUSS die bestehenden report.json-Zahlen
    treffen. Nach der V4-P4-Remessung (v4-Scoring): 58,3 % Agreement (14/24),
    kappa 0,25 (vorher 37,5 % / kappa 0,06) -- sonst Logik-Fehler im Backtest."""
    backtest = _load_backtest_module()
    roi_config = backtest.load_roi_config(backtest.ROI_CONFIG_PATH)
    base_classifier = backtest.load_zone_classifier()

    golden_cases = [
        c
        for c in backtest.load_eval_cases(backtest.GOLDEN_CASES_PATH)
        if c.expected_zone is not None
    ]
    golden_facts = backtest._collect_facts(golden_cases, roi_config, is_golden=True)

    baseline = backtest._run_candidate(
        "aktuell (composite<=4)", 4, base_classifier, golden_facts, golden_facts, None
    )

    report = json.loads(backtest.GOLDEN_REPORT_PATH.read_text(encoding="utf-8"))
    assert baseline["golden_agreement_count"] == report["agreement_count"]
    assert baseline["golden_labeled_cases"] == report["labeled_cases"]
    assert baseline["golden_raw_agreement_rate"] == report["agreement_rate"]
    assert round(baseline["golden_cohens_kappa"], 2) == 0.25


def test_candidate_composite_6_changes_more_cases_than_composite_5() -> None:
    """Breiterer LIKELY_WIN-Korridor bewegt mehr Faelle (composite<=6 > <=5) --
    strukturell garantiert, ein weiterer Schwellenwert kann nur mehr Cases
    umklassifizieren.

    Golden-Agreement ist unter v4-Scoring dagegen NICHT monoton im Korridor:
    das Optimum liegt bei composite<=5 (16/24 = 0,667); composite<=6 faellt
    wieder auf 15/24 = 0,625 zurueck (ein Grenzfall kippt faelschlich nach
    LIKELY_WIN). Der Test haelt genau diese Nicht-Monotonie fest -- vor der
    V4-P4-Remessung war Agreement noch monoton steigend im Korridor."""
    backtest = _load_backtest_module()
    roi_config = backtest.load_roi_config(backtest.ROI_CONFIG_PATH)
    base_classifier = backtest.load_zone_classifier()

    golden_cases = [
        c
        for c in backtest.load_eval_cases(backtest.GOLDEN_CASES_PATH)
        if c.expected_zone is not None
    ]
    synthetic_cases = backtest.load_eval_cases(backtest.SYNTHETIC_CASES_PATH)
    golden_facts = backtest._collect_facts(golden_cases, roi_config, is_golden=True)
    synthetic_facts = backtest._collect_facts(
        synthetic_cases, roi_config, is_golden=False
    )
    all_facts = golden_facts + synthetic_facts

    baseline = backtest._run_candidate(
        "aktuell (composite<=4)", 4, base_classifier, all_facts, golden_facts, None
    )
    baseline_predictions = baseline["_predictions"]
    candidate_5 = backtest._run_candidate(
        "composite<=5",
        5,
        base_classifier,
        all_facts,
        golden_facts,
        baseline_predictions,
    )
    candidate_6 = backtest._run_candidate(
        "composite<=6",
        6,
        base_classifier,
        all_facts,
        golden_facts,
        baseline_predictions,
    )

    assert (
        candidate_6["cases_changed_vs_baseline"]
        > candidate_5["cases_changed_vs_baseline"]
    )
    # Nicht-Monotonie unter v4-Scoring: composite<=5 ist das Agreement-Optimum,
    # composite<=6 faellt wieder zurueck (siehe Docstring).
    assert (
        candidate_5["golden_raw_agreement_rate"]
        > candidate_6["golden_raw_agreement_rate"]
    )
    assert (
        candidate_5["golden_raw_agreement_rate"] > baseline["golden_raw_agreement_rate"]
    )
