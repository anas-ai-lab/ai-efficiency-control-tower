# ADR-0040: SQLite + lokales ChromaDB -- bewusste Beibehaltung und explizite Decke

**Status:** Accepted
**Datum:** 2026-07-02
**Autor:** Anas

## Kontext

AECT ist ein privates Portfolio-Projekt (Projektziel: Zeigbarkeit einer
AI-Engineer-/Solution-Architect-Rolle im DACH-Interview, kein SaaS, kein
Verkauf -- Projekt-Charta). Zur Laufzeit existiert ein Nutzer: der
Entwickler selbst im Demo- bzw. Interview-Kontext. Persistenz laeuft ueber
`SQLiteRepository` (ADR-007) und `SQLiteIdempotencyStore` (ADR-005),
Vektor-Suche ueber einen lokalen ChromaDB-Container (ADR-0018).

Phase G (Post-v1-Audit) hat zwei Concurrency-Bugs in dieser Persistenz-
Schicht gefunden und behoben: F-010 (Idempotency-Race, `get`->`set` nicht
atomar, erzeugte Duplikat-Cases bei parallelen Requests mit demselben
Idempotency-Key, Fix `1acd972`) und F-011 (Lost-Update-Race, paralleles
`/sharpen` + `/propose-solution` ueberschrieb per `INSERT OR REPLACE` das
Feld der jeweils anderen Operation, Fix `530f62f`). Beide Fixes sind durch
gezielte Concurrency-Tests abgesichert:
`tests/application/test_service_concurrency.py::test_parallel_sharpen_and_propose_keep_both_narratives`
und `tests/adapters/sqlite/test_idempotency_store.py::test_claim_is_atomic_under_parallel_access`
sowie `tests/adapters/api/test_idempotency.py::test_concurrent_requests_with_same_key_create_only_one_case`.
Diese Tests verifizieren *korrektes Verhalten bei parallelen Operationen
auf demselben Case innerhalb eines Nutzers* (z. B. zwei Browser-Tabs, ein
doppelt gesendeter Request) -- nicht Verhalten unter vielen gleichzeitigen
Nutzern oder hoher Last. Diese ADR haelt fest, warum das fuer den
Projektkontext ausreicht und wo die Grenze verlaeuft, damit diese
Unterscheidung nicht stillschweigend verloren geht.

## Entscheidung

Wir behalten SQLite (dateibasiert, `AECT_DB_PATH`) und lokales ChromaDB
(Docker-Container, 127.0.0.1-only, ADR-0018) als alleinige Persistenz- und
Retrieval-Schicht bei. Kein Wechsel auf einen Server-basierten
DB-/Vektor-Store fuer v1 oder den absehbaren Post-v1-Horizont.

## Begruendung

| Alternative | Warum verworfen |
|---|---|
| PostgreSQL + pgvector | Server-Prozess, Connection-Pooling, Migrations-Tooling und Vektor-Index-Tuning fuer einen Lastfall (ein Nutzer, < 10k Cases, vgl. ADR-0039) loesen ein Problem, das nicht existiert. Over-Engineering: die zusaetzliche operative Flaeche (Docker-Compose-Service mehr, Backup-Strategie, Schema-Migrationen) kauft Skalierbarkeit, die im Interview-/Demo-Kontext nie ausgenutzt wird -- widerspricht Local-First und Budget-Cap (50 EUR/Monat). |
| Managed Cloud-DB (z. B. Supabase, Neon) | Laufende Kosten und ein externer Kontoabhaengigkeit fuer ein Projekt, das explizit keine dauerhaft laufenden Cloud-Ressourcen haben soll (Hard Stop, Projekt-Constitution). |
| Docker-Compose-Cluster (mehrere App-/DB-Instanzen) | Erzeugt genau die Betriebs-Komplexitaet, die in einem Interview nicht in einem Satz erklaerbar ist -- widerspricht dem Erklaerbarkeits-Ziel dieses Projekts. |

