# ADR-0051: Entfernung des Lifecycle-Status `integrated`

**Status:** Accepted
**Datum:** 2026-07-13
**Autor:** Anas

## Kontext

Das `CaseStatus`-Enum (Lifecycle-ADR, ADR-0045) hatte sieben Werte, darunter
`integrated` und `implemented`. Die beiden ueberlappen semantisch stark:
`integrated` ("in einen Prozess integriert") und `implemented` ("umgesetzt")
bezeichnen beide einen abgeschlossenen, produktiven Endzustand. In der
Ideenliste, im Board und im Status-Select stiftete `integrated` damit eine kaum
trennscharfe zusaetzliche Kategorie ohne eigenen Informationswert -- ein
Reviewer musste zwischen zwei praktisch gleichbedeutenden Endzustaenden waehlen.

## Entscheidung

`integrated` wird aus `CaseStatus` entfernt; der Lifecycle ist damit
sechsstufig (`submitted`, `in_review`, `approved`, `already_exists`, `rejected`,
`implemented`). Bestehende Rows mit `status = 'integrated'` werden beim naechsten
`_init_db` idempotent auf `implemented` gehoben -- eine reine Daten-Migration im
bestehenden Migrations-Block der SQLite-Adapter (PRAGMA-gestuetzt, kein ALTER
noetig). Ohne diese Migration wuerde `CaseStatus('integrated')` beim Lesen eines
Alt-Records eine `ValueError` werfen (fail loud). In den lokalen Demo-DBs gab es
zum Zeitpunkt der Aenderung 0 solche Rows; die Migration bleibt trotzdem
zwingend fuer die Reproduzierbarkeit auf beliebigen DBs.

`implemented` als Ziel (nicht `approved`) haelt die Lifecycle-Monotonie: ein
bereits produktiver Case wird nicht in einen frueheren Zustand zurueckgestuft.

## Konsequenzen

Die Aenderung beruehrt keine ROI-/Zonen-/Routing-Logik -- nur den Lifecycle.
Betroffen: `domain/types.py` (Enum), `StatusUpdateRequest`-Literal (`POST
/status` antwortet fuer `"integrated"` jetzt `422`), die SQLite-Migration, sowie
im Frontend `STATUS_CONFIG`, drei `STATUS_ORDER`-Listen und der `CaseStatus`-
Union-Typ. `openapi.json` und `api.generated.ts` sind neu erzeugt. Der bewusst
transitionsfreie Charakter des Lifecycles (jeder Zustand aus jedem setzbar)
bleibt unveraendert -- es entfaellt lediglich ein Zielwert.
