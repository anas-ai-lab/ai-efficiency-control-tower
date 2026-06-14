# Phase B — Review

**Datum:** Juni 2026
**Tests bei Gate-Abschluss (Tag 29):** 214 grün, Auth- + Idempotency-Tests inklusive
**Gate-Status:** Bestanden (`/health` live verifiziert, Tag 30)

---

## Gebaute Artefakte

| Datei | Inhalt (1 Satz) |
|---|---|
| `application/ports/{repository,clock,id_generator}.py` | Port-Protokolle für Persistenz, Zeit, ID-Generierung. |
| `adapters/in_memory/{repository,clock,id_generator}.py` | In-Memory-Implementierungen für Tests. |
| `application/service.py` | `TriageService` — orchestriert Domain ausschließlich über Ports (Dependency Inversion). |
| `adapters/api/app.py` | FastAPI-App-Factory, CORS-Allowlist, `debug=False`, globaler Exception-Handler. |
| `adapters/api/dependencies.py` | DI-Provider (`get_triage_service`, `get_settings`, `require_api_key`). |
| `adapters/api/routes/{health,cases,triage}.py` | `/health`, `/cases`, `POST /triage`. |
| `adapters/api/settings.py` | `pydantic-settings` — API-Key, DB-Pfad, `extra="ignore"`. |
| `adapters/api/logging_config.py` + `rate_limit.py` | structlog mit Correlation-ID, slowapi Rate-Limiting. |
| `adapters/sqlite/repository.py` | `SQLiteRepository` — Persistenz via getrennter JSON-Serialisierung (Pydantic vs. Dataclass). |
| `adapters/{in_memory,sqlite}/idempotency_store.py` | Idempotency-Key-Speicher, zwei Adapter hinter einem Port. |
| `docs/adr/ADR-004-hexagonal-architecture.md` | Ports/Adapters-Entscheidung. |
| `docs/adr/ADR-005-idempotency-keys.md` | Idempotency-Design. |
| `docs/adr/ADR-006-api-key-auth.md` | API-Key statt JWT/RBAC. |
| `docs/adr/ADR-007-sqlite-persistence.md` | SQLite statt ORM, Audit-Trail via `submitted_at`. |

---

## Was ich heute anders designen würde

**1. `SQLiteRepository` wird pro Request neu instanziiert.**
`_init_db()` (CREATE TABLE IF NOT EXISTS) läuft dadurch bei jedem Request —
idempotent, aber unnötig. Für Produktionslast wäre ein Lifespan-Singleton
richtig; für privaten Build/Portfolio-Traffic akzeptabel (bereits als
Doku-Punkt in ADR-007 festgehalten).

**2. Idempotency-Store hat kein TTL/Cleanup.**
Wächst bei Dauerbetrieb unbegrenzt. Für ein privates Projekt ohne
Dauerbetrieb folgenlos — relevant nur bei echtem internem Einsatz.

**3. API-Key als einzelner globaler Secret (kein Multi-User).**
Bewusste v1-Entscheidung laut Security-Checkliste, kein Redesign-Punkt.

---

## Offene technische Schulden

| Punkt | Priorität | Wann adressieren |
|---|---|---|
| `SQLiteRepository` pro Request neu instanziiert | Niedrig | Phase F, falls für Demo relevant |
| Idempotency-Store ohne TTL | Niedrig | Nur bei Dauerbetrieb — kein v1-Thema |
| §7 Wochen-Reviews nicht durchgeführt | — | Bewusst übersprungen (8–15h/Woche, Tiefe über Breite). Ab jetzt dokumentiert statt verschwiegen — kein Nachzug geplant. |

---

## Vertrauen ins Phase-B-Design (1–10)

**Hexagonal/DI:** 9 — Service kennt nur Ports, Adapter austauschbar, in Phase C bereits bewiesen (Mock → Resilient → Azure ohne Service-Änderung).
**Persistenz:** 8 — funktioniert, getrennte Serialisierung (Pydantic/Dataclass) ist etwas Boilerplate, aber explizit und getestet.
**Auth/Security:** 8 — API-Key + Exception-Handler + Rate-Limiting decken Phase-B-Checkliste vollständig.
**API-Layer:** 9 — Response-Schemas trennen Domain von API sauber, in Phase C mehrfach wiederverwendet (Sharpen/Report/Propose-Solution folgen demselben Muster).

---

## Offene Punkte für Phase D (Stand Tag 43)

1. **Budget-Sentinel** (erster echter Azure-Call) — Voraussetzung für das
   Master-Plan-Phase-C-Gate, noch ausstehend.
2. **ADR-0013 Teil 2** (strukturiertes Schärfungs-Output, Wiring) —
   additiv vorbereitet, noch nicht verdrahtet.
3. **EU-AI-Act-Re-Check** (§4-Vorab-Check) vor erstem RAG-Code.
