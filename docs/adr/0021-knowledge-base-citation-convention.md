# ADR-0021: Knowledge-Base-Citation-Konvention und Index-Records

**Status:** Accepted
**Datum:** 2026-06-19
**Serie:** 000X (Phase-C/D-Serie, session-protocol v3 SS6.13)
**Kontext-Quelle:** Master-Plan v3.1 Phase D; aect-security-checklist v2.1 Phase D; ADR-0017 (Chunker), ADR-0019 (gleiches Embedding-Modell Index/Query), ADR-0020 (EU-AI-Act-Stand)

## Kontext

Phase D braucht belegte Hinweise: jeder Compliance-/Stack-Hinweis im Output
zitiert eine echte Quelle (Master-Plan v3.1 Phase-D-Gate: Antworten mit
[1]/[2]-Citations; keine halluzinierte Artikel-Nummer). Vorhanden ist der
Lese-Pfad (ChromaRetriever, RetrievedChunk mit source_id) und der Chunker
(Chunk mit source_id + chunk_index). Es fehlte der Schreib-Pfad: aus
kuratierten Markdown-Quellen upsert-fertige Datensaetze mit Quellen-Metadaten
bauen.

RetrievedChunk traegt heute nur (text, source_id, score). source_id allein
ist ein technischer Anker, kein menschenlesbares Zitat ("DSGVO Art. 35").
Die menschenlesbare Citation muss also als Metadatum mitwandern.

## Entscheidung

1. **Provenance liegt als Front-Matter in der KB-Datei.** Jede Datei in
   knowledge_base/ beginnt mit einem `---`-umrahmten Block aus einfachen
   `key: value`-Zeilen. Pflichtschluessel: `source_id`, `title`, `citation`.
   Optional: `url`. Keine Listen, keine Verschachtelung.

2. **Front-Matter wird dependency-frei geparst** (eigener Mini-Parser, kein
   YAML-Lib). Begruendung: voll kontrolliertes, flaches Format; kein ungesehener
   Import (session-protocol v3 SS1.4); simplest-solution-first. Falls je
   reichhaltigeres Front-Matter noetig wird, auf den vorhandenen YAML-Loader
   (zone_thresholds.yaml) umstellen.

3. **IndexRecord (id, document, metadata) ist die upsert-Einheit.** id =
   Chunk.chunk_id ("<source_id>:<index>", ADR-0017). metadata = Front-Matter +
   chunk_index, ausschliesslich str-Werte (Chroma-Metadaten erlauben nur
   str/int/float/bool; wir bleiben bei str fuer Einheitlichkeit).

4. **build_index_records(kb_dir) ist offline und rein** (Datei-I/O + Chunking,
   kein Embedding, kein Chroma). Der eigentliche Upsert in eine laufende
   Collection (Docker, echtes MiniLM-Modell, collection.add) ist bewusst ein
   eigener Folge-Tag und nicht Teil dieser ADR.

## Sicherheit (aect-security-checklist v2.1 Phase D)

- **Records taggen (source_id):** erfuellt -- jeder Record traegt source_id im
  id-Prefix UND in metadata.
- **Provenance-Tag pro Dokument:** erfuellt -- citation/title/url als Metadaten.
- **Nur kuratierte, vertrauenswuerdige Quellen:** die beiden ersten KB-Files
  sind oeffentlicher Gesetzestext (DSGVO, KI-VO), kein firmenspezifischer
  Inhalt (IP-Trennung, interne Referenz (entfernt) SS5).
- **PII-Redaction vor Embedding (LLM08):** hier bewusst NICHT umgesetzt.
  Kuratierter oeffentlicher Rechtstext enthaelt keine personenbezogenen Daten.
  Die Redaction-Pflicht gilt dem User-Case-/Query-Pfad und etwaigen kuenftigen
  PII-haltigen Quellen; der Redactor wird als eigener Tag eingezogen (eigenes
  Comprehension-Gate-Thema "PII-Redaction"). Diese Auslassung ist eine
  begruendete Entscheidung, kein No-Op-Stub.

## Konsequenzen

- Der Lese-Pfad gibt heute noch keine Citation-Metadaten zurueck: RetrievedChunk
  hat kein metadata-Feld, ChromaRetriever._parse liest keine metadatas. Das
  Schliessen der Citation-Schleife im Output (RetrievedChunk + _parse +
  ChromaCollection.query-include um metadatas erweitern) ist ein bewusster
  Folge-Tag, kein Teil dieses Tages (Scope-Disziplin).
- Zeitliche Geltung der AI-Act-Transparenzpflicht wird NICHT in KB-Files
  dupliziert, sondern bleibt allein in ADR-0020 (eine Quelle der Wahrheit fuer
  volatile Fristen; KB-Content bleibt auf stabile Rechtssubstanz beschraenkt).
