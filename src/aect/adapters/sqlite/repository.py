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
  Kurzlebige Verbindungen (connection.connect: WAL, busy_timeout,
  explizites close) -- kein geteilter State.

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

reviewer_decision/reviewer_note/decided_at (ADR-0043, minimaler
Decision-Record): reviewer_decision NOT NULL DEFAULT 'pending' (jeder Case
hat ab Einreichung einen Entscheidungs-Zustand), reviewer_note/decided_at
nullable. Geschrieben ueber record_decision() -- ein dediziertes UPDATE,
NICHT ueber save()/INSERT OR REPLACE (vermeidet das F-011-Lost-Update-Muster
bei parallelen LLM-Feld-Schreibvorgaengen auf demselben Case).

save() ist weiterhin INSERT OR REPLACE -- ein erneuter save() mit gesetztem
Feld ueberschreibt den vorherigen Wert.

status/status_updated_at (Case-Lifecycle, siehe Lifecycle-ADR): status NOT NULL
DEFAULT 'submitted' (jeder Case hat ab Einreichung einen Lifecycle-Zustand),
status_updated_at nullable (Zeitstempel des letzten Wechsels, analog decided_at
zur reviewer_decision). Geschrieben ueber update_status() -- ein dediziertes
UPDATE beider Spalten in einem Statement, analog record_decision() (F-011).

architecture_sketch (P11, ADR-0049): nullable Spalte mit dem JSON der
On-Demand-Architektur-Skizze (graph + mermaid_source + generated_at +
prompt_version). Geschrieben ueber update_field() (F-011, ein einzelnes
Feld -- analog sharpened_content_json). Dieselbe PRAGMA-Migrationsstrategie
wie embedding/status. Liegt in der Case-Zeile -> DSGVO-Loesch-Kaskade greift
automatisch (delete() entfernt die Zeile mit der Spalte).

sharpening_draft (V4, Draft/Accept-Flow): nullable Spalte mit dem JSON des
noch nicht uebernommenen Schaerfungs-Entwurfs (original/sharpened/vorschlaege).
Geschrieben ueber update_field() (F-011). POST /cases/{id}/sharpen fuellt sie,
/sharpen/accept traegt den Draft nach sharpened_content_json und leert die
Spalte, /sharpen/reject leert sie. Dieselbe PRAGMA-Migrationsstrategie wie
embedding/status/architecture_sketch. Liegt in der Case-Zeile -> DSGVO-
Loesch-Kaskade greift automatisch.

