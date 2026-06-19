# ADR-0023: Citation-Metadaten im Retrieval-Lese-Pfad durchreichen

## Status
Accepted

## Kontext
Tag 53 (ADR-0021) hat die Citation-Konvention und das Front-Matter-Schema
fuer die Wissensbasis definiert. Tag 54 (ADR-0022) hat den Schreib-Pfad
gebaut: `index_knowledge_base()` schreibt `metadatas` (citation, title, url,
source_id, chunk_index) bereits beim Upsert in ChromaDB, obwohl
`RetrievedChunk` diese Felder beim Lesen bisher nicht ausgegeben hat.
Master-Plan v3.1 verlangt fuer das Phase-D-Gate, dass eine Antwort eine
echte Quelle zitiert (`[1]`, `[2]`), keine erfundene Artikel-Nummer. Ohne
Metadaten im Lese-Pfad gibt es nichts, was zitiert werden koennte -- nur
eine Chunk-id.

## Entscheidung
1. `RetrievedChunk` (ports/retriever.py) bekommt ein zusaetzliches Feld
   `metadata: Mapping[str, str] = field(default_factory=dict)`. Generisches
   Mapping statt eines dedizierten `citation`-Felds: haelt den Port offen
   fuer weitere Provenance-Felder (title, url), ohne den Vertrag bei jedem
   neuen Front-Matter-Key erneut zu aendern. Default leer, damit Adapter
   ohne Provenance (MockRetriever) gueltig bleiben.
2. `ChromaCollection.query()` (adapters/rag/retriever.py) bekommt ein
   explizites `include: list[str]`-Argument; `ChromaRetriever._run_query()`
   fordert `["documents", "distances", "metadatas"]` aktiv an, statt sich
   auf den Chroma-Server-Default zu verlassen.
3. `ChromaRetriever._parse()` liest `raw["metadatas"]` analog zu `documents`
   und `distances` (gleiches `_first_row`-Pattern), baut pro Treffer ein
   `dict[str, str]` und reicht es als `RetrievedChunk.metadata` durch.
   Fehlender oder `None`-Eintrag -> leeres dict (Graceful Degradation,
   konsistent mit dem bestehenden Umgang mit fehlenden documents/distances).

## Alternativen erwogen
- **Dediziertes `citation: str | None`-Feld statt generischem `metadata`:**
  verworfen. Wuerde bei jedem weiteren Provenance-Feld (z. B. `title` im
  UI) eine erneute Port-Aenderung erzwingen. Ein Mapping deckt das ab, ohne
  den Kontrakt wachsen zu lassen.
- **Sich auf den Chroma-Default-`include` verlassen** (kein expliziter
  Parameter): verworfen. Der Default ist Implementierungsdetail einer
  Fremdbibliothek und nicht Teil eines dokumentierten, versionsfesten
  Vertrags -- explizit ist robuster und macht in `_run_query` sofort
  sichtbar, was angefordert wird.
- **Citation-Aufloesung als separate Lookup-Tabelle (source_id -> citation)
  statt am Chunk:** verworfen, bereits in ADR-0022 verworfen (zweite Quelle
  pflegen ist fehleranfaelliger als das Etikett am Datensatz zu lassen).

## Konsequenzen
- Additiv: `indexer.py`/`indexing.py` (Schreib-Pfad) unveraendert.
  `MockRetriever` unveraendert, liefert weiterhin leeres `metadata`.
- `metadata`-Werte sind Daten, keine Instruktion -- gleicher Untrusted-
  Umgang wie `text`, auch wenn sie heute ausschliesslich aus kuratiertem,
  selbst geschriebenem Front-Matter stammen. Die eigentliche
  Prompt-Montage mit Delimiter-Abgrenzung (aect-security-checklist v2.1,
  Phase D) ist ein separater Folge-Tag, nicht Teil dieser Aenderung.
- Schliesst die technische Voraussetzung fuer das Phase-D-Gate
  ([1]/[2]-Citations mit echter Quelle). Die eigentliche Verdrahtung in
  Service/Prompt (Compliance-Hinweis zitiert die Quelle im Output) bleibt
  offen -- naechster Schritt.

## Datum
2026-06
