# CV Bullets -- AECT Portfolio-Projekt

> Ziel-Rolle: AI Engineer / Solution Architect, DACH-Markt.
> Verwendung: XING, LinkedIn, Bewerbungsunterlagen. IP-Klaerung liegt vor
> (schriftliche Bestaetigung des Arbeitgebers). Alle Zahlen aus dem Repo verifizierbar.

---

## Projekt-Ueberschrift

**AI Efficiency Control Tower (AECT)** | Privates Portfolio-Projekt
Python 3.12 - FastAPI - Azure OpenAI (gpt-4.1-mini) - ChromaDB - RAG

---

## Technische Bullets

- Vollstaendiges ROI-Bewertungsmodell deterministisch implementiert
  (Lookup-Tabellen je Land x Senioraet, Composite-Aufwand-Score,
  3-Zonen-Einstufung) -- 715 Tests, 95% Coverage, kein LLM fuer Zahlen

- Hexagonale Architektur: Domain-Layer vollstaendig isoliert von LLM-,
  Datenbank- und API-Adaptern; Adapter-Swap ohne Domain-Code-Aenderung
  nachgewiesen (ADR-004, ADR-007)

- RAG-Pipeline: Hybrid-Retrieval (BM25 + Vektor, Reciprocal Rank Fusion)
  auf ChromaDB, Cross-Encoder-Reranking, Citations-before-LLM-Pattern
  gegen halluzinierte Artikel-Nummern (ADR-0024, 0027, 0028)

- LLM-Integration: Azure OpenAI EU-Datenzone, Function-Calling-Loop,
  Graceful Degradation, Cost-Logger (tiktoken), Resilience (tenacity)

- Frontend: Next.js 16 (App Router, shadcn/ui, TypeScript strict),
  6-Schritt-Flow Intake bis Report, Server Actions fuer API-Key-
  Sicherheit (kein Secret im Client-Bundle)

- Control-Tower-Layer (v3): Case-Lifecycle-Status (7 Zustaende, an die
  Reviewer-Freigabe gekoppelt), Portfolio-Board als Nutzen-Machbarkeits-Matrix
  (recharts: Nettonutzen x invertierter Aufwand-Score, Zone als Farbe),
  append-only Monitoring-Zeitleiste mit Status-Snapshots (Lost-Update-sicher
  per INSERT statt JSON-Rewrite, F-011) -- ADR-0045/0046/0047

- Generative Assistenz-Features (v3.1) mit striktem Schema-Zwang und ohne
  erfundene Zahlen: Ideen-Assistent erzeugt qualitative Use-Case-Entwuerfe
  (ROI-Zahlen bleiben menschlicher Input), Architektur-Skizze via LLM-Graph-JSON
  + deterministischem Mermaid-Builder (Syntaxfehler- und Injection-Klasse
  strukturell eliminiert), plus deterministische Dedup-Sicht (Embedding-
  Aehnlichkeit, gleiche Schwellen wie Intake) und client-seitiger CSV-Export --
  ADR-0048/0049

- Eval-Framework: JSONL Golden-Cases, 3-valued Match (True/False/None),
  Score-Breakdown-Diagnostik, 36 synthetische Cases fuer Konsistenz-Test,
  dokumentierter Experten-Abgleich inkl. Limitationsanalyse

- Security: OWASP LLM Top 10 gegen AECT geprueft (Prompt-Injection-Detection
  mit Flagging, Logging-Allowlist, constant-time API-Key-Auth, Rate-Limiting),
  STRIDE-Threat-Model, EU AI Act Limited-Risk-Klassifikation hergeleitet (ADR-0020)

- CI/CD: GitHub Actions mit gitleaks, bandit, pip-audit, SHA-gepinnte
  Actions, mypy strict, ruff, pre-commit (10 Hooks)

---

## Entscheidungs-Bullets

- 55 ADRs mit Alternativen und Trade-offs -- Interview-verteidigbar

- Scope-Disziplin dokumentiert: kein SaaS, kein Fine-Tuning, kein n8n
  (begruendet im projekteigenen Strategiedokument mit Aenderungshistorie)

- 24 Limitationen offen kommuniziert (`docs/known_limitations.md`) --
  staerker als Marketing-Darstellung ohne Schwaechen

---

## Interview-Anker (ein konkretes Beispiel pro Thema)

| Thema | Anker |
|---|---|
| RAG vs. Fine-Tuning | Citations-before-LLM -- strukturell, nicht Prompt-Disziplin |
| Evaluation | Zirkulaere Validierung vermieden: ADR-0029 |
| Security | OWASP LLM01 -- 4 Lagen, Flagging vor Blocking |
| Architektur | Adapter-Swap: AzureOpenAI -> Mock in einer Zeile |
| Schwaeche benennen | Enge LIKELY_WIN-Schwelle + Hard-Threshold-Brittleness -- Agreement 9/24 Golden-Cases, Divergenzen dokumentiert statt kaschiert |
| Datenmodell-Design | Append-only Monitoring statt JSON-Rewrite -- Lost-Update strukturell vermieden (F-011, ADR-0046) |

---

*v3.1 -- Juli 2026. IP-Klaerung liegt vor (schriftliche Bestaetigung des Arbeitgebers).*
