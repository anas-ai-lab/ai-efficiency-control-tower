"""Tests fuer den public GET /cases/{id} -- read-only Sicht (E9/SDR-0003).

Schema-Split (V4.1-S8): der anonyme Einreicher liest die beim Einreichen
erfassten Grunddaten, den Status und die Board-Entscheidung samt Begruendung --
sonst nichts. Die Bewertung (Zone, Nettonutzen, Scores, Analyse/Empfehlung,
Loesung, Compliance, Report) ist Admin-Material und steht im anonymen JSON
ueberhaupt nicht, auch nicht als null. Diese Tests belegen den public Zugriff,
den Schema-Split in beide Richtungen, das 404 fuer fehlende Cases, das
Durchreichen admin-ausgeloester Ergebnisse an Admins und die Routing-Ordnung
gegen similarity-pairs.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from aect.adapters.api.app import create_app
from aect.adapters.api.dependencies import get_settings, get_triage_service
from aect.adapters.api.settings import Settings
from aect.adapters.in_memory.clock import SystemClock
from aect.adapters.in_memory.id_generator import UUIDGenerator
from aect.adapters.in_memory.llm import MockLLMAdapter
from aect.adapters.in_memory.repository import InMemoryRepository
from aect.adapters.in_memory.retriever import MockRetriever
from aect.application.service import TriageService
from aect.domain.roi import load_roi_config

TEST_API_KEY = "test-api-key-aect-2026"

VALID_PAYLOAD: dict = {
    "title": "Automatische Rechnungsverarbeitung mit AI",
    "submitter": "Maria Muster",
    "department": "Finance",
    "country": "de",
    "current_state": (
        "Aktuell werden eingehende Rechnungen manuell gescannt und die "
        "relevanten Felder von Mitarbeitern in SAP eingetragen. Der Prozess "
        "bindet erhebliche Kapazitaet im Finance-Team."
    ),
    "desired_state": (
        "Kuenftig soll ein KI-System eingehende Rechnungen automatisch "
        "auslesen, Pflichtfelder erkennen und direkt in SAP befuellen. Ziel "
        "ist eine Reduktion der manuellen Bearbeitungszeit pro Vorgang."
    ),
    "example_process": (
        "Eingehende Rechnung von Lieferant X wird manuell gescannt und "
        "Betraege sowie Kostenstellen haendig abgetippt."
    ),
    "time_per_case_hours_current": 0.2,
    "time_per_case_hours_with_ai": 0.0,
    "occurrences_per_employee_per_year": 5000,
    "affected_employees_count": 10,
    "employee_category": "professional",
    "adoption_type": "fixed_process_step",
    "evidence_level": "pure_estimate",
    "implementation_approach": "development_on_existing",
    "data_classification": "no_personal_data",
}


def _make_app() -> FastAPI:
    """App mit gemeinsamem Repository (Submit + Read ueber mehrere Requests)."""
    app = create_app()
    repository = InMemoryRepository()
    app.dependency_overrides[get_settings] = lambda: Settings(
        api_key=TEST_API_KEY, chroma_host=""
    )
    app.dependency_overrides[get_triage_service] = lambda: TriageService(
        repository=repository,
        clock=SystemClock(),
        id_generator=UUIDGenerator(),
        roi_config=load_roi_config(),
        llm=MockLLMAdapter(),
        retriever=MockRetriever(),
    )
    return app


async def _submit_public(client: AsyncClient) -> str:
    """Anonyme Einreichung (kein X-API-Key) -> Case-ID."""
    created = await client.post("/triage", json=VALID_PAYLOAD)
    assert created.status_code == 201
    return created.json()["id"]


# Jeder Schluessel, der eine Bewertungsgroesse traegt oder ihre Existenz
# verraet. Die Liste ist bewusst breiter als das aktuelle Schema (z. B.
# assessment_visible aus V4-P7): faellt eine dieser Groessen je wieder in eine
# Public-Response, schlaegt der Test an -- auch wenn sie unter einem alten Namen
# zurueckkehrt.
ASSESSMENT_KEYS = frozenset(
    {
        "triage",
        "report",
        "zone",
        "net_expected_benefit_eur",
        "composite",
        "composite_total",
        "hours_per_year",
        "is_actionable",
        "feasibility_score",
        "feasibility_definition",
        "assessment_visible",
        "evaluation_pending",
        "score_breakdown",
        "roi",
        "routing",
        "vorfilter",
        "decision_report",
        "technical_report",
        "business_summary",
        "technical_detail",
        "solution_business",
        "proposal_text",
        "sharpened_text",
        "compliance_hint_text",
        "compliance_citations",
        "recommendation",
        "empfehlung_satz",
    }
)


def _all_keys(node: Any) -> set[str]:
    """Sammelt ALLE Schluessel rekursiv -- auch aus verschachtelten Objekten.

    Ein Bewertungsfeld waere sonst nur auf der obersten Ebene widerlegt; ein in
    einem Unterobjekt mitgereichter Score bliebe unentdeckt.
    """
    keys: set[str] = set()
    if isinstance(node, dict):
        for key, value in node.items():
            keys.add(key)
            keys |= _all_keys(value)
    elif isinstance(node, list):
        for item in node:
            keys |= _all_keys(item)
    return keys


async def test_case_detail_anonymous_before_decision_hides_assessment() -> None:
    """V4.1-S8: vor der Board-Entscheidung sieht der anonyme Einreicher NUR die
    rohen Eingaben + Status. Kein Bewertungsfeld im JSON -- auch nicht als null
    (frueher trugen triage/report null und verrieten damit ihre Existenz)."""
    app = _make_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        case_id = await _submit_public(client)
        response = await client.get(f"/cases/{case_id}")  # kein X-API-Key -> anonym

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == case_id
    assert body["status"] == "submitted"
    # Eingaben immer sichtbar (Erklaerbarkeit), Bewertung nie.
    assert body["eingaben"]["title"] == VALID_PAYLOAD["title"]
    # Noch nicht entschieden -> kein Entscheidungs-Objekt.
    assert body["decision"] is None
    assert set(body) == {
        "id",
        "submitted_at",
        "status",
        "discontinued",
        "eingaben",
        "decision",
    }


async def test_case_detail_anonymous_carries_no_assessment_field() -> None:
    """Erfolgskriterium (V4.1-S8): der anonyme Detail-Read enthaelt KEINES der
    Bewertungsfelder -- geprueft rekursiv ueber das gesamte JSON, im schaerfsten
    Zustand: Case ist bewertet, geschaerft, geloest UND vom Board freigegeben.
    Gaebe es einen Pfad, ueber den eine Bewertungsgroesse anonym sichtbar wird,
    liefe er hier auf."""
    app = _make_app()
    auth = {"X-API-Key": TEST_API_KEY}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        case_id = await _submit_public(client)
        # Alles, was ein Admin ausloesen kann, wird ausgeloest und uebernommen.
        assert (
            await client.post(f"/cases/{case_id}/sharpen", headers=auth)
        ).status_code == 200
        assert (
            await client.post(f"/cases/{case_id}/sharpen/accept", headers=auth)
        ).status_code == 200
        assert (
            await client.post(f"/cases/{case_id}/propose-solution", headers=auth)
        ).status_code == 200
        assert (
            await client.post(f"/cases/{case_id}/propose-solution/accept", headers=auth)
        ).status_code == 200
        assert (
            await client.post(
                f"/cases/{case_id}/decision",
                json={"decision": "approved", "note": "Tragfaehig, Board-Freigabe."},
                headers=auth,
            )
        ).status_code == 200

        body = (await client.get(f"/cases/{case_id}")).json()  # anonym

    leaked = _all_keys(body) & ASSESSMENT_KEYS
    assert leaked == set(), f"Bewertungsfelder im anonymen JSON: {sorted(leaked)}"


async def test_case_detail_anonymous_sees_board_decision_with_rationale() -> None:
    """Was der Anonyme statt der Bewertung bekommt: die Board-Entscheidung mit
    Begruendung -- das Ergebnis, nicht die Herleitung."""
    app = _make_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        case_id = await _submit_public(client)
        await client.post(
            f"/cases/{case_id}/decision",
            json={"decision": "rejected", "note": "Aufwand steht nicht zum Nutzen."},
            headers={"X-API-Key": TEST_API_KEY},
        )
        body = (await client.get(f"/cases/{case_id}")).json()  # anonym

    assert body["decision"]["reviewer_decision"] == "rejected"
    assert body["decision"]["reviewer_note"] == "Aufwand steht nicht zum Nutzen."
    assert body["decision"]["decided_at"] is not None


async def test_case_detail_admin_sees_assessment_before_decision() -> None:
    """V4-P7: das AI Board (Admin, hier via X-API-Key) sieht die Bewertung schon
    VOR der Entscheidung -- sonst koennte es nicht entscheiden."""
    app = _make_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        case_id = await _submit_public(client)
        body = (
            await client.get(f"/cases/{case_id}", headers={"X-API-Key": TEST_API_KEY})
        ).json()

    assert body["triage"] is not None
    assert body["report"] is not None
    assert body["triage"]["score_breakdown"] is not None
    assert body["report"]["business_summary"]["decision_report"]["empfehlung_satz"]


async def test_case_detail_admin_full_after_board_decision() -> None:
    """Der Admin-Read liefert die volle Bewertung: Composite inkl. Subscores,
    Konfidenz-Begruendung, decision_report, technical_report. Bis V4.1-S7 war
    das nach der Board-Entscheidung auch anonym lesbar -- jetzt Admin-only, die
    Inhalte selbst bleiben unveraendert."""
    app = _make_app()
    auth = {"X-API-Key": TEST_API_KEY}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        case_id = await _submit_public(client)
        decision_resp = await client.post(
            f"/cases/{case_id}/decision",
            json={"decision": "approved", "note": None},
            headers=auth,
        )
        assert decision_resp.status_code == 200
        body = (await client.get(f"/cases/{case_id}", headers=auth)).json()

    triage = body["triage"]
    assert triage is not None
    assert {
        "complexity_score",
        "cost_score",
        "data_protection_score",
        "total",
        "effort_label",
    } <= set(triage["composite"])
    conf = triage["zone"]["confidence_reasoning"]
    assert conf["level"] in {"hoch", "mittel", "niedrig"}
    assert conf["gruende"]
    assert triage["routing"]["recommendation_text"]
    breakdown = triage["score_breakdown"]
    assert len(breakdown["components"]) == 3
    assert breakdown["max_total"] == 9
    assert breakdown["feasibility_score"] == 10 - breakdown["total"]

    report = body["report"]
    assert "summary_text" not in report["business_summary"]
    decision = report["business_summary"]["decision_report"]
    assert decision["empfehlung_satz"]
    assert decision["kennzahlen"]["aufwand"]["max"] == 9
    assert len(decision["contra_punkte"]) >= 2
    assert report["technical_detail"]["technical_report"]["datenlage"]


async def test_case_detail_public_returns_raw_inputs() -> None:
    """Anonym: GET /cases/{id} liefert die rohen Eingaben (UseCaseInput)
    unveraendert zurueck -- Erklaerbarkeit: pruefbar gegen die erfassten Daten."""
    app = _make_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        case_id = await _submit_public(client)
        body = (await client.get(f"/cases/{case_id}")).json()

    eingaben = body["eingaben"]
    # Vollstaendiges UseCaseInput-Schema (Freitext, Zahlen, Enums als .value).
    assert eingaben["title"] == VALID_PAYLOAD["title"]
    assert eingaben["submitter"] == VALID_PAYLOAD["submitter"]
    assert eingaben["department"] == VALID_PAYLOAD["department"]
    assert eingaben["country"] == "de"
    assert eingaben["current_state"] == VALID_PAYLOAD["current_state"]
    assert eingaben["desired_state"] == VALID_PAYLOAD["desired_state"]
    assert eingaben["time_per_case_hours_current"] == 0.2
    assert eingaben["time_per_case_hours_with_ai"] == 0.0
    assert eingaben["occurrences_per_employee_per_year"] == 5000
    assert eingaben["affected_employees_count"] == 10
    assert eingaben["employee_category"] == "professional"
    assert eingaben["adoption_type"] == "fixed_process_step"
    assert eingaben["implementation_approach"] == "development_on_existing"
    assert eingaben["data_classification"] == "no_personal_data"
    # Enum-Werte sind Strings (StrEnum.value), keine Objekte -- direkt fuer die
    # Label-Map im Frontend nutzbar.
    assert isinstance(eingaben["country"], str)


async def test_case_detail_untriggered_steps_are_null() -> None:
    """Read-only, kein Trigger: nie ausgeloeste LLM-Schritte stehen auf null.
    Als Admin gelesen (X-API-Key), damit der Report vor der Entscheidung sichtbar
    ist -- die Bedingung betrifft die Sichtbarkeit, nicht die null-Semantik."""
    app = _make_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        case_id = await _submit_public(client)
        body = (
            await client.get(f"/cases/{case_id}", headers={"X-API-Key": TEST_API_KEY})
        ).json()

    assert body["report"]["business_summary"]["sharpened_text"] is None
    assert body["report"]["business_summary"]["compliance_hint_text"] is None
    assert body["report"]["technical_detail"]["proposal_text"] is None


async def test_case_detail_missing_returns_404() -> None:
    app = _make_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/cases/gibt-es-nicht")
    assert response.status_code == 404


async def test_case_detail_reflects_admin_triggered_sharpening() -> None:
    """Was der Admin ausloest und akzeptiert, liest der Admin-Detail-Read
    zurueck: sharpen + accept -> report.business_summary.sharpened_text traegt
    den Text (Read-Pfad liest die Persistenz, kein erneuter Trigger)."""
    app = _make_app()
    auth = {"X-API-Key": TEST_API_KEY}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        case_id = await _submit_public(client)

        # Admin loest Schaerfung aus, uebernimmt sie und entscheidet.
        sharpen = await client.post(f"/cases/{case_id}/sharpen", headers=auth)
        assert sharpen.status_code == 200
        accept = await client.post(f"/cases/{case_id}/sharpen/accept", headers=auth)
        assert accept.status_code == 200
        # Admin-Detail-Read spiegelt den persistierten Stand.
        after = (await client.get(f"/cases/{case_id}", headers=auth)).json()

    assert after["report"]["business_summary"]["sharpened_text"] is not None


async def test_similarity_pairs_not_shadowed_by_detail_route() -> None:
    """Routing-Order-Guard: GET /cases/similarity-pairs bleibt die Admin-Route
    (401 anonym) und wird NICHT als case_id='similarity-pairs' vom public
    Detail-Read geschluckt (das waere 200/404)."""
    app = _make_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/cases/similarity-pairs")
    assert response.status_code == 401
