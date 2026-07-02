# 0028 - Cross-Encoder-Reranking nach Hybrid-Retrieval

Status: Accepted
Datum: 2026-06-22
Kontext: Phase D, HybridRetriever (ADR-0027), RetrieverPort (ADR-0014),
Master-Plan v3.1 Phase-D-Kerninhalt ("Cross-Encoder-Reranking")

## Kontext

HybridRetriever (ADR-0027) liefert per RRF eine kombinierte Rangliste aus
Vektor- und BM25-Treffern. Beide Sub-Verfahren bewerten Query und Dokument
unabhaengig voneinander (Bi-Encoder-Prinzip bei der Vektorsuche, reine
Term-Statistik bei BM25) -- keines der beiden Verfahren sieht Query und
Dokument je gemeinsam. Ein Cross-Encoder bewertet das Paar gemeinsam
(volle Attention zwischen beiden Texten) und ist dadurch praeziser, aber
pro Vergleich teurer -- ungeeignet fuer den gesamten Korpus, gut geeignet
als zweite Stufe auf einer bereits vorgefilterten Kandidatenmenge
(Retrieve-then-Rerank, Standardmuster).

## Entscheidung

1. **Wrapping statt Erweiterung.** `CrossEncoderReranker` implementiert
   `RetrieverPort` und nimmt im Konstruktor einen beliebigen inneren
   `RetrieverPort` entgegen (im echten Pfad: `HybridRetriever`) --
   analog dazu, wie `HybridRetriever` zwei Sub-Retriever wrappt statt
   eine dritte, monolithische Implementierung zu bauen. `TriageService`
   kennt weiterhin nur `RetrieverPort`, der Reranking-Schritt ist fuer
   ihn unsichtbar (ADR-0014).

2. **Modell: `cross-encoder/ms-marco-MiniLM-L-6-v2`.** Standard-Reranking-
   Modell aus dem sentence-transformers-Oekosystem, trainiert auf MS
   MARCO Passage Ranking. Keine neue Dependency -- `sentence-transformers`
   ist seit Tag 48 vorhanden (`SentenceTransformerEmbedder`, ADR-0016),
   `CrossEncoder` ist Teil desselben Pakets.

   | Alternative | Warum verworfen |
   |---|---|
   | Groesseres Cross-Encoder-Modell (z. B. `ms-marco-MiniLM-L-12-v2`) | Mehr Latenz fuer marginalen Genauigkeitsgewinn auf einer kleinen, kuratierten Wissensbasis -- Budget-/Scope-Disziplin |
   | LLM-basiertes Reranking (Azure-Call mit Relevanz-Prompt) | Kosten + Latenz pro Query, fuer eine lokale Wissensbasis mit wenigen Dokumenten nicht gerechtfertigt; widerspricht dem Local-first-Prinzip |

3. **candidate_pool=10 (Default), analog HybridRetriever.candidate_pool.**
   Der innere Retriever wird mit `top_k=candidate_pool` abgefragt, nicht
   mit dem finalen `top_k` -- der Cross-Encoder soll auf einer breiteren
   Kandidatenmenge sortieren, nicht nur die vom Hybrid-Schritt bereits
   vorsortierten Top-`top_k` reranken.

4. **`RetrievedChunk.score` wird durch den Cross-Encoder-Score ersetzt.**
   `score` ist laut Kontrakt (`ports/retriever.py`) "nur fuer Reihenfolge/
   Anzeige, nicht fuer Berechnungen" -- die Ersetzung ist vertragskonform.
   Der urspruengliche RRF-Score wird nicht weitergereicht; bei Bedarf
   (z. B. Debugging) muesste er separat geloggt werden -- heute kein
   Anwendungsfall.

5. **Modellname als Code-Konstante, kein Settings-Feld.** Anders als
   `kb_dir`/`chroma_host` (Infrastruktur-Adressen, Umgebungs-spezifisch)
   ist der Modellname ein generischer, oeffentlicher Identifier ohne
   Firmenbezug -- kein IP-Trennungs-Grund fuer ein `AECT_`-Env-Feld.

6. **lru_cache auf `_get_cross_encoder_model()`, analog
   `_get_local_embedding_model`/`_get_chroma_collection`/`_get_bm25_index`.**
   Modellgewichte werden einmal pro Prozess geladen, nicht pro Request.

## Konsequenzen

**Positiv:**
- Keine neue Dependency, kein zusaetzlicher `uv.lock`-Eintrag.
- Reranking-Pfad nur im realen Retrieval aktiv (`AECT_CHROMA_HOST`
  gesetzt) -- Mock-Pfad und alle bestehenden Tests unveraendert.
- Citation-Nummerierung in `generate_compliance_hints()` (ADR-0024)
  profitiert automatisch: die `[N]`-Reihenfolge im Compliance-Hinweis
  folgt jetzt der Cross-Encoder-Rangfolge statt der reinen RRF-Rangfolge,
  ohne dass `service.py` etwas davon weiss oder geaendert werden musste --
  reiner Vorteil der Port-Abstraktion.

**Negativ / Trade-offs:**
- Zusaetzliche Inferenz-Latenz pro Query (Cross-Encoder-Forward-Pass auf
  `candidate_pool` Paaren) -- bei der aktuellen, kleinen Wissensbasis
  vernachlaessigbar, Folgepunkt bei wachsender KB oder spuerbarer Latenz
  im Demo-Betrieb (Phase F).
- Modell-Laden ist synchron beim ersten Request (kein Pre-Warming),
  analog der bereits dokumentierten Limitation bei
  `_get_local_embedding_model`/`_get_bm25_index`.

**Neutral / Folgeentscheidungen:**
- Phase-D-Gate-Check (session-protocol v3 SS2, 3 Test-Queries mit
  Citations) ist bewusst NICHT Teil dieses Tages -- folgt als naechster
  Schritt, jetzt da die volle Hybrid+Reranking-Pipeline steht.
- session-protocol v3 SS3 (Comprehension-Gate-Themenliste) enthaelt noch
  keinen Reranking-Eintrag -- mit diesem Tag faktisch ergaenzt, sollte in
  einer naechsten Protokoll-Revision (v3.3) nachgezogen werden.
