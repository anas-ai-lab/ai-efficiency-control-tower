# ADR-001 — ROI-Modell: Deterministisches v5-Bewertungsmodell

**Status:** Accepted
**Datum:** Juni 2026
**Phase:** A
**Entscheider:** Anas

---

## Kontext

Der reale Use-Case-Intake-Prozess (v5) berechnet den Nutzwert einer
AI-Einreichung nach folgendem Modell:

    Theoretisches Potenzial = Stundenwert x Zeitersparnis/Vorgang
                              x Vorgaenge/Jahr x Mitarbeiterzahl
    Erwarteter Nutzen       = Potenzial x Nutzungsfaktor x Evidenzfaktor
    Netto-Nutzen            = Erwarteter Nutzen - Lizenzkosten p.a.

Vorfilter pruefen drei Mindestgrenzen:
  Potenzial >= 20.000 EUR / Stunden/Jahr >= 120 / Netto-Nutzen >= 5.000 EUR

AECT muss dieses Modell deterministisch und vollstaendig getestet
abbilden - ohne LLM, ohne Approximation, mit konfigurierbaren Parametern.

---

## Entscheidung

Das ROI-Modell wird als reine Python-Funktion `_calculate_roi_values()`
implementiert, die ausschliesslich Zahlen und ein `ROIConfig`-Objekt
entgegennimmt - kein `UseCaseInput`, kein Dateisystem, kein Netzwerk.
Der oeffentliche Einstiegspunkt `calculate_roi()` mappt
`UseCaseInput`-Felder auf diese Kernfunktion.

### Konkrete Designentscheidungen

**1. `Decimal` fuer alle Geldwerte, `float` fuer Stunden.**
Monetaere Werte erfordern exakte Dezimalarithmetik (ROUND_HALF_UP auf
2 Stellen). Stunden sind Naeherungswerte - `float` genuegt, da sie nie
direkt in EUR-Reports erscheinen.

**2. `frequency_unit_value="ANNUALLY"` hardkodiert in `calculate_roi()`.**
`UseCaseInput.frequency_per_year` ist bereits ein Jahreswert - Feldname
und Constraint (le=1_000_000) sind eindeutig. Der interne Multiplikator
fuer "ANNUALLY" ist 1. Alternative (FrequencyUnit-Feld + Konvertierung)
verworfen: das Formular kennt keinen Periodenbegriff, Nachruesten waere
ein Interface-Bruch ohne v1-Mehrwert.

**3. Defensives Default bei unbekanntem Land/Level: `Decimal("0")`.**
Kein `raise KeyError`. Unbekannte Kombination fuehrt zu Potenzial = 0,
Vorfilter schlaegt fehl mit lesbarem `prefilter_fail_reason`. Der Fehler
wird sichtbar gemacht, nicht durch eine unbehandelte Exception
mitten in der Berechnung verdeckt. Phase B: Application Service validiert
`country` gegen bekannte Keys in `ROIConfig.hourly_rates`.

**4. Alle Parameter von `_calculate_roi_values()` sind keyword-only.**
7+ Parameter ohne Labels sind eine zuverlässige Fehlerquelle.
`*` erzwingt Named Arguments und macht falsche Reihenfolge unmoeglich.
Tests koennen direkt gegen `_calculate_roi_values()` schreiben ohne
ein UseCaseInput-Objekt zu bauen.

**5. `ROIConfig` als injiziertes Objekt, nicht als Singleton.**
`load_roi_config()` liest TOML und gibt ein `ROIConfig`-Objekt zurueck.
Tests konstruieren `ROIConfig` direkt - kein Dateisystem in Unit-Tests.
`calculate_roi()` erhaelt Config als Argument.

**6. TOML-Keys = StrEnum-`.value`-Strings (lowercase).**
Mismatch erzeugt einen stillen Fehler (Faktor = 0.0, Potenzial = 0),
keine Exception. Bekannte Fehlerquelle, in session-protocol §6.5
dokumentiert. Abgleich: `cat src/aect/domain/types.py` vor jedem
neuen Config-Key.

---

## Konsequenzen

**Positiv:**
- Vollstaendig deterministisch und ohne Mocks testbar.
- `_calculate_roi_values()` in Unit-Tests isolierbar ohne Pydantic-Schema.
- Property-Based Tests (Hypothesis) pruefen numerische Invarianten
  (`expected_benefit <= theoretical_potential`).
- Config-Wechsel (Stundensaetze, Schwellen) ohne Code-Aenderung moeglich.

**Einschraenkungen:**
- Stiller Fehler bei unbekanntem Land/Level erfordert Awareness.
  Mitigation: Phase-B-Validierung im Application Service.
- `frequency_per_year` ist ein Jahreswert ohne Periodenkonzept.
  Sub-annuale Eingaben sind nicht unterstuetzt (Post-v1).
- `_FREQUENCY_TO_ANNUAL` enthaelt UPPERCASE-Keys; `FrequencyUnit` hat
  lowercase-Values (StrEnum). Funktioniert nur weil `calculate_roi()`
  "ANNUALLY" hardkodiert - nicht durch direkte Enum-Value-Nutzung.
  Technical Debt, adressiert in Phase-A-Review.

---

## Interview-Verteidigbarkeit (Vorfilter-Schwellen)

**20.000 EUR theoretisches Potenzial:** Unterhalb dieser Schwelle deckt das theoretische
Potenzial nicht einmal den administrativen Overhead einer Umsetzung (Projektmanagement,
Change Management, initialer Aufwand). Eine 2:1-Mindest-Ratio ist konservativ und
vertretbar.

**120 Stunden/Jahr:** Entspricht ca. 0,06 FTE. Unterhalb dieser Marke ist der
Automatisierungsgewinn marginal und der Change-Management-Aufwand uebersteigt den Ertrag.
Der Schwellenwert stammt aus dem v5-Bewertungsmodell und wurde als generischer Platzhalter
mit IP-Trennung implementiert (interne Referenz (entfernt) SS5).

**5.000 EUR Netto-Nutzen:** Stellt sicher, dass der Use Case nach Abzug der Lizenzkosten
einen positiven Beitrag leistet. Ohne diesen Filter koennte ein Use Case mit hohem Potenzial,
aber hohen Lizenzkosten faelschlicherweise als wirtschaftlich attraktiv eingestuft werden.

## Verworfene Alternativen

**Pandas-basierte Berechnung:** Overhead unnoetig fuer diese Datenmenge.
Decimal + Dataclass ist leichter, schneller, direkt testbar.

**Schwellen hardkodiert:** IP-Risiko (interne Referenz (entfernt) §5) und fehlende
Kalibrierbarkeit sprechen dagegen.
