# ADR-006: API-Key-Authentifizierung fuer geschuetzte Endpoints

**Status:** Accepted
**Datum:** Juni 2026

## Kontext

AECT exponiert HTTP-Endpoints (GET /cases, POST /triage), die lesend bzw.
schreibend auf Use-Case-Daten zugreifen. Ohne Authentifizierung kann jeder
mit Netzwerkzugriff Cases einsehen oder einreichen. aect-security-checklist
v2.1 (Phase B) fordert Auth fuer alle Endpoints ausser /health.

## Entscheidung

Wir verwenden API-Key-Authentifizierung via Custom-Header `X-API-Key`. Der
Key wird serverseitig ueber `AECT_API_KEY` (pydantic-settings, `.env`)
konfiguriert und in `require_api_key()` (FastAPI-Dependency) gegen den
Request-Header geprueft. `APIKeyHeader(auto_error=False)` liefert bei
fehlendem Header `None` statt automatischem 403 -- die Dependency gibt
einheitlich 401 zurueck (kein Mechanismus-Leak ueber "Header fehlt" vs.
"Header falsch"). Fehlt die Server-Konfiguration (`AECT_API_KEY` leer),
gibt die Dependency 500 zurueck. `/health` ist explizit von
`require_api_key` ausgenommen.

## Begruendung

| Alternative | Warum verworfen |
|---|---|
| JWT + RBAC | Mehraufwand (Token-Issuance, Refresh, Rollenmodell) ohne Mehrwert fuer Single-User-System. v1-Projekt-Scope: JWT/RBAC ist nicht v1-Kern -- nur falls ein Multi-User-Frontend es verlangt, dann als Design/ADR. |
| OAuth2 / Session-Cookies | Setzt Login-Flow und User-Verwaltung voraus -- existiert nicht und ist fuer ein privates Portfolio-Backend nicht gerechtfertigt. |
| Kein Auth (nur Netzwerk-Isolation) | Verstoesst gegen aect-security-checklist v2.1 Phase B; bei spaeterer oeffentlicher Demo-Instanz sofort offen. |

API-Key ist der einfachste Mechanismus, der das Bedrohungsmodell (ungewollter
Zugriff durch Dritte bei einer erreichbaren Instanz) abdeckt, ohne
Infrastruktur aufzubauen, die fuer ein Single-User-System ungenutzt bliebe.

## Konsequenzen

**Positiv:**
- Ein Header, ein Konfigurationswert -- minimaler Implementierungsaufwand.
- `auto_error=False` + einheitliches 401 verhindert Information-Disclosure
  ueber den Auth-Mechanismus (OWASP-konform).
- `get_settings()` ohne `lru_cache` erlaubt Tests, den Key per
  `dependency_overrides` zu setzen, ohne Cache-Invalidierung.

**Negativ / Trade-offs:**
- Ein einziger Key fuer das gesamte System -- keine Differenzierung
  zwischen Nutzern/Rollen, kein Auth-seitiges Audit "wer hat das gemacht"
  (der Audit-Trail via `submitted_at` bleibt davon unabhaengig).
- Kein Key-Rotation-Mechanismus -- Rotation bedeutet manuelles Aendern von
  `AECT_API_KEY` + Redeploy.
- Bei Kompromittierung des Keys ist das gesamte System offen, bis der Key
  rotiert wird.

**Neutral / Folgeentscheidungen:**
- Falls Phase F ein Multi-User-Frontend erfordert: JWT/RBAC wird dann als
  eigenes ADR evaluiert (Projekt-Scope-Tabelle: Design/ADR, kein
  Vollausbau).
- Rate Limiting (30/min POST /triage, 60/min GET /cases via `slowapi`) ist
  die zweite Verteidigungslinie gegen Missbrauch eines kompromittierten
  Keys.
