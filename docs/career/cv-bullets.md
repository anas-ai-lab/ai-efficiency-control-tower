# CV Bullets -- AECT Portfolio-Projekt

> Ziel-Rolle: AI Engineer / Solution Architect, DACH-Markt.
> Verwendung: XING, LinkedIn, Bewerbungsunterlagen -- nach IP-Klaerung
> (interne Referenz (entfernt) SS5). Alle Zahlen aus dem Repo verifizierbar.

---

## Projekt-Ueberschrift

**AI Efficiency Control Tower (AECT)** | Privates Portfolio-Projekt
Python 3.12 - FastAPI - Azure OpenAI (gpt-4.1-mini) - ChromaDB - RAG

---

## Technische Bullets

- Vollstaendiges ROI-Bewertungsmodell deterministisch implementiert
  (Lookup-Tabellen je Land x Senioraet, Composite-Aufwand-Score,
  3-Zonen-Einstufung) -- 448 Tests, 97% Coverage, kein LLM fuer Zahlen

- Hexagonale Architektur: Domain-Layer vollstaendig isoliert von LLM-,
  Datenbank- und API-Adaptern; Adapter-Swap ohne Domain-Code-Aenderung
  nachgewiesen (ADR-0002, ADR-007)

- RAG-Pipeline: Hybrid-Retrieval (BM25 + Vektor, Reciprocal Rank Fusion)
  auf ChromaDB, Cross-Encoder-Reranking, Citations-before-LLM-Pattern
  gegen halluzinierte Artikel-Nummern (ADR-0024, 0027, 0028)

- LLM-Integration: Azure OpenAI EU-Datenzone, Function-Calling-Loop,
  Graceful Degradation, Cost-Logger (tiktoken), Resilience (tenacity)

- Frontend: Next.js 15 (App Router, shadcn/ui, TypeScript strict),
  6-Schritt-Flow Intake bis Report, Server Actions fuer API-Key-
  Sicherheit (kein Secret im Client-Bundle)

- Eval-Framework: JSONL Golden-Cases, 3-valued Match (True/False/None),
  Score-Breakdown-Diagnostik, 36 synthetische Cases fuer Konsistenz-Test,
  dokumentierter Experten-Abgleich inkl. Limitationsanalyse

- Security: OWASP LLM Top 10 gegen AECT geprueft, PII-Redaction vor
  LLM-Calls, API-Key-Auth, Rate-Limiting, EU AI Act Limited-Risk-
  Klassifikation hergeleitet (ADR-0020, 35 ADRs gesamt)

- CI/CD: GitHub Actions mit gitleaks, bandit, pip-audit, SHA-gepinnte
  Actions, mypy strict, ruff, pre-commit (10 Hooks)

- API-Key-Auth, Rate-Limiting, EU AI Act Limited-Risk-
  Klassifikation hergeleitet (ADR-0020, 41 ADRs gesamt)

---

## Entscheidungs-Bullets

- 41 ADRs mit Alternativen und Trade-offs -- Interview-verteidigbar

- Scope-Disziplin dokumentiert: kein SaaS, kein Fine-Tuning, kein n8n
  (begruendet in interne Referenz (entfernt) -- Strategiedokument mit Aenderungshistorie)

- 13 Limitationen offen kommuniziert (`docs/known_limitations.md`) --
  staerker als Marketing-Darstellung ohne Schwaechen

---

## Interview-Anker (ein konkretes Beispiel pro Thema)

| Thema | Anker |
|---|---|
| RAG vs. Fine-Tuning | Citations-before-LLM -- strukturell, nicht Prompt-Disziplin |
| Evaluation | Zirkulaere Validierung vermieden: ADR-0029 |
| Security | OWASP LLM01 -- 4 Lagen, Flagging vor Blocking |
| Architektur | Adapter-Swap: AzureOpenAI -> Mock in einer Zeile |
| Schwaeche benennen | Hard-Threshold-Brittleness -- off-by-one in 2/3 Golden-Cases |

---

*v1.0 -- Juni 2026. Nach IP-Klaerung (interne Referenz (entfernt) SS5) veroeffentlichen.*
