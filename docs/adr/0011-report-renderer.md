# ADR-0011: Zweischichtiger Report-Renderer als Regel-Schicht

## Status
Accepted

## Kontext

Master-Plan v3.1 (Phase C) und das Projekt-Zielbild fordern einen
zweischichtigen Report (Business-Zusammenfassung fuer Entscheider +
technische Detailebene fuer Reviewer), "maschinell als striktes JSON
validiert".

ADR-0006 haelt als offenen Punkt fest: strikte Pydantic-Validierung von
LLM-Output folgt, sobald ein Provider strukturierte (JSON-)Antworten
liefert. MockLLMAdapter liefert aktuell nur `"[mock-response] {last_user}"`
-- ein Report, der ein striktes JSON-Schema *aus dem LLM* parsen wuerde,
waere mit dem Mock nicht testbar (Mock-First, Tag 35).

## Entscheidung

**1. Report v1 ist eine reine Regel-Schicht ueber TriageResult.** Kein
LLM-Call. `TriageService.generate_report()` leitet `BusinessSummary` und
`TechnicalDetail` deterministisch aus den bereits vollstaendig typisierten
Domain-Ergebnissen ab (Vorfilter, ROI, Composite, Zone, Routing,
Feasibility). Das "strikte JSON" aus dem Projekt-Zielbild ist der
Pydantic-`response_model` der Route -- erfuellt, ohne auf LLM-JSON-Parsing
zu warten.

**2. sharpen_case()- und propose_solution()-Ergebnisse werden nicht
persistiert.** `POST /cases/{id}/report` nimmt `sharpened_text` /
`proposal_text` optional im Request-Body entgegen und reicht sie
unveraendert in `business_summary.sharpened_text` /
`technical_detail.proposal_text` durch. Persistenz dieser Narrative auf
`SubmittedCase` waere eine Schema-Aenderung mit Auswirkung auf Repository,
SQLite-Adapter und mehrere Bestandstests -- nicht additiv, nicht Scope von
Tag 41.

**3. Zwei-Layer-Aufteilung:**
- `business_summary`: title, zone, is_actionable, recommendation,
  expected_benefit_eur, summary_text (deterministisch formuliert),
  sharpened_text.
- `technical_detail`: vollstaendige Rohwerte aus Vorfilter, Composite,
  Feasibility, Routing, ROI, proposal_text.

`zone`/`expected_benefit_eur`/`composite_*`/`roi_*` sind `None`, wenn
`passed_vorfilter` `False` ist (TriageResult-Invariante aus
domain/pipeline.py).

## Konsequenzen

Positiv: additiv, kein neuer Prompt, kein Cost-Logging-Eintrag, mit
MockLLMAdapter und Azure-Adapter identisch (Report ist providerunabhaengig).
Volle Coverage ohne Azure-Credentials.

## Offene Punkte

- **LLM-generierter Fliesstext-Report mit strikter JSON-Validierung**
  (ADR-0006-Punkt): eigener Folge-Tag, sobald ein Provider strukturierte
  Antworten liefert oder ein Function-Calling-Schema fuer den Report
  definiert ist.
- **Persistenz von sharpened_text/proposal_text auf SubmittedCase**: eigener
  Tag, falls eine Case-Detail-Ansicht (Phase F Frontend) das verlangt --
  betrifft Repository-Interface + SQLite-Adapter + Bestandstests.
- **summary_text-Formulierung** ist bewusst minimal/deterministisch (kein
  SCHREIBSTIL.md-Anspruch -- das ist interner API-Output, kein
  Praesentationstext). Falls der Report spaeter direkt im Frontend gerendert
  wird: Formulierung ueberarbeiten.