monitoring_entries (Monitoring-ADR): EIGENE append-only Tabelle (nicht eine
JSON-Spalte am Case -- das haette dasselbe Lost-Update-Risiko wie die per-Feld-
UPDATEs, F-011). Nur INSERT + SELECT; die einzige Loeschung ist die DSGVO-
Kaskade in delete() (Art. 17, ADR-0038), die die Eintraege eines Case
mit-loescht. list_monitoring_entries sortiert ORDER BY created_at, id (der
Sekundaerschluessel id haelt die Reihenfolge stabil, wenn zwei Eintraege in
dieselbe sekundengenaue ISO-Zeit fallen).
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import asdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from aect.adapters.sqlite.connection import connect
from aect.application.models import MonitoringEntry, SubmittedCase
from aect.application.ports.repository import CaseUpdateField
from aect.domain.feasibility import FeasibilityFlag, FeasibilityResult
from aect.domain.filters import FilterResult
from aect.domain.models import UseCaseInput
from aect.domain.pipeline import TriageResult
from aect.domain.roi import ROIResult
from aect.domain.routing import RoutingRecommendation, RoutingResult
from aect.domain.scoring import CompositeScore
from aect.domain.types import CaseStatus, ReviewerDecision, TriageZone
from aect.domain.zones import ZoneResult

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS submitted_cases (
    id                      TEXT PRIMARY KEY,
    submitted_at            TEXT NOT NULL,
    use_case_json           TEXT NOT NULL,
    result_json             TEXT NOT NULL,
    sharpened_content_json  TEXT,
    proposal_text           TEXT,
    compliance_hints_json   TEXT,
    embedding               TEXT,
    reviewer_decision       TEXT NOT NULL DEFAULT 'pending',
    reviewer_note           TEXT,
    decided_at              TEXT,
    status                  TEXT NOT NULL DEFAULT 'submitted',
    status_updated_at       TEXT,
    architecture_sketch     TEXT,
    sharpening_draft        TEXT,
    solution_business       TEXT
)
"""

# embedding (ADR-0039): JSON-Float-Liste des Intake-Embeddings fuer die
# Dedup-Aehnlichkeitspruefung, nullable. SQLite kann ALTER TABLE ADD COLUMN
# nicht IF NOT EXISTS -> Migration in _init_db() prueft erst PRAGMA table_info.
# reviewer_decision/reviewer_note/decided_at (ADR-0043): dieselbe Migrations-
# strategie, drei weitere Spalten.
# status/status_updated_at (Lifecycle-ADR): dieselbe Migrations-strategie, zwei
# weitere Spalten.

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
    "sharpened_content_json, proposal_text, compliance_hints_json, embedding, "
    "reviewer_decision, reviewer_note, decided_at, status, status_updated_at, "
    "architecture_sketch, sharpening_draft, solution_business) "
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)

_SELECT_BY_ID_SQL = (
    "SELECT id, submitted_at, use_case_json, result_json, "
    "sharpened_content_json, proposal_text, compliance_hints_json, embedding, "
    "reviewer_decision, reviewer_note, decided_at, status, status_updated_at, "
    "architecture_sketch, sharpening_draft, solution_business "
    "FROM submitted_cases WHERE id = ?"
)

_SELECT_ALL_SQL = (
    "SELECT id, submitted_at, use_case_json, result_json, "
    "sharpened_content_json, proposal_text, compliance_hints_json, embedding, "
    "reviewer_decision, reviewer_note, decided_at, status, status_updated_at, "
    "architecture_sketch, sharpening_draft, solution_business "
    "FROM submitted_cases ORDER BY submitted_at ASC"
)

_DELETE_BY_ID_SQL = "DELETE FROM submitted_cases WHERE id = ?"

# Per-Feld-UPDATE (F-011): vollstaendige Literale je Feld (kein String-Concat,
# siehe bandit-B608-Hinweis oben) -- der Feldname kommt aus CaseUpdateField
# (Literal-Typ im Port), nie aus Laufzeit-Input.
_UPDATE_FIELD_SQL: dict[str, str] = {
    "sharpened_content_json": (
        "UPDATE submitted_cases SET sharpened_content_json = ? WHERE id = ?"
    ),
    "proposal_text": "UPDATE submitted_cases SET proposal_text = ? WHERE id = ?",
    "compliance_hints_json": (
        "UPDATE submitted_cases SET compliance_hints_json = ? WHERE id = ?"
    ),
    "embedding": "UPDATE submitted_cases SET embedding = ? WHERE id = ?",
    "architecture_sketch": (
        "UPDATE submitted_cases SET architecture_sketch = ? WHERE id = ?"
    ),
    "sharpening_draft": (
        "UPDATE submitted_cases SET sharpening_draft = ? WHERE id = ?"
    ),
    "solution_business": (
        "UPDATE submitted_cases SET solution_business = ? WHERE id = ?"
    ),
}

# record_decision (ADR-0043): eigenes dediziertes UPDATE statt Eintrag in
# _UPDATE_FIELD_SQL -- setzt drei zusammengehoerige Spalten atomar in einem
# Statement, analog zum F-011-Muster oben (kein INSERT OR REPLACE der ganzen
# Zeile, kein Lost-Update-Risiko gegenueber parallelen LLM-Feld-Schreibvorgaengen).
_RECORD_DECISION_SQL = (
    "UPDATE submitted_cases "
    "SET reviewer_decision = ?, reviewer_note = ?, decided_at = ? "
    "WHERE id = ?"
)

# update_status (Lifecycle-ADR): dediziertes UPDATE beider zusammengehoeriger
# Spalten (status + status_updated_at) in einem Statement, analog
# _RECORD_DECISION_SQL (F-011).
_UPDATE_STATUS_SQL = (
    "UPDATE submitted_cases SET status = ?, status_updated_at = ? WHERE id = ?"
)

# monitoring_entries (Monitoring-ADR): eigene append-only Tabelle. Kein
# Fremdschluessel-Constraint -- SQLite erzwingt FKs nur mit PRAGMA foreign_keys
# (pro Verbindung), und die Loesch-Kaskade wird ohnehin explizit in delete()
# gefahren. INSERT-only; Loeschung nur ueber die case-weite DSGVO-Kaskade.
_CREATE_MONITORING_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS monitoring_entries (
    id               TEXT PRIMARY KEY,
    case_id          TEXT NOT NULL,
    created_at       TEXT NOT NULL,
    note             TEXT NOT NULL,
    status_snapshot  TEXT NOT NULL
)
"""

