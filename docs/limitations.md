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
> als sie offenzulegen (Projekt-Prinzip "Grenzen offenlegen").

---

## 1. Hard-Threshold-Brittleness (Zonen-Grenzen)

**Befund (Tag 64/65, ADR-0031; Sample spaeter auf 24 Labels erweitert):**
Schon im ersten Sample wichen zwei der drei gelabelten Golden-Cases
(golden-001, golden-003) um exakt eine Zone von der Experten-Einschaetzung ab
-- jeweils die benachbarte Zone, nicht eine entfernte.

**Ursache:** Das Zonen-Modell zieht harte numerische Grenzen ueber
kontinuierliche Werte (ROI-Punkte, Composite-Score). Faelle nahe einer
Zonengrenze sind inhaerent ambig -- ob CALCULATED_RISK oder LIKELY_WIN
haengt von kleinen Eingabevariationen ab. Das Modell trifft eine
katagorische Entscheidung ueber ein Kontinuum.

**Konsequenz fuer die Eval-Interpretation:** Auf dem erweiterten Sample (24
gelabelte Cases) liegt die Agreement-Rate bei 9/24 (37,5 %). Die Off-by-one-
Mismatches an Zonengrenzen bleiben, sind aber jetzt Spezialfall eines
breiteren Befunds: Die Engine definiert LIKELY_WIN eng (Composite <= 4),
das Experten-Urteil "klarer High-Value-Fall" ist breiter -- Composite 5-7
landet als CALCULATED_RISK. Score-Breakdown-Diagnostik (ADR-0031) macht die
Grenzwert-Naehe je Case sichtbar.

**Interview-Relevanz:** "Warum liegt agreement_rate bei 37,5 %?" -- Antwort:
nachweisbares Schwellen-Artefakt (enge LIKELY_WIN-Grenze), kein Modell-Fehler.
Labels wurden nicht an die Engine angeglichen; die Divergenz ist das Ergebnis
der Analyse, nicht deren Symptom.

---

## 2. Praediktive Validitaet nicht erreichbar (privater Build)

**Was fehlt:** Echte praediktive Validitaet erfordert plan-vs.-actual-
Vergleich: Hat der Use Case den prognostizierten expected_benefit_eur
realisiert? Das misst der Monitoring-Teil des realen Prozesses.

**Warum strukturell nicht erreichbar:** Kein Produktiv-Einsatz, keine
Feedback-Schleife mit realisierten Ergebnissen. AECT misst Ex-ante-
Schaetzguete, nicht Ex-post-Treffsicherheit (Eval-Methodik: offen als
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

**Stand:** 25 Golden-Cases, davon 24 mit unabhaengigen Experten-Labels
(golden-004 bewusst unlabeled -- Vorfilter-Grenzfall). Erweitert von
urspruenglich 4 Cases (3 gelabelt).

**Konsequenz:** Agreement-Rate (9/24, 37,5 %) ist bei n=24 aussagekraeftiger
als bei n=3, bleibt aber kein Signifikanztest. Eignung: Eval-Mechanismus
demonstrieren und den Schwellen-Befund (enge LIKELY_WIN-Grenze) belastbarer
aufzeigen -- keine statistisch belastbare Treffsicherheits-Aussage.

**Weg nach vorne (nicht v1):** Cross-Rater-Agreement (zweiter Labeler) und
Pruefung, ob die LIKELY_WIN-Composite-Schwelle ans Experten-Urteil angepasst
werden sollte.

---

## 5. Laender-Scope

**Stand:** Alle Eval-Cases laufen mit country="DE" (Default run_eval()).

**Was nicht abgedeckt:** Multi-Country-Konfiguration ist in roi_config.toml
vorhanden und in der Domain-Test-Suite geprueft (test_roi.py,
test_zones.py) -- aber nicht im Eval-Runner-Lauf erfasst.

---

*Erstellt: Tag 67 (Phase E, Gate E->F). Aktualisieren bei neuen Befunden.*
