# LinkedIn Case Study -- AECT

> Stil: SCHREIBSTIL.md (Anti-Hype, Argument vor Gefuehl).
> Veroeffentlichung: erst nach IP-Klaerung (interne Referenz (entfernt) SS5).
> 3 Post-Versionen fuer unterschiedliche Zielgruppen.

---

## Version 1 -- Technische Entscheidung (Engineering-Publikum)

Compliance-Hinweise aus einer Wissensbasis statt vom Modell -- und warum
der Unterschied entscheidend ist.

Wenn ein System "DSGVO Art. 35 koennte relevant sein" sagt und du nicht
weisst, woher diese Information kommt, ist das kein Hinweis. Das ist Rauschen.

Im AECT-Projekt habe ich frueh entschieden: Compliance-Outputs nur mit
Quellenangabe. Nicht als Prompt-Disziplin ("cite your sources"), sondern
strukturell.

Das Muster nennt sich Citations-before-LLM. Retrieval aus kuratierter
Wissensbasis, dann Citation-Liste deterministisch aus den Retrieval-Metadaten
bauen, dann erst LLM-Call mit nummerierten Data-Bloecken [1], [2]. Das Modell
referenziert Nummern im Fliesstext. Die Aufloesung dieser Nummern passiert
im Code, nicht im Modell.

Ergebnis: Halluzinierte Artikel-Nummern sind strukturell ausgeschlossen.
Nicht unwahrscheinlich -- ausgeschlossen. Der Unterschied ist relevant,
wenn das System in einem echten Bewertungsprozess entscheidet.

Die instruktionsbasierte Alternative ("beziehe dich nur auf echte Quellen")
habe ich nicht gebaut, weil die Fehlerrate messbar hoeher ist. Kein Grund
zu experimentieren, wenn die robustere Loesung einfacher zu implementieren ist.

Was machst du, wenn dein System Quellen aus dem Nutzerkontext halluziniert?

---

## Version 2 -- Evaluation (AI-Fachpublikum)

Eine Agreement-Rate von 1 aus 3 ist kein Misserfolg. Sie ist das Ergebnis.

Ich habe AECT gegen ein Experten-Urteil auf 3 gelabelten Golden-Cases
evaluiert. Eine Uebereinstimmung von drei.

Das klingt schlecht. Es ist das Ergebnis, das ich erwartet und gebraucht habe.

Beide Mismatches sind off-by-one: Das System liegt je eine Zone neben dem
menschlichen Urteil. Der Score-Breakdown zeigt, warum: harte Zahlengrenzen
auf kontinuierlichen Eingabewerten. Nicht "das Modell rechnet falsch",
sondern "die Grenze liegt genau zwischen beiden Beurteilungen".

Das ist eine konkrete Aussage ueber eine konkrete Schwaeche.
Nicht "das System ist unzuverlaessig".

Die Alternative: 36 synthetische Cases, self-labeled mit dem System selbst.
Agreement-Rate 36 von 36. Aussagewert null. Zirkulaere Validierung misst,
ob ein System mit sich selbst konsistent ist -- nicht ob es richtig liegt.

Eine Eval, die eine Schwaeche findet, ist wertvoller als eine, die keine
findet. Letztere bedeutet meistens, dass man nicht gesucht hat.

---

## Version 3 -- Strategisch (Fuehrungs- und Entscheider-Publikum)

AI-Projekte scheitern nicht an zu wenig Technologie.

Sie scheitern daran, dass niemand beantwortet hat: Ist das ueberhaupt
ein AI-Problem?

Im AECT-Projekt gibt es einen expliziten AI-vs-Automation-Routing-Schritt.
Bevor das System einen LLM-Call macht, prueft regelbasierter Code: Gibt es
Signale, dass klassische Automatisierung -- Regelwerke, RPA, einfaches ML --
ausreicht?

Fuer deterministische Prozesse mit klaren Regeln lautet die Antwort oft: Ja.
Das muss kein Berater sagen. Das sagt ein Entscheidungsbaum im Code,
schneller und konsistenter als jeder Workshop.

Der Use Case, der als "AI-Projekt" eingereicht wird, ist haeufig ein
Automatisierungsfall mit einem LLM-Wrapper, der das Problem teurer und
weniger wartbar macht.

AI fuer Ambiguitaet. Regeln fuer Klarheit.

---

*Entwurf -- Stil nach SCHREIBSTIL.md geprueft: kein "revolutionaer",
kein "Game-Changer", kein "Du musst jetzt handeln".*
*Veroeffentlichung erst nach IP-Klaerung (interne Referenz (entfernt) SS5).*