_INSERT_MONITORING_SQL = (
    "INSERT INTO monitoring_entries "
    "(id, case_id, created_at, note, status_snapshot) "
    "VALUES (?, ?, ?, ?, ?)"
)

# ORDER BY created_at, id: id als Sekundaerschluessel gegen Reihenfolge-
# Kollisionen in derselben (sekundengenauen) ISO-Zeit.
_SELECT_MONITORING_BY_CASE_SQL = (
    "SELECT id, case_id, created_at, note, status_snapshot "
    "FROM monitoring_entries WHERE case_id = ? ORDER BY created_at, id"
)

# DSGVO-Kaskade (Art. 17, ADR-0038): loescht die Eintraege eines Case. Die
# einzige DELETE-Operation auf monitoring_entries -- kein Einzel-Delete.
_DELETE_MONITORING_BY_CASE_SQL = "DELETE FROM monitoring_entries WHERE case_id = ?"


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
        # .get()-Fallback haelt aeltere persistierte Records ohne dieses V4-Feld
        # lesbar (additiv, analog confidence_*): 0.0 = "unbekannt".
        time_saved_per_case_hours=float(d.get("time_saved_per_case_hours", 0.0)),
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
    """SQLite-Row (16-Tupel) -> SubmittedCase."""
    (
        case_id,
        submitted_at_str,
        use_case_json,
        result_json,
        sharpened_content_json,
        proposal_text,
        compliance_hints_json,
        embedding_json,
        reviewer_decision_str,
        reviewer_note,
        decided_at_str,
        status_str,
        status_updated_at_str,
        architecture_sketch,
        sharpening_draft,
        solution_business,
    ) = row
    embedding = (
        [float(x) for x in json.loads(str(embedding_json))]
        if embedding_json is not None
        else None
    )
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
        embedding=embedding,
        reviewer_decision=ReviewerDecision(str(reviewer_decision_str)),
        reviewer_note=str(reviewer_note) if reviewer_note is not None else None,
        decided_at=(
            datetime.fromisoformat(str(decided_at_str))
            if decided_at_str is not None
            else None
        ),
        status=CaseStatus(str(status_str)),
        status_updated_at=(
            datetime.fromisoformat(str(status_updated_at_str))
            if status_updated_at_str is not None
            else None
        ),
        architecture_sketch=(
            str(architecture_sketch) if architecture_sketch is not None else None
        ),
        sharpening_draft=(
            str(sharpening_draft) if sharpening_draft is not None else None
        ),
        solution_business=(
            str(solution_business) if solution_business is not None else None
        ),
    )


def _row_to_monitoring_entry(row: tuple[Any, ...]) -> MonitoringEntry:
    """SQLite-Row (5-Tupel) -> MonitoringEntry."""
    (entry_id, case_id, created_at_str, note, status_snapshot) = row
    return MonitoringEntry(
        id=str(entry_id),
        case_id=str(case_id),
        created_at=datetime.fromisoformat(str(created_at_str)),
        note=str(note),
        status_snapshot=str(status_snapshot),
    )


# ---------------------------------------------------------------------------
# SQLiteRepository
# ---------------------------------------------------------------------------


