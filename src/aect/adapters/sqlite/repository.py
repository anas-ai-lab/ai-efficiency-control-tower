"""SQLiteRepository -- implementiert RepositoryPort mit SQLite.

Persistenz-Strategie:
  use_case:  Pydantic .model_dump_json() / .model_validate_json()
  result:    dataclasses.asdict() + _DecimalEncoder / explizite Rekonstruktion

Warum nicht dataclasses.asdict(case) auf das gesamte SubmittedCase?
  use_case ist UseCaseInput (Pydantic BaseModel, kein Dataclass). asdict()
  loest nur Dataclasses rekursiv auf -- ein BaseModel bleibt unveraendert und
  ist nicht JSON-serialisierbar. Deshalb beide Felder getrennt behandeln.

Security (aect-security-checklist v2.1, Phase B):
  Kein PII in Logs -- Repository loggt nicht.
  Audit-Trail: submitted_at als ISO-8601-UTC-String persistiert.
  Kurzlebige Verbindungen (Context Manager) -- kein geteilter State.

Hinweis: SQLiteRepository wird in get_triage_service() pro Request erzeugt.
  _init_db() (CREATE TABLE IF NOT EXISTS) laeuft damit pro Request -- idempotent
  und bei Portfolio-Traffic akzeptabel. Fuer Produktionslast: Lifespan-Singleton
  (Doku-Punkt in Phase-B-ADR).

sharpened_content_json/proposal_text (Tag 42 ADR-0012, Spalte umbenannt
ADR-0013 Teil 2): zwei zusaetzliche nullable Spalten fuer persistierte
LLM-Narrative aus sharpen_case() / propose_solution(). sharpened_content_json
enthaelt ein JSON-Objekt (strukturierte Schaerfung oder raw_text bei
Graceful Degradation, siehe application/structured_output.py).

compliance_hints_json (ADR-0026): dritte nullable Spalte, analog zu den
beiden oberen. Enthaelt ein JSON-Objekt mit hint_text (str | None) und
citations (Liste von Citation-Dicts), gefuellt durch generate_compliance_
hints() (application/service.py).

save() ist weiterhin INSERT OR REPLACE -- ein erneuter save() mit gesetztem
Feld ueberschreibt den vorherigen Wert.
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
from dataclasses import asdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from aect.application.models import SubmittedCase
from aect.domain.feasibility import FeasibilityFlag, FeasibilityResult
from aect.domain.filters import FilterResult
from aect.domain.models import UseCaseInput
from aect.domain.pipeline import TriageResult
from aect.domain.roi import ROIResult
from aect.domain.routing import RoutingRecommendation, RoutingResult
from aect.domain.scoring import CompositeScore
from aect.domain.types import TriageZone
from aect.domain.zones import ZoneResult

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS submitted_cases (
    id                      TEXT PRIMARY KEY,
    submitted_at            TEXT NOT NULL,
    use_case_json           TEXT NOT NULL,
    result_json             TEXT NOT NULL,
    sharpened_content_json  TEXT,
    proposal_text           TEXT,
    compliance_hints_json   TEXT
)
"""

# Spaltenliste vierfach dupliziert statt ueber eine _SELECT_COLUMNS-Variable
# geteilt: jede "+"-Verkettung mit einem Namens-Knoten matcht bandit B608
# erneut, unabhaengig vom Laufzeitwert der Variable (AST-Form entscheidet,
# nicht Inhalt -- das war der Grund, warum der Tag-43-Fix nicht griff).
# Reine adjazente String-Literale ohne Operator umgehen das strukturell.
# Bei Schema-Aenderung: alle vier Stellen synchron halten (CREATE_TABLE,
# INSERT, SELECT_BY_ID, SELECT_ALL) plus Positions-Reihenfolge in
# _row_to_case().

_INSERT_SQL = (
    "INSERT OR REPLACE INTO submitted_cases "
    "(id, submitted_at, use_case_json, result_json, "
    "sharpened_content_json, proposal_text, compliance_hints_json) "
    "VALUES (?, ?, ?, ?, ?, ?, ?)"
)

_SELECT_BY_ID_SQL = (
    "SELECT id, submitted_at, use_case_json, result_json, "
    "sharpened_content_json, proposal_text, compliance_hints_json "
    "FROM submitted_cases WHERE id = ?"
)

_SELECT_ALL_SQL = (
    "SELECT id, submitted_at, use_case_json, result_json, "
    "sharpened_content_json, proposal_text, compliance_hints_json "
    "FROM submitted_cases ORDER BY submitted_at ASC"
)


