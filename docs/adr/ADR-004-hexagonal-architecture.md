# ADR-004 -- Hexagonal Architecture (Ports & Adapters)

**Status:** Accepted
**Datum:** Juni 2026
**Phasen-Kontext:** Phase B Beginn (Tag 22)

## Kontext

AECT benoetigt klare Trennung zwischen Businesslogik (Domain), Anwendungsorchestrierung
(Application Service) und Infrastruktur (Datenbank, HTTP, LLM-Clients). Ohne explizite
Schichttrennung waechst die Kopplung: Tests werden fragil, Adapter-Austausch teuer,
Security-Kontrolle (PII-Redaction, Logging-Allowlists) schwer durchzusetzen.

## Entscheidung

Hexagonal Architecture (Ports & Adapters) als Strukturprinzip ab Phase B:

- **Domain** (`src/aect/domain/`): reine Businesslogik, keine I/O. Bereits in Phase A
  vollstaendig isoliert implementiert.
- **Application** (`src/aect/application/`): orchestriert Domain-Calls, definiert Port-
  Protokolle. Darf nur aus `aect.domain` importieren.
- **Adapters** (`src/aect/adapters/`): implementieren Ports. Darf aus
  `aect.application.ports` und `aect.domain` importieren. Nie umgekehrt.

Port-Implementierung via `typing.Protocol` (strukturelles Subtyping): Adapter erben NICHT
von Ports. Das haelt Adapter unabhaengig von der Application-Schicht und erlaubt echtes
strukturelles Dependency Inversion ohne Kreisabhaengigkeiten.

## Begruendung

Alternativen:
- **Direkte Implementierung** (Service importiert direkt DB/LLM): schneller initial,
  aber Tests brauchen echte Infrastruktur; Security-Kontrolle schwerer isolierbar.
- **ABC statt Protocol**: erfordert explizites Erben -- Adapter muessten die Application-
  Schicht importieren, was die Trennlinie aufweicht.

Hexagonal gewinnt weil:
1. Tests mit FakeClock und FakeIdGenerator sind deterministisch ohne Mocking-Framework.
2. Phase C (LLM-Adapter) und Phase D (RAG-Adapter) werden eingehaengt ohne Domain-Umbau.
3. PII-Redaction, Logging-Allowlists, Cost-Tracking liegen in Adaptern -- nie in Domain.

## Konsequenzen

- Import-Invariante dauerhaft pruefen (in CI und manuell):
  `grep -rn "from aect.adapters|from aect.application" src/aect/domain/` muss leer bleiben.
- In-Memory-Adapter ist der einzige Adapter in Phase B Tag 22. SQLiteRepository folgt.
- Jeder neue Infrastruktur-Concern (LLM, RAG, HTTP, Embedding) bekommt einen eigenen
  Ordner unter `src/aect/adapters/`.
- `typing.Protocol` ohne `@runtime_checkable`: kein `isinstance()`-Check gegen Ports --
  nur statische mypy-Pruefung. Bewusste Entscheidung (kein Runtime-Overhead).
