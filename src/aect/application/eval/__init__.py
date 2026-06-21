"""Eval-Infrastruktur (Master-Plan v3.1 Phase E).

Oeffentliche API der application.eval-Schicht.
"""

from aect.application.eval.loader import EvalCaseLoadError, load_eval_cases
from aect.application.eval.models import EvalCase

__all__ = ["EvalCase", "EvalCaseLoadError", "load_eval_cases"]
