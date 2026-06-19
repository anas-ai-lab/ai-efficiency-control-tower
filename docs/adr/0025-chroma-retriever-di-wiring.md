# 0025: ChromaRetriever-Verdrahtung in der DI (Mock-vs-Real-Schalter)

**Status:** Accepted
**Datum:** 2026-06-19
**Phase:** D (RAG)

## Kontext

ChromaRetriever (ADR-0019) und SentenceTransformerEmbedder (ADR-0016)
existieren seit mehreren Tagen, waren aber in get_retriever_port()
(dependencies.py, ADR-0024) noch nicht verdrahtet -- TriageService lief
bislang ausschliesslich gegen MockRetriever. Heute: echte Verdrahtung,
analog zum bestehenden Azure-vs-Mock-Schalter in get_llm_adapter() (ADR-0010).

## Entscheidung

1. **Settings-gesteuerter Schalter** (wie bei Azure): AECT_CHROMA_HOST
   gesetzt -> ChromaRetriever gegen die echte Collection; leer (Default)
   -> MockRetriever. Kein Docker-Container noetig fuer normale
   Testlaeufe/lokale Entwicklung.
2. **Lokale Imports von chromadb/sentence-transformers** in dependencies.py
   (nicht Modulkopf): nur der scharfe Pfad zieht diese schweren
   Abhaengigkeiten. Der Default-Pfad (MockRetriever, alle normalen
   Testlaeufe) bleibt torch-/chromadb-frei -- direkte Fortsetzung des
   Patterns aus ADR-0016 ("src/ bleibt import-frei von
   sentence-transformers/torch").
3. **lru_cache auf zwei Hilfsfunktionen** (_get_chroma_collection(host, port),
   _get_local_embedding_model()): Chroma-HttpClient+Collection-Handle und
   das geladene sentence-transformers-Modell werden je einmal pro Prozess
   gebaut, nicht pro Request -- Modell-Laden kostet Sekunden, waere als
   Pro-Request-Kosten inakzeptabel (anders als der AsyncAzureOpenAI-Client
   in get_llm_adapter(), dessen Konstruktion guenstig ist und deshalb
   bewusst NICHT gecached wird).
4. **Feste Collection "aect-knowledge-base"**: ein Name, kein Parameter --
   generisch, keine Firmenspezifika (IP-Trennung, interne Referenz (entfernt) SS5).
5. **Seeding ueber ein eigenes Skript** (scripts/seed_knowledge_base.py),
   nicht beim App-Start: App-Start soll nicht von einer laufenden,
   befuellten ChromaDB abhaengen (sonst Kaltstart-Fehler ohne Container);
   Seeding ist ein bewusster, expliziter Schritt, idempotent ueber
   upsert() (ADR-0022).

## Begruendung

| Alternative | Warum verworfen |
|---|---|
| chromadb/sentence-transformers am Modulkopf importieren | Wuerde jeden Testlauf + jeden Mock-Pfad-Request mit Torch belasten -- widerspricht ADR-0016 direkt. |
| Kein lru_cache, Neuaufbau pro Request | SentenceTransformer-Laden kostet Sekunden -- pro Request inakzeptabel; bei der Mock-LLM-Analogie (AsyncAzureOpenAI) gibt es diese Kosten nicht, deshalb dort bewusst ungecached. |
| Collection-Name aus Settings konfigurierbar | Spekulative Flexibilitaet ohne aktuellen Bedarf (ein Prozess, eine Wissensbasis) -- YAGNI. |
| Seeding im App-Startup-Event | Koppelt App-Start an Chroma-Erreichbarkeit; bricht den Mock-Pfad als Fallback-Garantie. |
| Seeding inline per `uv run python -c` | Verboten als Verifikations-/Operationsmuster (session-protocol v3 SS5.2); ein committetes Skript ist reproduzierbar und Teil des "frischer Clone in 10 Min"-Ziels (Phase F). |

## Konsequenzen

**Positiv:**
- Erste echte semantische Vektor-Suche end-to-end nutzbar (Live-Test-geprueft),
  ohne den Default-Testlauf zu verlangsamen.
- Phase-D-Gate-Kriterium ("3 Test-Queries mit Citations") jetzt automatisiert
  pruefbar (Live-Test, AECT_RUN_CHROMA_LIVE=1).

**Negativ / Trade-offs:**
- lru_cache auf _get_chroma_collection haelt den Chroma-HttpClient fuer die
  Prozess-Lebensdauer offen -- bei Container-Neustart waere ein App-Neustart
  noetig, um neu zu verbinden (akzeptabel fuer privates Solo-Dev-Setup).
- Reines Vektor-Retrieval (kein BM25, kein RRF, kein Reranking) -- Hybrid-
  Suche bleibt offener Phase-D-Scope-Punkt (Master-Plan v3.1).

**Neutral / Folgeentscheidungen:**
- Hybrid Search (BM25 + Vektor + RRF), Cross-Encoder-Reranking.
- PII-Redaction-Pipeline vor Embedding bei echten Nutzereingaben (Folge-Tag,
  heute weiterhin nur kuratierte, nicht-personenbezogene KB-Texte).
- Persistenz von compliance_hints auf SubmittedCase + /report-Einbau
  (naechster Schritt aus Tag-56-Daily-Note).