# ---------------------------------------------------------------------------
# JSON-Encoder
# ---------------------------------------------------------------------------


class _DecimalEncoder(json.JSONEncoder):
    """Serialisiert Decimal als str (Praezision bleibt erhalten)."""

    def default(self, obj: object) -> object:
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)


# ---------------------------------------------------------------------------
# Serialisierung: TriageResult -> JSON
# ---------------------------------------------------------------------------


def _serialize_result(result: TriageResult) -> str:
    """TriageResult -> JSON-String via dataclasses.asdict().

    asdict() loest verschachtelte Dataclasses rekursiv auf.
    StrEnum-Werte: str-Subklasse, wird als JSON-String serialisiert.
    tuple-Felder: asdict() wandelt in list -- bei Load explizit rekonstruiert.
    Decimal-Felder: via _DecimalEncoder als str.
    """
    return json.dumps(asdict(result), cls=_DecimalEncoder)


# ---------------------------------------------------------------------------
# Deserialisierung: JSON -> TriageResult
# ---------------------------------------------------------------------------


def _filter_result_from_dict(d: dict[str, Any]) -> FilterResult:
    return FilterResult(
        passes=bool(d["passes"]),
        failed_criteria=[str(s) for s in d["failed_criteria"]],
        details={str(k): bool(v) for k, v in d["details"].items()},
    )


def _routing_result_from_dict(d: dict[str, Any]) -> RoutingResult:
    return RoutingResult(
        recommendation=RoutingRecommendation(d["recommendation"]),
        confidence=str(d["confidence"]),
        automation_signals=tuple(str(s) for s in d["automation_signals"]),
        ai_signals=tuple(str(s) for s in d["ai_signals"]),
        risk_flags=tuple(str(s) for s in d["risk_flags"]),
    )


def _feasibility_result_from_dict(d: dict[str, Any]) -> FeasibilityResult:
    raw_rec = d.get("recommendation")
    return FeasibilityResult(
        is_feasible=bool(d["is_feasible"]),
        flags=tuple(FeasibilityFlag(str(f)) for f in d["flags"]),
        recommendation=str(raw_rec) if raw_rec is not None else None,
    )


def _roi_result_from_dict(d: dict[str, Any]) -> ROIResult:
    raw_reason = d.get("prefilter_fail_reason")
    return ROIResult(
        theoretical_potential_eur=Decimal(str(d["theoretical_potential_eur"])),
        usage_factor=float(d["usage_factor"]),
        evidence_factor=float(d["evidence_factor"]),
        expected_benefit_eur=Decimal(str(d["expected_benefit_eur"])),
        license_cost_annual_eur=Decimal(str(d["license_cost_annual_eur"])),
        net_expected_benefit_eur=Decimal(str(d["net_expected_benefit_eur"])),
        hours_per_year=float(d["hours_per_year"]),
        passes_prefilter=bool(d["passes_prefilter"]),
        prefilter_fail_reason=str(raw_reason) if raw_reason is not None else None,
    )


def _composite_score_from_dict(d: dict[str, Any]) -> CompositeScore:
    return CompositeScore(
        complexity_score=int(d["complexity_score"]),
        cost_score=int(d["cost_score"]),
        data_protection_score=int(d["data_protection_score"]),
        total=int(d["total"]),
    )


def _zone_result_from_dict(d: dict[str, Any]) -> ZoneResult:
    # confidence_* sind additiv (ADR-0036). .get()-Fallback haelt aeltere
    # persistierte Records ohne diese Felder lesbar: Score 0.5 = "unsicher".
    return ZoneResult(
        base_zone=TriageZone(str(d["base_zone"])),
        final_zone=TriageZone(str(d["final_zone"])),
        handlungsdruck_elevated=bool(d["handlungsdruck_elevated"]),
        reason=str(d["reason"]),
        confidence_score=float(d.get("confidence_score", 0.5)),
        confidence_label=str(d.get("confidence_label", "niedrig")),
    )


