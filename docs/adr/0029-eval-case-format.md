# ADR-0029: Eval-Case-Schema und -Format (JSONL)

## Status
Accepted

## Kontext
Phase E (Master-Plan v3.1) braucht eine maschinenlesbare Grundlage fuer zwei
unterschiedliche Eval-Arten: Konsistenz-Eval (das System wird gegen sich
selbst geprueft, kein Soll-Wert noetig) und Experten-Abgleich (Vorbewertung
gegen ein menschliches Urteil). Beide brauchen denselben Case-Korpus -- nur
der Experten-Abgleich braucht zusaetzlich ein Label pro Case.

Der Gate-Befehl Phase E->F aus Master-Plan v3.1 referenziert bereits einen
konkreten Pfad: `evals/synthetic/use_cases.jsonl`, ausgefuehrt ueber
`aect.application.eval.runner`. Schema und Speicherort muessen vor dem
Runner feststehen, sonst entsteht der Runner gegen ein instabiles Format.

## Entscheidung
1. **Format: JSON Lines (.jsonl)**, eine Zeile = ein Case. Nicht ein
   JSON-Array. Einzelne Cases sind diffbar, ein defekter Case bricht beim
   Parsen nicht die gesamte Datei (jede Zeile wird einzeln geparst), Cases
   lassen sich anhaengen, ohne die Datei neu zu serialisieren.
2. **Ein Schema fuer Golden- und Synthetic-Cases** (`EvalCase`,
   `aect.application.eval.models`): `case_id`, `use_case: UseCaseInput`,
   `expected_zone: TriageZone | None`, `notes: str`. Der Unterschied
   zwischen Golden und Synthetic ist der Speicherort (`evals/golden/` vs.
   `evals/synthetic/`), nicht das Format.
3. **`use_case` validiert ueber das produktive `UseCaseInput`-Schema**
   (`extra='forbid'`, alle Constraints aktiv) statt ueber ein eigenes,
   laxeres Eval-Schema. Ein Case, der gegen das produktive Schema nicht
   validiert, ist kein realistischer Case.
4. **`expected_zone` ist optional (None erlaubt).** Konsistenz-Eval
   funktioniert ohne Label. Das Label fuer den Experten-Abgleich wird
   bewusst NICHT von Claude vorausgefuellt (kein automatisiertes Raten von
   Experten-Urteilen) -- separater, expliziter Schritt von Anas an einem
   spaeteren Phase-E-Tag.
5. **Speicherort `application/eval/`, nicht `adapters/eval/`.** Der Loader
   liest vom Dateisystem (I/O), bleibt aber in `application/`, weil
   Master-Plan v3.1 den Eval-Runner bereits unter `aect.application.eval.*`
   fuehrt (Gate-Kommando E->F) -- Konsistenz mit bestehender Namensgebung
   hat Vorrang vor strikter Hexagonal-Lesart. Kein Bruch der Schicht-Regel
   `domain/` importiert nur aus `domain/`, da hier kein Domain-Code liegt.

## Alternativen erwogen
- **JSON-Array statt JSONL:** verworfen -- ein Syntaxfehler irgendwo im
  Array macht die gesamte Datei unparsebar, Diffs sind unleserlicher.
- **YAML statt JSON:** verworfen -- keine zusaetzliche Library noetig
  (JSON ist Stdlib); YAML bleibt bewusst auf `zone_thresholds.yaml`
  (Config) beschraenkt, Format-Wahl nach Verwendungszweck getrennt.
- **Eigenes, laxeres Use-Case-Schema fuer Evals:** verworfen -- wuerde
  Cases zulassen, die das produktive System nie annehmen wuerde; Eval
  haette geringere Aussagekraft.

## Konsequenzen
- Golden-Cases (`evals/golden/use_cases.jsonl`) sind ab heute synthetisch,
  noch ohne Experten-Label. Ein spaeterer Phase-E-Tag ergaenzt
  `expected_zone` und/oder erweitert um anonymisierte echte Cases.
  `evals/synthetic/` bleibt heute leer (Volumen-Generierung ist ein
  separater Tag).
- Tag 62 baut keinen Runner. Das Schema steht zuerst, der Runner folgt,
  sobald genug Cases vorliegen, um ihn sinnvoll zu testen.
- `EvalCase`-Validierungsfehler werden mit Zeilennummer geworfen
  (`EvalCaseLoadError`), niemals der rohe Payload geloggt (Logging-
  Allowlist, aect-security-checklist v2.1) -- nur `path` und
  `error_count`/`case_count`.
