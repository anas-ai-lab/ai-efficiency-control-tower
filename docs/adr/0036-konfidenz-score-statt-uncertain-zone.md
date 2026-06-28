# ADR-0036: Konfidenz-Score statt UNCERTAIN-Zone

**Status:** Accepted
**Datum:** 2026-06-28
**Autor:** Anas

## Kontext

Die Zonen-Klassifikation (`MARGINAL_GAIN` / `CALCULATED_RISK` / `LIKELY_WIN`)
trennt ueber harte Zahlenschwellen in `config/zone_thresholds.yaml`. Werte knapp
neben einer Grenze landen in der Nachbarzone, obwohl der wirtschaftliche
Unterschied minimal ist (known_limitations #2, Evidenz: golden-001/003
off-by-one beim Experten-Abgleich Tag 64).

Gesucht war eine Anreicherung, die diese Brittleness sichtbar macht, OHNE die
deterministische Zonen-Entscheidung oder die Downstream-Logik
(`is_actionable`, Routing, Persistenz, API) zu veraendern.

## Entscheidung

Wir ergaenzen `ZoneResult` um einen kontinuierlichen `confidence_score`
(float in `[0.5, 1.0]`) und ein abgeleitetes `confidence_label`
("hoch" >= 0.85 | "mittel" >= 0.70 | "niedrig"). Der Score misst den Abstand
des `composite_score` zur naechsten Zonengrenze, normiert auf die halbe
Zonenbreite:

    score = 0.5 + min(distance / half_width, 1.0) * 0.5

0.5 = direkt auf der Grenze (maximale Unsicherheit), 1.0 = Zonenmitte. Die
Randzonen haben nur eine Grenze (`MARGINAL_GAIN` keine untere, `LIKELY_WIN`
keine obere). `base_zone`, `final_zone` und alle Enum-Werte bleiben unveraendert
-- die Aenderung ist rein additiv.

## Begruendung

| Alternative | Warum verworfen |
|---|---|
| UNCERTAIN-Flag (boolean) | Verliert Granularitaet -- "wie unsicher" geht verloren, nur ein Schwellwert-Sprung statt Gradient. |
| Neuer Zonen-Wert UNCERTAIN | Bricht Downstream-Logik (`is_actionable`, Routing, Reports, persistierte Records, API-Contract); grosse Change-Surface fuer einen Diagnose-Zusatz. |
| Fuzzy-Membership-Funktionen | Overengineering fuer n=3 Golden-Cases; mehr Parameter zu kalibrieren als belastbare Validierungsdaten existieren. |

Der kontinuierliche Score traegt die meiste Information, ist additiv und bricht
keinen einzigen Aufrufer. Die Konfidenz bezieht sich auf `base_zone` (reine
benefit/composite-Einstufung); die Handlungsdruck-Hochstufung bleibt ein
separates, deterministisches Signal (`handlungsdruck_elevated`).

## Konsequenzen

**Positiv:**
- Off-by-one-Faelle sind jetzt sichtbar: ein Grenzfall liefert `confidence ~0.5`,
  ein Kernfall `~1.0`. Konsument kann Grenzfaelle zur manuellen Pruefung markieren.
- Zero Breaking Changes: Zonen-Werte, `is_actionable`, Routing, API unveraendert.
- Persistenz abwaertskompatibel: aeltere Records ohne `confidence_*` werden mit
  Fallback 0.5/"niedrig" gelesen.

**Negativ / Trade-offs:**
- Bewusst eindimensional (nur composite-Achse). Eine Zone, die durch zu geringen
  `expected_benefit` (nicht durch composite) bestimmt wird, kann composite-seitig
  "tief im falschen Band" liegen; der geklemmte Abstand liefert dann 0.5
  (unsicher) statt einer benefit-basierten Konfidenz. Damit ist #2 nur
  **teilweise** entschaerft -- die Benefit-Achse bleibt offen (v2-Backlog).
- Auf dem ganzzahligen composite-Raster erreicht die beidseitig begrenzte
  Mittelzone `CALCULATED_RISK` ihren theoretischen 1.0-Peak nicht: der
  kontinuierliche Mittelpunkt 5.5 ist kein gueltiger Integer-Input, das
  Zonen-Maximum liegt bei composite 5/6 = 0.83 ("mittel"). Die offenen
  Randzonen erreichen 1.0. Bewusst so belassen statt die Normierung zu
  verbiegen.

**Neutral / Folgeentscheidungen:**
- known_limitations #2 von "v2-Kandidat" auf "teilweise behoben" aktualisiert.
- Falls die Benefit-Achse spaeter einbezogen wird: 2D-Distanz (composite +
  benefit-Abstand zu `min_expected_benefit`) als eigene ADR.
