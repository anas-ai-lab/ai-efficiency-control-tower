"""Auth-Endpoints -- Admin-Login per Passwort + Session-Cookie (V4-P-Auth).

Zwei Zugriffsstufen (SDR-0003, V4-Demo): anonym (einreichen, Ideen-Assistent,
Ideenliste + Case-Detail read-only) und admin (alles). Kein Multi-User, kein
JWT/OAuth, keine neue Dependency -- scrypt (hashlib) + ein Session-Token
(secrets) + ein httpOnly-Cookie reichen fuer einen Single-User-Demo-Build.

  POST /auth/login   {password} -> setzt Cookie aect_session (12 h), {authenticated}
  POST /auth/logout             -> loescht Session + Cookie, {authenticated: false}
  GET  /auth/me                 -> {authenticated: bool} (Session ODER API-Key)

Alle drei sind bewusst OHNE require_admin: Login/Me muessen anonym erreichbar
sein (sonst kaeme man nie an eine Session), Logout ist idempotent und raeumt
nur das mitgeschickte Cookie ab.

Security:
  - Passwort-Vergleich konstante Laufzeit (verify_password -> hmac.compare_digest).
  - Fehlversuch -> 401 + strukturiertes Log OHNE Passwort (admin_login_failed).
  - Token nur als sha256-Hash persistiert (SessionStorePort), nie im Klartext.
  - Cookie httpOnly + SameSite=Lax; Secure konfigurierbar (Default aus, Demo).
"""

from __future__ import annotations

import secrets
from datetime import timedelta

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, ConfigDict, Field
from starlette.responses import Response

from aect.adapters.api.dependencies import (
    SESSION_COOKIE_NAME,
    SESSION_TTL_HOURS,
    authenticate_admin,
    get_session_store,
    get_settings,
    key_fingerprint,
)
from aect.adapters.api.password import verify_password
from aect.adapters.api.rate_limit import limiter
from aect.adapters.api.settings import Settings
from aect.adapters.in_memory.clock import SystemClock
from aect.application.ports.session_store import AdminSession, SessionStorePort

router = APIRouter(prefix="/auth", tags=["auth"])

# Eigener, auto_error=False APIKeyHeader fuer /auth/me: ein fehlender Header
# liefert None statt 403 -- /auth/me antwortet dann schlicht authenticated=false.
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class LoginRequest(BaseModel):
    """Login-Body -- nur das Passwort.

    max_length: Token-Flooding-/DoS-Schutz (scrypt auf sehr langem Input ist
    teuer), konsistent mit der Eingabe-Disziplin der uebrigen Request-Schemas.
    """

    model_config = ConfigDict(extra="forbid")

    password: str = Field(min_length=1, max_length=1024)


class AuthResponse(BaseModel):
    """Einheitliche Auth-Statusantwort fuer login/logout/me."""

    authenticated: bool


@router.post("/login", response_model=AuthResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    response: Response,
    body: LoginRequest,
    settings: Settings = Depends(get_settings),  # noqa: B008
    session_store: SessionStorePort = Depends(get_session_store),  # noqa: B008
) -> AuthResponse:
    """Prueft das Admin-Passwort und legt bei Erfolg eine Session an.

    request/response: von slowapi benoetigt (Rate-Limit-Key) bzw. zum Setzen des
    Cookies. Rate Limit: 10/Minute (Brute-Force-Bremse fuer den anonymen Pfad).

    Raises:
        HTTPException 503: kein AECT_ADMIN_PASSWORD_HASH konfiguriert (Login
            serverseitig gar nicht eingerichtet -- kein Client-Fehler).
        HTTPException 401: falsches Passwort.
    """
    if not settings.admin_password_hash:
        raise HTTPException(
            status_code=503,
            detail="Admin login not configured on server",
        )
    if not verify_password(body.password, settings.admin_password_hash):
        # Kein Passwort, kein Hash im Log -- nur die Tatsache des Fehlversuchs.
        structlog.get_logger().info("admin_login_failed")
        raise HTTPException(status_code=401, detail="Invalid password")

    token = secrets.token_urlsafe(32)
    now = SystemClock().now()
    session = AdminSession(
        token_hash=key_fingerprint(token, length=0),
        created_at=now,
        expires_at=now + timedelta(hours=SESSION_TTL_HOURS),
    )
    session_store.create(session)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_TTL_HOURS * 3600,
        httponly=True,
        samesite="lax",
        secure=settings.session_cookie_secure,
        path="/",
    )
    structlog.get_logger().info("admin_login_succeeded")
    return AuthResponse(authenticated=True)


@router.post("/logout", response_model=AuthResponse)
async def logout(
    request: Request,
    response: Response,
    session_store: SessionStorePort = Depends(get_session_store),  # noqa: B008
) -> AuthResponse:
    """Loescht die Session (falls vorhanden) und raeumt das Cookie ab.

    Idempotent und ohne Auth: ist kein/ein ungueltiges Cookie gesetzt, wird
    nichts geloescht -- die Antwort ist in jedem Fall authenticated=false.
    """
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        session_store.delete(key_fingerprint(token, length=0))
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return AuthResponse(authenticated=False)


@router.get("/me", response_model=AuthResponse)
async def auth_me(
    request: Request,
    api_key: str | None = Depends(_api_key_header),
    settings: Settings = Depends(get_settings),  # noqa: B008
    session_store: SessionStorePort = Depends(get_session_store),  # noqa: B008
) -> AuthResponse:
    """Meldet, ob der Aufrufer als Admin authentifiziert ist.

    Spiegelt exakt require_admin (Session-Cookie ODER gueltiger API-Key) -- das
    Frontend blendet daran seine Admin-Flaechen ein/aus. Eine abgelaufene
    Session wird dabei (in authenticate_admin) verworfen.
    """
    identity = authenticate_admin(request, api_key, settings, session_store)
    return AuthResponse(authenticated=identity is not None)
