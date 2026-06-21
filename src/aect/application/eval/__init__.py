"""Eval-Infrastruktur (Master-Plan v3.1 Phase E).
Oeffentliche API der application.eval-Schicht.
"""

from aect.application.eval.breakdown import (
    ScoreBreakdown,
    build_score_breakdown,
    write_breakdown_report,
)
from aect.application.eval.loader import EvalCaseLoadError, load_eval_cases
from aect.application.eval.models import EvalCase
from aect.application.eval.runner import EvalCaseResult, run_eval, write_report

__all__ = [
    "EvalCase",
    "EvalCaseLoadError",
    "EvalCaseResult",
    "ScoreBreakdown",
    "build_score_breakdown",
    "load_eval_cases",
    "run_eval",
    "write_breakdown_report",
    "write_report",
]
