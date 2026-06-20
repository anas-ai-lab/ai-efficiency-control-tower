# 0027 - Hybrid Search: BM25 + Vektor via Reciprocal Rank Fusion

Status: Accepted
Datum: 2026-06-21
Kontext: Phase D, RetrieverPort (ADR-0014), ChromaRetriever (ADR-0019),
Master-Plan v3.1 Phase-D-Kerninhalt ("Hybrid Search (BM25 + Vektor, RRF)")

## Kontext

ChromaRetriever (ADR-0019) findet semantisch Aehnliches ueber Embeddings.
Exakte Begriffstreffer (Gesetzes-Artikelnummern, Produktnamen wie "Open
WebUI") koennen dabei verfehlt werden, wenn das Embedding-Modell die
Formulierung anders gewichtet als der Nutzer. BM25 (Stichwortsuche) hat
das umgekehrte Problem: kein semantisches Verstaendnis. Master-Plan v3.1
sieht beide kombiniert vor, nicht als Alternative zueinander.

## Entscheidung

1. **BM25 hand-rolled, keine neue Dependency.** Okapi-BM25 (k1=1.5,
   b=0.75) ist ein kompakter, gut dokumentierter Algorithmus ohne I/O --
   analog zur Chunker-Entscheidung (ADR-0017: deterministische Funktion
   ohne Port-Abstraktion). Alternative gepruefr: `rank_bm25` (PyPI).

   | Alternative | Warum verworfen |
   |---|---|
   | `rank_bm25`-Bibliothek | Keine Typstubs (mypy-Reibung), zusaetzliche Dependency fuer ~30 Zeilen Algorithmus, weniger Kontrolle ueber Tokenizer-Verhalten auf der ASCII-only-KB (ADR-0021) |
   | Elasticsearch/OpenSearch fuer BM25 | Eigene Infrastruktur-Komponente -- Overkill fuer eine handvoll KB-Files, widerspricht Budget-/Scope-Disziplin (interne Referenz (entfernt) SS4) |

2. **Reciprocal Rank Fusion, k=60.** Cormack/Clarke/Buettcher (2009):
   score(d) = Summe ueber alle Listen, in denen d vorkommt, von
   1 / (k + rang(d)). k=60 ist der literaturuebliche Daempfungswert.
   Vorteil gegenueber direkter Score-Kombination: BM25-Scores (Okapi-
   Skala) und Chroma-Scores (1/(1+distance), ADR-0019) sind nicht
   direkt vergleichbar -- RRF braucht nur die Rang-Position, keine
   Skalen-Normalisierung.

3. **candidate_pool=10 statt finalem top_k.** Beide Sub-Retriever werden
   mit top_k=candidate_pool abgefragt. Ein Dokument auf Position 6 einer
   Liste muss eine Chance haben, nach der Fusion noch in die finalen
   top_k=5 zu kommen -- mit top_k=5 pro Sub-Retriever waere das
   strukturell ausgeschlossen.

4. **Merge-Schluessel: source_id (= IndexRecord.id = Chroma-Document-ID).**
   Beide Pfade nutzen denselben Chunk-Identifier ("<source_id>:
   <chunk_index>", ADR-0017) -- kein zweiter Lookup noetig.

5. **BM25-Index lru_cache auf kb_dir (dependencies.py), analog
   _get_chroma_collection/_get_local_embedding_model.** Aendert sich die
   Wissensbasis, braucht es einen Prozess-Neustart -- dieselbe
   dokumentierte Limitation wie bei den beiden bestehenden Caches.

6. **Settings.kb_dir neu (AECT_KB_DIR, Default "knowledge_base").**
   __file__-relative Pfadberechnung (wie in scripts/seed_knowledge_base.py)
   waere in dependencies.py 5 Verzeichnisebenen tief und fragil. Settings-
   Feld ist konsistent mit chroma_host/chroma_port als bestehendem Muster
   fuer Infra-Overrides.

## Konsequenzen

**Positiv:**
- Keine neue Dependency, kein zusaetzlicher uv.lock-Eintrag.
- Hybrid-Pfad nur im realen Retrieval aktiv (AECT_CHROMA_HOST gesetzt) --
  Mock-Pfad und alle bestehenden Tests unveraendert.
- Citation-Metadaten (ADR-0021/0023) bleiben im BM25-Pfad vollstaendig
  erhalten (IndexRecord.metadata wird direkt durchgereicht).

**Negativ / Trade-offs:**
- Hand-rolled BM25 ist weniger battle-tested als eine etablierte
  Bibliothek -- akzeptiert fuer ein privates Portfolio-Projekt mit
  kleiner, kuratierter Wissensbasis.
- BM25-Index-Aufbau ist synchron beim ersten Request (kein Pre-Warming) --
  bei der aktuellen KB-Groesse (2 Dokumente) vernachlaessigbar, Folgepunkt
  bei wachsender KB.

**Neutral / Folgeentscheidungen:**
- Cross-Encoder-Reranking (Master-Plan v3.1 Phase D) bleibt bewusst
  separater Folgetag -- baut auf dem Hybrid-Ergebnis auf, nicht Teil
  dieser Entscheidung.
- Phase-D-Gate-Check (session-protocol v3 SS2, 3 Test-Queries mit
  Citations) bleibt offener Punkt seit Tag 57/58, unveraendert.
