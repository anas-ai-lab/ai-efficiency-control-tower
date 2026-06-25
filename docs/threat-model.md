# AECT — Threat Model (STRIDE)

**Methodik:** STRIDE
**Stand:** Juni 2026
**System:** AI Efficiency Control Tower v0.1.0
**Deployment-Scope:** Localhost, Einzelbenutzer, privates Portfolio-Build.

---

## 1. System-Uberblick

### Komponenten und Trust-Stufen

| Komponente | Typ | Trust-Stufe |
|---|---|---|
| API-Consumer | Extern | Niedrig -- nur API-Key-Auth |
| FastAPI (Port 8000) | Intern | Hoch |
| SQLite (aect.db) | Lokal Filesystem | Hoch |
| Azure OpenAI (gpt-4.1-mini) | Extern (Internet) | Mittel -- Microsoft DPA, EU-Data-Zone |
| ChromaDB (Docker, Port 8001) | Lokal Docker | Hoch -- kein oeffentlicher Bind |
| SentenceTransformer (all-MiniLM-L6-v2) | In-Process | Hoch |
| BM25-Index | In-Memory | Hoch |
| Knowledge Base (knowledge_base/) | Lokal Filesystem | Hoch -- nur kuratierte Quellen |

### Datenfluesse und Trust Boundaries
Client (X-API-Key) --- HTTP ---> FastAPI (Port 8000)

|

+------------+---------------+

|            |               |

v            v               v

SQLite    Azure OpenAI     ChromaDB

(Persist)  (gpt-4.1-mini)  (Port 8001)

^

SentenceTransformer

+ BM25 (In-Process)

- **TB-1:** Client <-> FastAPI -- Netzwerk, HTTP (localhost) / HTTPS (Server-Deploy)
- **TB-2:** FastAPI <-> Azure OpenAI -- Internet, HTTPS, TLS
- **TB-3:** FastAPI <-> ChromaDB -- Docker-internes Netz, localhost-only
- **TB-4:** FastAPI <-> SQLite / KB-Markdown -- lokales Filesystem, OS-Rechte

---

## 2. STRIDE-Analyse

### S -- Spoofing

| ID | Bedrohung | Komponente | Wahrscheinlichkeit | Mitigation | Status |
|---|---|---|---|---|---|
| S-01 | Brute-Force / Leak des API-Keys | TB-1 | Mittel | Rate Limiting (slowapi, 30/min POST /triage); starke Key-Entropie deployment-seitig | OK aktiv |
| S-02 | MITM auf Azure-OpenAI-Verbindung | TB-2 | Niedrig | TLS, openai-Library erzwingt HTTPS, Microsoft CA | OK |
| S-03 | ChromaDB-Port von aussen erreichbar | TB-3 | Niedrig (localhost) | Kein oeffentlicher Bind; Docker-internes Netz | WARN Hardening-Punkt bei Server-Deploy |

### T -- Tampering

| ID | Bedrohung | Komponente | Wahrscheinlichkeit | Mitigation | Status |
|---|---|---|---|---|---|
| T-01 | Prompt Injection via Use-Case-Eingabe | FastAPI -> Azure | Mittel | `detect_injection_patterns()`, User-Input in abgegrenztem Block, Flag-not-block, LLM-Red-Team-Tests | OK LLM01 |
| T-02 | Direkte SQLite-Datei-Manipulation | TB-4 (Filesystem) | Niedrig | OS-Rechte; kein oeffentlicher Zugriff | INFO Dokumentierte Limitation, lokales Build |
| T-03 | ChromaDB-Embedding-Manipulation | TB-3 (Docker Volume) | Niedrig | chmod 700 auf Persist-Dir; Non-root im Container | OK Non-root-User aect:aect (uid/gid 1000) im Dockerfile implementiert (Tag 75) |
| T-04 | Knowledge-Base-Vergiftung | TB-4 (Filesystem) | Niedrig | Nur kuratierte Quellen, kein Upload-Endpoint | OK |
| T-05 | LLM-Output-Injection in Downstream | FastAPI (Pydantic) | Mittel | Pydantic-Schema-Validation auf LLM-Output als untrusted; kein direktes SQL/Exec | OK LLM05 |

### R -- Repudiation

| ID | Bedrohung | Komponente | Wahrscheinlichkeit | Mitigation | Status |
|---|---|---|---|---|---|
| R-01 | Kein Nachweis wer welchen Case eingereicht hat | SQLite / Logging | Niedrig (Einzelbenutzer) | Correlation-ID (request_id) in jedem Log-Eintrag; append-only Case-Persistenz in SQLite | OK Single-Tenant; WARN kein User-Audit bei Mehrbenutzerbetrieb |
| R-02 | LLM-Call-Zeitpunkt nicht belegbar | Cost-Logger | Niedrig | Cost-Logger loggt Timestamp, Modell, Token-Count | OK |

### I -- Information Disclosure

