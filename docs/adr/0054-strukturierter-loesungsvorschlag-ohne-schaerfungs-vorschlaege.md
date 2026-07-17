# ADR-0054: Strukturierter Lösungsvorschlag, Schärfungs-Vorschläge ersatzlos

**Status:** Accepted
**Datum:** 2026-07-17
**Autor:** Anas

## Kontext

Der LLM-generierte Lösungsvorschlag (`propose-solution`, Prompt v3, Schema
`SolutionProposalV2`) lieferte für beide Zielgruppen unbrauchbare Fließtext-Wände.
Das Schema hatte genau zwei Freitext-Felder — `solution_business` (max. 1500
Zeichen) und `solution_technical` (max. 3000 Zeichen). Die Struktur stand
ausschließlich im Prompt („ein Absatz", „skizziere als Fließtext"), und ein Prompt
ist keine Garantie: das Modell füllte die erlaubte Länge aus. Ergebnis: die
Geschäftsleitung bekam einen Absatz, den sie nicht las, und die technische Fassung
war eine Textwüste ohne erkennbare Gliederung.

Der Vokabular-Guard (`domain/solution_guard`) lief nur über `solution_business`.

Zusätzlich hängte die Schärfung (`sharpen_use_case`, Prompt v3,
`SharpenedContentV2`) an jedes Ergebnis bis zu drei `improvement_suggestions`
(`bezugsfeld`/`vorschlag`/`hebel`). Diese nachgelagerten Vorschläge trugen keinen
Entscheidungswert: sie wiederholten, was der Intake ohnehin erfragt, und ihr
`hebel` bezifferte Bewertungsgrößen, die die eigentliche Schärfung nicht berührt.

## Entscheidung

Wir strukturieren beide Lösungs-Ebenen im Schema statt nur im Prompt
(`SolutionProposalV3`, Prompt v4) und entfernen die Schärfungs-Vorschläge
ersatzlos (Prompt v4, `SharpenedContentV2` ohne `improvement_suggestions`).

Management-Ebene: `management_summary` (2–3 Sätze, max. 700 Zeichen) +
`management_benefits` (max. 3 Stichpunkte à max. 200 Zeichen).
Technik-Ebene: `architecture_summary` (2–3 Sätze) + `components` / `data_flow` /
`integration_points` / `open_assumptions` (Stichpunkt-Listen).

Der Vokabular-Guard läuft ab jetzt über `management_summary` UND
`management_benefits` — die Stichpunkte sind ebenso Management-Text.

Die Struktur wird als JSON in den **bestehenden** Spalten persistiert
(`solution_business`, `proposal_text`) — keine neuen Spalten, keine Migration.
`application/solution_content.py` kapselt Lesen/Schreiben/Rendern.

Die eigentliche Schärfung (Diff, Draft/Accept/Reject) und der Zahlen-Validator
(`domain/sharpening_guard`) bleiben unangetastet.

## Begründung

Die Längen-Obergrenzen sind der Kern der Entscheidung: `max_length=700` auf der
Summary und `max_length=200` je Stichpunkt machen die „keine Absatz-Wände"-Regel
zur Schema-Invariante. Verletzt das Modell sie, greift die bestehende
Retry-/Fail-loud-Mechanik (genau ein Korrektur-Retry, dann 422) — dieselbe, die
schon Zahlen-Guard und Vokabular-Guard trägt. LLM-Output bleibt untrusted; eine
Prompt-Instruktion allein ist keine Durchsetzung.

| Alternative | Warum verworfen |
|---|---|
| Nur den Prompt schärfen, Schema (2 Freitext-Felder) lassen | Genau das war der Ist-Zustand — v3 wies bereits auf „ein Absatz" hin und bekam trotzdem die Wand. Ohne Schema-Grenze gibt es keinen Durchsetzungspunkt. |
| Neue Spalten für die Struktur, Textspalten weiter mit gerendertem Text füllen | Migration + Dual-Write + zwei Wahrheiten, die driften können. Der einzige Nutzen wäre Legacy-Eindeutigkeit — die liefert der tolerante Reader billiger. |
| Guard nur auf `management_summary` (wie bisher) | Kleinerer Diff, aber die Nutzen-Stichpunkte wären ungeprüft: „Die Erfassung läuft künftig per OCR" wäre durchgerutscht. Der Guard ist an die Zielgruppe gebunden, nicht an ein Feld. |
| Schärfungs-Vorschläge behalten und stattdessen verbessern | Der Befund ist nicht „schlecht formuliert", sondern „trägt keine Entscheidung". Ein besserer Prompt hätte die Floskeln nur teurer gemacht. |

## Konsequenzen

**Positiv:**
- Beide Ebenen sind im Schema strukturiert; die Anzeige rendert Summary + Listen
  ohne den Text zu parsen (`components/solution-view.tsx`, geteilt zwischen
  Draft-Modal und Report).
- Die „keine Absatz-Wände"-Regel ist durchgesetzt, nicht erbeten.
- Der Vokabular-Guard deckt die gesamte Management-Ebene ab.
- Keine Migration; Alt-Cases bleiben lesbar.

**Negativ / Trade-offs:**
- Die Spalten `solution_business` / `proposal_text` tragen jetzt zwei Formate
  (JSON neu, Klartext legacy). Der Reader entscheidet am Inhalt — ein Klartext,
  der zufällig valides JSON-Objekt mit passendem Schlüssel wäre, würde
  fehlinterpretiert. Praktisch ausgeschlossen, aber es ist eine Heuristik.
- Legacy-Cases zeigen nur ihr Summary-Feld, ohne Stichpunkte — sichtbar ärmer als
  frisch erzeugte. Bewusst: kein Backfill für ein Demo-Artefakt.
- Der Skizzen-Prompt braucht jetzt einen Rück-Renderer
  (`render_technical_text`), weil er Text erwartet, kein JSON.
- Ein strengeres Schema heißt mehr mögliche Retries (min. 2 Komponenten, min. 2
  Datenfluss-Schritte). Bewusst: eine leere Komponenten-Liste ist keine
  technische Fassung.

**Neutral / Folgeentscheidungen:**
- Prompt-Versionen v1/v2 (propose_solution) und v3 (beide Familien) bleiben als
  Dateien liegen (Versionierung, `application/prompts.py`); Default ist v4.
- Die Sprache des LLM-Outputs läuft unverändert über `with_language()`
  (V4.1-S6): die Prompt-Dateien sind deutsch, bei `lang="en"` wird die
  EN-Instruktion vorangestellt. Die Feldnamen sind sprachunabhängig — kein
  Locale-Durchgriff nötig, die neuen Prompts erben den Mechanismus.
