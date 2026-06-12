# ADR-005: Idempotency-Keys fuer POST /triage

## Status
Accepted

## Kontext
POST /triage erzeugt bei jedem Aufruf einen neuen Case (UUID, Zeitstempel,
Persistenz). Bei Netzwerk-Timeouts oder Client-Retries kann derselbe
Use Case mehrfach eingereicht werden -- jeder Retry erzeugt einen
zusaetzlichen, identischen Case (Doppelverarbeitung).
aect-security-checklist v2.1 (Phase B) fordert Idempotency-Keys als
Schutzmassnahme.

## Entscheidung
Optionaler HTTP-Header `Idempotency-Key` (max. 200 Zeichen). Bildet ab:
Key -> Case-ID, via IdempotencyStorePort (InMemory- oder SQLite-Backend,
analog RepositoryPort). Bei Replay mit bekanntem Key: Status 200,
Header `Idempotent-Replay: true`, urspruengliches Ergebnis aus dem
Repository nachgeladen (kein erneuter Domain-Run). Ohne Header:
unveraendertes Verhalten (Status 201).

Die Pruefung liegt in der Adapter-Schicht (adapters/api/routes/triage.py),
nicht im TriageService -- Idempotency ist ein HTTP-/Transport-Anliegen,
keine Domain- oder Anwendungslogik. Der Service bleibt unveraendert.

## Bewusste Grenze
Der Key wird nicht gegen den Request-Body validiert (kein Payload-Hash).
Ein wiederverwendeter Key mit geaendertem Body liefert das alte Ergebnis,
nicht 409 Conflict. Fuer ein privates Single-User-System ausreichend --
in einem Multi-Tenant-Produktivsystem waere Payload-Hashing (z. B.
SHA-256 ueber den normalisierten Body, Vergleich bei Replay, 409 bei
Mismatch) der naechste Schritt.

## Konsequenzen
- Plus: Schutz vor Doppelverarbeitung bei Client-Retries, ohne
  Domain/Service anzufassen.
- Plus: Gleiches Muster wie RepositoryPort -- konsistente Architektur.
- Minus: Idempotency-Tabelle waechst unbegrenzt (kein TTL/Cleanup in v1).
  Fuer ein Portfolio-System ohne Produktionslast akzeptabel; dokumentierte
  Limitation fuer einen echten Produktiv-Einsatz.
- Minus: kein Schutz vor "gleicher Use Case, anderer Key" -- das ist
  fachlich auch nicht das Ziel von Idempotency-Keys.
