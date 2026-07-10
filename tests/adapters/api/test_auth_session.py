"""Tests fuer den Admin-Session-Login (V4-P-Auth): Passwort, Cookie, Ablauf.

Ergaenzt test_auth.py (API-Key-Zweig + Public/Admin-Matrix) um den Browser-Weg:
POST /auth/login setzt ein httpOnly-Session-Cookie, das require_admin als
gueltige Admin-Identitaet akzeptiert -- ganz ohne X-API-Key. Deshalb setzen die
Session-Apps hier bewusst api_key="" (nur der Passwort-Hash ist konfiguriert):
so ist bewiesen, dass die Session allein autorisiert.

Isolation: jede App injiziert einen frischen InMemorySessionStore per
dependency_overrides[get_session_store] -- kein geteilter Prozess-Singleton
zwischen Tests.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from aect.adapters.api.app import create_app
from aect.adapters.api.dependencies import (
    SESSION_COOKIE_NAME,
    get_retriever_port,
    get_session_store,
    get_settings,
    key_fingerprint,
)
from aect.adapters.api.password import hash_password
from aect.adapters.api.settings import Settings
from aect.adapters.in_memory.retriever import MockRetriever
from aect.adapters.in_memory.session_store import InMemorySessionStore
from aect.application.ports.session_store import AdminSession

ADMIN_ENDPOINT = "/cases/similarity-pairs"

PASSWORD = "geheimes-admin-passwort-2026"
# Hash einmal beim Import berechnen (scrypt, ~ms) -- verify_password im
# Login-Endpoint prueft gegen genau diesen Wert.
PASSWORD_HASH = hash_password(PASSWORD)


def _make_session_app(
    *,
    store: InMemorySessionStore | None = None,
    secure: bool = False,
) -> tuple[FastAPI, InMemorySessionStore]:
    """App mit konfiguriertem Passwort-Hash, aber OHNE API-Key (api_key='')."""
    session_store = store if store is not None else InMemorySessionStore()
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(
        api_key="",
        admin_password_hash=PASSWORD_HASH,
        session_cookie_secure=secure,
        chroma_host="",
    )
    app.dependency_overrides[get_retriever_port] = lambda: MockRetriever()
    app.dependency_overrides[get_session_store] = lambda: session_store
    return app, session_store


# ---------------------------------------------------------------------------
# Login: Erfolg + Cookie-Attribute
# ---------------------------------------------------------------------------


async def test_login_with_correct_password_sets_session_cookie() -> None:
    app, _ = _make_session_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/auth/login", json={"password": PASSWORD})
    assert response.status_code == 200
    assert response.json() == {"authenticated": True}
    set_cookie = response.headers.get("set-cookie", "")
    lowered = set_cookie.lower()
    assert f"{SESSION_COOKIE_NAME}=" in set_cookie
    assert "httponly" in lowered
    assert "samesite=lax" in lowered
    assert "path=/" in lowered
    # Default-Demo ueber http: kein Secure-Flag.
    assert "secure" not in lowered


async def test_login_secure_flag_sets_secure_cookie() -> None:
    app, _ = _make_session_app(secure=True)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/auth/login", json={"password": PASSWORD})
    assert "Secure" in response.headers.get("set-cookie", "")


async def test_login_with_wrong_password_returns_401_no_cookie() -> None:
    app, store = _make_session_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/auth/login", json={"password": "falsch"})
    assert response.status_code == 401
    assert SESSION_COOKIE_NAME not in response.headers.get("set-cookie", "")


async def test_login_does_not_leak_password_in_response() -> None:
    app, _ = _make_session_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/auth/login", json={"password": "falsch-xyz"})
    assert "falsch-xyz" not in response.text
    assert PASSWORD not in response.text


async def test_login_unconfigured_returns_503() -> None:
    """Kein AECT_ADMIN_PASSWORD_HASH -> Login serverseitig nicht eingerichtet."""
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(
        api_key="", admin_password_hash="", chroma_host=""
    )
    app.dependency_overrides[get_retriever_port] = lambda: MockRetriever()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/auth/login", json={"password": PASSWORD})
    assert response.status_code == 503


# ---------------------------------------------------------------------------
# Session autorisiert Admin-Routen (require_admin via Cookie, ohne API-Key)
# ---------------------------------------------------------------------------


async def test_session_cookie_authorizes_admin_route() -> None:
    app, _ = _make_session_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Vor dem Login: Admin-Route gesperrt.
        assert (await client.get(ADMIN_ENDPOINT)).status_code == 401
        # Login setzt das Cookie in den Client-Cookie-Jar.
        login = await client.post("/auth/login", json={"password": PASSWORD})
        assert login.status_code == 200
        # Danach autorisiert allein das Cookie (kein X-API-Key gesetzt).
        authed = await client.get(ADMIN_ENDPOINT)
    assert authed.status_code == 200


async def test_auth_me_reflects_session_state() -> None:
    app, _ = _make_session_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        assert (await client.get("/auth/me")).json() == {"authenticated": False}
        await client.post("/auth/login", json={"password": PASSWORD})
        me = await client.get("/auth/me")
    assert me.json() == {"authenticated": True}


async def test_logout_clears_session_and_cookie() -> None:
    app, store = _make_session_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.post("/auth/login", json={"password": PASSWORD})
        assert (await client.get(ADMIN_ENDPOINT)).status_code == 200
        logout = await client.post("/auth/logout")
        assert logout.status_code == 200
        assert logout.json() == {"authenticated": False}
        # Nach dem Logout ist die Admin-Route wieder gesperrt.
        assert (await client.get(ADMIN_ENDPOINT)).status_code == 401
        assert (await client.get("/auth/me")).json() == {"authenticated": False}


# ---------------------------------------------------------------------------
# Ablauf: abgelaufene Session wird beim Zugriff verworfen
# ---------------------------------------------------------------------------


async def test_expired_session_is_rejected_and_deleted() -> None:
    store = InMemorySessionStore()
    token = "abgelaufenes-test-token"
    token_hash = key_fingerprint(token, length=0)
    now = datetime.now(tz=UTC)
    store.create(
        AdminSession(
            token_hash=token_hash,
            created_at=now - timedelta(hours=13),
            expires_at=now - timedelta(hours=1),  # bereits abgelaufen
        )
    )
    app, _ = _make_session_app(store=store)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            ADMIN_ENDPOINT, cookies={SESSION_COOKIE_NAME: token}
        )
    assert response.status_code == 401
    # Beim Zugriff verworfen (Vorgabe): der Eintrag ist weg.
    assert store.get(token_hash) is None


async def test_unknown_session_cookie_is_rejected() -> None:
    """Ein Cookie ohne passenden Store-Eintrag autorisiert nicht (kein Crash)."""
    app, _ = _make_session_app()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            ADMIN_ENDPOINT, cookies={SESSION_COOKIE_NAME: "kein-echtes-token"}
        )
    assert response.status_code == 401
