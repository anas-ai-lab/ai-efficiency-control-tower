# ADR-0024: RAG-gegruendete Compliance-Hinweise — Trigger, Citation-Determinismus, DI-Erweiterung

## Status
Accepted

## Kontext
ADR-0021/0022/0023 haben Schreib- und Lese-Pfad fuer Citation-Metadaten
geschlossen: `RetrievedChunk` traegt jetzt `metadata` mit `citation`/`title`/
`url`. Master-Plan v3.1 Phase D verlangt die eigentliche Verdrahtung: ein
Compliance-Hinweis im Output zitiert eine echte Quelle (`[1]`, `[2]`), keine
halluzinierte Artikel-Nummer. Bisher gab es dafuer keinen Aufrufer im
Service -- `RetrieverPort` war seit ADR-0014 unbenutzter Kontrakt.

## Entscheidung

1. **Retrieval-Trigger ist regelbasiert, nicht aus Freitext.** Zwei feste
   Queries: Transparenz (EU AI Act Art. 50) immer, DSFA (DSGVO Art. 35)
   zusaetzlich wenn `case.result.routing.risk_flags` nicht leer ist. Dieses
   Feld existiert bereits (`domain/routing.py`, `_collect_risk_flags`) und
   wird bereits in `_build_technical_detail()` ausgegeben -- keine zweite,
   lose PII-Schwelle in der neuen Methode (eine Quelle der Wahrheit, gleiche
   Begruendung wie die in ADR-0023 verworfene Citation-Lookup-Tabelle).
2. **Citations werden deterministisch aus dem Retrieval gebaut, nicht aus
   der LLM-Antwort geparst.** Die App nummeriert die Treffer (`[1]`, `[2]`,
   ...) und kennt `metadata["citation"]` vor dem LLM-Call. Das LLM
   referenziert im Fliesstext nur die Nummer. Einzige Methode, die
   "keine halluzinierte Artikel-Nummer" strukturell statt durch
   Prompt-Disziplin allein garantiert.
3. **Kein LLM-Call ohne Treffer.** Liefert das Retrieval ueber alle Queries
   zusammen null Chunks, bricht `generate_compliance_hints()` vor dem
   LLM-Call ab (`hint_text=None`, `citations=()`). Spart Kosten, verhindert
   ungegruendete Hinweise.
4. **`TriageService` bekommt `retriever: RetrieverPort` als Pflicht-
   Parameter**, kein Default (Begruendung analog `llm: LLMPort`, Modul-
   Docstring `service.py`). `get_retriever_port()` liefert in der DI heute
   `MockRetriever` -- `ChromaRetriever` ist bewusst noch NICHT verdrahtet
   (braucht laufenden Collection-Client + Embedder-Wahl, ADR-0016/0018,
   eigener Folge-Tag).
5. **v1-Prompt liefert Fliesstext, kein JSON-Schema** -- konsistent mit
   `sharpen_use_case/v1` und `propose_solution/v1`. Strukturierte
   Validierung ist hier ohnehin nicht noetig, da die Quellenliste nicht aus
   der LLM-Antwort geparst wird (Punkt 2).
6. **Persistenz auf `SubmittedCase` und Report-Integration bewusst NICHT
   heute.** Gleiches Muster wie `sharpen_case`/`propose_solution`: erst
   eigenstaendiger Endpoint, Persistenz kam dort erst Tag 42 (ADR-0012).

## Alternativen erwogen

- **PII-/Risiko-Schwelle direkt aus `UseCaseInput`-Feldern neu bauen**
  (`contains_pii`, `data_classification`, `regulatory_pressure` einzeln
  pruefen): verworfen. Wuerde dieselbe Entscheidung zweimal treffen --
  `domain/routing.py` hat sie bereits getroffen und getestet. Zwei Quellen
  der Wahrheit fuer dieselbe Risikoeinschaetzung sind fehleranfaelliger als
  eine.
- **Citations aus der LLM-Antwort per Regex extrahieren** (`[1]`, `[2]` im
  Text suchen, gegen eine separate Liste aufloesen): verworfen. Die
  Nummerierung im Fliesstext ist ohnehin von der App vorgegeben (Punkt 2) --
  ein Parser der LLM-Antwort waere zusaetzliche Fehlerflaeche ohne
  Mehrwert, und ein vom LLM frei erfundenes `[3]` ohne Entsprechung waere
  nicht abfangbar.
- **`ChromaRetriever` direkt heute verdrahten statt `MockRetriever`**:
  verworfen. Ein Folge-Tag (Embedder-Wahl + laufender Container in der DI)
  ist ein eigener Schritt, kein Anhaengsel an die Service-/Prompt-Logik
  dieses Tages (Scope-Disziplin, session-protocol v3 SS5.2 Punkt 6).

## Konsequenzen

- Additiv auf Domain- und bestehenden Adapter-Code: `domain/routing.py`,
  `adapters/rag/retriever.py`, `adapters/in_memory/retriever.py`
  unveraendert.
- Breaking auf `TriageService.__init__` (neuer Pflicht-Parameter
  `retriever`) -- betrifft alle 7 Konstruktions-Stellen in Tests plus
  `dependencies.py`; mechanisch nachgezogen, kein Verhaltensunterschied an
  bestehenden Endpoints (`MockRetriever` ist seiteneffektfrei).
- Offen fuer einen Folge-Tag: `ChromaRetriever`-DI-Verdrahtung,
  Persistenz von `compliance_hints` auf `SubmittedCase`, Einbau in
  `/report` (analog ADR-0012-Muster fuer `sharpen_case`/`propose_solution`).

## Datum
2026-06