Fuer den tatsaechlichen Kontext -- ein Nutzer, Zeigbarkeit und
Erklaerbarkeit in einem Interview, kein Produktions-Traffic -- bringt
SQLite + lokales Chroma drei konkrete Vorteile: null Infrastrukturkosten
(dateibasiert, kein Server-Prozess ausser dem einen Chroma-Container),
vollstaendige Erklaerbarkeit in einem Satz ("eine Datei, ein Repository-
Adapter, strukturell typisiert gegen `RepositoryPort`"), und keine
Docker-Compose-Orchestrierung ueber den einen bestehenden Chroma-Container
hinaus.

## Konsequenzen

**Positiv:**
- Keine laufenden Infrastrukturkosten, Budget-Cap bleibt automatisch
  eingehalten.
- Backup/Reset sind triviale Dateioperationen (`cp` / `rm`).
- Architektur bleibt in einem Satz erklaerbar -- das ist der eigentliche
  Zweck eines Portfolio-Projekts, nicht Produktionsreife.

**Negativ / Trade-offs (die explizite Decke):**
- **Kein produktionsreifes Concurrency-Modell fuer viele Nutzer.** F-010
  und F-011 beweisen, dass SQLite-Concurrency-Bugs real und findbar sind --
  die Fixes (Claim-then-fill fuer Idempotency, per-Feld-`UPDATE` statt
  `INSERT OR REPLACE`) machen das System korrekt fuer *parallele Requests
  eines Nutzers auf denselben Case*. Verifiziert ist das durch die oben
  genannten drei Tests. Verifiziert ist NICHT: Verhalten unter vielen
  gleichzeitigen Nutzern, unter Last, oder bei Schreibkonflikten ueber
  verschiedene Nutzer-Sessions hinweg. SQLite serialisiert Schreibzugriffe
  prozessweit (Single-Writer) -- bei mehr als einer Handvoll gleichzeitiger
  Schreiber wuerde das zu Wartezeiten oder `database is locked` fuehren,
  nicht getestet und nicht abgefangen.
- **Kein horizontaler Scaling-Pfad.** Die SQLite-Datei ist an einen
  Host-Pfad gebunden; mehrere App-Instanzen koennen nicht gegen dieselbe
  Datei parallel schreiben (kein Netzwerk-Protokoll, kein Locking ueber
  Hosts hinweg). Ein Scale-out (mehrere uvicorn-Worker/Instanzen hinter
  einem Load-Balancer) ist mit dieser Persistenz-Schicht nicht moeglich,
  ohne sie zu ersetzen.
- **ChromaDB lokal = kein Multi-Instance-Deploy ohne Umbau.** Der Chroma-
  Container laeuft als Einzelinstanz mit host-gemountetem Persist-Dir
  (ADR-0018); mehrere App-Instanzen gegen denselben Container waeren
  moeglich, aber mehrere Chroma-Instanzen mit synchronisiertem Index nicht,
  ohne auf einen verteilten Betrieb (Chroma Cloud/Server-Cluster oder einen
  anderen Vektor-Store) umzusteigen.
- Diese drei Punkte ueberschneiden sich mit `known_limitations.md` #11
  ("Kein Produktivbetrieb"), praezisieren dort aber bewusst vage
  gehaltene Aussagen ("kein Clustering, kein HA") auf konkrete,
  testbare Grenzen.

**Neutral / Folgeentscheidungen:**
- ADR-007 (SQLite-Begruendung) und ADR-0018 (ChromaDB-Container) bleiben
  in Kraft und werden durch diese ADR nicht ersetzt, sondern um die
  Skalierungs-Perspektive ergaenzt.

## Migrationstrigger

Ein Wechsel auf einen Server-basierten Stack (z. B. PostgreSQL statt
SQLite, Chroma-Server-Cluster oder ein Managed-Vektor-Store statt lokalem
Container) ist faellig, sobald **eine** der folgenden konkreten
Bedingungen eintritt -- nicht "irgendwann skalieren":

1. **Mehr als ein gleichzeitiger Reviewer/Nutzer** greift regelmaessig
   (nicht einmalig zu Demo-Zwecken) auf dieselbe laufende Instanz zu.
2. **Deployment ueber eine einzelne Host-Instanz hinaus** wird noetig
   (z. B. mehrere uvicorn-Worker-Prozesse gegen dieselbe DB-Datei, oder
   ein Load-Balancer vor mehreren App-Instanzen).
3. Die Fallzahl ueberschreitet die in ADR-0039 dokumentierte
   Linear-Scan-Grenze (< 10k Cases) UND ChromaDB-Retrieval-Latenz wird
   spuerbar (misst sich, wird aber nicht vorab spekuliert).

Trifft eine dieser Bedingungen ein, ist das der Ausloeser fuer eine neue
ADR (Migrationsentscheidung SQLite -> PostgreSQL, lokales Chroma ->
Server-/Cloud-Chroma), nicht fuer eine stillschweigende Erweiterung des
bestehenden Stacks.
