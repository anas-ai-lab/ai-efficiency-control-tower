# Phase D — Review

**Datum:** 21. Juni 2026
**Tests bei Review:** 417 passed, 4 skipped (`uv run pytest -q`, nach venv-Rebuild Tag 61 bestaetigt)
**Gate-Status:** Bestanden — 3 Live-Test-Queries gegen den vollen Hybrid+Reranking-Pfad
(ChromaRetriever + BM25Retriever + HybridRetriever + CrossEncoderReranker, Tag 61,
session-protocol v3 SS2). Zwei Faelle mit echten Compliance-Hints (mit/ohne risk_flags),
alle Citations stimmen exakt mit den [N]-Markern im Fliesstext ueberein, keine
halluzinierte Artikel-Nummer. Eine themenfremde Probe-Query bestaetigt: das Retrieval
hat keine Relevanz-Schwelle (siehe unten).

---

## Gebaute Artefakte

| Datei | Inhalt (1 Satz) |
|---|---|
| `adapters/rag/chunker.py` | Token-basiertes, gieriges Absatz-Chunking mit optionalem Overlap (tiktoken o200k_base). |
| `adapters/rag/indexing.py` | `build_index_records()` — liest KB-Markdown, trennt Front-Matter, baut upsert-fertige IndexRecords (rein, offline, kein Embedding/Chroma). |
| `adapters/rag/indexer.py` | `index_knowledge_base()` — bettet Records ein und schreibt sie via upsert in eine ChromaDB-Collection. |
| `adapters/rag/embedder.py` | `SentenceTransformerEmbedder` — lokales Embedding (all-MiniLM-L6-v2), `asyncio.to_thread`. |
| `adapters/rag/retriever.py` | `ChromaRetriever` — HTTP-only Vektor-Retrieval, Score-Transform `1/(1+distance)`. |
| `adapters/rag/bm25_retriever.py` | Hand-gerollter Okapi-BM25-Retriever (k1=1.5, b=0.75), keine externe Library. |
| `adapters/rag/hybrid_retriever.py` | `HybridRetriever` — kombiniert BM25 + Vektor via Reciprocal Rank Fusion (ADR-0027). |
| `adapters/rag/reranker.py` | `CrossEncoderReranker` — wrappt einen RetrieverPort, sortiert Kandidaten praeziser neu (ADR-0028). |
| `application/service.py` | `generate_compliance_hints()` — regelbasierte Query-Triggerung (Transparenz immer, DSFA bei risk_flags), Citations deterministisch aus dem Retrieval gebaut, nicht aus der LLM-Antwort geparst (ADR-0024). |
| `adapters/api/routes/cases.py` | `POST /cases/{id}/compliance-hints`-Endpoint. |
| `adapters/api/dependencies.py` | `get_retriever_port()` — Settings-Schalter MockRetriever vs. CrossEncoderReranker(HybridRetriever(...)). |
| `knowledge_base/*.md` | Kuratierte Quellen: DSGVO Art. 35 (DSFA), EU AI Act Art. 50 (Transparenz). |
| `scripts/seed_knowledge_base.py` | Einmaliges, idempotentes Seeding der echten Chroma-Collection. |
| `scripts/gate_check_phase_d.py` | Manueller Pfad-Check (Tag 61) — themenfremde Probe-Query direkt gegen den vollen Pfad, ohne FastAPI. |
| `docker-compose.yml` | ChromaDB 1.5.3, ausschliesslich an 127.0.0.1 gebunden (ADR-0018). |
| `docs/adr/0014-0028` | RAG-Kontrakt, Embedding-Kontrakt, Chunker, Chroma-Container/-Retriever, EU-AI-Act-Recheck, Citation-Konvention, KB-Live-Indexing, Citation-Metadata-Passthrough, RAG-grounded Compliance-Hints, Chroma-DI-Wiring, Hints-Persistenz, Hybrid-Search/RRF, Cross-Encoder-Reranking. |

---

## Was ich heute anders designen wuerde

**1. Keine Relevanz-Schwelle im Retrieval-Pfad.** Die Gate-Check-Probe (Tag 61, Query
"Mittagessen Kantine Speiseplan Wochenmenue") liefert trotz fehlendem thematischen
Bezug 2 Treffer mit deutlich negativen Cross-Encoder-Scores (-9.75, -10.25) statt einer
leeren Liste — `top_k` liefert unbedingt, unabhaengig von der tatsaechlichen Relevanz.
Aktuell folgenlos: `generate_compliance_hints()` nutzt ausschliesslich zwei feste
kanonische Query-Strings, nie freien Nutzertext (siehe service.py-Docstring) — das
Szenario tritt im echten Pfad nicht auf. Wird relevant, sobald Queries je dynamisch
werden oder die Wissensbasis stark waechst.

