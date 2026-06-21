# ADR-0030: Eval-Runner-Vergleichslogik und Report-Format

**Status:** Accepted
**Datum:** Juni 2026
**Kontext:** Master-Plan v3.1 Phase E, baut auf ADR-0029 (Eval-Case-Format) auf.

## Kontext

Der Eval-Runner muss fuer jeden EvalCase die deterministische Phase-A-Pipeline
aufrufen und das Ergebnis mit einem optionalen Experten-Label (expected_zone)
vergleichen. Aktuell tragen alle vier Golden-Cases expected_zone=null (Tag 62).
Zwei Entscheidungen waren noetig, bevor Code entstehen konnte:

1. Wie wird ein fehlendes Experten-Label im Vergleichsergebnis dargestellt?
2. In welchem Format wird der Report geschrieben?

## Entscheidung

**1. Drei-Werte-Logik statt Zwei-Werte-Logik fuer is_match.**
`is_match: bool | None` statt `is_match: bool`. `None` bedeutet "kein Vergleich
moeglich" (expected_zone fehlt) und ist explizit verschieden von `False`
("Vergleich durchgefuehrt, System lag falsch"). Eine Zwei-Werte-Variante haette
unlabeled Cases als `False` werten muessen -- das waere eine stille Falschaussage
("System hat falsch gelegen"), obwohl schlicht kein menschliches Urteil vorliegt.
Direkte Konsequenz aus interne Referenz (entfernt) SS7: Konsistenz-Eval und Experten-Abgleich sind
zwei verschiedene Dinge, die Datenstruktur darf sie nicht vermischen.

**2. Report-Format: JSON, kein Markdown/CSV.**
Der Report ist heute ein Zwischenartefakt fuer den naechsten Tag (Labeling +
moeglichen CLI-Runner), kein Endkunden-Dokument. JSON ist maschinell
weiterverarbeitbar (spaeterer CLI-Runner, evtl. CI-Auswertung) und verlustfrei
fuer `None`-Werte (`null`). Markdown waere fuer Phase F als Anzeige-Format
relevant, ist aber heute verfrueht (kein Frontend, keine Demo-Notwendigkeit).

**3. Report enthaelt nur case_id + Zonen-Werte, keinen use_case-Inhalt.**
Konsistent mit der Logging-Allowlist (aect-security-checklist v2.1): Reports
sind wie Logs zu behandeln, auch wenn sie keine echten Personendaten enthalten
(synthetische Cases) -- das Schema soll fuer echte/Golden-Cases mit PII bereits
sicher sein, nicht erst spaeter nachgeruestet werden.

## Alternativen erwogen

- **bool statt bool | None fuer is_match:** verworfen, siehe oben (stille
  Falschaussage bei unlabeled Cases).
- **CSV-Report:** verworfen, schlechtere Verschachtelung fuer das
  summary+per-case-Format, kein echter Vorteil gegenueber JSON in diesem Schritt.
- **Sofortiger CLI-Entrypoint mit --provider-Flag (Master-Plan-Gate-Kommando):**
  verworfen fuer heute. Das Gate-Kommando aus Master-Plan v3.1 (Phase E->F)
  bewertet auch LLM-Pfade (Schaerfung/Loesungsvorschlag) -- das ist erst relevant,
  sobald der Eval ueber die reine Regel-Pipeline hinausgeht. Heute: Python-API
  (run_eval, write_report), kein CLI.

## Konsequenzen

- `EvalCaseResult.is_match` muss bei jeder Auswertung auf `None` geprueft werden,
  bevor eine Aggregation (Agreement-Rate) berechnet wird -- sonst falsche Quote.
- Sobald echte Experten-Labels gesetzt werden (naechster Schritt), liefert
  derselbe Runner ohne Codeaenderung echte Agreement-Zahlen.
- Der CLI-Entrypoint mit --provider-Flag aus dem Master-Plan-Gate-Kommando wird
  in einem spaeteren Phase-E-Tag nachgezogen, sobald LLM-Konsistenz Teil des
  Evals wird.
