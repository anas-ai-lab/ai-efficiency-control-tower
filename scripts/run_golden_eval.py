"""Einmal-Script: fuehrt die vier Golden-Cases durch die Eval-Pipeline und
schreibt den ersten echten Experten-Abgleich-Report (Tag 64, Master-Plan v3.1
Phase E, baut auf ADR-0029/0030 auf).

Bewusst kein CLI mit --provider-Flag -- das kommt erst, sobald LLM-Pfade Teil
des Evals werden (ADR-0030 Konsequenzen). Heute: reiner Aufruf der Python-API
gegen die deterministische Regel-Pipeline.

Logging-Allowlist (aect-security-checklist v2.1): Ausgabe enthaelt nur
case_id und Zonen-Werte, keinen use_case-Inhalt.
"""

from __future__ import annotations

from pathlib import Path

from aect.application.eval import load_eval_cases, run_eval, write_report
from aect.domain import load_roi_config

REPO_ROOT = Path(__file__).parent.parent
GOLDEN_CASES_PATH = REPO_ROOT / "evals" / "golden" / "use_cases.jsonl"
ROI_CONFIG_PATH = REPO_ROOT / "config" / "roi_config.toml"
REPORT_PATH = REPO_ROOT / "evals" / "golden" / "report.json"


def main() -> None:
    cases = load_eval_cases(GOLDEN_CASES_PATH)
    roi_config = load_roi_config(ROI_CONFIG_PATH)
    results = run_eval(cases, roi_config)
    write_report(results, REPORT_PATH)

    labeled = [r for r in results if r.expected_zone is not None]
    agreement = sum(1 for r in labeled if r.is_match)

    print(f"Report geschrieben: {REPORT_PATH}")
    print(f"Gelabelte Cases: {len(labeled)}/{len(results)}")
    print(f"Agreement: {agreement}/{len(labeled)}")
    for r in results:
        print(
            f"  {r.case_id}: predicted={r.predicted_zone}, "
            f"expected={r.expected_zone}, is_match={r.is_match}"
        )


if __name__ == "__main__":
    main()
