# ADR-0050: Optionaler Implementierungsansatz und Vor-Bewertungs-Zustand

**Status:** Accepted
**Datum:** 2026-07-13
**Autor:** Anas

## Kontext

Der Einreicher eines Use Case kennt den Implementierungsansatz oft noch nicht --
das ist eine Loesungs-Entscheidung, die haeufig erst der Admin/das Board trifft.
Bisher war `implementation_approach` ein Pflichtfeld: ohne Angabe keine
Einreichung. Zugleich ist das Feld load-bearing fuer die Bewertung -- die
Komplexitaet (1-5) und damit Composite-Score, Zone und Routing leiten sich
ausschliesslich daraus ab (`COMPLEXITY_BY_APPROACH`). Ein einfacher Default oder
ein stiller Fallback waere ein erfundener Aufwands-Score (verletzt "fail loud")
und wuerde die bestehende Formel fuer einen Fall aendern, der vorher gar nicht
existierte.

## Entscheidung

`implementation_approach` wird optional (`ImplementationApproach | None`, default
`None`). Ein Case ohne Ansatz durchlaeuft **keine** Regel-Pipeline (kein
ROI/Vorfilter/Routing/Composite/Zone), sondern landet in einem expliziten
Vor-Bewertungs-Zustand `TriageResult.evaluation_pending` -- alle evaluativen
Schichten sind `None`, `passed_vorfilter`/`is_actionable` sind `False`. API und UI
behandeln ihn wie den bestehenden Vorfilter-Fail-Zustand ("noch nicht bewertet",
kein 5xx, kein Fallback-Wert). Ein dedizierter Admin-Endpoint
(`POST /cases/{id}/implementation-approach`) traegt den Ansatz nach: er mutiert
den `use_case_json`-Blob und ruft `evaluate_use_case()` **einmal vollstaendig**
neu auf (kein Teil-Patch) -- Eingaben und Bewertung stammen aus einem
konsistenten Lauf und werden atomar persistiert (`reevaluate`, F-011-Muster).

Dies ist eine bewusste, dokumentierte Ausnahme von "keine Score-Aenderung an
bestehenden Formeln": Es aendert **keine** Formel, sondern fuehrt einen neuen
Eingangszustand fuer einen neuen Falltyp ein (Cases ohne Ansatz gab es vorher
nicht). Die Scores eines nachgetragenen Case sind identisch zu einem Case, der
den Ansatz von Anfang an hatte (gleiche `use_case` -> gleiche Pipeline).

## Konsequenzen

`TriageResult.vorfilter/routing/feasibility` werden nullable; alle
bewertungsabhaengigen Konsumenten (Report-/Compliance-Bausteine, Explainability)
sind gegen den Vor-Bewertungs-Zustand gegated -- die Endpoints `POST /report` und
`POST /compliance-hints` antworten fuer einen pending Case mit `409` statt
abzustuerzen. `evaluation_pending` erscheint zusaetzlich in `TriageResponse`,
`CaseDetailResponse` und `CaseSummary`, damit die UI den Zustand von "wird vom
Board geprueft" unterscheiden kann. Aeltere persistierte Records ohne das Feld
deserialisieren als `evaluation_pending=False` (abwaertskompatibel). Der Preis:
eine zusaetzliche `None`-Verzweigung in mehreren Read-Pfaden statt einer
garantiert befuellten Bewertung.