class SQLiteRepository:
    """SQLite-Backend fuer SubmittedCase-Persistenz.

    Implementiert RepositoryPort via strukturelle Subtypisierung (kein
    explizites Erben noetig -- mypy prueft Methodensignaturen gegen Protocol).

    Jede DB-Operation oeffnet eine eigene, kurzlebige Verbindung ueber
    connection.connect() (WAL, busy_timeout=5000, explizites close) --
    kein geteilter Connection-State, kein Threading-Problem.

    IP-Trennung (vertraglich bedingt): keine firmenspezifischen Werte im Code.
    Security: submitted_at = unveraenderlicher Audit-Trail pro Case.
    """

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Legt die Tabelle an falls nicht vorhanden (idempotent).

        Migration embedding-Spalte (ADR-0039), reviewer_decision/
        reviewer_note/decided_at-Spalten (ADR-0043) und status-Spalte
        (Lifecycle-ADR): SQLite kennt kein ALTER TABLE ... ADD COLUMN IF NOT
        EXISTS -- daher erst PRAGMA table_info pruefen und nur ergaenzen, wenn
        die Spalte fehlt (Tabelle stammt dann aus einer aelteren Version).
        """
        with connect(self._db_path) as conn:
            conn.execute(_CREATE_TABLE_SQL)
            conn.execute(_CREATE_MONITORING_TABLE_SQL)
            columns = {
                row[1] for row in conn.execute("PRAGMA table_info(submitted_cases)")
            }
            if "embedding" not in columns:
                conn.execute("ALTER TABLE submitted_cases ADD COLUMN embedding TEXT")
            if "reviewer_decision" not in columns:
                conn.execute(
                    "ALTER TABLE submitted_cases ADD COLUMN reviewer_decision "
                    "TEXT NOT NULL DEFAULT 'pending'"
                )
            if "reviewer_note" not in columns:
                conn.execute(
                    "ALTER TABLE submitted_cases ADD COLUMN reviewer_note TEXT"
                )
            if "decided_at" not in columns:
                conn.execute("ALTER TABLE submitted_cases ADD COLUMN decided_at TEXT")
            if "status" not in columns:
                conn.execute(
                    "ALTER TABLE submitted_cases ADD COLUMN status "
                    "TEXT NOT NULL DEFAULT 'submitted'"
                )
            if "status_updated_at" not in columns:
                conn.execute(
                    "ALTER TABLE submitted_cases ADD COLUMN status_updated_at TEXT"
                )
            if "architecture_sketch" not in columns:
                conn.execute(
                    "ALTER TABLE submitted_cases ADD COLUMN architecture_sketch TEXT"
                )
            if "sharpening_draft" not in columns:
                conn.execute(
                    "ALTER TABLE submitted_cases ADD COLUMN sharpening_draft TEXT"
                )
            if "solution_business" not in columns:
                conn.execute(
                    "ALTER TABLE submitted_cases ADD COLUMN solution_business TEXT"
                )

    def save(self, case: SubmittedCase) -> None:
        """Persistiert einen SubmittedCase. INSERT OR REPLACE bei Duplikat-ID."""
        use_case_json = case.use_case.model_dump_json()
        result_json = _serialize_result(case.result)
        embedding_json = (
            json.dumps(case.embedding) if case.embedding is not None else None
        )
        decided_at_str = (
            case.decided_at.isoformat() if case.decided_at is not None else None
        )
        status_updated_at_str = (
            case.status_updated_at.isoformat()
            if case.status_updated_at is not None
            else None
        )
        with connect(self._db_path) as conn:
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
                    embedding_json,
                    case.reviewer_decision.value,
                    case.reviewer_note,
                    decided_at_str,
                    case.status.value,
                    status_updated_at_str,
                    case.architecture_sketch,
                    case.sharpening_draft,
                    case.solution_business,
                ),
            )

    def get(self, case_id: str) -> SubmittedCase | None:
        """Gibt einen Case per ID zurueck oder None."""
        with connect(self._db_path) as conn:
            row = conn.execute(
                _SELECT_BY_ID_SQL,
                (case_id,),
            ).fetchone()
        if row is None:
            return None
        return _row_to_case(row)

    def list_all(self) -> list[SubmittedCase]:
        """Alle gespeicherten Cases, chronologisch nach submitted_at."""
        with connect(self._db_path) as conn:
            rows = conn.execute(_SELECT_ALL_SQL).fetchall()
        return [_row_to_case(row) for row in rows]

    def delete(self, case_id: str) -> None:
        """Loescht einen Case + seine Monitoring-Eintraege (DSGVO Art. 17,
        ADR-0038; Monitoring-Kaskade Monitoring-ADR).

        Beide DELETEs laufen in derselben kurzlebigen Verbindung (eine
        Transaktion) -- ein Case und seine append-only Zeitleiste verschwinden
        gemeinsam, kein verwaister Eintrag. Idempotent: DELETE auf eine nicht
        existierende ID ist ein No-op. Die Existenzpruefung (-> 404) liegt im
        Service, nicht hier.
        """
        with connect(self._db_path) as conn:
            conn.execute(_DELETE_BY_ID_SQL, (case_id,))
            conn.execute(_DELETE_MONITORING_BY_CASE_SQL, (case_id,))

    def update_field(
        self, case_id: str, field: CaseUpdateField, value: str | None
    ) -> None:
        """Schreibt genau ein nachgelagert befuelltes Feld (F-011).

        Per-Feld-UPDATE statt INSERT OR REPLACE des ganzen Case: parallele
        LLM-Operationen (sharpen/propose/compliance) ueberschreiben sich
        nicht mehr gegenseitig. No-op bei unbekannter case_id (analog delete).
        """
        with connect(self._db_path) as conn:
            conn.execute(_UPDATE_FIELD_SQL[field], (value, case_id))

    def record_decision(
        self,
        case_id: str,
        decision: ReviewerDecision,
        note: str | None,
        decided_at: datetime,
    ) -> None:
        """Setzt Entscheidung + Notiz + Zeitstempel atomar (ADR-0043).

        Dediziertes UPDATE ueber alle drei Spalten in einem Statement --
        kein INSERT OR REPLACE der ganzen Zeile (F-011-Lost-Update-Muster,
        siehe Modul-Docstring). No-op bei unbekannter case_id (analog
        delete/update_field).
        """
        with connect(self._db_path) as conn:
            conn.execute(
                _RECORD_DECISION_SQL,
                (decision.value, note, decided_at.isoformat(), case_id),
            )

    def update_status(
        self, case_id: str, status: CaseStatus, updated_at: datetime
    ) -> None:
        """Setzt Lifecycle-Status + Zeitstempel atomar (Lifecycle-ADR).

        Dediziertes UPDATE beider Spalten (status + status_updated_at) in einem
        Statement -- kein INSERT OR REPLACE der ganzen Zeile
        (F-011-Lost-Update-Muster, analog record_decision). No-op bei
        unbekannter case_id (analog delete/update_field).
        """
        with connect(self._db_path) as conn:
            conn.execute(
                _UPDATE_STATUS_SQL, (status.value, updated_at.isoformat(), case_id)
            )

    def add_monitoring_entry(self, entry: MonitoringEntry) -> None:
        """Haengt einen Monitoring-Eintrag an (append-only INSERT, Monitoring-ADR).

        Kein UPDATE, kein OR REPLACE -- die id ist ein frischer generierter
        Wert je Eintrag; ein Konflikt kaeme nur bei einem ID-Generator-Bug
        vor und soll dann laut scheitern, nicht still ueberschreiben.
        """
        with connect(self._db_path) as conn:
            conn.execute(
                _INSERT_MONITORING_SQL,
                (
                    entry.id,
                    entry.case_id,
                    entry.created_at.isoformat(),
                    entry.note,
                    entry.status_snapshot,
                ),
            )

    def list_monitoring_entries(self, case_id: str) -> list[MonitoringEntry]:
        """Eintraege eines Case, chronologisch aufsteigend (created_at, id)."""
        with connect(self._db_path) as conn:
            rows = conn.execute(_SELECT_MONITORING_BY_CASE_SQL, (case_id,)).fetchall()
        return [_row_to_monitoring_entry(row) for row in rows]

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

    async def delete_async(self, case_id: str) -> None:
        """Async-Wrapper um delete() via asyncio.to_thread (ADR-0037/0038)."""
        await asyncio.to_thread(self.delete, case_id)

    async def update_field_async(
        self, case_id: str, field: CaseUpdateField, value: str | None
    ) -> None:
        """Async-Wrapper um update_field() via asyncio.to_thread (F-011)."""
        await asyncio.to_thread(self.update_field, case_id, field, value)

    async def record_decision_async(
        self,
        case_id: str,
        decision: ReviewerDecision,
        note: str | None,
        decided_at: datetime,
    ) -> None:
        """Async-Wrapper um record_decision() via asyncio.to_thread (ADR-0043)."""
        await asyncio.to_thread(
            self.record_decision, case_id, decision, note, decided_at
        )

    async def update_status_async(
        self, case_id: str, status: CaseStatus, updated_at: datetime
    ) -> None:
        """Async-Wrapper um update_status() via asyncio.to_thread (Lifecycle-ADR)."""
        await asyncio.to_thread(self.update_status, case_id, status, updated_at)

    async def add_monitoring_entry_async(self, entry: MonitoringEntry) -> None:
        """Async-Wrapper um add_monitoring_entry() via asyncio.to_thread."""
        await asyncio.to_thread(self.add_monitoring_entry, entry)

    async def list_monitoring_entries_async(
        self, case_id: str
    ) -> list[MonitoringEntry]:
        """Async-Wrapper um list_monitoring_entries() via asyncio.to_thread."""
        return await asyncio.to_thread(self.list_monitoring_entries, case_id)
