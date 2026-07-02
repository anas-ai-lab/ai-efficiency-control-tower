# Warum meine Rule Engine mir widerspricht

Divergenz-Analyse: AECT-Zonen-Engine vs. Autor-Labels auf den 25 Golden
Cases, plus Einordnung durch einen LLM-Zweitannotator. Quellen:
`evals/golden/report.json`, `evals/golden/score_breakdown.json`,
`evals/golden/inter_annotator_report.md`, `known_limitations.md` #2.
Stand: 2026-07-02.

## 1. Die Zahl vorneweg: 37,5 % Raw Agreement, kappa 0,06

9 von 24 gelabelten Golden Cases stimmen in der Zone ueberein -- 37,5 % Raw
Agreement, Cohen's kappa 0,06 (n=24, inkl. 3 Vorfilter-Ablehnungen). kappa
korrigiert die Rohuebereinstimmung um das, was allein aus den
Randverteilungen zu erwarten waere: Autor labelt 16x LIKELY_WIN / 8x
CALCULATED_RISK (optimistisch), Engine 5x LIKELY_WIN / 14x CALCULATED_RISK /
2x MARGINAL_GAIN plus 4x ohne Zone (konservativ). Bei so unterschiedlich
schiefen Verteilungen waere ein Teil der 37,5 % schon durch Zufall zu
erwarten -- kappa 0,06 heisst: nahezu der gesamte beobachtete Rest ist genau
dieser Zufallsanteil, keine echte Uebereinstimmung.

