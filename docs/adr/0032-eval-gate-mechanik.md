# ADR-0032 — Eval-Gate E->F: pytest-Regression statt CLI-Modul-Einstieg

**Status:** Accepted
**Datum:** Juni 2026
**Kontext:** Phase E, Gate-Aufloesung (Tag 67)

---

## Kontext

session-protocol v3 SS2 dokumentierte das Gate E->F als:

    uv run python -m aect.application.eval.runner \
      --cases evals/synthetic/use_cases.jsonl --provider mock

Dieser Befehl existiert nicht. runner.py hat keinen __main__-Block
und kein --provider-Konzept. Die Diskrepanz entstand, weil das Protokoll
ein CLI-Interface antizipierte, das beim Bau von ADR-0029/0030 nicht
realisiert wurde -- die Python-API wurde als alleinige Schicht entschieden.

Wesentliche Eigenschaft des Runners: run_eval() ruft ausschliesslich
evaluate_use_case() aus der Domain-Schicht auf -- keine LLM-Abhaengigkeit,
kein Adapter-Aufruf. Ein --provider-Flag waere semantisch leer: "mock" und
"azure" wuerden identische Ergebnisse produzieren.

---

## Alternativen

**A) CLI-Wrapper bauen:** __main__-Block in runner.py, argparse mit
--cases und --provider (mock|azure, DI-Switching).

Contra: --provider waere eine Leerhuelle -- der Runner testet keine
LLM-Pfade. Das Interface wuerde faelschlich suggerieren, dass provider-
spezifisches Verhalten evaluiert wird. Technische Schuld ohne Gegenwert.

**B) Protokoll korrigieren:** Gate-Befehl ersetzen durch tatsaechlich
existierende Mechanismen: pytest TestRunEvalOnSyntheticCases +
run_golden_eval.py.

Pro: Ehrliche Abbildung der Implementierung.
Pro: pytest ist staerker als ein einmaliger CLI-Lauf -- Gate-Kriterium
ist CI-erzwungen, kein manueller Einmalig-Lauf.
Pro: Master-Plan-Gate-Kriterien (>= 30 Cases ohne Crash, Report erzeugt,
Agreement dokumentiert) sind vollstaendig erfuellt.

---

## Entscheidung

B) Protokoll korrigieren.

---

## Konsequenzen

- session-protocol.md SS2 Gate E->F ersetzt durch:
  uv run pytest tests/application/eval/test_runner.py::TestRunEvalOnSyntheticCases -v
  uv run python scripts/run_golden_eval.py
- Kein __main__-Block in runner.py -- Python-API bleibt alleinige Schicht
  (konsistent mit ADR-0029/0030).
- Offen (Phase F/post-v1): sobald der Eval-Runner LLM-Output-Qualitaet
  testet, braucht er eine echte Provider-Abstraktion und dann ist ein
  CLI-Interface gerechtfertigt.
