"""Integrations-Tests fuer POST/GET /cases/{case_id}/architecture-sketch (P11).

Mock-E2E: Case anlegen -> Loesungsvorschlag erzeugen -> Skizze generieren ->
lesen. Dazu die Fehlerpfade (409 ohne Loesungsvorschlag, 404, Auth), das
Regenerieren (ueberschreibt) und die DSGVO-Loesch-Kaskade (Case weg -> Skizze weg).
"""

from __future__ import annotations

import json

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from structlog.testing import capture_logs

from aect.adapters.api.app import create_app
from aect.adapters.api.dependencies import get_settings, get_triage_service
from aect.adapters.api.settings import Settings
from aect.adapters.in_memory.clock import SystemClock
from aect.adapters.in_memory.id_generator import UUIDGenerator
from aect.adapters.in_memory.llm import MockLLMAdapter
from aect.adapters.in_memory.repository import InMemoryRepository
from aect.adapters.in_memory.retriever import MockRetriever
from aect.application.ports.llm import LLMMessage, LLMPort, LLMResponse, ToolDefinition
from aect.application.ports.repository import CaseUpdateField
from aect.application.service import TriageService
from aect.application.structured_output import (
    ArchitectureSketch,
    IdeationResult,
    parse_structured_llm_output,
)
from aect.domain.roi import load_roi_config

TEST_API_KEY = "test-api-key-aect-2026"

_VALID_PAYLOAD: dict = {
    "title": "Automatische Rechnungsverarbeitung mit AI",
    "submitter": "Maria Muster",
    "department": "Finance",
    "country": "de",
    "current_state": (
        "Aktuell werden eingehende Rechnungen manuell gescannt und die "
        "relevanten Felder von Mitarbeitern in SAP eingetragen. "
        "Dieser Prozess dauert pro Rechnung ca. 15 Minuten."
    ),
    "desired_state": (
        "Kuenftig soll ein KI-System eingehende Rechnungen automatisch "
        "auslesen, Pflichtfelder erkennen und direkt in SAP befuellen."
    ),
    "example_process": (
        "Eingehende Rechnung von Lieferant X wird manuell gescannt "
        "und Betraege sowie Kostenstellen haendig abgetippt."
    ),
    "time_per_case_hours_current": 0.2,
    "time_per_case_hours_with_ai": 0.0,
    "occurrences_per_employee_per_year": 5000,
    "affected_employees_count": 10,
    "employee_category": "professional",
    "adoption_type": "fixed_process_step",
    "implementation_approach": "development_on_existing",
    "data_classification": "no_personal_data",
}


def _make_app(
    llm: LLMPort | None = None, repository: InMemoryRepository | None = None
) -> FastAPI:
    """Repository ausserhalb der Lambda -- State muss ueber mehrere Requests
    (Case anlegen, propose, sketch, get) erhalten bleiben (wie test_sharpen)."""
    app = create_app()
    repo = repository if repository is not None else InMemoryRepository()
    inner_llm = llm if llm is not None else MockLLMAdapter()
    app.dependency_overrides[get_settings] = lambda: Settings(api_key=TEST_API_KEY)
    app.dependency_overrides[get_triage_service] = lambda: TriageService(
        repository=repo,
        clock=SystemClock(),
        id_generator=UUIDGenerator(),
        roi_config=load_roi_config(),
        llm=inner_llm,
        retriever=MockRetriever(),
    )
    return app


# Schema-valides, technikfreies Loesungs-JSON (V4-P6) -- propose_solution() setzt
# damit proposal_text (Voraussetzung fuer die Skizze), bevor die Skizze scheitert.
_SOLUTION_JSON = json.dumps(
    {
        "solution_business": (
            "Die Vorgaenge werden kuenftig automatisch vorbereitet und den "
            "Mitarbeitenden strukturiert vorgelegt; die Entscheidung bleibt beim "
            "Menschen."
        ),
        "solution_technical": "Ein knapper technischer Loesungsvorschlag als Grundlage.",
    }
)


class _BrokenSketchLLM:
    """complete() liefert eine valide Antwort (fuer propose_solution), aber
    generate_architecture_sketch wirft ueber den realen Schema-Validierungspfad
    eine InvalidLLMOutputError -- die Route muss sie sauber auf 422 mappen
    (kein 500/502-Stack-Trace). Analog _BrokenIdeationLLM in test_ideation.py.
    """

    async def complete(
        self, messages: list[LLMMessage], tools: list[ToolDefinition] | None = None
    ) -> LLMResponse:
        return LLMResponse(content=_SOLUTION_JSON)

    async def generate_ideation(self, problem_description: str) -> IdeationResult:
        raise NotImplementedError

    async def generate_architecture_sketch(
        self, case_id: str, title: str, description: str, proposal_text: str
    ) -> ArchitectureSketch:
        # Fehlende Pflichtfelder (nodes/edges) -> InvalidLLMOutputError.
        return parse_structured_llm_output("{}", ArchitectureSketch)


