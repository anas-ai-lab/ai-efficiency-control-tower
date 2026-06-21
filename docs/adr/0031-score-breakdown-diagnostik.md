# ADR-0031: Score-Breakdown als separate Diagnostik-Schicht (kein TriageResult-Feld)

**Status:** Accepted
**Datum:** Juni 2026
**Kontext:** Master-Plan v3.1 Phase E, baut auf ADR-0029 (Eval-Case-Format) und
ADR-0030 (Eval-Runner-Vergleichslogik) auf.

## Kontext

Tag 64 zeigte ein Agreement von 1/3 zwischen Experten-Label und Engine-Ergebnis
auf den drei gelabelten Golden-Cases. EvalCaseResult (ADR-0030) liefert nur
predicted_zone, expected_zone und is_match -- keine Information darueber,
WELCHE Pipeline-Komponente (ROI-Nutzen, Composite-Score, Zonen-Schwelle,
Handlungsdruck-Hochstufung) das Ergebnis trieb. Ohne diese Information ist
jede weitere Eval-Iteration Raetselraten statt gezielter Diagnose (interne Referenz (entfernt)
SS7: Experten-Abgleich soll Erkenntnis liefern, nicht nur eine Quote).

Zwei Implementierungsfragen waren zu klaeren, bevor Code entstehen konnte:
1. Wird der Breakdown ein neues Feld auf TriageResult/EvalCaseResult, oder ein
   separater Diagnose-Pfad?
2. Woher kommt handlungsdruck_score, der bisher privat in domain/pipeline.py
   lebt und nirgends auf TriageResult sichtbar ist?

## Entscheidung

**1. Score-Breakdown ist ein neues Modul (application/eval/breakdown.py),
kein Feld auf TriageResult oder EvalCaseResult.**
TriageResult ist seit Phase A Gate-getestet (Snapshot-Tests, Property-Based-
Tests, Equality-Test test_pipeline_is_deterministic in test_pipeline.py).
EvalCaseResult ist seit Phase D->E Gate Teil eines bestandenen Quality-Gates
(Master-Plan v3.1). Ein neues Feld auf beiden Typen ist eine nicht-additive
Aenderung an bereits abgenommenem Code -- gegen Strict Condition "Ein Tag =
aktueller Scope" (session-protocol v3 SS5.2). Ein separates Modul, das
evaluate_use_case() erneut aufruft (reine Berechnung, kein I/O, keine
Seiteneffekte) und die vollen Zwischenwerte liest, ist additiv und beruehrt
keinen Gate-getesteten Code.

**2. handlungsdruck_score wird in domain/pipeline.py public gemacht (Rename
_handlungsdruck_score -> handlungsdruck_score), nicht als neues Feld auf
TriageResult ergaenzt.**
Alternative waere gewesen, TriageResult um ein handlungsdruck_score-Feld zu
erweitern -- verworfen aus demselben Grund wie oben (Blast-Radius auf
Equality-/Snapshot-Tests). Der Rename ist reine Sichtbarkeitsaenderung ohne
Verhaltensaenderung; der einzige Call-Site (evaluate_use_case()) bleibt
unveraendert in der Logik.

**3. ZoneClassifier bekommt fuenf neue read-only Properties**
(likely_win_min_benefit, likely_win_max_composite, calculated_risk_min_
benefit, calculated_risk_max_composite, handlungsdruck_elevation_threshold)
statt dass der Breakdown die Config-Datei ein zweites Mal parst. Single
Source of Truth bleibt der bereits geladene ZoneClassifier; die Properties
exponieren nur, was intern bereits als self._lw_min etc. vorliegt.

**4. Die Erklaerung (ScoreBreakdown.explanation) wird deterministisch aus den
Zwischenwerten generiert, nicht vom LLM formuliert.** Diagnostik fuer Anas
als Entwickler, kein Endkunden-Text -- Regeln vor LLM gilt auch hier
(interne Referenz (entfernt) SS3.2). Die Logik spiegelt ZoneClassifier._base_zone() und
_apply_handlungsdruck() (domain/zones.py) in derselben Vergleichsreihenfolge,
liest aber zusaetzlich die konfigurierten Schwellenwerte mit -- ZoneResult.
reason (domain/zones.py) nennt nur die finalen Zahlen, keine Schwellen.

## Alternativen erwogen

- **Feld auf TriageResult/EvalCaseResult:** verworfen, siehe oben
  (Blast-Radius auf Gate-getesteten Code).
- **CLI-Entrypoint mit --provider-Flag zuerst (Master-Plan-Gate-Kommando,
  ADR-0030 als Folge-Punkt benannt):** verworfen fuer heute -- loest kein
  aktuelles Problem (LLM-Pfade sind noch nicht Teil des Evals), waehrend der
  Score-Breakdown das akute 1/3-Agreement-Problem direkt adressiert.
- **LLM-generierte Erklaerung statt deterministischer Text-Bausteine:**
  verworfen -- Diagnostik braucht exakte Zahlen, kein Stilrisiko/
  Halluzinationsrisiko fuer einen internen Debug-Output.

## Konsequenzen

- run_eval()/EvalCaseResult/write_report() (ADR-0030) bleiben unveraendert --
  Score-Breakdown ist ein paralleler, optionaler Diagnose-Pfad.
- _base_zone_explanation()/_elevation_explanation() (breakdown.py) muessen
  bei jeder Aenderung an ZoneClassifier._base_zone()/_apply_handlungsdruck()
  (domain/zones.py) manuell synchron gehalten werden -- keine automatische
  Kopplung, da deterministisch dupliziert statt aus ZoneResult.reason
  geparst. Bekannte technische Schuld, dokumentiert statt versteckt
  (interne Referenz (entfernt) SS7).
- handlungsdruck_score ist ab heute oeffentliche domain-API
  (aect.domain.handlungsdruck_score) -- jeder zukuenftige Consumer (Frontend
  Phase F, weitere Eval-Tools) kann sie direkt importieren statt sie erneut
  zu berechnen.
