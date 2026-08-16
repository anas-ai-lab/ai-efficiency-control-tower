"""Vertragstests fuer den oeffentlichen GET /cases/top (Ticket 4b)."""

from __future__ import annotations

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from aect.adapters.api.app import create_app
from aect.adapters.api.dependencies import get_triage_service
from aect.domain.top_cases import TopCaseRef


class _TopCasesServiceStub:
    """Liefert feste Domain-Referenzen ohne ROI-/Persistenz-Abhaengigkeit."""

    def list_top_cases(self, limit: int = 3) -> list[TopCaseRef]:
        return [
            TopCaseRef(case_id="case-3", title="Dritter Top-Case"),
            TopCaseRef(case_id="case-1", title="Erster Top-Case"),
        ][:limit]


def _make_app() -> FastAPI:
    app = create_app()
    app.dependency_overrides[get_triage_service] = _TopCasesServiceStub
    return app


async def test_top_cases_is_public_and_exposes_exactly_id_and_title() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as client:
        response = await client.get("/cases/top")

    assert response.status_code == 200
    assert response.json() == [
        {"case_id": "case-3", "title": "Dritter Top-Case"},
        {"case_id": "case-1", "title": "Erster Top-Case"},
    ]
    assert all(set(item) == {"case_id", "title"} for item in response.json())
