# LinkedIn Case Study -- AECT

> Stil: SCHREIBSTIL.md (Anti-Hype, Argument vor Gefuehl).
> Veroeffentlichung: erst nach vertraglicher IP-Klaerung.
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

Eine Agreement-Rate von 9 aus 24 ist kein Misserfolg. Sie ist das Ergebnis.

Ich habe AECT zuerst gegen 3 gelabelte Golden-Cases evaluiert -- Agreement 1
aus 3. Zu klein, um etwas zu beweisen. Also habe ich das Sample auf 24
gelabelte Cases erweitert. Neue Rate: 9 aus 24. Die Zahl wurde nicht besser,
weil ich keine Labels angepasst habe -- die Labels sind das menschliche
Urteil, nicht eine Stellschraube fuer die Quote.

Das klingt schlecht. Es ist das Ergebnis, das ich erwartet und gebraucht habe.

Das dominante Muster wird im groesseren Sample erst sichtbar: Die Engine
vergibt LIKELY_WIN nur bei niedrigem Aufwands-Score (Composite <= 4). Mein
menschliches Urteil "das ist ein klarer High-Value-Fall" ist breiter -- viele
Faelle mit Composite 5-7 stufe ich als Gewinn ein, die Engine als
CALCULATED_RISK. Die urspruenglichen Off-by-one-Mismatches (golden-001,
golden-003) sind weiterhin da; sie sind jetzt ein Spezialfall desselben
Befunds: harte Zahlengrenzen auf kontinuierlichen Eingabewerten. Nicht "das
Modell rechnet falsch", sondern "Mensch und Schwelle ziehen die Grenze an
unterschiedlicher Stelle".

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
*Veroeffentlichung erst nach vertraglicher IP-Klaerung.*
