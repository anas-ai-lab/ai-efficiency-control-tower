# Phase F — Kickoff

**Datum:** Juni 2026
**Basis:** Master-Plan v3.1 Phase F. Claude Code Setup: `claude-code-setup.md`
wird in Block 2 reaktiviert.
**Gate-Bedingung (session-protocol v3 SS2):** System aus frischem Clone in ~10 Min
startbar; Frontend-Code verstanden (Comprehension Gate verbindlich, nicht optional);
Demo zeigt Problem -> Schaerfung -> Loesung -> Verdict -> Quellen.

---

## Arbeitsreihenfolge

### Block 1 — Dokumentation vor dem Frontend

**Tag 69: ADRs fuer downgraded Topics**
Drei Themen, die bewusst nicht gebaut wurden, bekommen je eine ADR mit
"verstanden, hier ist das Design, hier warum jetzt nicht gebaut":
- OpenTelemetry/Jaeger (structlog bleibt, kein Tracing-Deploy)
- Semantic Caching + Model Routing (Cost-Logging bleibt, kein Routing-Layer)
- Azure Container Apps Deploy (ADR/Design only, kein produktiver Deploy)

**Tag 70: `docs/threat-model.md` (STRIDE)**
STRIDE-Analyse auf die AECT-Architektur: 6 Angriffsvektoren, je Mitigations-
massnahme und Teststatus. Quelle: aect-security-checklist SS F.

**Tag 71: README Gold-Standard + ADR-Review**
- README: frischer-Clone-Quickstart, Architecture-Overview, CI-Badge,
  Demo-Link (Platzhalter bis Frontend fertig).
- ADR-Review: beide Serien (`000X` / `ADR-00X`), stale Docstrings markieren,
  Nummerierungsluecke ADR-004 auflosen, `resilient.py`-Docstring-Fix (offen
  seit Phase C).

### Block 2 — Frontend

**Tag 72-74: Frontend bauen (Claude Code)**
- claude-code-setup.md reaktivieren, Skills installieren
  (taste-skill + vercel/skills, CLAUDE.md anlegen).
- Frontend: Formular-Eingabe -> API -> gerenderter Report.
  Anforderungen: Original + geschaerfte Version nebeneinander, Verdict oben,
  Quellen aufklappbar.
- Frischer-Clone-Test nach Fertigstellung.

**Tag 74 (Ende Block 2): Frontend Comprehension Gate**
Verbindlich laut session-protocol v3 SS3: Anas erklaert in eigenen Worten
wie Eingabe-Formular, Report-Anzeige und Fehlerbehandlung zusammenhaengen.
Kein Bestehen = Frontend zaehlt nicht als Portfolio-Asset.

### Block 3 — Hardening + Abschluss

**Tag 75: Security-Hardening-Pass**
- SHA-Pinning aller GitHub-Actions (aect-security-checklist SS F, bewusst
  hierher verschoben).
- Non-root User im finalen Dockerfile.
- SBOM (`cyclonedx-py`).
- `docs/owasp-llm-checklist.md`: LLM Top 10 gegen AECT, je Mitigation +
  Teststatus.

**Tag 76: Demo-Skript + Interview-QA**
- Case-Auswahl (je ein MARGINAL_GAIN / CALCULATED_RISK / LIKELY_WIN).
- 10 schriftliche Interview-Fragen mit Antworten (Architektur, LLM, RAG,
  Security, Eval, Limitationen).

**Tag 77: Karriere-Assets + v1.0.0-Tag**
- CV-Bullets (3-5 Punkte, STAR-Format, quantifiziert wo moeglich).
- LinkedIn-Case-Study (nach SCHREIBSTIL.md: Anti-Hype, Argument vor Gefuehl,
  nur generische Schicht -- keine Firmen-IP, IP-Klaerung vorher).
- `git tag v1.0.0 && git push origin v1.0.0`.

---

## Offene Schulden, die Phase F erbt

| Punkt | Quelle |
|---|---|
| `resilient.py`-Docstring stale | Phase-C-Review, Phase-D-Review, Phase-E-Review |
| ADR-0010: Exception-Translation-Tabelle fehlt im ADR-Text | Phase-C-Review |
| `SQLiteRepository` pro Request instanziiert | Phase-B-Review |
| Beide ADR-Serien (`000X` / `ADR-00X`), Nummerierungsluecke ADR-004 | Phase-B-Review, session-protocol v3 SS6.13 |
| `breakdown.py`-Coverage 80 % | Phase-E-Review |

---

*Erstellt: Tag 68 (Phase-F-Kickoff). Tag-Nummern sind Schaetzungen, keine Positionen.*
