# 0044 -- Country-Pflichtfeld + 5-stufiges Employee-Level (Schema-Nachtrag)

**Status:** Accepted
**Datum:** 2026-07-04
**Phase:** G (Post-v1-Audit)

## Kontext

Dieser ADR ist ein **Nachtrag**: die hier beschriebene Schema-Erweiterung wurde
bereits gebaut (Commit `1ba2a52`, "feat(domain): UseCaseInput um country, 5
Level, Impl.-Kosten, Notizen, Soll-Beispiel"), ohne dass die Entscheidung zum
Zeitpunkt der Aenderung als ADR festgehalten wurde. Der Nachtrag schliesst die
Luecke, damit die Blast-Radius- und Alternativ-Abwaegung nachvollziehbar bleibt
(Audit-Nachvollziehbarkeit ist ein Staerke-Argument des Projekts, vgl.
`docs/known_limitations.md`).

Ausgangslage: `UseCaseInput` kannte urspruenglich weder ein Land noch eine
fein aufgeloeste Senioritaets-Stufe. Der Stundensatz-Lookup lief ueber ein
`EmployeeCategory`-Enum mit einer groeberen Stufung, die eine `MIXED`-Kategorie
("gemischtes Team") enthielt, und ohne Landesdimension -- der Satz war implizit
DACH. Damit liess sich derselbe Prozess in unterschiedlichen Laendern nicht
korrekt bewerten, und `MIXED` unterlief die IP-saubere Stundensatz-Matrix
(kein definierter Satz, sondern ein Misch-Konstrukt).

## Entscheidung

Wir erweitern `UseCaseInput` und die zugehoerigen Domain-Typen:

1. **`country: Country` als Pflichtfeld** (kein Default). Steuert den
   Stundensatz-Lookup je Land x Level. `Country` ist ein StrEnum generischer
   ISO-3166-alpha-2-Kuerzel (lowercase); die konkreten Saetze liegen
   ausschliesslich in Config (`roi_config.toml` generisch, `.local.toml` echt),
   nie im Code (IP-Trennung).
2. **`EmployeeCategory` auf 5 Stufen** (JUNIOR, PROFESSIONAL, CONSULTANT,
   SENIOR, MANAGEMENT), aufsteigend nach Senioritaet. Die fruehere
   `MIXED`-Kategorie **entfaellt**.
3. **`implementation_cost_eur`** (einmalige Implementierungskosten) fliesst in
   die Kostenstufe des Composite-Aufwand-Scores ein -- NICHT in den jaehrlichen
   Netto-Nutzen des ROI (einmalige vs. wiederkehrende Kosten sauber getrennt).
4. Begleitend additiv: `desired_example_process` (Soll-Beispiel) und `notes`
   (Freitext-Anmerkungen), beide optional -- ohne Wirkung auf die Berechnung.

Kein Default fuer `country`: das Land bestimmt das ROI-Ergebnis direkt und muss
bewusst gesetzt werden -- ein stiller DACH-Default wuerde falsche Ergebnisse
plausibel aussehen lassen.

## Begruendung

| Alternative | Warum verworfen |
|---|---|
| Land als optionales Feld mit DACH-Default | Ein Default fuer eine Groesse, die das ROI-Ergebnis direkt bestimmt, produziert stille Falschbewertungen (ein Case aus Land X wird zu DACH-Saetzen gerechnet, ohne Fehler). Widerspricht der projektweiten "kein stiller Fehler"-Linie (vgl. TOML/StrEnum-Invariante). |
| `MIXED`-Kategorie beibehalten | `MIXED` hat keinen definierten Stundensatz, sondern mischt -- das unterlaeuft die IP-saubere Matrix (ein Satz je Land x Level). Wer ein gemischtes Team hat, reicht die dominante Stufe ein; eine Aufsplittung waere ein eigenes Feature, kein Enum-Wert. |
| Implementierungskosten in den ROI-Netto-Nutzen einrechnen | Vermischt einmalige mit wiederkehrenden Groessen -- der jaehrliche Netto-Nutzen wuerde im ersten Jahr kuenstlich gedrueckt und in Folgejahren zu hoch. Die Kostenstufe des Composite-Scores ist der richtige Ort fuer eine einmalige Groesse. |

## Konsequenzen

**Positiv:**
- Landeskorrekte ROI-Bewertung ueber die Config-Matrix (Land x Level), ohne
  eine Firmenzahl in den Code zu ziehen.
- `MIXED`-Sonderfall entfernt -- die Stundensatz-Matrix ist wieder vollstaendig
  und eindeutig (jeder Enum-Wert hat genau einen Satz je Land).
- Einmalige vs. wiederkehrende Kosten sauber getrennt.

**Negativ / Trade-offs (Blast Radius):**
- **Breite Fixture-Migration.** Der Schema-Wechsel beruehrte ~20 Fixture-/
  Testdateien und synthetische Cases (jeder `UseCaseInput`-Konstruktionsort
  brauchte `country` + gueltiges 5-Stufen-Level, `MIXED`-Vorkommen mussten
  ersetzt werden). Einmaliger, aber breiter Aufwand.
- **Config-Kopplung.** Jeder `Country`-Wert braucht eine
  `[hourly_rates.<wert>]`-Section mit allen 5 Leveln, sonst stiller ROI=0
  (TOML/StrEnum-Invariante). Ein neues Land ist kein reiner Code-Change.
- **Breaking Change am API-Schema.** `country` ist Pflicht -- Requests ohne
  Land liefern jetzt 422 (Frontend-/openapi-Sync war ein separater
  Folge-Schritt).

**Neutral / Folgeentscheidungen:**
- `desired_example_process`/`notes` sind rein additiv (optional, keine
  Berechnungswirkung) -- sie erweitern nur die dokumentarische Tiefe eines Case.
