"""Integrations-Tests fuer require_token_budget (Phase G, 429 vor dem LLM-Call).

Deckt /sharpen, /propose-solution, /compliance-hints -- alle drei nutzen
dieselbe require_token_budget-Dependency (dependencies.py). Budget wird ueber
Settings(token_budget_per_hour=...) exakt auf die per count_tokens() (F-031)
geschaetzte Groesse des Testfalls zugeschnitten -- kein Raten, deterministisch.

Jeder Test verwendet einen EIGENEN API-Key (statt eines gemeinsamen
TEST_API_KEY): get_token_budget_store() cached den In-Memory-Store
lru_cache-artig pro budget_per_hour-Wert (dependencies.py) -- mehrere Tests
mit demselben (deterministischen) Token-Budget wuerden sich sonst denselben
Store-Zustand teilen und sich gegenseitig das Budget wegkonsumieren. Ein
eigener Key pro Test gibt jedem Test einen frischen (api_key_hash,
Fenster)-Eintrag, unabhaengig davon, welcher Store dahinter gecached ist --
analog dazu, wie bestehende Tests _repository/_idempotency_store-Singletons
ueber eindeutige Case-IDs statt eigener Store-Instanzen isolieren.
"""

from __future__ import annotations

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
from aect.application.cost_logger import count_tokens
from aect.application.service import TriageService
from aect.domain.roi import load_roi_config

_VALID_PAYLOAD: dict = {
    "title": "Automatische Rechnungsverarbeitung mit AI",
    "submitter": "Maria Muster",
    "department": "Finance",
    "country": "de",
    "current_state": (
        "Aktuell werden eingehende Rechnungen manuell gescannt und die "
        "relevanten Felder von Mitarbeitern in SAP eingetragen. "
        "Dieser Prozess dauert pro Rechnung ca. 15 Minuten und bindet "
        "erhebliche Kapazitaet im Finance-Team."
    ),
    "desired_state": (
        "Kuenftig soll ein KI-System eingehende Rechnungen automatisch "
        "auslesen, Pflichtfelder erkennen und direkt in SAP befuellen. "
        "Ziel ist eine Reduktion der manuellen Bearbeitungszeit auf unter "
        "2 Minuten pro Vorgang und eine Fehlerquote von unter 1 Prozent."
    ),
    "example_process": (
        "Eingehende Rechnung von Lieferant X wird manuell gescannt "
        "und Betraege sowie Kostenstellen haendig abgetippt."
    ),
    "time_savings_hours_per_case": 0.2,
    "frequency_per_year": 5000,
    "affected_employees_count": 10,
    "employee_category": "professional",
    "adoption_type": "mandatory",
    "implementation_approach": "standard_product",
    "implementation_complexity": 2,
    "data_classification": "no_personal_data",
}


def _expected_tokens(payload: dict) -> int:
    """Exakt dieselbe Textzusammensetzung wie require_token_budget
    (dependencies.py) -- title + current_state + desired_state + example_process."""
    text = (
        f"{payload['title']} {payload['current_state']} "
        f"{payload['desired_state']} {payload['example_process']}"
    )
    return count_tokens(text)