class _OverlongLabelSketchLLM:
    """Liefert VOLLSTAENDIGES, sonst valides Graph-JSON -- aber mit einem Label
    > 60 Zeichen. Das ist der reale Fehlerfall (verbose deutsche Funktions-
    Labels), der live zum 502 fuehrte: der LLM-Call gelingt (komplettes JSON,
    nicht abgeschnitten), erst die Schema-Validierung im Adapter schlaegt fehl.
    """

    _OVERLONG_LABEL = (
        "Automatisierte Klassifikation und Weiterleitung eingehender "
        "Dokumente an die zustaendige Fachabteilung"
    )

    async def complete(
        self, messages: list[LLMMessage], tools: list[ToolDefinition] | None = None
    ) -> LLMResponse:
        return LLMResponse(content=_SOLUTION_JSON)

    async def generate_ideation(self, problem_description: str) -> IdeationResult:
        raise NotImplementedError

    async def generate_architecture_sketch(
        self, case_id: str, title: str, description: str, proposal_text: str
    ) -> ArchitectureSketch:
        raw = json.dumps(
            {
                "nodes": [
                    {"id": "nutzer", "label": "Sachbearbeiter", "kind": "user"},
                    {
                        "id": "klassifikation",
                        "label": self._OVERLONG_LABEL,
                        "kind": "ai_service",
                    },
                    {"id": "db", "label": "Fall-Datenbank", "kind": "data_store"},
                ],
                "edges": [{"source": "nutzer", "target": "klassifikation"}],
            }
        )
        return parse_structured_llm_output(raw, ArchitectureSketch)


class _FailingSketchPersistRepo(InMemoryRepository):
    """update_field_async wirft NUR fuer 'architecture_sketch' -- simuliert einen
    Persistenzfehler HINTER dem gelungenen LLM-Call und dem Mermaid-Bau. Der
    proposal_text-Write (vorher) bleibt intakt, sonst scheiterte schon propose-
    solution. Die Route muss das auf 500 mappen (strukturiert geloggt), nicht 502.
    """

    async def update_field_async(
        self, case_id: str, field: CaseUpdateField, value: str | None
    ) -> None:
        if field == "architecture_sketch":
            raise RuntimeError("db write failed")
        await super().update_field_async(case_id, field, value)


async def test_sketch_invalid_llm_output_returns_422_with_reason() -> None:
    app = _make_app(llm=_BrokenSketchLLM())
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        case_id = await _create_case(client)
        await _add_proposal(client, case_id)
        response = await client.post(
            f"/cases/{case_id}/architecture-sketch",
            headers={"X-API-Key": TEST_API_KEY},
        )
    # Schema-Verstoss -> 422 (nicht 502): der LLM-Call gelang, der Inhalt nicht.
    assert response.status_code == 422
    detail = response.json()["detail"]
    # Praezise Begruendung: nennt das verletzte Schema.
    assert "ArchitectureSketch" in detail
    # Kein Stack-Trace / keine internen Details in der Antwort.
    assert "Traceback" not in response.text


async def test_sketch_realistic_schema_violation_returns_422_naming_rule() -> None:
    """Realer Fehlerfall: vollstaendiges Graph-JSON, aber ein Label > 60 Zeichen.
    Die 422-Begruendung nennt die konkret verletzte Regel (label/string_too_long),
    damit das naechste Vorkommnis selbst-diagnostizierend ist."""
    app = _make_app(llm=_OverlongLabelSketchLLM())
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        case_id = await _create_case(client)
        await _add_proposal(client, case_id)
        response = await client.post(
            f"/cases/{case_id}/architecture-sketch",
            headers={"X-API-Key": TEST_API_KEY},
        )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "label" in detail
    assert "string_too_long" in detail
    assert "Traceback" not in response.text


async def test_sketch_internal_persistence_error_returns_500_structured_log() -> None:
    """Fehler HINTER dem LLM-Call (Persistenz) bleibt 500 -- aber strukturiert
    geloggt (sketch_generation_failed) und ohne internes Leck an den Client."""
    app = _make_app(repository=_FailingSketchPersistRepo())
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        case_id = await _create_case(client)
        await _add_proposal(client, case_id)
        with capture_logs() as logs:
            response = await client.post(
                f"/cases/{case_id}/architecture-sketch",
                headers={"X-API-Key": TEST_API_KEY},
            )
    assert response.status_code == 500
    assert "Traceback" not in response.text
    assert "db write failed" not in response.text
    events = [e for e in logs if e.get("event") == "sketch_generation_failed"]
    assert len(events) == 1
    assert events[0]["case_id"] == case_id
    assert events[0]["error_type"] == "RuntimeError"


