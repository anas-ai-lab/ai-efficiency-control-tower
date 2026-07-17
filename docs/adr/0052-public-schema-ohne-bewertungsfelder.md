# ADR-0052: Public-Schema ohne Bewertungsfelder statt genullter Felder

**Status:** Accepted
**Datum:** 2026-07-17
**Autor:** Anas

## Kontext

`GET /cases` (Ideenliste) und `GET /cases/{id}` (Fall-Detail) sind im Zugriff
public (kein `require_admin`) -- ein anonymer Einreicher soll den Stand seines
eigenen Falls lesen koennen (E9/SDR-0003). Welche Inhalte er dabei sieht, wurde
dreimal anders beantwortet:

1. **V4-P7** (`2c1d440`/`5dfc58e`): die volle Bewertung war sofort anonym
   sichtbar -- Zone, Nettonutzen, Scores, Report.
2. **Erste Korrektur:** die Bewertung wurde an die Board-Entscheidung gekoppelt
   (`reviewer_decision != PENDING`). Vor der Entscheidung standen `triage` und
   `report` auf `null`, ein zusaetzliches Feld `assessment_visible` sagte dem
   Frontend, ob es "wird geprueft" oder "—" anzeigen soll. Nach der Entscheidung
   war der volle Report weiterhin anonym lesbar.
3. **Jetzt (V4.1-S8):** Nicht-Admins sehen ausschliesslich die beim Einreichen
   erfassten Grunddaten, den Lifecycle-Status und die AI-Board-Entscheidung samt
   Begruendung.

Auslöser fuer Schritt 3 ist das Rollenmodell aus SDR-0003 (Entscheidung 7): die
Bewertung ist **Entscheidungsgrundlage des Boards**, kein Feedback an den
Einreicher. Der Einreicher bekommt das Ergebnis, nicht die Herleitung.

Die Loesung aus Schritt 2 hatte ueber den Inhalt hinaus ein strukturelles
Problem: die Bewertungsfelder standen weiterhin im Response-Schema, nur eben mit
`null` gefuellt. Ein `null`-Feld verraet, dass es die Groesse gibt; und jedes
neu ergaenzte Bewertungsfeld war automatisch Teil des public Vertrags, solange
niemand daran dachte, es ebenfalls zu maskieren. Die Sichtbarkeit hing an einer
Laufzeit-Bedingung (`visible = is_admin or ...`) verteilt ueber zwei Mappings --
sie war nie am Typ ablesbar.

## Entscheidung

Wir serialisieren **zwei getrennte Response-Schemas je Route** und waehlen
anhand von `is_admin_request` aus:

| Route | Nicht-Admin | Admin |
|---|---|---|
| `GET /cases` | `PublicCaseSummary` | `CaseSummary` |
| `GET /cases/{id}` | `PublicCaseDetailResponse` | `CaseDetailResponse` |

Die Public-Klassen **fuehren die Bewertungsfelder nicht** -- sie sind nicht
`null`, sie existieren auf der Klasse nicht. Es gibt damit kein Attribut, das ein
Mapping versehentlich fuellen koennte. Die Admin-Klassen erben von den
Public-Klassen und ergaenzen die Bewertung; `response_model` ist die Union beider
(`list[CaseSummary] | list[PublicCaseSummary]` bzw.
`CaseDetailResponse | PublicCaseDetailResponse`).

Beide Public-Klassen tragen `model_config = ConfigDict(extra="forbid")`. Das ist
hier **kein Stilmittel, sondern tragende Mechanik**: Pydantic entscheidet die
Union anhand der Feld-Anwesenheit. Ohne `forbid` wuerde ein Admin-Dict auch gegen
das Public-Schema validieren (ueberzaehlige Felder waeren erlaubt) und die Union
waere mehrdeutig. Mit `forbid` ist sie in beide Richtungen eindeutig: ein
Admin-Dict scheitert am Public-Schema (Extra-Felder), ein Public-Dict scheitert
am Admin-Schema (fehlende Pflichtfelder).

Die Board-Entscheidung wandert in ein eigenes Feld `decision`
(`CaseDecisionResponse`), das beide Schichten fuehren -- fuer Nicht-Admins ist es
der einzige Board-Output. Es ist `null`, solange `reviewer_decision` `PENDING`
ist (kein Pseudo-Objekt mit `"pending"`).

## Begründung

