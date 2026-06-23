"""Einmal-Script: fuehrt alle synthetischen Eval-Cases durch die
Eval-Pipeline (Master-Plan v3.1 Phase E, Gate E->F: >= 30 Cases ohne Crash).

Synthetic-Cases sind bewusst unlabeled (siehe generate_synthetic_cases.py) --
labeled_cases/agreement_rate sind hier strukturell 0/None, kein Fehlerfall.
Der Experten-Abgleich laeuft weiterhin ueber die Golden-Cases
(run_golden_eval.py, Tag 64). Zweck dieses Laufs: Volumen- und Crash-Test der
Pipeline ueber ein breiteres Eingabe-Spektrum, plus Konsistenz-Stichprobe.

Logging-Allowlist (aect-security-checklist v2.1): Ausgabe enthaelt nur
case_id und Zonen-Werte, keinen use_case-Inhalt.

Aufruf:
    uv run python scripts/run_synthetic_eval.py
"""

from __future__ import annotations

from pathlib import Path

from aect.application.eval import load_eval_cases, run_eval, write_report
from aect.domain import load_roi_config

REPO_ROOT = Path(__file__).parent.parent
SYNTHETIC_CASES_PATH = REPO_ROOT / "evals" / "synthetic" / "use_cases.jsonl"
ROI_CONFIG_PATH = REPO_ROOT / "config" / "roi_config.toml"
REPORT_PATH = REPO_ROOT / "evals" / "synthetic" / "report.json"


def main() -> None:
    cases = load_eval_cases(SYNTHETIC_CASES_PATH)
    roi_config = load_roi_config(ROI_CONFIG_PATH)
    results = run_eval(cases, roi_config)
    write_report(results, REPORT_PATH)

    passed_vorfilter = sum(1 for r in results if r.passed_vorfilter)
    zone_counts: dict[str, int] = {}
    for r in results:
        if r.predicted_zone is not None:
            zone_counts[r.predicted_zone.value] = (
                zone_counts.get(r.predicted_zone.value, 0) + 1
            )

    print(f"Report geschrieben: {REPORT_PATH}")
    print(f"Cases gesamt: {len(results)}")
    print(f"Vorfilter bestanden: {passed_vorfilter}/{len(results)}")
    print("Zonen-Verteilung (nur bestandene Vorfilter-Cases):")
    for zone, count in sorted(zone_counts.items()):
        print(f"  {zone}: {count}")


if __name__ == "__main__":
    main()