def _make_app(api_key: str, token_budget_per_hour: int) -> FastAPI:
    """Repository ausserhalb der Lambda -- State muss zwischen 'Case anlegen'
    und 'Case schaerfen' (zwei Requests) erhalten bleiben (analog test_sharpen.py)."""
    app = create_app()
    repository = InMemoryRepository()
    app.dependency_overrides[get_settings] = lambda: Settings(
        api_key=api_key, token_budget_per_hour=token_budget_per_hour
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


async def _create_case(client: AsyncClient, api_key: str) -> str:
    created = await client.post(
        "/triage", json=_VALID_PAYLOAD, headers={"X-API-Key": api_key}
    )
    case_id: str = created.json()["id"]
    return case_id


async def test_sharpen_within_budget_succeeds() -> None:
    api_key = "budget-test-within-budget"
    tokens = _expected_tokens(_VALID_PAYLOAD)
    app = _make_app(api_key, token_budget_per_hour=tokens)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        case_id = await _create_case(client, api_key)
        response = await client.post(
            f"/cases/{case_id}/sharpen", headers={"X-API-Key": api_key}
        )
    assert response.status_code == 200


async def test_sharpen_exceeding_budget_returns_429() -> None:
    """Budget kleiner als die Case-Groesse -- schon der erste Call schlaegt fehl."""
    api_key = "budget-test-sharpen-exceeds"
    tokens = _expected_tokens(_VALID_PAYLOAD)
    app = _make_app(api_key, token_budget_per_hour=tokens - 1)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        case_id = await _create_case(client, api_key)
        response = await client.post(
            f"/cases/{case_id}/sharpen", headers={"X-API-Key": api_key}
        )
    assert response.status_code == 429
    assert response.json()["detail"] == "Token budget exceeded for this API key"


async def test_second_sharpen_call_exhausts_budget() -> None:
    """Budget reicht fuer genau einen Call -- der zweite (identische Groesse,
    gleicher Case) ueberschreitet das bereits verbrauchte Stundenfenster."""
    api_key = "budget-test-second-call-exhausts"
    tokens = _expected_tokens(_VALID_PAYLOAD)
    app = _make_app(api_key, token_budget_per_hour=tokens)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        case_id = await _create_case(client, api_key)
        first = await client.post(
            f"/cases/{case_id}/sharpen", headers={"X-API-Key": api_key}
        )
        second = await client.post(
            f"/cases/{case_id}/sharpen", headers={"X-API-Key": api_key}
        )
    assert first.status_code == 200
    assert second.status_code == 429


async def test_propose_solution_exceeding_budget_returns_429() -> None:
    api_key = "budget-test-propose-solution-exceeds"
    tokens = _expected_tokens(_VALID_PAYLOAD)
    app = _make_app(api_key, token_budget_per_hour=tokens - 1)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        case_id = await _create_case(client, api_key)
        response = await client.post(
            f"/cases/{case_id}/propose-solution", headers={"X-API-Key": api_key}
        )
    assert response.status_code == 429


async def test_compliance_hints_exceeding_budget_returns_429() -> None:
    api_key = "budget-test-compliance-hints-exceeds"
    tokens = _expected_tokens(_VALID_PAYLOAD)
    app = _make_app(api_key, token_budget_per_hour=tokens - 1)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        case_id = await _create_case(client, api_key)
        response = await client.post(
            f"/cases/{case_id}/compliance-hints", headers={"X-API-Key": api_key}
        )
    assert response.status_code == 429


async def test_unknown_case_returns_404_not_429_even_with_zero_budget() -> None:
    """require_token_budget prueft nur, wenn der Case existiert -- ein
    unbekannter Case bleibt 404, unabhaengig vom Budget (keine Duplizierung
    der 404-Antwort im Budget-Check)."""
    api_key = "budget-test-unknown-case"
    app = _make_app(api_key, token_budget_per_hour=0)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/cases/does-not-exist/sharpen", headers={"X-API-Key": api_key}
        )
    assert response.status_code == 404


async def test_different_api_keys_have_independent_budgets() -> None:
    """Zwei verschiedene API-Keys (Rotation aktiv) -- jeder Key hat sein
    eigenes Budget, ein erschoepfter Key blockiert den anderen nicht."""
    primary_key = "budget-test-independent-primary"
    next_key = "budget-test-independent-next"
    tokens = _expected_tokens(_VALID_PAYLOAD)
    app = create_app()
    repository = InMemoryRepository()
    app.dependency_overrides[get_settings] = lambda: Settings(
        api_key=primary_key,
        api_key_next=next_key,
        token_budget_per_hour=tokens,
    )
    app.dependency_overrides[get_triage_service] = lambda: TriageService(
        repository=repository,
        clock=SystemClock(),
        id_generator=UUIDGenerator(),
        roi_config=load_roi_config(),
        llm=MockLLMAdapter(),
        retriever=MockRetriever(),
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        case_id = await _create_case(client, primary_key)
        # Primaerer Key erschoepft sein Budget.
        first = await client.post(
            f"/cases/{case_id}/sharpen", headers={"X-API-Key": primary_key}
        )
        # Rotation-Partner-Key hat ein unabhaengiges Budget.
        second = await client.post(
            f"/cases/{case_id}/sharpen", headers={"X-API-Key": next_key}
        )
    assert first.status_code == 200
    assert second.status_code == 200