**2. PII-Redaction vor Embedding bewusst nicht gebaut — Einordnung praezisiert.**
`indexer.py` und `indexing.py` dokumentieren das bereits explizit (ADR-0021): der
Redactor gehoert auf den "User-Case-/Query-Pfad", nicht auf den KB-Indexing-Pfad, der
ausschliesslich kuratierten oeffentlichen Gesetzestext verarbeitet. Bestaetigt bei
Tag-61-Review: dieser User-Case-Embedding-Pfad existiert im aktuellen Build schlicht
noch nicht — `generate_compliance_hints()` embedded keinen Nutzerfreitext, nur feste
Query-Strings. Eine Redaction-Funktion jetzt zu bauen, haette keinen Aufrufer gehabt.
Keine Schuld, sondern eine korrekt vorausschauende ADR-Entscheidung — nachzuholen,
sobald ein solcher Pfad tatsaechlich entsteht.

**3. Keine Deduplizierung bei Mehrfach-Treffer ueber mehrere Queries.** Bereits in
`service.py` dokumentiert (Tag 61 nicht neu, aber bei der Live-Verifikation relevant):
liefert die Transparenz- und die DSFA-Query denselben Chunk, taucht er doppelt in den
Citations auf. Bei der heutigen, kleinen Wissensbasis nicht beobachtet und nicht
relevant — Folge-Punkt, sobald die KB waechst.

---

## Offene technische Schulden

| Punkt | Prioritaet | Wann adressieren |
|---|---|---|
| Keine Relevanz-Schwelle im Retrieval (siehe oben) | Niedrig | Sobald Queries dynamisch werden oder die KB waechst |
| PII-Redaction fuer User-Case-/Query-Pfad (ADR-0021, bewusst verschoben) | Niedrig | Sobald ein Embedding-Pfad fuer nutzergenerierten Freitext entsteht — aktuell nicht im Scope |
| Keine Deduplizierung bei Mehrfach-Query-Treffern (service.py-Docstring) | Niedrig | Sobald die KB waechst |
| `resilient.py`-Docstring stale (aus Phase-C-Review uebernommen) | Niedrig | weiterhin offen |

---

## Vertrauen ins Phase-D-Design (1–10)

**Hybrid-Retrieval (BM25+Vektor+RRF):** 8 — RRF kombiniert zwei unabhaengige
Ranking-Signale ohne Score-Normalisierungs-Probleme; bislang nur an einer kleinen,
synthetischen KB getestet, Skalierungsverhalten bei wachsender KB unbekannt.

**Cross-Encoder-Reranking:** 8 — Live-Test (Tag 61) zeigt eine funktionierende,
korrekt verdrahtete Praezisions-Stufe nach dem Hybrid-Ranking; `candidate_pool=10`
als Sicherheitsabstand ist konzeptionell bestaetigt (Comprehension-Gate Tag 60), aber
am echten Gate-Check nicht in einer Situation beobachtet, in der ein Top-Treffer
tatsaechlich erst auf Position 5–7 lag.

**Citation-Grounding:** 9 — die strukturelle Garantie (Citations werden aus dem
Retrieval gebaut, nie aus der LLM-Antwort geparst) haelt im Live-Test fuer beide
Faelle (mit und ohne risk_flags) ohne jede Abweichung. Staerkster Beleg des gesamten
Gate-Checks.

**Graceful Degradation:** 8 — der Code-Pfad fuer "keine Treffer -> kein LLM-Call" ist
unit-getestet, wurde im Live-Gate aber nicht ausgeloest (beide Test-Cases hatten
Treffer) — am echten Pfad noch nicht beobachtet.

---

## Offene Punkte fuer Phase E

1. Relevanz-Schwellenwert-Frage (siehe oben) — kein Blocker, als Beobachtung
   mitnehmen, falls Eval-Cases spaeter zeigen, dass Off-Topic-Retrieval ein Problem ist.
2. PII-Redaction fuer den User-Case-Pfad — aktuell nicht in Phase E geplant
   (Master-Plan v3.1: Phase E ist Eval, kein neuer RAG-Schreibpfad).
3. Graceful-Degradation-Pfad ("keine Treffer") ist bislang nur unit-, nicht
   live-getestet — Golden-Case-Set in Phase E sollte mindestens einen Case ohne
   jeden Retrieval-Treffer enthalten, um das auch am echten Pfad zu zeigen.