def _deserialize_result(json_str: str) -> TriageResult:
    """JSON-String -> TriageResult (jede Schicht explizit rekonstruiert)."""
    d: dict[str, Any] = json.loads(json_str)
    roi_raw: Any = d["roi"]
    comp_raw: Any = d["composite"]
    zone_raw: Any = d["zone"]
    return TriageResult(
        title=str(d["title"]),
        passed_vorfilter=bool(d["passed_vorfilter"]),
        vorfilter=_filter_result_from_dict(d["vorfilter"]),
        routing=_routing_result_from_dict(d["routing"]),
        feasibility=_feasibility_result_from_dict(d["feasibility"]),
        roi=_roi_result_from_dict(roi_raw) if roi_raw is not None else None,
        composite=_composite_score_from_dict(comp_raw)
        if comp_raw is not None
        else None,
        zone=_zone_result_from_dict(zone_raw) if zone_raw is not None else None,
    )


def _row_to_case(row: tuple[Any, ...]) -> SubmittedCase:
    """SQLite-Row (7-Tupel) -> SubmittedCase."""
    (
        case_id,
        submitted_at_str,
        use_case_json,
        result_json,
        sharpened_content_json,
        proposal_text,
        compliance_hints_json,
    ) = row
    return SubmittedCase(
        id=str(case_id),
        submitted_at=datetime.fromisoformat(str(submitted_at_str)),
        use_case=UseCaseInput.model_validate_json(str(use_case_json)),
        result=_deserialize_result(str(result_json)),
        sharpened_content_json=(
            str(sharpened_content_json) if sharpened_content_json is not None else None
        ),
        proposal_text=str(proposal_text) if proposal_text is not None else None,
        compliance_hints_json=(
            str(compliance_hints_json) if compliance_hints_json is not None else None
        ),
    )


# ---------------------------------------------------------------------------
# SQLiteRepository
# ---------------------------------------------------------------------------


class SQLiteRepository:
    """SQLite-Backend fuer SubmittedCase-Persistenz.

    Implementiert RepositoryPort via strukturelle Subtypisierung (kein
    explizites Erben noetig -- mypy prueft Methodensignaturen gegen Protocol).

    Jede DB-Operation oeffnet eine eigene Verbindung (Context Manager) --
    kein geteilter Connection-State, kein Threading-Problem.

    IP-Trennung (interne Referenz (entfernt) SS5): keine firmenspezifischen Werte im Code.
    Security: submitted_at = unveraenderlicher Audit-Trail pro Case.
    """

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Legt die Tabelle an falls nicht vorhanden (idempotent)."""
        with sqlite3.connect(str(self._db_path)) as conn:
            conn.execute(_CREATE_TABLE_SQL)

    def save(self, case: SubmittedCase) -> None:
        """Persistiert einen SubmittedCase. INSERT OR REPLACE bei Duplikat-ID."""
        use_case_json = case.use_case.model_dump_json()
        result_json = _serialize_result(case.result)
        with sqlite3.connect(str(self._db_path)) as conn:
            conn.execute(
                _INSERT_SQL,
                (
                    case.id,
                    case.submitted_at.isoformat(),
                    use_case_json,
                    result_json,
                    case.sharpened_content_json,
                    case.proposal_text,
                    case.compliance_hints_json,
                ),
            )

    def get(self, case_id: str) -> SubmittedCase | None:
        """Gibt einen Case per ID zurueck oder None."""
        with sqlite3.connect(str(self._db_path)) as conn:
            row = conn.execute(
                _SELECT_BY_ID_SQL,
                (case_id,),
            ).fetchone()
        if row is None:
            return None
        return _row_to_case(row)

    def list_all(self) -> list[SubmittedCase]:
        """Alle gespeicherten Cases, chronologisch nach submitted_at."""
        with sqlite3.connect(str(self._db_path)) as conn:
            rows = conn.execute(_SELECT_ALL_SQL).fetchall()
        return [_row_to_case(row) for row in rows]

    # -- async-Varianten (AUDIT-001, ADR-0037) -----------------------------
    # Lagern die blockierende SQLite-I/O in einen Worker-Thread aus, damit
    # async-Aufrufer den Event-Loop nicht blockieren. Die sync-Methoden bleiben
    # die Single Source of Truth -- to_thread ruft sie nur auf.

    async def save_async(self, case: SubmittedCase) -> None:
        """Async-Wrapper um save() via asyncio.to_thread."""
        await asyncio.to_thread(self.save, case)

    async def get_async(self, case_id: str) -> SubmittedCase | None:
        """Async-Wrapper um get() via asyncio.to_thread."""
        return await asyncio.to_thread(self.get, case_id)

    async def list_all_async(self) -> list[SubmittedCase]:
        """Async-Wrapper um list_all() via asyncio.to_thread."""
        return await asyncio.to_thread(self.list_all)
