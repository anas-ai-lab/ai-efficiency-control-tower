# ADR-002 — Zonen-Logik: 3-Zonen-Modell mit Handlungsdruck-Hochstufung

**Status:** Accepted
**Datum:** Juni 2026
**Phase:** A
**Entscheider:** Anas

---

## Kontext

Das v5-Modell klassifiziert Use Cases in drei Handlungszonen:

| Zone | Bedeutung |
|---|---|
| LIKELY_WIN | Hoher Nutzen, ueberschaubarer Aufwand - empfohlen |
| CALCULATED_RISK | Sinnvoll mit Vorbehalten - bedingt empfohlen |
| MARGINAL_GAIN | Nutzen oder Aufwand nicht ausreichend |

Regulatorischer Druck, Wettbewerbsdruck oder strategische Prioritaet
koennen eine Zone um eine Stufe hochstufen (Handlungsdruck-Elevation).

AECT muss diese Logik deterministisch, konfigurierbar und
mit einem deutschen Reason-String im Report ausgeben.

---

## Entscheidung

`ZoneClassifier.classify()` nimmt ausschliesslich Zahlen
(`expected_benefit_eur: Decimal`, `composite_score: int`,
`handlungsdruck_score: int`). Alle Schwellenwerte werden per Konstruktor
injiziert und kommen aus `config/zone_thresholds.yaml`.

### Klassifikationslogik (Prioritaetsreihenfolge)
LIKELY_WIN       wenn benefit >= 50.000 EUR UND composite <= 4
CALCULATED_RISK  wenn benefit >=  5.000 EUR UND composite <= 7
MARGINAL_GAIN    sonst

### Handlungsdruck-Elevation

Score aus `pipeline._handlungsdruck_score()`: 1 (Basis) + je 1 Punkt
pro aktivem Flag (regulatory / competitive / strategic). Wertebereich 1-4.

Ab Score >= 4 (alle drei Flags aktiv) wird die Zone um eine Stufe
hochgestuft - maximal bis LIKELY_WIN:
MARGINAL_GAIN    → CALCULATED_RISK
CALCULATED_RISK  → LIKELY_WIN
LIKELY_WIN       → LIKELY_WIN  (bereits Maximum)

### Konkrete Designentscheidungen

**1. `ZoneClassifier` nimmt Zahlen, nicht `UseCaseInput`.**
Lose Kopplung: die Klassifikationslogik kennt keine Eingabe-Feldnamen.
Der Application Service (Phase B) verbindet ROIResult + CompositeScore
mit dem Classifier. Tests brauchen kein vollstaendiges UseCaseInput-Objekt.

**2. Konfigurierbare Schwellen via Konstruktor-Injektion.**
Schwellenwerte sind firmenspezifisch kalibrierbar (vertraglich bedingte IP-Trennung).
YAML-Config + `load_zone_classifier()` ermoeglicht Wechsel ohne
Code-Aenderung. `ZoneClassifier` selbst ist IP-sauber und zeigbar.

**3. `base_zone` und `final_zone` separat im Result.**
Transparenz: ob eine Elevation stattgefunden hat, ist explizit als
`handlungsdruck_elevated: bool` sichtbar. Der `reason`-String erklaert
die Entscheidung auf Deutsch fuer den Reviewer.

**4. Elevation maximal eine Stufe, auch bei Score 4.**
Keine Ueberklassifikation. LIKELY_WIN ist das Maximum unabhaengig
vom Handlungsdruck-Score.

---

## Konsequenzen

**Positiv:**
- Vollstaendig deterministisch: identischer Input, identischer Output.
- Threshold-Tuning (z.B. nach Kalibrierung mit echten Cases) ohne
  Code-Deploy durch Config-Aenderung.
- `reason`-String macht Zonen-Entscheidungen im Report nachvollziehbar.

**Einschraenkungen:**
- Harte Schwellenwerte: 49.999 EUR Nutzen → CALCULATED_RISK,
  50.000 EUR → LIKELY_WIN. Bewusste Vereinfachung - das v5-Modell
  arbeitet ebenfalls mit Schwellenwerten.
