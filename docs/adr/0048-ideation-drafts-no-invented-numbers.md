# ADR-0048: Ideation-Entwuerfe ohne erfundene Zahlen

**Status:** Accepted
**Datum:** 2026-07-05
**Autor:** Anas

## Kontext

P10 fuehrt einen Ideation-Endpoint ein: aus einer vagen Problembeschreibung
erzeugt ein LLM 1-3 konkrete AI-Use-Case-Entwuerfe fuer den internen Intake.
Ein Entwurf soll spaeter in ein vollstaendiges `UseCaseInput` uebernommen und
von der deterministischen Regel-Schicht (Vorfilter, Composite-Score, ROI,
Zonen-Logik) bewertet werden.

Diese Regel-Schicht rechnet mit quantitativen Eingaben: Zeitersparnis pro
Vorgang, Vorgaenge pro Jahr, betroffene Mitarbeiter, Lizenz-/Implementierungs-
kosten. Genau diese Zahlen bestimmen ROI und Zone. Die Frage ist, ob das LLM
solche Zahlen im Entwurf schon selbst liefern (und ggf. schaetzen) soll, oder
ob sie leer bleiben und der Einreicher sie beibringt.

## Entscheidung

Wir erlauben dem Ideation-LLM KEINE quantitativen Angaben in den Entwuerfen.
Die Entwuerfe sind rein qualitativ (Ist-Zustand, Soll-Zustand, Beispielvorgang,
Begruendung). Jede quantitative Luecke wird als `open_questions`-Eintrag
formuliert, den der Einreicher beantworten muss (z. B. "Wie viele Vorgaenge pro
Jahr?", "Wie viele Minuten pro Vorgang?", "Welche Evidenz fuer die
Zeitersparnis?").

Die Regel wird doppelt gesichert, aber bewusst OHNE Ziffern-Regex-Validator:

1. Prompt-Instruktion (`prompts/ideation/v1/system.md`): explizite harte Regel,
   keine Stunden/Mengen/EUR/Prozent, auch nicht als "ca."-Schaetzung.
2. Der nachgelagerte Intake (P14) befuellt die quantitativen `UseCaseInput`-
   Felder grundsaetzlich nicht aus dem Entwurf vor -- sie bleiben leer, bis der
   Mensch sie setzt.

## Begruendung

ROI-Zahlen sind der Input der deterministischen Regel-Schicht. Erfundene
Zahlen wuerden die Bewertung kontaminieren: ein vom LLM geschaetztes
"ca. 5000 Vorgaenge/Jahr" saehe im Report identisch aus wie eine belegte
Zahl des Einreichers, obwohl es geraten ist. Das Projekt-Prinzip lautet
"Regeln vor LLM" -- die Zahlen muessen aus einer verantwortbaren Quelle kommen,
nicht aus einem Sprachmodell.

| Alternative | Warum verworfen |
|---|---|
| LLM schaetzt Zahlen mit Kennzeichnung ("geschaetzt: ...") | Kennzeichnung ueberlebt Copy/Paste in den Intake nicht zuverlaessig; eine geschaetzte Zahl im ROI ist gefaehrlicher als eine fehlende. Vermischt LLM-Vermutung mit belegter Eingabe genau dort, wo die Regel-Schicht Trennschaerfe braucht. |
| Ziffern-Regex-Validator im Schema (jede Ziffer -> Fehler) | Zu fehleranfaellig: legitime Ziffern in Systemnamen ("SAP S/4", "ISO 27001", "Art. 35") wuerden valide Entwuerfe abweisen. Hohe False-Positive-Rate ohne Sicherheitsgewinn -- die eigentliche Absicherung ist der leere Intake (Punkt 2). |
| Felder leer + offene Fragen (gewaehlt) | Trennt qualitative Idee (LLM-Staerke) von quantitativer Bewertung (Regel-Schicht, menschliche Verantwortung) sauber. |

## Konsequenzen

**Positiv:**
- Kein erfundener Wert kann in ROI/Zone einfliessen -- die Bewertung bleibt auf
  belegten Eingaben gegruendet.
- `open_questions` macht dem Einreicher explizit, welche Zahlen und Evidenz er
  liefern muss -- der Entwurf ist eine Arbeitsvorlage, kein fertiges Urteil.
- Kein fragiler Ziffern-Regex; Systemnamen mit Ziffern bleiben erlaubt.

**Negativ / Trade-offs:**
- Die Entwuerfe sind bewusst unvollstaendig -- ohne die Folge-Eingaben des
  Einreichers nicht bewertbar. Das ist gewollt, kann aber als "das LLM haette
  doch schon Zahlen liefern koennen" missverstanden werden.
- Die Zahlen-Regel ist nicht schema-hart erzwungen (kein Regex): ein LLM, das
  die Prompt-Instruktion ignoriert, koennte eine Zahl in den Fliesstext
  schreiben. Restrisiko akzeptiert, weil die quantitativen Intake-Felder ohnehin
  nicht vorbefuellt werden (Punkt 2 traegt die eigentliche Absicherung).

**Neutral / Folgeentscheidungen:**
- P14 (Intake-Uebernahme) muss die Nicht-Vorbefuellung der quantitativen Felder
  umsetzen -- diese ADR ist die Referenz dafuer.
- Der Pfad ist ephemer (D16): kein Case, keine Persistenz. Ein Entwurf wird erst
  beim spaeteren, menschlich getriebenen Intake zu einem `SubmittedCase`.