| Alternative | Warum verworfen |
|---|---|
| **Felder auf `null` setzen** (Loesung aus Schritt 2) | Ein `null` steht weiter im JSON und verraet die Existenz der Groesse. Neue Bewertungsfelder landen automatisch im public Vertrag, bis jemand aktiv daran denkt -- das Vergessen ist still und faellt erst bei einem Leak auf. Die Sichtbarkeit ist eine Bedingung im Mapping, kein Typ. |
| **`response_model_exclude` / dynamisches Feld-Filtern** | Der Filter ist Laufzeit-Verhalten und steht nicht im Vertrag: `openapi.json` (Single Source fuer `api.generated.ts`, CI-geprueft) zeigt weiter alle Felder, das Frontend bekaeme Typen mit Feldern, die nie ankommen. Ein vergessener Eintrag in der exclude-Liste leakt still. |
| **Zwei getrennte Routen** (`/cases/{id}` public + `/admin/cases/{id}`) | Verdoppelt Routing-, Rate-Limit- und Testflaeche fuer denselben Read. Der Client muesste seinen Auth-Zustand kennen, um die richtige URL zu waehlen -- heute entscheidet die Antwort, nicht die Erwartung des Clients (siehe `lib/case-view.ts`). |
| **`response_model=None` + reine Rueckgabe-Annotation** | Waere die simpelste Absicherung (FastAPI serialisiert dann die konstruierte Instanz ungefiltert), kostet aber das Response-Schema in `openapi.json`. Die CI erzwingt `openapi.json` -> `api.generated.ts`; der Vertrag waere danach leer und das Frontend typlos. |

## Konsequenzen

**Positiv:**

- Ein Bewertungs-Leak ueber diese Routen ist **strukturell ausgeschlossen**, nicht
  nur durch eine korrekte Bedingung verhindert. Ein durchgereichtes
  Bewertungsfeld scheitert laut (`extra="forbid"`), statt still mitzuwandern.
- Die Asymmetrie ist im Vertrag dokumentiert: `openapi.json` fuehrt beide Schemas
  als `anyOf`, `api.generated.ts` erbt die Union.
- `assessment_visible` entfaellt ersatzlos. Das Feld existierte nur, um "fuer dich
  verborgen" auszudruecken -- Verbergen ist jetzt Abwesenheit. Ein Feld, das
  immer `true` waere, waere schlechter als keins.

**Negativ / Trade-offs:**

- Das Frontend muss von der schmalen auf die volle Sicht **schliessen**, statt sie
  anzunehmen: `lib/case-view.ts` (`isAdminSummary`/`isAdminDetail`) prueft die
  Anwesenheit eines Bewertungsfeldes. Reine Admin-Seiten (Board, Monitoring)
  verengen ueber `adminSummaries()` fail-loud.
- Die Union-Aufloesung haengt an `extra="forbid"` und an der Tatsache, dass
  `triage`/`report` im Admin-Schema **required** sind. Beides ist Mechanik, kein
  Stil (siehe unten).
- Der Einreicher erfaehrt nie, *warum* abgelehnt wurde, ausser das Board schreibt
  es in `reviewer_note` -- die Qualitaet dieses Freitexts traegt die gesamte
  Rueckmeldung (`docs/known_limitations.md` #30).

**Was hier bewusst NICHT "repariert" werden darf:**

Die folgenden Punkte sehen wie Inkonsistenzen aus und sind Absicht. Wer sie
glattzieht, oeffnet das Leck wieder:

- **Zwei Schemas fuer eine Route sind kein Duplikat.** Sie zu einem Schema mit
  optionalen Feldern zusammenzufuehren ("ist doch dasselbe, nur mal `null`")
  stellt exakt den Zustand aus Schritt 2 wieder her.
- **`extra="forbid"` auf den Public-Klassen ist nicht entfernbar.** Ohne das Flag
  wird die Union mehrdeutig und ein Admin-Dict kann als Public-Schema
  serialisiert werden -- ohne Fehler.
- **`triage`/`report` duerfen im Admin-Schema keine Default-Werte bekommen.**
  Waeren sie optional, wuerde ein Public-Dict gegen das Admin-Schema validieren
  und die Union kippt.
- **Die anonyme Ideenliste ist nicht "kaputt", weil Zone/Nettonutzen fehlen.**
  Sie hat diese Spalten nicht mehr; der Zonenfilter, die Netto-Sortierung und die
  CSV-Bewertungsspalten sind Admin-UI.

Der rekursive Guard-Test
`tests/adapters/api/test_case_detail.py::test_case_detail_anonymous_carries_no_assessment_field`
prueft das gesamte anonyme JSON gegen eine Liste von Bewertungs-Schluesseln, die
bewusst breiter ist als das aktuelle Schema (inkl. Altnamen wie
`assessment_visible`). Der Playwright-Smoke
`e2e/public-visibility.spec.ts` prueft dasselbe an der gerenderten Oberflaeche.

**Neutral / Folgeentscheidungen:**

- Die Bewertungslogik selbst (ROI, Zonen, Routing, Composite) ist unberuehrt --
  die Entscheidung betrifft ausschliesslich Sichtbarkeit und Serialisierung.
- Die Architektur-Skizze bleibt aussen vor: sie hat einen eigenen Admin-Endpoint
  (`GET`/`POST` beide `require_admin`) und war nie Teil des public Read.
