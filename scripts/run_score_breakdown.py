"""Einmal-Script: Score-Breakdown fuer alle Golden-Cases (Tag 65, Master-Plan
v3.1 Phase E, ADR-0031, baut auf ADR-0029/0030 auf).

Beantwortet die Comprehension-Gate-Frage aus session-protocol v3 SS3
("warum bekommt dieser Fall genau diese Bewertung?") strukturiert statt nur
per Augenschein im Eval-Report.

Logging-Allowlist (aect-security-checklist v2.1): Ausgabe enthaelt nur
case_id, Zahlenwerte und die deterministisch generierte Erklaerung -- keinen
use_case-Freitext.
"""

from __future__ import annotations

from pathlib import Path

from aect.application.eval import (
    build_score_breakdown,
    load_eval_cases,
    write_breakdown_report,
)
from aect.domain import load_roi_config, load_zone_classifier

REPO_ROOT = Path(__file__).parent.parent
GOLDEN_CASES_PATH = REPO_ROOT / "evals" / "golden" / "use_cases.jsonl"
ROI_CONFIG_PATH = REPO_ROOT / "config" / "roi_config.toml"
ZONE_CONFIG_PATH = REPO_ROOT / "config" / "zone_thresholds.yaml"
REPORT_PATH = REPO_ROOT / "evals" / "golden" / "score_breakdown.json"


def main() -> None:
    cases = load_eval_cases(GOLDEN_CASES_PATH)
    roi_config = load_roi_config(ROI_CONFIG_PATH)
    classifier = load_zone_classifier(ZONE_CONFIG_PATH)

    breakdowns = [build_score_breakdown(case, roi_config, classifier) for case in cases]
    write_breakdown_report(breakdowns, REPORT_PATH)

    print(f"Report geschrieben: {REPORT_PATH}\n")
    for b in breakdowns:
        print(
            f"{b.case_id}: predicted={b.predicted_zone}, "
            f"expected={b.expected_zone}, is_match={b.is_match}"
        )
        print(f"  {b.explanation}\n")


if __name__ == "__main__":
    main()