Was die Zahl WIRKLICH misst: Konsistenz zwischen zwei unabhaengigen
Bewertungsprozessen (Schwellen-Arithmetik vs. Werturteil) auf denselben
Input -- nicht, wer "richtiger" liegt. Was sie NICHT misst: Korrektheit.
Keine der beiden Zonen ist an einem tatsaechlich eingetretenen Ergebnis
validiert (known_limitations #1) -- der Autor-Label ist ein zweites Urteil,
keine Ground Truth. Die 37,5 % sind ausserdem nicht rein: 3 der 24 Cases
(golden-005/006/016) sind Vorfilter-Ablehnungen (predicted=None), die per
Konstruktion als Mismatch zaehlen -- das ist eine Gate-Frage ("Case ueberhaupt
bewerten?"), keine Zonen-Frage. Ohne diese 3 steigt die Rate auf 9/21
(42,9 %), kappa 0,13 -- weiterhin schwach ("slight"), aber die im README
gefuehrten 0,06 vermischen zwei verschiedene Fehlerarten in einer Zahl.

## 2. Das dominante Muster: composite_total 5-7 schlaegt jeden Nutzen

10 der 12 echten Zonen-Mismatches (Vorfilter-Ablehnungen ausgenommen) teilen
dieselbe Form: Engine CALCULATED_RISK, Autor LIKELY_WIN, composite_total
5-7 -- knapp ueber der LIKELY_WIN-Obergrenze von 4. Drei Beispiele:

| Case | Nutzen (EUR) | Complexity/Cost/DSGVO | composite | Engine | Autor |
|---|---|---|---|---|---|
| golden-012 | 936.000 | 2/2/2 | 6 | CALCULATED_RISK | LIKELY_WIN |
| golden-010 | 675.000 | 2/2/2 | 6 | CALCULATED_RISK | LIKELY_WIN |
| golden-007 | 583.200 | 3/2/2 | 7 | CALCULATED_RISK | LIKELY_WIN |

Alle drei liegen beim Nutzen 12-19x ueber der LIKELY_WIN-Mindestschwelle
(50.000 EUR) -- der Nutzen ist in keinem Fall das Problem. Der Composite
kippt, weil der Datenschutz-Teilscore ohne Zwischenstufe direkt von 0 auf 2
springt (PERSONAL/SENSITIVE_PERSONAL -> 2 Punkte; nur PSEUDONYMOUS liegt
dazwischen), sobald personenbezogene Daten involviert sind. complexity=2-3
und cost=2 sind unauffaellig -- der DSGVO-Flag allein traegt 2-3 Punkte ueber
die LIKELY_WIN-Grenze. (Zweite Variante desselben Effekts ohne DSGVO-Flag:
golden-009/024, composite=5 durch complexity=4 statt DSGVO.) Ein Nutzen in
Millionenhoehe kompensiert das nicht, weil Nutzen und Composite als getrennte
Bedingungen geprueft werden (UND-Verknuepfung), nicht gegeneinander
aufgewogen.

## 3. Der Zweitannotator: kein Tiebreaker, ein drittes Urteil

Engine (konservativ) < Zweitannotator < Autor (optimistisch) in der
Zonen-Vergabe. "In der Mitte" heisst nicht "naeher an richtig": Der
Zweitannotator stimmt mit dem Autor in 14/24 (58,3 %, kappa 0,33, "fair")
ueberein, mit der Engine nur in 8/21 (38,1 %, kappa 0,11). Bei LIKELY_WIN ist
die Uebereinstimmung mit dem Autor perfekt (11/11) -- die Divergenz entsteht
ausschliesslich in der Grauzone, und dort nutzt der Zweitannotator
MARGINAL_GAIN 8x, der Autor 0x, die Engine 2x. Diese Verteilungen
ueberschneiden sich kaum: von den Faellen mit Zweitannotator-Urteil
MARGINAL_GAIN trifft die Engine (Teilmenge mit Engine-Zone, n=21) in KEINEM
einzigen Fall ebenfalls MARGINAL_GAIN (0 von 5 in der Kreuztabelle).

Am deutlichsten zeigen das golden-009/011/025: Autor LIKELY_WIN,
Zweitannotator MARGINAL_GAIN -- ein Sprung ueber CALCULATED_RISK hinweg. Bei
009/011 urteilt zusaetzlich die Engine CALCULATED_RISK (drei Bewerter, drei
Zonen); bei 025 dagegen stimmen Engine und Autor ueberein (LIKELY_WIN), nur
der Zweitannotator weicht ab. Kappa 0,33 zwischen zwei qualitativen, blind
arbeitenden Urteilen (Zweitannotator/Autor, ganz ohne Engine-Mechanik) gilt
selbst nur als "fair" -- das bestaetigt von der Label-Seite her, was
known_limitations #2 von der Schwellen-Seite zeigt: Die Zonen-Zuordnung ist
ein strittiges Konstrukt, kein objektiv wiederauffindbares Faktum.

## 4. MARGINAL_GAIN: eine Zone, die praktisch nie feuert

2 von 24 Golden Cases, 0 von 36 synthetischen Cases landen in MARGINAL_GAIN.
Nach Vorfilter ist die Zone fast nur ueber composite_total >= 8 erreichbar --
und im Golden-Sample braucht das complexity=5, die Skalen-Obergrenze:
golden-003 und golden-017 sind exakt die 2 Cases mit complexity=5 (5/1/2 -> 8
in beiden Faellen), und beide landen in MARGINAL_GAIN. Alle 19 anderen
bewerteten Cases haben complexity <= 4 -- keiner erreicht composite 8, auch
die 5 Faelle mit complexity=4 nicht (dort bleibt cost durchgaengig bei 1,
Maximum waere 4+1+2=7). MARGINAL_GAIN ist damit faktisch kein drittes
Urteil, sondern ein Alias fuer "complexity traf die Skalen-Obergrenze".

**Empfehlung: Richtung (a) -- auf 2 Zonen + numerischen Konfidenz-Score
eindampfen, nicht (b) Schwellen nachjustieren.** Begruendung: Der Autor nutzt
MARGINAL_GAIN in 24 Cases kein einziges Mal -- keine Schwellenverschiebung
auf der composite-Achse kann Uebereinstimmung mit einem Label gewinnen, das
nie vergeben wird. Eine Senkung der CALCULATED_RISK-Obergrenze (aktuell
composite <= 7), um MARGINAL_GAIN haeufiger feuern zu lassen, wuerde zudem
aktiv schaden: Sie trifft golden-013/014 (composite=7, aktuell korrekte
CALCULATED_RISK-Matches) und kippt sie nach MARGINAL_GAIN, und sie
verschlechtert golden-007/015 (composite=7, bereits 1 Zone daneben) auf
2 Zonen Abstand zum Autor-Urteil. Und selbst wenn MARGINAL_GAIN haeufiger
feuern wuerde: Die composite-Achse (complexity+cost+DSGVO) misst nicht
dieselbe Groesse wie das Vorsicht-Urteil des Zweitannotators (Abschnitt 3:
0 von 5 Ueberschneidungen). Das ist keine falsch kalibrierte Schwelle auf
einer richtigen Achse, sondern eine Achse ohne das Signal (Unsicherheit,
Evidenzqualitaet), das ein drittes Urteil rechtfertigen wuerde.

Der `confidence_score` aus ADR-0036 ist bereits die richtige Form dieser
Information, und known_limitations #2 fuehrt seine Erweiterung auf die
Nutzen-Achse ("2D-Konfidenz") schon als offenen v2-Kandidaten. Konkreter
Vorschlag fuer eine spaetere Session: MARGINAL_GAIN als Zone entfernen,
CALCULATED_RISK uebernimmt deren heutigen Wertebereich, `confidence_score`
wird 2D (Distanz zur naechsten Composite-Grenze UND zur naechsten
Benefit-Grenze) und ersetzt die verlorene Differenzierung durch eine Zahl
statt eine dritte, kaum feuernde Kategorie.

## 5. Fazit

37,5 % Agreement klingt nach einem Fehler, der behoben werden sollte. Ist es
nicht: Es ist eine gemessene Distanz zwischen deterministischer
Schwellen-Arithmetik und einem menschlichen Werturteil, mit einem
dokumentierten, reproduzierbaren Mechanismus dahinter (Abschnitt 2 und 4)
und einer unabhaengigen Zweitmeinung, die die Unsicherheit bestaetigt statt
sie aufzuloesen (Abschnitt 3). Eine Engine, auf 90 % gruen getuned, ohne dass
sich an der zugrundeliegenden Konstrukt-Ambiguitaet etwas aendert, waere
nicht praeziser -- sie haette nur gelernt, die Autor-Meinung zu imitieren,
inklusive ihrer unbelegten Optimismus-Verzerrung (Abschnitt 1 und 3). Die
37,5 % plus die drei hier dokumentierten Mechanismen zusammen sind mehr
Aussage ueber das System als eine hohe gruene Zahl ohne sie waere.
