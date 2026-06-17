# ADR-0015: Embedding-Kontrakt -- EmbedderPort (Mock-First)

**Status:** Accepted
**Datum:** 2026-06-17
**Autor:** Anas

## Kontext

Phase D braucht Vektoren fuer zwei Zwecke: Indexierung der Wissensbasis in
ChromaDB und Query-Embedding zur Laufzeit (Master-Plan v3.1 Phase D, interne Referenz (entfernt)
SS3.2). RetrieverPort (ADR-0014) definiert bereits den Retrieval-Kontrakt,
aber dessen MockRetriever arbeitet noch ohne Vektoren (reines Token-Matching).
Bevor ein echter Embedding-Provider (lokal: sentence-transformers; Cloud:
Azure text-embedding-3-small, EU Data Zone) angebunden wird, braucht es einen
stabilen Kontrakt -- analog LLMPort (ADR-0003/0005) und RetrieverPort
(ADR-0014), die ihre Integrationen jeweils mock-first eroeffnet haben.

sentence-transformers ist eine neue, schwere Dependency (Torch-Backend,
Modell-Download) und die Inferenz ist blockierend -- beides verdient einen
eigenen, fokussierten Folge-Tag statt am selben Tag wie der Kontrakt
entschieden zu werden.

## Entscheidung

Wir definieren den Embedding-Kontrakt und einen deterministischen Mock, ohne
echte Inferenz und ohne bestehenden Code zu aendern:

1. application/ports/embedder.py:
   - EmbedderPort (Protocol): async def embed(texts: Sequence[str])
     -> list[tuple[float, ...]]; ein Vektor pro Eingabetext, gleiche
     Reihenfolge wie `texts`, leere Eingabe -> leere Rueckgabe.
2. adapters/in_memory/embedder.py: MockEmbedder -- deterministischer
   Pseudo-Vektor pro Text (SHA-256-Digest, normiert auf [0.0, 1.0]).

Kein eigenes Werteobjekt fuer den Vektor (kein Embedding-Dataclass wie
RetrievedChunk): der Vektor traegt keine Zusatz-Metadaten, die
Text-zu-Vektor-Zuordnung haelt der Aufrufer ueber die Listenreihenfolge.

## Begruendung

| Alternative | Warum verworfen |
|---|---|
| Sofort sentence-transformers statt Mock | Neue schwere Dependency (Torch, Modell-Download) + blockierende Inferenz verdienen einen eigenen Tag mit eigener asyncio.to_thread-Kapselung, nicht denselben Tag wie der Kontrakt. Widerspraeche Mock-First (ADR-0003, ADR-0014). |
| Einzeltext-Signatur (embed_one) statt Batch | sentence-transformers.encode() und ChromaDB-Upserts sind batchweise effizienter als Einzelaufrufe. Batch-Signatur jetzt erzwingen, statt sie als Adapter-Detail nachzuruesten. |
| Eigenes Embedding-Dataclass (analog RetrievedChunk) | Ein Vektor ohne Zusatz-Metadaten (kein source_id-Aequivalent noetig) -- ein nackter tuple[float, ...] reicht, ein Wrapper waere Spekulation ohne Verbraucher. |
| Synchroner Port | Echte Inferenz (lokal: blockierend; Azure: netzwerkgebunden) wuerde den Event-Loop blockieren. async + asyncio.to_thread bzw. nativer async-Client im jeweiligen Adapter (Folge-Tag) haelt den Loop frei -- konsistent mit LLMPort und RetrieverPort. |
| MockEmbedder mit semantischen Eigenschaften (z. B. TF-IDF-aehnlich) | Wuerde Komplexitaet in den Mock tragen, die der Kontrakt nicht braucht (Kontrakt-Test, nicht Qualitaets-Test). SHA-256-Pseudo-Vektor reicht fuer Determinismus + Unterscheidbarkeit. |

## Konsequenzen

**Positiv:**
- Additiv: kein bestehender Code geaendert, isoliert testbar ohne echte
  Inferenz, keine neue Dependency.
- ChromaDB-Indexierung und Embedding-Provider-Wahl werden gegen einen
  feststehenden Kontrakt gebaut -- kleinere, fokussiertere Folge-Tage.

**Negativ / Trade-offs:**
- EmbedderPort ist bis zur Service-/Indexer-Verdrahtung unbenutzter Kontrakt --
  kein nutzer-sichtbarer Effekt heute.
- MockEmbedder-Vektoren tragen keine Semantik -- Tests gegen MockEmbedder
  pruefen nur den Kontrakt (Determinismus, Reihenfolge, Dimension), nicht
  Retrieval-Qualitaet. Das ist beabsichtigt, nicht uebersehen.

**Neutral / Folgeentscheidungen:**
- Lokaler Embedding-Adapter (sentence-transformers, Modellwahl +
  asyncio.to_thread-Kapselung), Azure-Embedding-Adapter (EU Data Zone,
  Budget-Sentinel SS4), ChromaDB-Persistenz, Chunker-DTO und
  Service-Verdrahtung sind bewusst Folge-Tage.
- PII-Redaction vor dem Embedding (LLM08, aect-security-checklist v2.1
  Phase D) ist dokumentierte Pflicht fuer den Tag des echten
  Embedding-Adapters -- heute nicht relevant (MockEmbedder verarbeitet keine
  echten Daten).
