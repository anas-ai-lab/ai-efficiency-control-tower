# ADR-0037: async Repository via asyncio.to_thread

**Status:** Accepted
**Datum:** 2026-06-28
**Autor:** Anas

## Kontext

`SQLiteRepository.save/get/list_all` sind synchron und fuehren blockierende
Datei-I/O aus. Sie werden u. a. aus den async-Service-Methoden
(`sharpen_case`, `propose_solution`, `generate_compliance_hints`) aufgerufen,
die zwischen `get()` und `save()` ein `await self._llm.complete()` haben. Der
synchrone DB-Zugriff laeuft damit auf dem Event-Loop und blockiert unter
nebenlaeufiger Last alle anderen Requests (AUDIT-001).

## Entscheidung

Wir ergaenzen je eine async-Variante (`save_async`, `get_async`,
`list_all_async`) im `RepositoryPort` und in beiden Implementierungen. In
`SQLiteRepository` lagern sie die blockierende Arbeit via `asyncio.to_thread`
in einen Worker-Thread aus; die sync-Methoden bleiben die Single Source of
Truth und werden von `to_thread` nur aufgerufen. `InMemoryRepository`
implementiert die async-Varianten als direkte Delegation (dict-Zugriffe
blockieren nicht). Die async-Service-Methoden rufen ab jetzt die `*_async`-
Wrapper auf.

Die rein synchronen Service-Methoden (`submit_use_case`, `get_case`,
`list_cases`, `generate_report`) bleiben synchron -- AUDIT-001 nennt
ausdruecklich nur die "aus async-Service-Methoden" aufgerufenen Pfade.

## Begruendung

| Alternative | Warum verworfen |
|---|---|
| `aiosqlite` | Neue Laufzeit-Dependency + Umschreiben jeder Query auf await; groesserer Footprint fuer ein Portfolio-SQLite-Backend. |
| Sync lassen, Blocking akzeptieren | Genau der von AUDIT-001 gemeldete Defekt; unter Last blockiert ein DB-Zugriff den gesamten Loop. |
| `ThreadPoolExecutor` manuell | `asyncio.to_thread` ist exakt der Standard-Wrapper darum (Py 3.9+); manuelles Executor-Management waere mehr Code ohne Mehrwert. |

`asyncio.to_thread` ist idiomatisches Python 3.9+, bringt **null neue
Dependencies**, hat minimale Change-Surface (die sync-Logik bleibt unveraendert)
und passt zum async-Modell von FastAPI.

## Konsequenzen

**Positiv:**
- Async-Service-Methoden blockieren den Event-Loop nicht mehr bei DB-I/O.
- Keine neue Dependency, sync-Pfad und bestehende Repository-Tests unveraendert.

**Negativ / Trade-offs:**
- `to_thread` nutzt den Default-ThreadPool; bei sehr hoher Parallelitaet ist
  dessen Groesse die Grenze. Fuer Portfolio-Last unkritisch.
- Doppelte Methoden-Oberflaeche (sync + async) im Port. Bewusst akzeptiert --
  beide Aufrufstile bleiben gueltig.

**Neutral / Folgeentscheidungen:**
- Die verbleibenden sync-Service-Methoden werden aus async-Routes aufgerufen
  und blockieren dort theoretisch ebenfalls. Nicht Teil von AUDIT-001;
  dokumentiert als separater Folgepunkt, falls Last es erfordert.
- `delete_async` kommt mit dem DSGVO-Loeschpfad hinzu (ADR-0038).
