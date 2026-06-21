"""Loader fuer Eval-Case-Dateien (JSONL) -- Master-Plan v3.1 Phase E, ADR-0029.

Format: eine Zeile = ein JSON-Objekt = ein EvalCase (siehe models.py).
Bewusst JSONL statt JSON-Array: Cases koennen einzeln angehaengt/diffed
werden, ein kaputter Case bricht nicht die gesamte Datei (ADR-0029).

Schicht: application -- liest vom Dateisystem (I/O), bleibt aber in
application/, nicht adapters/, da Master-Plan v3.1 den Eval-Runner explizit
unter aect.application.eval.* fuehrt (Gate-Kommando Phase E->F).
"""

from __future__ import annotations

import json
from pathlib import Path

import structlog
from pydantic import ValidationError

from aect.application.eval.models import EvalCase

logger = structlog.get_logger(__name__)


class EvalCaseLoadError(Exception):
    """Eine oder mehrere Zeilen in der Eval-Case-Datei sind ungueltig."""


def load_eval_cases(path: Path) -> list[EvalCase]:
    """Laedt und validiert alle EvalCase-Zeilen aus einer JSONL-Datei.

    Jede Zeile wird einzeln geparst und gegen EvalCase validiert. Bei einem
    Fehler wird die Datei NICHT teilweise zurueckgegeben -- alle Fehler
    werden gesammelt und als EvalCaseLoadError mit Zeilennummern geworfen
    (fail-fast, kein stilles Ueberspringen kaputter Cases).

    Args:
        path: Pfad zur .jsonl-Datei (z. B. evals/golden/use_cases.jsonl).

    Returns:
        Liste aller EvalCase, in Datei-Reihenfolge.

    Raises:
        EvalCaseLoadError: wenn die Datei fehlt oder mindestens eine Zeile
            nicht geparst/validiert werden kann.
    """
    if not path.exists():
        raise EvalCaseLoadError(f"Eval-Case-Datei nicht gefunden: {path}")

    cases: list[EvalCase] = []
    errors: list[str] = []

    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"Zeile {line_number}: kein valides JSON ({exc})")
            continue
        try:
            cases.append(EvalCase.model_validate(payload))
        except ValidationError as exc:
            errors.append(f"Zeile {line_number}: Validierung fehlgeschlagen ({exc})")

    if errors:
        # Allowlist-konform: nur Zeilennummern-Anzahl loggen, kein Payload-Inhalt
        logger.error("eval_case_load_failed", path=str(path), error_count=len(errors))
        raise EvalCaseLoadError(
            f"{len(errors)} ungueltige Zeile(n) in {path}:\n" + "\n".join(errors)
        )

    logger.info("eval_cases_loaded", path=str(path), case_count=len(cases))
    return cases
