# ADR-0002: Hexagonale Architektur (Ports & Adapters)

**Status:** Accepted
**Datum:** 2026-06-05
**Autor:** Anas

## Kontext

AECT koppelt an mehrere externe Systeme: Azure OpenAI (LLM), ChromaDB (Vektordatenbank),
SQLite (Persistenz), FastAPI (HTTP). Die Kernlogik — ROI-Berechnung, Zonenbestimmung,
AI-vs-Automation-Routing — muss ohne Cloud-Credentials und ohne laufende Container
testbar sein.

Ohne formale Architektur würde Domain-Logik direkt gegen Infrastruktur importieren.
Tests bräuchten Azure-Credentials, laufende Docker-Container oder echte DB-Files.
Das bricht Mock-First-Entwicklung und macht CI fragil.

## Entscheidung

Wir strukturieren AECT nach Hexagonaler Architektur (Ports & Adapters, Alistair Cockburn).

**Schicht-Layout:**
src/aect/
domain/          ← Reine Businesslogik; keine Infrastruktur-Imports
application/     ← Use-Case-Orchestrierung; importiert nur Ports
ports/         ← Port-Interfaces: LLMPort, RepositoryPort, EmbeddingPort
adapters/
api/           ← FastAPI HTTP-Adapter
persistence/   ← SQLite-Adapter
llm/           ← Azure OpenAI-Adapter + deterministischer Mock-Adapter
rag/           ← ChromaDB-Adapter + Hybrid-Retriever
**Kern-Regel:** `domain/` und `application/` importieren niemals aus `adapters/`.
Verstöße sind per mypy / Import-Analyse messbar und werden sofort behoben.

**Port-Beispiele** (in `application/ports/`):
- `LLMPort`: `generate(messages: list[Message]) -> LLMResponse`
- `RepositoryPort`: `save(case: UseCaseIntake) -> None` / `get_by_id(id: str) -> UseCaseIntake | None`
- `EmbeddingPort`: `embed(text: str) -> list[float]`

Adapters implementieren die Ports. Dependency Injection übergibt den konkreten Adapter
dem Application Service — ohne dass Domain oder Application den Adapter kennen.

## Begründung

**Testbarkeit:** Domain-Tests laufen ohne Cloud. Der Mock-LLM-Adapter liefert
deterministische Antworten. Unit-Tests sind in Millisekunden durch.

**Mock-First:** Der Mock-LLM-Adapter kommt in Phase C vor dem echten Azure-Adapter.
Nur mit Hexagonal ist das sauber trennbar — beide Adapter implementieren denselben Port,
der Application Service merkt den Unterschied nicht.

**Provider-Austauschbarkeit:** Azure OpenAI kann durch OpenAI Direct oder ein lokales
Modell ersetzt werden, ohne Domain-Änderung. Nur ein neuer Adapter.

**Portfolio-Wert:** Hexagonale Architektur ist ein etabliertes Enterprise-Muster.
Korrekte Umsetzung inkl. Dependency Inversion wird im Senior-AI-Engineer-Interview
geprüft.

| Alternative | Warum verworfen |
|---|---|
| Layered/MVC | Domain koppelt an Infrastruktur; Tests benötigen echte Cloud-Abhängigkeiten |
| Clean Architecture (Uncle Bob) | Gleiche Prinzipien, mehr Abstraktionsschichten (Entities, Use Cases, Interface Adapters). Für dieses Projekt oversized. |
| Keine formale Architektur | Für ein Portfolio-Projekt unvertretbar; schlechter Interview-Auftritt |

## Konsequenzen

**Positiv:**
- Domain vollständig ohne Cloud testbar (Coverage-Ziel Phase A: ≥ 90 % auf `domain/`)
- LLM-Provider austauschbar ohne Domain-Änderung
- Import-Regel messbar und erzwingbar
- Starkes Portfolio-Statement für Enterprise-Rollen

**Negativ / Trade-offs:**
- Mehr initiales Struktur-Overhead vs. einfaches Skript
- In Phase B gibt es einen einmaligen nicht-additiven Refactor-Schritt
  (🛑 HARD STOP in session-protocol, Agent 1 — wird rechtzeitig angekündigt)

**Neutral:**
- Verstöße gegen die Import-Regel werden in Phase B als Architektur-Test implementiert
- Comprehension Gate nach Application-Service + Ports: „Erkläre Dependency Inversion
  an deinem eigenen Code. Welcher Import würde beweisen, dass du das Prinzip verletzt?"