- `handlungsdruck_score`-Berechnung liegt in `pipeline.py`, nicht im
  Classifier. Loose Coupling erfordert Awareness: Classifier hat keinen
  Einblick in Herkunft des Scores.
- Schwellen in `zone_thresholds.yaml` sind noch Platzhalter und nicht
  gegen echte v5-Cases kalibriert. Kalibrierung in Phase E (Eval).

---

## Interview-Verteidigbarkeit (Zonen-Schwellen)

**LIKELY_WIN: benefit >= 50.000 EUR, composite <= 4:**
50.000 EUR entspricht grob einer Senior-AI-Engineer-Jahresstelle in der DACH-Region.
Ein Use Case muss diesen Betrag mindestens einsparen, um die Umsetzungsinvestition zu
rechtfertigen. Composite <= 4 (NIEDRIG) bedeutet ueberschaubare Komplexitaet und kein
erhoehtes Datenschutzrisiko -- typisch fuer klare LIKELY_WIN-Kandidaten.

**CALCULATED_RISK: benefit >= 5.000 EUR, composite <= 7:**
Praezisierung (H-009 -- Klarstellung Brutto vs. Netto): Die Benefit-ACHSE der
Zonen-Einstufung nutzt den BRUTTO-Nutzen -- `roi.expected_benefit_eur` (Potenzial
x Nutzung x Evidenz, VOR Lizenzabzug), so wie ihn `pipeline.py` an `classify()`
uebergibt. Der Netto-Nutzen (nach Lizenzabzug) wirkt ausschliesslich im
vorgelagerten Vorfilter (`_check_prefilter`, `min_expected_benefit_eur`): ein
Case, der den Netto-Vorfilter nicht besteht, erreicht die Zonen-Einstufung gar
nicht erst. Die 5.000-EUR-Schwelle hier ist also die untere BRUTTO-Grenze fuer
CALCULATED_RISK, NICHT die Netto-Vorfilter-Schwelle -- beide Werte koennen
zufaellig zusammenfallen, sind aber semantisch verschiedene Achsen. Lizenzkosten
bleiben nicht folgenlos: sie schlagen ueber den Composite-Kostentier
(`_cost_tier`) auf die Aufwand-Achse durch, statt den Nutzen zu mindern -- teure
Lizenzen heben den Composite-Score und verschieben die Zone nach unten. Diese
bewusste Trennung (Brutto auf der Nutzen-Achse, Kosten auf der Aufwand-Achse) ist
als Limitation #23 in `docs/known_limitations.md` offen dokumentiert. Composite
<= 7 erlaubt mittlere bis hohe Komplexitaet, solange der Nutzen das rechtfertigt.
CALCULATED_RISK signalisiert: wirtschaftlich grundsaetzlich sinnvoll, aber mit
Vorbehalten (Datenschutz, Kosten, Komplexitaet).

**Handlungsdruck-Elevation (Schwelle >= 4, alle 3 Flags):**
Drei aktive Flags (regulatorisch + Wettbewerb + strategisch) sind ein starkes externes
Signal. Ein einzelner oder zwei externe Druckfaktoren begruenden allein keine
Zone-Hochstufung -- das wuerde das ROI-Modell aushebeln. Alle drei gleichzeitig aktiv
ist in der Praxis selten und dann tatsaechlich ein Ausnahmefall.

**v2-Kandidat (Elevation-Schwelle = 3):** Zwei von drei Flags (statt alle drei) als
Elevation-Trigger wuerde Grenzfaelle wie golden-003 (Handlungsdruck=3) korrekt stufen.
Nicht implementiert in v1, weil n=3 Golden Cases keine ausreichende empirische Basis
fuer eine Schwellen-Aenderung bilden. Adressieren in Phase G+/v2 nach mehr Golden-Case-Labels.

## Verworfene Alternativen

**Kontinuierliche Scoring-Funktion statt Zonen:** Flexibler, aber
schwerer erklaerbar und schwerer fuer Entscheider vertretbar. Das
Zielprofil erfordert Board-kompatible Outputs.

**Handlungsdruck als Multiplikator statt Elevation:** Zu viel Spielraum
fuer unerwartete Klassifikationen. Einstufige Elevation mit Deckel ist
deterministisch und verteidigbar.