async def _create_case(client: AsyncClient) -> str:
    created = await client.post(
        "/triage", json=_VALID_PAYLOAD, headers={"X-API-Key": TEST_API_KEY}
    )
    assert created.status_code == 201
    case_id: str = created.json()["id"]
    return case_id


async def _add_proposal(client: AsyncClient, case_id: str) -> None:
    resp = await client.post(
        f"/cases/{case_id}/propose-solution", headers={"X-API-Key": TEST_API_KEY}
    )
    assert resp.status_code == 200


async def test_sketch_without_key_returns_401() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        response = await client.post("/cases/some-id/architecture-sketch")
    assert response.status_code == 401


async def test_sketch_unknown_case_returns_404() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        response = await client.post(
            "/cases/does-not-exist/architecture-sketch",
            headers={"X-API-Key": TEST_API_KEY},
        )
    assert response.status_code == 404


async def test_sketch_without_proposal_returns_409() -> None:
    """Ohne Loesungsvorschlag kein Beschreibungsmaterial -> 409 (typisiert)."""
    app = _make_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        case_id = await _create_case(client)
        response = await client.post(
            f"/cases/{case_id}/architecture-sketch",
            headers={"X-API-Key": TEST_API_KEY},
        )
    assert response.status_code == 409
    assert "Loesungsvorschlag" in response.json()["detail"]


async def test_sketch_e2e_generates_persists_and_reads() -> None:
    app = _make_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        case_id = await _create_case(client)
        await _add_proposal(client, case_id)

        post = await client.post(
            f"/cases/{case_id}/architecture-sketch",
            headers={"X-API-Key": TEST_API_KEY},
        )
        assert post.status_code == 200
        body = post.json()
        assert body["case_id"] == case_id
        assert body["prompt_version"] == "v1"
        # Mock-Adapter: user -> system -> data_store.
        assert len(body["nodes"]) == 3
        assert {n["kind"] for n in body["nodes"]} == {"user", "system", "data_store"}
        assert body["mermaid_source"].startswith("flowchart LR")
        # Label-Klammern des Mock-Knotens ("[mock] ...") werden escaped.
        assert "[mock]" not in body["mermaid_source"]
        assert "mock Verarbeitungs-System" in body["mermaid_source"]

        # GET liefert dieselbe Skizze.
        get = await client.get(
            f"/cases/{case_id}/architecture-sketch",
            headers={"X-API-Key": TEST_API_KEY},
        )
        assert get.status_code == 200
        sketch = get.json()["sketch"]
        assert sketch is not None
        assert sketch["case_id"] == case_id
        assert sketch["mermaid_source"] == body["mermaid_source"]


async def test_sketch_regenerate_overwrites_generated_at() -> None:
    app = _make_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        case_id = await _create_case(client)
        await _add_proposal(client, case_id)

        first = await client.post(
            f"/cases/{case_id}/architecture-sketch",
            headers={"X-API-Key": TEST_API_KEY},
        )
        second = await client.post(
            f"/cases/{case_id}/architecture-sketch",
            headers={"X-API-Key": TEST_API_KEY},
        )

    assert first.status_code == 200
    assert second.status_code == 200
    # Abgeleitetes Artefakt (D20): Regenerieren ueberschreibt, generated_at
    # aendert sich, der Graph bleibt (deterministischer Mock) gleich.
    assert first.json()["generated_at"] != second.json()["generated_at"]
    assert first.json()["nodes"] == second.json()["nodes"]


async def test_get_sketch_none_when_never_generated() -> None:
    """Case existiert, aber nie eine Skizze -> 200 {"sketch": null}."""
    app = _make_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        case_id = await _create_case(client)
        response = await client.get(
            f"/cases/{case_id}/architecture-sketch",
            headers={"X-API-Key": TEST_API_KEY},
        )
    assert response.status_code == 200
    assert response.json() == {"sketch": None}


async def test_get_sketch_unknown_case_returns_404() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        response = await client.get(
            "/cases/does-not-exist/architecture-sketch",
            headers={"X-API-Key": TEST_API_KEY},
        )
    assert response.status_code == 404


async def test_delete_case_removes_sketch() -> None:
    """DSGVO-Kaskade (Art. 17): stirbt der Case, ist die Skizze mit weg."""
    app = _make_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        case_id = await _create_case(client)
        await _add_proposal(client, case_id)
        await client.post(
            f"/cases/{case_id}/architecture-sketch",
            headers={"X-API-Key": TEST_API_KEY},
        )

        deleted = await client.delete(
            f"/cases/{case_id}", headers={"X-API-Key": TEST_API_KEY}
        )
        assert deleted.status_code == 204

        # Case (und damit die Skizze) ist weg -> GET liefert 404, nicht null.
        get = await client.get(
            f"/cases/{case_id}/architecture-sketch",
            headers={"X-API-Key": TEST_API_KEY},
        )
    assert get.status_code == 404
