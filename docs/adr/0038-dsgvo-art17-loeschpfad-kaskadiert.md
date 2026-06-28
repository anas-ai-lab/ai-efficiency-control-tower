# ADR-0038: DSGVO Art. 17 Loeschpfad (kaskadiert)

**Status:** Accepted
**Datum:** 2026-06-28
**Autor:** Anas

## Kontext

DSGVO Art. 17 (Recht auf Loeschung) verlangt, dass personenbezogene Daten auf
Verlangen tatsaechlich entfernt werden. AECT persistiert Cases im Repository
(SQLite) und taggt Wissensbasis-Records im Vektor-Store (ChromaDB) mit einem
`source_id` -- der Port-Kontrakt nennt `source_id` ausdruecklich als
"Loesch-Tag fuer gezielte Entfernung" (ports/retriever.py). Bisher gab es
keinen Loeschpfad.

## Entscheidung

Wir implementieren einen kaskadierten Loeschpfad: `RepositoryPort.delete(_async)`
(SQLite + InMemory), `RetrieverPort.delete_by_source_id` (ChromaRetriever real
via `collection.delete(where={"source_id": ...})`, Mock/BM25/Wrapper als
Delegation bzw. No-op) und ein Application-Service `delete_case(case_id)`, der
beide Stores raeumt und das Loesch-Ereignis als Audit-Log emittiert. Die Route
`DELETE /cases/{case_id}` (Auth, Rate-Limit 10/min) liefert 204, fehlende IDs
204->404 ueber `CaseNotFoundError`.

Echte Loeschung, KEIN Soft-Delete-Flag und KEINE Anonymisierung.

## Begruendung

**Warum kaskadiert?** Art. 17 verlangt tatsaechliche Loeschung in allen Stores,
nicht nur in der Primaerquelle. Der Vektor-Store-Schritt ist best-effort und
faellt nicht hart (die Repository-Loeschung darf nicht zurueckgedreht werden,
nur weil ChromaDB kurz nicht erreichbar ist). Cases liegen aktuell nur im
Repository, nicht im Vektor-Store -- der ChromaDB-Schritt ist daher eine
vorausschauende Absicherung, falls Case-Inhalte spaeter eingebettet werden.

**Warum loggen statt das Loesch-Log loeschen?** Der Audit-Trail (Datum +
case_id, OHNE personenbezogenen Inhalt) ist nach Art. 5(2) (Rechenschaftspflicht)
erforderlich -- das Loesch-Ereignis selbst ist KEINE personenbezogene
Information und muss erhalten bleiben, gerade weil die Daten geloescht wurden.

| Alternative | Warum verworfen |
|---|---|
| Soft-Delete-Flag (`is_deleted`) | Daten bleiben physisch erhalten -- erfuellt Art. 17 nicht. |
| Anonymisierung statt Loeschung | Re-Identifikationsrisiko bleibt; bei Freitext-Cases nicht belastbar anonymisierbar. Echte Loeschung ist eindeutig. |
| Nur SQLite loeschen | Laesst potentielle Vektor-Store-Kopien stehen -- unvollstaendig gegenueber Art. 17. |

## Konsequenzen

**Positiv:**
- Vollstaendiger, testbarer Loeschpfad ueber alle Stores; Audit-Trail erhalten.
- `source_id`-Tag (bereits beim Indexing geschrieben) wird wie vorgesehen genutzt.

**Negativ / Trade-offs:**
- `delete_by_source_id` erweitert den `RetrieverPort` um eine mutierende
  Operation -- der Port ist nicht mehr rein lesend. Bewusst akzeptiert: der
  Kontrakt nannte `source_id` schon als Loesch-Tag; alle Implementierungen
  (inkl. Wrapper Hybrid/Reranker) tragen die Delegation mit.
- ChromaDB-Loeschung ist best-effort -- ein stiller Store-Ausfall wird geloggt,
  nicht eskaliert. Akzeptabel, da Cases derzeit nicht im Vektor-Store liegen.

**Neutral / Folgeentscheidungen:**
- Kein GET /cases/{id}-Detail-Endpoint vorhanden -- Tests belegen die Entfernung
  ueber ein zweites DELETE (404).
- CORS `allow_methods` um DELETE ergaenzt; Logging-Allowlist um `deleted_at`.
