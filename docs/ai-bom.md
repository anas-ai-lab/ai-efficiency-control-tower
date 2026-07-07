# AI-BOM — AI Efficiency Control Tower (AECT)

> AI Bill of Materials: alle KI-Komponenten, Modelle und Wissensquellen.
> Ergaenzt das Software-SBOM (`docs/sbom.json`) um KI-spezifische Komponenten.
> Stand: Juni 2026. Vor produktivem Einsatz auf Aktualitaet pruefen.

---

## Inference Models

| Komponente | Modell | Anbieter | Datenzone | Zweck |
|---|---|---|---|---|
| LLM | `gpt-4.1-mini` | Azure OpenAI | Sweden Central / West Europe | Use-Case-Schaerfung, Loesungsvorschlag, Compliance-Hints |
| Cross-Encoder | `cross-encoder/ms-marco-MiniLM-L-6-v2` | HuggingFace (lokal) | Lokal | RAG Reranking |
| Embedding | `all-MiniLM-L6-v2` | HuggingFace (lokal) | Lokal | Vektorisierung KB + Queries (384d) |

**EU-Datenresidenzpflicht:** Azure-Deployment ausschliesslich in `swedencentral`
oder `westeurope` — kein Global-Routing fuer Nutzerdaten.
Konfiguriert in `AECT_AZURE_OPENAI_ENDPOINT` (Settings, ADR-0010).

**Hinweis:** `gpt-4.1-mini` ersetzt `gpt-4o-mini` (fuer neue Kunden seit 2025
nicht mehr verfuegbar — ADR-0010).

---

## RAG Knowledge Base

Kuratierte Markdown-Dateien in `knowledge_base/`. Keine externen Live-Quellen.
Jede Datei traegt ein Front-Matter-Feld `citation` (ADR-0021).

| Datei | Inhalt | Letzte Pruefung |
|---|---|---|
| `eu-ai-act-art-50-transparenz.md` | EU AI Act Art. 50 — Transparenzpflichten | Juni 2026 |
| `dsgvo-art-35-dsfa.md` | DSGVO Art. 35 — Datenschutz-Folgenabschaetzung | Juni 2026 |
| *(weitere nach Bedarf)* | | |

**Wichtige Einschraenkung:** Die KB ist statisch. Rechtsaenderungen
(z. B. Digital Omnibus im EU-Amtsblatt) fliessen erst nach manuellem Update
ein. Kein automatisiertes Staleness-Monitoring in v1.

---

## Trainingsdaten-Kontext

AECT fuehrt **kein Fine-Tuning** durch. Basismodell (`gpt-4.1-mini`):
trainiert durch Microsoft/OpenAI — Details im OpenAI Transparency Report.

Die Entscheidungslogik (Zonen, ROI, Composite-Score) ist vollstaendig
regelbasiert und unabhaengig vom LLM-Training. LLM generiert ausschliesslich
Sprache (Schaerfung, Loesung, Compliance-Fliesstext) — keine numerischen
Bewertungen.

---

## Lizenz-Kontext

| Komponente | Lizenz |
|---|---|
| `all-MiniLM-L6-v2` | Apache 2.0 |
| `cross-encoder/ms-marco-MiniLM-L-6-v2` | Apache 2.0 |
| Azure OpenAI | Microsoft Azure ToS + DPA (Art. 28 DSGVO) |

---

*v1.0 — Juni 2026*