| ID | Bedrohung | Komponente | Wahrscheinlichkeit | Mitigation | Status |
|---|---|---|---|---|---|
| I-01 | System-Prompt-Leakage via LLM-Antwort | Azure -> Client | Niedrig | Kein Secret/Auth im System-Prompt (LLM07); Pydantic-Output-Schema als Filter | OK |
| I-02 | Stack-Trace in Error-Response | FastAPI -> Client | Niedrig | Globaler Exception-Handler: `{"detail": "Internal error", "request_id": "..."}` | OK |
| I-03 | PII in structlog-Logs | FastAPI -> Logfile | Niedrig | Allowlist: request_id, route, status, latency, token_count -- kein Body, kein Prompt | OK |
| I-04 | Use-Case-Inhalt ausserhalb EU-Data-Zone | TB-2 | Niedrig (by config) | Deployment-Pflicht: swedencentral/westeurope; ADR-0003, ADR-0010 | OK deployment-seitig |
| I-05 | ChromaDB-Embeddings extern lesbar | TB-3 (Port 8001) | Niedrig (localhost) | Kein oeffentlicher Bind; bei Server-Deploy: Netzwerk-Isolation erforderlich | WARN Server-Deploy-Punkt |

### D -- Denial of Service

| ID | Bedrohung | Komponente | Wahrscheinlichkeit | Mitigation | Status |
|---|---|---|---|---|---|
| D-01 | Token-Flooding via lange Freitextfelder | FastAPI -> Azure | Mittel | `max_length` auf allen Pydantic-Freitextfeldern; Max-Tokens-Cap im Azure-Adapter | OK LLM10 |
| D-02 | Rate-Limit-Erschoepfung (LLM-Endpoints) | FastAPI (slowapi) | Mittel | 10/min /sharpen, /propose-solution, /compliance-hints; 30/min /triage; 60/min GET /cases | OK |
| D-03 | Denial-of-Wallet (unkontrollierte Azure-Kosten) | Azure OpenAI | Mittel | Azure Budget Alerts (10/20/28 EUR); Cost-Logger; Rate Limiting | OK ADR-0034 |
| D-04 | ChromaDB-Abfrage-Flooding | ChromaDB | Niedrig | Upstream Rate-Limiting auf /compliance-hints (10/min) schuetzt indirekt | OK indirekt |

### E -- Elevation of Privilege

| ID | Bedrohung | Komponente | Wahrscheinlichkeit | Mitigation | Status |
|---|---|---|---|---|---|
| E-01 | Prompt Injection -> unerlaubte Aktionen | LLM-Schicht | Niedrig | Kein Agentic-Muster; `lookup_stack_options` ist read-only; kein Dateisystem-/Netzwerk-Zugriff durch LLM | OK LLM06, limited by design |
| E-02 | LLM-Output direkt in SQL-Statement | SQLite | Niedrig | LLM-Output landet nie in SQL; Pydantic-Mapping als Pflichtschritt dazwischen | OK LLM05 |
| E-03 | Flaches Auth-Modell (kein RBAC) | FastAPI (API-Key) | Niedrig (Single-Tenant) | Einzelbenutzer-Deploy; ein API-Key; dokumentierte Limitation fuer Mehrbenutzerbetrieb | INFO ADR-006 |

---

## 3. Offene Punkte (nicht v1-Blocker fuer privates Build)

| ID | Punkt | Wird relevant bei |
|---|---|---|
| O-01 | ChromaDB ohne Auth (Port 8001) | Server-Deploy / Mehrbenutzerbetrieb |
| O-02 | Non-root-User im Dockerfile | Erledigt Tag 75 -- USER aect:aect (uid/gid 1000) implementiert |
| O-03 | Flaches API-Key-Auth (kein RBAC) | Mehrbenutzerbetrieb |
| O-04 | SHA-Pinning der GitHub-Actions | Erledigt Tag 75 -- alle Actions gepinnt |
| O-05 | Branch Protection auf main (GitHub Free, privat) | Dokumentierte Limitation -- kein Handlungspunkt |

---

## 4. Gesamtbewertung

Fuer Localhost-Deploy, Einzelbenutzer, privates Build: Risikoprofil **akzeptabel**.

Kritische OWASP-LLM-Bedrohungen (LLM01 Prompt Injection, LLM05 Improper Output Handling,
LLM07 System Prompt Leakage, LLM10 Unbounded Consumption) sind durch bestehende Massnahmen
strukturell adressiert -- nicht nur durch Prompt-Disziplin, sondern durch Architektur:
Pydantic-Validation als Pflichtschritt, Delimiter im Prompt, Rate Limiting, Max-Tokens-Cap.

Drei Punkte werden handlungsrelevant sobald das System auf einem Server laeuft oder
mehrere Nutzer hat: O-01, O-03, S-03. Dokumentiert in `docs/limitations.md`.

**Referenzen:** OWASP LLM Top 10 (2025) - STRIDE-Methodik - aect-security-checklist v2.1
- ADR-006 (Auth) - ADR-0003 (LLM-Provider) - ADR-0010 (Azure-Adapter)
- ADR-0020 (EU AI Act) - ADR-0034 (Semantic Caching / Denial-of-Wallet)
