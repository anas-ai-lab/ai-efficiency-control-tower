# Warum meine Rule Engine mir widerspricht

Divergenz-Analyse: AECT-Zonen-Engine vs. Autor-Labels auf 25 Golden Cases,
plus LLM-Zweitannotator und Schwellenwert-Backtest. Quellen:
`evals/golden/report.json`, `evals/golden/score_breakdown.json`,
`evals/golden/inter_annotator_report.md`,
`scripts/analysis/zone_threshold_backtest_results.json`,
`known_limitations.md` #2. Stand: 2026-07-02.

## 1. Die Zahl vorneweg: 37,5 % Raw Agreement, kappa 0,06

9 von 24 gelabelten Golden Cases stimmen in der Zone ueberein. kappa
korrigiert die Rohuebereinstimmung um das, was allein aus den
Randverteilungen zu erwarten waere: Autor labelt optimistisch (16x
LIKELY_WIN, 8x CALCULATED_RISK), Engine konservativ (5x LIKELY_WIN, 14x
CALCULATED_RISK, 2x MARGINAL_GAIN, 3x Vorfilter-Ablehnung). Bei so schiefen
Verteilungen waere ein Teil der 37,5 % schon durch Zufall zu erwarten --
kappa 0,06 heisst: fast der gesamte beobachtete Rest ist genau dieser
Zufallsanteil, keine echte Uebereinstimmung.

