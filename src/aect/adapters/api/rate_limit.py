"""Slowapi-Limiter-Instanz fuer AECT.

Schluessel-Strategie: API-Key statt Client-IP.
Gruende:
  - Authentifizierte Endpunkte -- der Key ist die Identitaet, nicht die IP.
  - Hinter Reverse-Proxy (Phase F) ist die Client-IP die des Proxys.
  - Test-Isolation: verschiedene Keys haben getrennte Zaehler.

Standard-Limits (Phase B):
  POST /triage : 30/minute -- Regel-Engine-Aufruf, rechenintensiv
  GET  /cases  : 60/minute -- lesender Zugriff

Security: slowapi setzt X-RateLimit-* Header automatisch.
  RateLimitExceeded -> 429 Too Many Requests (Handler in app.py).
"""

from __future__ import annotations

from fastapi import Request
from slowapi import Limiter


def _api_key_or_anonymous(request: Request) -> str:
    """Rate-Limit-Schluessel: API-Key oder 'anonymous'.

    'anonymous' greift nur bei /health (kein Auth-Header).
    /health hat keinen Limiter-Decorator -- kein Overhead.
    """
    return request.headers.get("X-API-Key", "anonymous")


limiter: Limiter = Limiter(key_func=_api_key_or_anonymous, headers_enabled=True)
