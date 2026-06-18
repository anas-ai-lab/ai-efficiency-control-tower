# ADR-0017: Chunker -- Absatz-basiertes Packen ohne eigenen Port

**Status:** Accepted
**Datum:** 2026-06-17
**Autor:** Anas

## Kontext

EmbedderPort (ADR-0015) erwartet Texte passender Groesse, nicht ganze
Dokumente -- ein zu langer Text verwaessert den Vektor (zu viele Themen)
oder wird vom Modell ohnehin abgeschnitten. ADR-0015 und ADR-0016 haben den
Chunker bereits als bewusste Folgeentscheidung benannt. Vor der eigentlichen
Wissensbasis (kuratierte Markdown-Dateien, Folge-Tage) und vor ChromaDB
(eigener Docker-Tag) braucht es eine deterministische, testbare
Chunking-Funktion.

## Entscheidung

1. `src/aect/adapters/rag/chunker.py` (neu):
   - `Chunk` (frozen dataclass): `text`, `source_id`, `chunk_index` +
     `chunk_id`-Property (`f"{source_id}:{chunk_index}"`). Bewusst kein
     `score`-Feld (anders als `RetrievedChunk`, ADR-0014) -- Chunking
     passiert vor jeder Suche, nicht als deren Ergebnis.
   - `chunk_document(text, source_id, *, max_tokens=200, overlap_tokens=0)
     -> list[Chunk]`: Absatz-basiertes, gieriges Packen bis zur
     Token-Obergrenze. Ein einzelner Absatz, der die Obergrenze allein
     ueberschreitet, wird hart in Token-Stuecke geschnitten
     (`encoding.encode`/`.decode`-Slicing). Optionales Overlap: ganze
     Absaetze vom Ende des vorherigen Chunks werden, soweit sie ins
     Overlap-Budget passen, an den Anfang des naechsten Chunks kopiert.
     `overlap_tokens >= max_tokens` -> `ValueError` (sonst inhaltlich
     sinnlose Konfiguration).
   - Token-Zaehlung ueber das bestehende `count_tokens()`
     (`application/cost_logger.py`, tiktoken `o200k_base`) -- keine zweite
     Zaehlweise im Projekt. Fuer das harte Token-Slicing wird zusaetzlich
     direkt `tiktoken.get_encoding("o200k_base")` verwendet (`count_tokens()`
     liefert nur eine Zahl, kein Encode/Decode).
2. **Kein ChunkerPort.** Anders als EmbedderPort/RetrieverPort/LLMPort gibt
   es keinen austauschbaren Provider -- Chunking ist eine deterministische
   Funktion ohne I/O, analog den reinen Domain-Funktionen (`domain/roi.py`,
   `domain/scoring.py`), die ebenfalls ohne Port direkt getestet werden.
   Platzierung trotzdem in `adapters/rag/` (Master-Plan v3.1 Phase D
   verortet den Chunker dort, als RAG-Pipeline-Baustein).
3. `adapters/rag/__init__.py` um `Chunk`, `chunk_document` erweitert.

## Begruendung

| Alternative | Warum verworfen |
|---|---|
| ChunkerPort + MockChunker (analog Embedder/Retriever) | Kein zweiter Provider in Sicht -- die Chunking-Logik selbst hat kein austauschbares Backend, ein Port ohne zweite Implementierung waere Spekulation (vgl. ADR-0015s Verzicht auf ein Embedding-Werteobjekt aus demselben Grund). |
| Zeichen-/Wort-Zaehlung statt Token-Zaehlung | Das Projekt kennt bereits eine Groessen-Metrik (Tokens, `cost_logger.py`). Zwei verschiedene Zaehlweisen fuer "Groesse" im selben Projekt waeren eine vermeidbare Inkonsistenz. |
| Fixe Zeichen-Fenster ohne Absatz-Ruecksicht (Sliding Window) | Zerschneidet Saetze/Gedanken willkuerlich mitten im Inhalt -- bei kuratierten Compliance-/Stack-Texten (Folge-Tage) ist Absatzstruktur meist bereits eine sinnvolle inhaltliche Grenze. |
| LangChain-TextSplitter o.ae. als neue Dependency | interne Referenz (entfernt) SS4 / Tag-48-Notiz: "additiv, keine neue schwere Dependency". `re` (Stdlib) + bereits vorhandenes `tiktoken` reichen. |
| Hartes Cutoff statt Fallback-Slicing fuer ueberlange Absaetze | Wuerde Inhalt stillschweigend verlieren. Token-Slicing (encode/decode) verliert nichts, nur die Absatzgrenze wird in diesem seltenen Fall ignoriert -- dokumentierter Trade-off, kein Datenverlust. |
| `overlap_tokens >= max_tokens` stillschweigend zulassen | Fuehrt zu einem Chunk, der ausschliesslich aus uebernommenem Overlap-Inhalt ohne neuen Inhalt bestehen kann -- ValueError macht die Fehlkonfiguration sofort sichtbar statt sie als stillen Bug ins Retrieval durchsickern zu lassen. |

## Konsequenzen

**Positiv:**
- Additiv: kein bestehender Code geaendert, isoliert testbar ohne echte
  Embeddings, keine neue Dependency.
- Token-Budget konsistent mit der einzigen anderen Groessen-Metrik im
  Projekt (Cost-Tracking).
- `Chunk` ist bewusst von `RetrievedChunk` getrennt (kein score-Feld) --
  beide Typen bleiben so einfach wie ihr jeweiliger Zweck es erlaubt.

**Negativ / Trade-offs:**
- `_DEFAULT_MAX_TOKENS=200` ist tiktoken-basiert (o200k_base), nicht das
  Tokenizer-Vokabular von all-MiniLM-L6-v2 (eigenes BERT-Wordpiece-Vokabular,
  max. 256 Tokens dieses Modells). Beide Zaehlweisen sind nicht 1:1
  vergleichbar -- 200 ist eine konservative Naeherung, keine exakte
  Garantie gegen Truncation durch den Embedder. Exakte Kalibrierung waere
  verfrueht ohne echte KB-Inhalte und Retrieval-Eval (Phase E).
- Bei `overlap_tokens` nahe `max_tokens` UND einem grossen unmittelbar
  folgenden Stueck kann der naechste Chunk knapp nach dem Packen sofort
  wieder finalisiert werden (ueberwiegend Overlap-Inhalt, wenig neuer
  Inhalt) -- kein Fehler, aber ein bekannter Sonderfall bei aggressiver
  Overlap-Konfiguration. Offen dokumentiert, nicht versteckt.
- Chunker liegt architektonisch "wie ein Adapter", verhaelt sich aber wie
  eine reine Domain-Funktion (kein I/O) -- bewusste Abweichung vom
  Hexagonal-Wortsinn, gerechtfertigt durch die explizite Verortung im
  Master-Plan v3.1.

**Neutral / Folgeentscheidungen:**
- Kuratierte Wissensbasis als Markdown-Dateien (`knowledge_base/`,
  Folge-Tag) -- erst dann bekommt `chunk_document()` echten Input.
- ChromaDB-Persistenz inkl. `chunk_id` als Upsert-Key (eigener Docker-Tag).
- Service-/Indexing-Pipeline-Verdrahtung (kein Consumer heute, analog
  `EmbedderPort` seit ADR-0015/0016).
- PII-Redaction vor Embedding bleibt Aufgabe der Indexing-Pipeline, nicht
  des Chunkers (Single Responsibility, bereits in ADR-0016 fuer den
  Embedder-Adapter festgehalten).
