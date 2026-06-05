# AI Efficiency Control Tower

> AI Use Case Intake & Triage Assistant for internal AI requests

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Status: In Development](https://img.shields.io/badge/status-in%20development-orange.svg)]()
[![CI](https://github.com/USERNAME/REPO-NAME/actions/workflows/ci.yml/badge.svg)](https://github.com/USERNAME/REPO-NAME/actions/workflows/ci.yml)

---

## Problem

Companies receive a growing number of internal AI requests — from HR, IT, Finance, Legal, and Operations.
Most organizations have no structured process to evaluate these requests.

The result:
- AI is applied where simple automation would suffice
- High-risk use cases skip compliance review
- Costs are unpredictable
- Teams waste weeks building the wrong thing

There is no lightweight, opinionated triage system that evaluates AI requests across business value, technical feasibility, cost, risk, and compliance — before a single line of code is written.

---

## Solution

The **AI Efficiency Control Tower** is a production-oriented intake and triage system for internal AI use cases.

It evaluates incoming requests across:

- **AI suitability** — Is AI the right tool, or is rule-based automation better?
- **Privacy & compliance risk** — Does this touch personal data? Is a DPIA required?
- **Technical complexity** — RAG needed? Function calling? Human review?
- **Cost estimate** — Monthly token cost, low/expected/high range
- **Implementation effort** — Rough person-week estimate
- **Recommended approach** — With rationale and next steps

Output: A structured, source-grounded assessment report — not a chatbot response.

---

## What this is NOT

- Not a generic AI chatbot
- Not a project management tool
- Not a decision engine that replaces human judgment on high-risk cases
- Not a fine-tuned model
- Not a SaaS product (MVP scope)
- Not a replacement for a DPIA or legal review

---

## Architecture (High-Level)
Intake (n8n Form / API) → Rule-based Triage → LLM Assessment (optional)
→ RAG Knowledge Base (Governance, GDPR, Cost) → Structured Report
→ Human Review (if risk: high or critical) → Audit Trail
Full architecture: see `docs/architecture.md` (in progress)

---

## Tech Stack (Planned)

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| API | FastAPI (async) |
| Domain Models | Pydantic V2 |
| Database | SQLite + SQLModel |
| LLM Provider | Azure OpenAI (GPT-4.1-mini) |
| Vector DB | ChromaDB (local) |
| Search | BM25 + Dense Hybrid |
| Workflow | n8n (self-hosted) |
| Deployment | Docker + Azure Container Apps |
| Observability | structlog + OpenTelemetry |

---

## Project Status

**Week 1 of 24 — Setup & Foundation**

This project is being built as part of a 24-week AI Engineering learning plan.
See `learning-log.md` for weekly progress.

---

## Repository Structure
src/aect/          # Application source code
tests/             # Test suite
docs/              # Architecture, ADRs, frameworks
knowledge_base/    # Governance and compliance documents
evals/             # Evaluation datasets and reports
workflows/         # n8n workflow exports
prompts/           # Versioned prompt files
sample_reports/    # Example triage outputs
src/aect/          # Application source code
tests/             # Test suite
docs/              # Architecture, ADRs, frameworks
knowledge_base/    # Governance and compliance documents
evals/             # Evaluation datasets and reports
workflows/         # n8n workflow exports
prompts/           # Versioned prompt files
sample_reports/    # Example triage outputs
---

## Author

Built by [Anas] as a capstone project for the AI Engineering Master Plan v2.
GitHub: [github.com/anas-ai-lab](https://github.com/anas-ai-lab)