Gemessen wird Konsistenz zwischen zwei unabhaengigen Bewertungsprozessen
(Schwellen-Arithmetik vs. Werturteil) auf demselben Input -- nicht
Korrektheit. Keine der beiden Zonen ist an einem tatsaechlich eingetretenen
Ergebnis validiert (known_limitations #1); der Autor-Label ist ein zweites
Urteil, keine Ground Truth. Drei der 24 Cases (golden-005/006/016) sind
Vorfilter-Ablehnungen, die per Konstruktion als Mismatch zaehlen -- eine
Gate-, keine Zonen-Frage. Ohne sie steigt die Rate auf 9/21 (42,9 %), kappa
0,13 -- die 37,5 % vermischen also zwei Fehlerarten.

## 2. Das dominante Muster: composite_total 5-7 schlaegt jeden Nutzen

10 der 12 echten Mismatches teilen dieselbe Form: Engine CALCULATED_RISK,
Autor LIKELY_WIN, composite_total 5-7 -- knapp ueber der
LIKELY_WIN-Obergrenze von 4.

| Case | Nutzen (EUR) | composite | Engine | Autor |
|---|---|---|---|---|
| golden-012 | 936.000 | 6 | CALCULATED_RISK | LIKELY_WIN |
| golden-010 | 675.000 | 6 | CALCULATED_RISK | LIKELY_WIN |
| golden-007 | 583.200 | 7 | CALCULATED_RISK | LIKELY_WIN |

Alle drei liegen 12-19x ueber der LIKELY_WIN-Mindestschwelle (50.000 EUR) --
der Nutzen ist nie das Problem. Der Composite kippt meist durch den
Datenschutz-Sprung (PERSONAL/SENSITIVE_PERSONAL -> +2 Punkte ohne
Zwischenstufe) oder durch complexity=4 (golden-009/024). Nutzen und
Composite werden als getrennte, UND-verknuepfte Bedingungen geprueft, nicht
gegeneinander aufgewogen -- Millionen-Nutzen kompensiert das nicht.

## 3. Der Zweitannotator: kein Tiebreaker, ein drittes Urteil

Engine (konservativ) < Zweitannotator < Autor (optimistisch). Der
Zweitannotator stimmt mit dem Autor in 14/24 (58,3 %, kappa 0,33, "fair")
ueberein, mit der Engine nur in 8/21 (38,1 %, kappa 0,11). Bei LIKELY_WIN
ist die Uebereinstimmung mit dem Autor perfekt (11/11); die Divergenz
entsteht ausschliesslich in der Grauzone, wo der Zweitannotator
MARGINAL_GAIN 8x nutzt, der Autor 0x, die Engine 2x -- praktisch
ueberschneidungsfrei. Kappa 0,33 zwischen zwei qualitativen Urteilen mit
gleichem Informationsstand (Zweitannotator/Autor, ohne Engine-Mechanik)
gilt selbst nur als "fair": Die Zonen-Zuordnung ist ein strittiges
Konstrukt, kein objektiv wiederauffindbares Faktum -- das bestaetigt von der
Label-Seite, was Abschnitt 4 von der Schwellen-Seite zeigt.

## 4. MARGINAL_GAIN-Empfehlung: Backtest statt Einschaetzung

`scripts/analysis/zone_threshold_backtest.py` rechnet alle 60 Cases (24
gelabelt + 36 synthetic) unter dem aktuellen LIKELY_WIN-Schwellenwert (4)
und zwei Kandidaten (5, 6) neu aus, per `ZoneClassifier.classify()`:

| Kandidat | Agreement | kappa | MARGINAL_GAIN-Anteil | Faelle geaendert (/60) |
|---|---|---|---|---|
| aktuell (composite<=4) | 37,5 % (9/24) | 0,06 | 3,3 % (2/60) | -- |
| composite<=5 | 41,7 % (10/24) | 0,07 | 3,3 % (2/60) | 3 |
| composite<=6 | 54,2 % (13/24) | 0,17 | 3,3 % (2/60) | 14 |

Schwellenwert composite<=6 erhoeht Raw Agreement von 37,5 % auf 54,2 % und
kappa von 0,06 auf 0,17, bei unveraendertem MARGINAL_GAIN-Anteil (3,3 % in
allen drei Kandidaten -- die Zone haengt an der CALCULATED_RISK-Obergrenze/
complexity=5, nicht am getesteten Schwellenwert) -- numerisch der staerkste
Kandidat, aber NICHT empfohlen. Zwei Gruende aus dem Backtest: Erstens
bleibt kappa 0,17 nach Landis/Koch "slight" (< 0,20) -- fast verdreifacht,
aber kein Sprung in eine andere Guete-Klasse. Zweitens erkauft der Zugewinn
(6 vormals falsche CALCULATED_RISK-Faelle korrekt: golden-001/008/010/
012/022/024) zwei neue Fehler: golden-018 und golden-020 waren korrekte
CALCULATED_RISK-Matches und werden durch die breitere LIKELY_WIN-Zone
faelschlich hochgestuft. Composite allein trennt die 5-7er-Faelle nicht
sauber -- eine Verschiebung tauscht eine Fehlerart gegen eine kleinere,
loest die Konstrukt-Ambiguitaet aus Abschnitt 3 nicht auf.

**Empfehlung bleibt (jetzt Backtest-bestaetigt): 2 Zonen + numerischer
Konfidenz-Score statt Schwellen-Nachjustierung.** Der `confidence_score` aus
ADR-0036 ist bereits die richtige Form dieser Information; known_limitations
#2 fuehrt seine Erweiterung auf die Nutzen-Achse ("2D-Konfidenz") als
offenen v2-Kandidaten. Konkret: MARGINAL_GAIN entfernen, CALCULATED_RISK
uebernimmt deren Wertebereich, `confidence_score` wird 2D und ersetzt die
verlorene Differenzierung durch eine Zahl statt eine dritte, kaum feuernde
Kategorie.

## 5. Fazit

37,5 % Agreement klingt nach einem Fehler. Ist es nicht: eine gemessene
Distanz zwischen deterministischer Schwellen-Arithmetik und menschlichem
Werturteil, mit dokumentiertem Mechanismus (Abschnitt 2), einer
Zweitmeinung, die die Unsicherheit bestaetigt statt aufloest (Abschnitt 3),
und einem Backtest, der zeigt: die naheliegende Reparatur (Schwelle
verschieben) bringt reale, aber gedeckelte Gewinne und neue Fehler
derselben Art (Abschnitt 4). Eine auf 90 % gruen getunte Engine haette nur
gelernt, die Autor-Meinung samt ihrer unbelegten Optimismus-Verzerrung zu
imitieren. Die 37,5 % plus die drei dokumentierten, jetzt teils
Backtest-verifizierten Mechanismen sind mehr Aussage ueber das System als
eine hohe gruene Zahl ohne sie waere.
