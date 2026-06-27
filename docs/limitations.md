# AECT v1 — Bekannte Grenzen der Validierung

> **Scope dieses Dokuments:** ausschliesslich die Phase-E-EVALUATION
> (Eval-Gate E->F, Tag 67). Die kanonische, projektweite Limitations-Liste ist
> `docs/known_limitations.md` (14 Punkte). Drei Punkte hier ueberschneiden sich
> bewusst mit dort (#1 Hard-Threshold = known #2, #2 Praediktive Validitaet =
> known #1, #4 Golden-Sample = known #3) -- dieses Dokument haelt die
> Eval-Gate-Provenienz fest, known_limitations.md den Gesamtstand. Bei Konflikt
> gilt known_limitations.md.
>
> Limitationen zu verbergen untergraebt die Glaubwuerdigkeit staerker
> als sie offenzulegen (interne Referenz (entfernt) SS7).

---

## 1. Hard-Threshold-Brittleness (Zonen-Grenzen)

**Befund (Tag 64/65, ADR-0031):** Zwei der drei gelabelten Golden-Cases
(golden-001, golden-003) weichen um exakt eine Zone von der Experten-
Einschaetzung ab -- jeweils die benachbarte Zone, nicht eine entfernte.

**Ursache:** Das Zonen-Modell zieht harte numerische Grenzen ueber
kontinuierliche Werte (ROI-Punkte, Composite-Score). Faelle nahe einer
Zonengrenze sind inhaerent ambig -- ob CALCULATED_RISK oder LIKELY_WIN
haengt von kleinen Eingabevariationen ab. Das Modell trifft eine
katagorische Entscheidung ueber ein Kontinuum.

**Konsequenz fuer die Eval-Interpretation:** Agreement-Rate allein (1/3)
unterschaetzt die Systemguete. Die Mismatch-Faelle sind Off-by-one-unit,
keine groben Fehlurteile. Score-Breakdown-Diagnostik (ADR-0031) macht
Grenzwert-Naehe sichtbar.

**Interview-Relevanz:** "Warum liegt agreement_rate bei 1/3?" -- Antwort:
nachweisbares Grenzwert-Artefakt, kein Modell-Fehler. Der Befund ist das
Ergebnis der Analyse, nicht deren Symptom.

---

## 2. Praediktive Validitaet nicht erreichbar (privater Build)

**Was fehlt:** Echte praediktive Validitaet erfordert plan-vs.-actual-
Vergleich: Hat der Use Case den prognostizierten expected_benefit_eur
realisiert? Das misst der Monitoring-Teil des realen Prozesses.

**Warum strukturell nicht erreichbar:** Kein Produktiv-Einsatz, keine
Feedback-Schleife mit realisierten Ergebnissen. AECT misst Ex-ante-
Schaetzguete, nicht Ex-post-Treffsicherheit (interne Referenz (entfernt) SS7: offen als
Limitation dokumentiert, nicht versteckt).

---

## 3. Eval-Scope: nur deterministische Regel-Schicht

**Was getestet wird:** Phase-E-Evaluation deckt ausschliesslich
evaluate_use_case() (ROI-Modell, Zonen-Logik, Routing-Rules).
Kein LLM-Aufruf findet im Eval-Lauf statt.

**Was nicht getestet wird:**
- Qualitaet der LLM-Schaerfung (sharpened_title, improvement_suggestions)
- Sinnhaftigkeit von Loesungsvorschlaegen (propose_solution)
- Relevanz und Korrektheit der Compliance-Hinweise
- RAG-Retrieval-Qualitaet (Praezision/Recall)

**Begruendung:** LLM-Output-Qualitaet erfordert einen separaten
Evaluationsrahmen (nicht-deterministisch, Prompt-Versionierung, Modell-
Abhaengigkeit). Phase-F/post-v1-Aufgabe, keine Luecke in Phase E.

---

## 4. Groesse des Golden-Case-Sets

**Stand:** 4 Golden-Cases, davon 3 mit unabhaengigen Experten-Labels
(golden-004 bewusst unlabeled -- Vorfilter-Grenzfall).

**Konsequenz:** Agreement-Rate hat breites Konfidenz-Intervall. Eignung:
Eval-Mechanismus demonstrieren, Brittleness-Befund aufdecken -- keine
statistisch belastbare Stichprobe.

**Weg nach vorne (nicht v1):** 10-20 weitere kuratierte Cases wuerden
einen repraesentativeren Wert liefern.

---

## 5. Laender-Scope

**Stand:** Alle Eval-Cases laufen mit country="DE" (Default run_eval()).

**Was nicht abgedeckt:** Multi-Country-Konfiguration ist in roi_config.toml
vorhanden und in der Domain-Test-Suite geprueft (test_roi.py,
test_zones.py) -- aber nicht im Eval-Runner-Lauf erfasst.

---

*Erstellt: Tag 67 (Phase E, Gate E->F). Aktualisieren bei neuen Befunden.*
