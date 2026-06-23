# Phase E — Review

**Datum:** Juni 2026
**Tests bei Review:** 448 passed, 4 skipped (`uv run pytest -q`, Tag 68 bestätigt)
**Gate-Status:** Bestanden — Gate E→F Tag 67: `pytest TestRunEvalOnSyntheticCases`
grün (36 Cases, kein Crash); `evals/golden/report.json` erzeugt; Agreement 1/3
(golden-002 match; golden-001, golden-003 Off-by-one-Mismatch, dokumentiert in
`docs/limitations.md` und ADR-0031).

---

## Gebaute Artefakte

| Datei | Inhalt (1 Satz) |
|---|---|
| `application/eval/models.py` | `EvalCase` (Pydantic, JSONL-kompatibel), `EvalResult` (3-wertig: `is_match: bool \| None`), `EvalReport`. |
| `application/eval/loader.py` | JSONL-Loader fuer Golden- und Synthetic-Cases, robuste Fehlerbehandlung. |
| `application/eval/runner.py` | `run_eval()` + `EvalRunner` + `write_report()` — orchestriert Eval-Lauf und schreibt JSON-Report. |
| `application/eval/breakdown.py` | `ScoreBreakdown`-Dataclass + deterministischer DE-Erklaerungsgenerator, keine LLM-Abhaengigkeit. |
| `evals/golden/use_cases.jsonl` | 4 Golden-Cases: 3 mit unabhaengigen Experten-Labels, 1 bewusst unlabeled (Vorfilter-Grenzfall, ADR-0029). |
| `evals/synthetic/use_cases.jsonl` | 36 Synthetic-Cases (5x6 Template-Varianten + 6 Boundary-Cases), `expected_zone=None` by design. |
| `scripts/run_golden_eval.py` | Golden-Eval-Skript (Gate-E->F-Mechanismus, ersetzt nicht-existenten CLI-Einstieg laut ADR-0032). |
| `scripts/run_synthetic_eval.py` | Synthetic-Eval-Lauf als Skript. |
| `scripts/generate_synthetic_cases.py` | Generator fuer Synthetic-Cases (Template-Varianten-Grid). |
| `scripts/run_diagnostics.py` | Diagnostik-Skript: `ScoreBreakdown`-Ausgabe fuer beliebigen Case. |
| `docs/limitations.md` | 5 Validierungsgrenzen offen dokumentiert (Tag 67). |
| `docs/adr/0029-0032` | EvalCase-Schema, EvalRunner-Design (3-wertiger `is_match`), Brittleness-Diagnose und Regression-Anker, Gate-Mechanik-Korrektur. |
| `tests/application/eval/test_runner.py::TestRunEvalOnSyntheticCases` | pytest-Klasse als CI-erzwungener Gate-Check (>= 30 Cases ohne Crash). |

---

## Was ich heute anders designen wuerde

**1. `breakdown.py`-Coverage bei 80 % — Erklaerungszweige nicht vollstaendig getestet.**
Einige DE-Erklaerungspfade (Zeilen 140-146, 250-256) sind nur ueber Live-Skripte
erreichbar, weil die synthetische Case-Menge nicht systematisch alle Score-Kombinationen
abdeckt. Kein Funktionsfehler — aber fehlende Test-Tiefe fuer ein Modul, das im
Interview ("wie entsteht die Erklaerung?") direkt verteidigt werden muss.

**2. Synthetic Cases testen Crash-Freiheit, nicht Korrektheit.**
`expected_zone=None` by design (ADR-0029/0030: zirkulaere Selbstlabelung waere
bedeutungslos). Das ist die richtige Entscheidung — aber es bedeutet, dass 36 Cases
ausschliesslich Robustheit belegen. "Laeuft es durch?" ist nicht dasselbe wie "ist das
Urteil richtig?". Das steht in `limitations.md` SS3, klar benannt. Als Design-
Entscheidung formulierbar: mehr kuratierte Golden-Cases haetten das Konfidenz-Intervall
der Agreement-Rate gesenkt.

**3. `run_diagnostics.py` ausserhalb des Test-Systems.**
Das Skript ist nuetzlich fuer Grenzwert-Debugging, aber kein pytest-Fall. Die
`ScoreBreakdown`-Diagnostik ist dadurch nicht CI-erzwungen. Waere die Diagnostik-
Funktion als Test-Helper in die Eval-Test-Suite integriert worden, waere `breakdown.py`-
Coverage hoeher und der Grenzwert-Befund automatisch bei jedem CI-Run sichtbar.

---

## Offene technische Schulden

| Punkt | Prioritaet | Wann adressieren |
|---|---|---|
| `breakdown.py`-Coverage 80 % (Erklaerungszweige) | Niedrig | Phase F, falls Diagnostik als Demo-Feature gezeigt wird |
| Synthetic-Cases ohne Experten-Labels (by design) | — | Post-v1: 10-20 weitere Golden-Cases wuerden Agreement-Rate stabilisieren |
| `run_diagnostics.py` ausserhalb pytest | Niedrig | Post-v1 |
| `resilient.py`-Docstring stale (seit Phase C) | Niedrig | Phase-F-Hardening-Pass |

---

## Vertrauen ins Phase-E-Design (1-10)

**EvalCase-Schema / JSONL-Loader:** 9 — Schema minimal und stabil; Loader
behandelt `expected_zone=None` sauber; kein Anpassungsbedarf in Phase F.

**EvalRunner / `run_eval()`:** 9 — kein LLM-Aufruf, rein deterministisch; Gate-E->F
ist jetzt CI-erzwungen statt einmaliger CLI-Lauf (ADR-0032). Staerkster
Strukturpunkt der Phase.

**ScoreBreakdown / Diagnostics:** 8 — deterministisch korrekt (Off-by-one-Mismatch
zeigt Grenzwert-Naehe, nicht Zufall); Coverage-Luecke bei 80 % (Punkt 1 oben).

**3-wertiger `is_match`:** 9 — `None`-Kategorie verhindert falsch positive "Agreement"
fuer Faelle ohne valides Experten-Urteil (golden-004). Korrekte Entscheidung, auch
wenn sie die Agreement-Rate nach aussen niedriger erscheinen laesst.

**Gate-Mechanik (ADR-0032):** 9 — Protokoll-Korrektur statt CLI-Wrapper-Bau ist die
richtige Entscheidung: `--provider` ueber einer LLM-freien Eval-Schicht waere eine
Leerform gewesen, die nach aussen eine Auswahl suggeriert die innen nicht existiert.

---

## Offene Punkte fuer Phase F

1. **LLM-Output-Qualitaet** nicht evaluiert (`limitations.md` SS3) — Phase-F/post-v1,
   sobald ein nicht-deterministischer Eval-Rahmen (Prompt-Versionierung, Modell-
   Abhaengigkeit) aufgesetzt wird.
2. **Golden-Case-Set** bleibt bei 4 Cases — statistisch nicht belastbar
   (`limitations.md` SS4). Post-v1, kein Phase-F-Blocker.
3. **SHA-Pinning** der GitHub-Actions — bewusst nach Phase F verschoben
   (aect-security-checklist SS F, ADR-0032 Konsequenzen).
4. **`resilient.py`-Docstring-Fix** — weiterhin offen, gehoert in den
   Phase-F-Hardening-Pass.
5. **Beide ADR-Serien** (`000X` / `ADR-00X`) — Review auf Redundanz und
   Nummerierungsluecke ADR-004 (session-protocol v3 SS6.13, phase-b-review.md).
