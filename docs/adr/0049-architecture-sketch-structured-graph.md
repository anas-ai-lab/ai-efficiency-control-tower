# ADR-0049: Architektur-Skizze als strukturierter Graph statt LLM-Mermaid

**Status:** Accepted
**Datum:** 2026-07-05
**Autor:** Anas

## Kontext

Zu einem Use Case mit Loesungsvorschlag (proposal_text) soll auf Anforderung
eine grobe Architektur-Skizze entstehen -- ein Diagramm der wesentlichen
Bausteine und ihres Datenflusses. Die Skizze ist On-Demand (kein Schritt der
Triage-Pipeline; Intake-Kosten und -Latenz bleiben unveraendert) und ein
abgeleitetes Artefakt (Regenerieren ueberschreibt, kein Verlauf).

Die naheliegende Umsetzung -- das LLM direkt Mermaid-Syntax erzeugen zu lassen
-- hat zwei Probleme: (1) Syntaxfehler sind eine ganze Fehlerklasse (eine
unbalancierte Klammer bricht das Rendering), die sich nur durch Nachbearbeitung
oder Prompt-Disziplin eindaemmen laesst. (2) Der Diagramm-Text wird spaeter
gerendert -- freier LLM-Text darin ist eine Injection-/HTML-Flaeche.
Erschwerend: die Eingabe enthaelt proposal_text, der selbst LLM-Output ist
(Injection-Kette LLM->LLM).

## Entscheidung

Wir lassen das LLM ausschliesslich ein schema-validiertes Graph-JSON emittieren
(ArchitectureSketch: nodes mit id/label/kind, edges mit source/target/label) und
bauen daraus die Mermaid-Zeichenkette mit einer deterministischen, reinen
Funktion (`build_mermaid`, application/mermaid.py). Das LLM erzeugt NIE
Mermaid-Syntax. Node-Labels werden vor der Einbettung escaped (form-brechende
und HTML-faehige Zeichen entfernt); Node-IDs sind per Pattern auf `[a-z0-9_]`
beschraenkt. Fuenf generische Bausteintypen (user/system/ai_service/data_store/
external), hoechstens zehn Knoten.

## Begruendung

| Alternative | Warum verworfen |
|---|---|
| LLM emittiert Mermaid direkt | Syntaxfehler-Klasse nicht ausschliessbar; grosse Injection-/HTML-Flaeche im gerenderten Text; nicht schema-validierbar |
| Bildgenerierung (LLM -> Bild) | Kosten/Latenz, kein editierbares/diffbares Artefakt, keine Schema-Garantie, Rendering-Blackbox |
| Graph-JSON + deterministischer Builder (gewaehlt) | Schema-validierbar (Referenz-Integritaet im Model-Validator), Syntaxfehler-Klasse strukturell eliminiert, Injection-Kette LLM->LLM auf escapte Labels reduziert, snapshot-testbar |

Der Builder ist eine reine Funktion: gleiche Eingabe -> exakt gleiche Ausgabe,
per Snapshot-Test gepinnt. Die Referenz-Integritaet (eindeutige Node-IDs, Kanten
zeigen auf existierende Knoten) prueft ein Pydantic-Model-Validator -- ein
Verstoss ist eine ValidationError (InvalidLLMOutputError), die die Route auf 502
mappt, kein 500.

## Konsequenzen

**Positiv:**
- Keine Mermaid-Syntaxfehler moeglich (der Builder erzeugt immer valides Mermaid).
- Injection-Flaeche minimiert: nur escapte Labels fliessen in den Diagramm-Text.
- Skizze ist schema-validiert, diffbar und snapshot-testbar.
- On-Demand, kein Pipeline-Schritt: Triage-Kosten/-Latenz unveraendert.

**Negativ / Trade-offs:**
- Begrenzte Ausdrucksmaechtigkeit: max 10 Knoten, genau 5 Bausteintypen, ein
  flowchart-LR-Layout. Bewusst -- eine Skizze, kein vollstaendiges
  Architekturbild.
- Der Builder muss jede Mermaid-Form, die wir unterstuetzen wollen, explizit
  kennen (kein Durchreichen beliebiger Syntax).

**Neutral / Folgeentscheidungen:**
- Persistenz als nullable Spalte architecture_sketch an der Case-Zeile (JSON:
  graph + mermaid_source + generated_at + prompt_version). Abgeleitetes Artefakt
  (D20): Regenerieren ueberschreibt. DSGVO-Loesch-Kaskade greift automatisch
  (liegt in der Case-Zeile, ADR-0038).
- Kein Function-Calling; tools.py bleibt unangetastet.
- Backend rendert kein Mermaid (nur String-Bau) -- das Rendering ist Frontend-Konzern.
