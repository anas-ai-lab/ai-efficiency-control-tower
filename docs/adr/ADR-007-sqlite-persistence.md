# ADR-007: SQLite als Persistenz-Adapter

**Status:** Accepted
**Datum:** Juni 2026

## Kontext

`InMemoryRepository` (RepositoryPort-Implementierung seit Phase-B-Beginn)
haelt `SubmittedCase`-Objekte in einem prozessgebundenen `dict`. Nach jedem
Server-Neustart (Dev-Reload, Deploy, Crash) sind alle Cases verloren.
Master-Plan v3.1 Phase B fordert einen persistenten Adapter;
aect-security-checklist v2.1 fordert einen Audit-Trail (append-only,
wer/wann eingereicht).

## Entscheidung

Wir verwenden SQLite als Persistenz-Backend via `SQLiteRepository`, das
`RepositoryPort` strukturell implementiert (kein explizites Erben, mypy
prueft Protocol-Konformitaet). Aktivierung ueber `AECT_DB_PATH`
(pydantic-settings): leer -> `InMemoryRepository` (Dev/Test, Status quo),
gesetzt -> `SQLiteRepository` gegen die angegebene Datei. `SubmittedCase`
wird in zwei Spalten serialisiert (`use_case_json` via Pydantic
`.model_dump_json()`, `result_json` via `dataclasses.asdict()` +
`_DecimalEncoder` fuer `Decimal`-Felder). Jede DB-Operation oeffnet eine
eigene `sqlite3.connect()`-Verbindung (Context Manager) -- kein geteilter
Connection-State. `_init_db()` (CREATE TABLE IF NOT EXISTS) laeuft
idempotent pro Instanziierung.

## Begruendung

| Alternative | Warum verworfen |
|---|---|
| PostgreSQL | Erfordert einen laufenden DB-Server (Docker-Container oder Managed Service) -- widerspricht Local-First-Prinzip und erzeugt laufende Infrastruktur fuer ein Single-User-Portfolio-System. |
| Weiter InMemoryRepository | Kein State-Erhalt nach Neustart -- ungeeignet fuer Demo (Phase F) und fuer Idempotency-Keys, die ueber Request-Grenzen hinweg gueltig bleiben muessen (ADR-005). |
| ORM (SQLAlchemy) | Fuer zwei Tabellen (`submitted_cases`, `idempotency_keys`) mit simplem Key-Value/Row-Zugriff unnoetiger Abstraktions-Overhead. Rohes `sqlite3` ist hier lesbarer und ohne zusaetzliche Dependency. |

SQLite ist dateibasiert, erfordert keinen Server-Prozess, ist in Pythons
Standardbibliothek enthalten und passt zum Budget- und
Local-First-Prinzip des Projekts.

## Konsequenzen

**Positiv:**
- Keine zusaetzliche Infrastruktur, kein laufender Server-Prozess, keine
  Kosten.
- Datei-basiert -- Backup ist ein `cp`, Demo-Reset ist `rm`.
- Strukturelle Subtypisierung: `TriageService` kennt weiterhin nur
  `RepositoryPort`, Wechsel In-Memory <-> SQLite ist eine
  Konfigurationsentscheidung (`AECT_DB_PATH`), kein Code-Wechsel.

**Negativ / Trade-offs:**
- Keine Migrations-Tooling (Alembic o.ae.) -- Schema-Aenderungen an
  `submitted_cases`/`idempotency_keys` muessen manuell behandelt werden
  (`CREATE TABLE IF NOT EXISTS` deckt nur Neuanlage ab, keine ALTER TABLE).
- Pro-Request-Verbindung + `_init_db()` pro Instanziierung ist fuer
  Portfolio-Traffic akzeptabel, aber nicht fuer hohe Last optimiert
  (dokumentierte Limitation, siehe `SQLiteRepository`-Docstring:
  Lifespan-Singleton als Alternative).
- SQLite-Concurrency-Modell (Single-Writer) limitiert parallele
  Schreibzugriffe -- fuer Single-User-System irrelevant.

**Neutral / Folgeentscheidungen:**
- `SQLiteIdempotencyStore` folgt demselben Muster (eigene Tabelle, gleiche
  DB-Datei, separate Connections) -- konsistente Architektur (ADR-005).
- Bei einem realen Produktiv-Einsatz wuerde Persistenz ueber die vorhandene
  Firmen-Infrastruktur laufen (aect-security-checklist v2.1, "Was echter
  Produktiv-Einsatz braeuchte") -- SQLite ist explizit eine
  Portfolio-Entscheidung, keine Produktionsempfehlung.
