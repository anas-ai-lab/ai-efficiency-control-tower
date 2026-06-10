# Phase A — Review

**Datum:** Juni 2026
**Coverage:** 98% domain, 148 Tests, 10 Snapshot-Cases
**Gate-Status:** Bestanden

---

## Gebaute Artefakte

| Datei | Inhalt (1 Satz) |
|---|---|
| `src/aect/domain/types.py` | 6 StrEnums als kontrolliertes Vokabular fuer alle Domain-Parameter. |
| `src/aect/domain/models.py` | `UseCaseInput` - Pydantic-V2-Schema mit `extra="forbid"`, `frozen=True`, 21 Feldern. |
| `src/aect/domain/roi.py` | Deterministisches ROI-Modell: `calculate_roi()` + `load_roi_config()` + Vorfilter-Pruefung. |
| `src/aect/domain/filters.py` | `apply_prefilter()` - 3 Mindestkriterien (Potenzial, Stunden, Netto-Nutzen). |
| `src/aect/domain/scoring.py` | `compute_composite_score()` - Aufwand-Score aus Komplexitaet + Kosten + Datenschutz-Stufe. |
| `src/aect/domain/zones.py` | `ZoneClassifier` - 3-Zonen-Logik mit Handlungsdruck-Elevation, Schwellen aus YAML-Config. |
| `src/aect/domain/feasibility.py` | `FeasibilityChecker` - Strukturelle Qualitaetspruefung (4 Flags, orthogonal zum ROI). |
| `src/aect/domain/routing.py` | `route_use_case()` - AI-vs-Automation-Routing: 4 Empfehlungen, Signal-Zaehlung + Matrix. |
| `src/aect/domain/pipeline.py` | `evaluate_use_case()` - Orchestriert alle Phase-A-Module zu `TriageResult`. |
| `src/aect/domain/__init__.py` | Oeffentliche API-Exports der Domain-Schicht. |
| `config/roi_config.toml` | Stundensaetze (DE/AT/CH), Evidenz- und Nutzungsfaktoren, Vorfilter-Schwellen. |
| `config/zone_thresholds.yaml` | Zonen-Schwellenwerte und Handlungsdruck-Elevation-Threshold. |
| `docs/adr/ADR-001-roi-modell.md` | Entscheidung: Decimal-Modell, Keyword-only-Parameter, defensives Default bei unbekanntem Land. |
| `docs/adr/ADR-002-zonen-logik.md` | Entscheidung: Zahlen-Interface, Config-Injektion, einstufige Elevation mit Deckel. |
| `docs/adr/ADR-003-ai-vs-automation.md` | Entscheidung: Signal-Zaehlung + Matrix, BORDERLINE als Phase-C-Hook. |

---

## Was ich heute anders designen wuerde

**1. `_cost_tier()` in `pipeline.py` ist ein Proxy, kein echtes Feld.**
Die Funktion mappt `estimated_license_cost_eur` (EUR-Wert) auf eine
Kostenstufe 1-3, weil `compute_composite_score()` einen Integer erwartet.
Das ist eine Heuristik im Orchestrierungscode. Sauberer waere ein
dediziertes `implementation_cost_level: int`-Feld in `UseCaseInput` -
dann entscheidet der Einreicher, nicht eine Schwellenwert-Funktion.
Post-v1-Candidate.

**2. `_FREQUENCY_TO_ANNUAL` in `roi.py` hat UPPERCASE-Keys.**
Die Dict-Keys ("DAILY", "WEEKLY", ...) sind UPPERCASE, aber `FrequencyUnit`
ist ein StrEnum mit lowercase-Values ("daily", "weekly", ...). Kein
aktiver Bug - `calculate_roi()` hardkodiert "ANNUALLY" (Multiplikator 1),
greift also nie auf FrequencyUnit-Values zu. Aber wer `_to_annual_hours()`
direkt mit `FrequencyUnit.DAILY.value` aufruft, bekommt einen `ValueError`.
Mitigation Phase B: wenn sub-annuale Inputs eingefuehrt werden, Keys auf
StrEnum-Values umstellen.

**3. `FeasibilityChecker` hat keine Config-Injektion.**
`_MIN_SITUATION_LEN` und `_MIN_EXAMPLE_LEN` sind Modul-Konstanten.
Fuer Enterprise-Einsatz waeren diese Schwellen konfigurierbar.
Fuer v1 akzeptabel - Feasibility-Check ist Qualitaets-Screening,
nicht Geschaeftslogik.

---

## Offene technische Schulden

| Punkt | Prioritaet | Wann adressieren |
|---|---|---|
| `_cost_tier()` Proxy statt dediziertem `implementation_cost_level`-Feld | Niedrig | Post-v1 beim naechsten UseCaseInput-Schema-Update |
| `_FREQUENCY_TO_ANNUAL` UPPERCASE-Keys vs. StrEnum lowercase-Values | Mittel | Phase B wenn sub-annuale Eingaben eingefuehrt werden |
| Unbekanntes Land/Level → stiller ROI=0-Fehler | Mittel | Phase B: Application Service validiert `country` gegen ROIConfig-Keys |
| Zonen-Schwellen sind Platzhalter, nicht gegen echte v5-Cases kalibriert | Mittel | Phase E (Eval + Experten-Abgleich) |
| Pipeline-Coverage Lines 48 + 73-75 | Erledigt | Tag 21 geschlossen |

---

## Vertrauen ins Phase-A-Design (1-10)

**ROI-Engine:** 9 - deterministisch, getestet, Config-getrennt, defensives Default.
**Zonen-Logik:** 8 - funktioniert, Schwellen noch nicht kalibriert.
**Routing:** 7 - Signal-Heuristiken sind grob; das ist bewusst, Phase C verfeinert.
**Pipeline-Orchestrierung:** 9 - Ausfuehrungsreihenfolge korrekt (ROI vor Vorfilter), TriageResult immutabel.
**Feasibility:** 8 - einfach, klar, testbar; Schwellen koennen in der Praxis zu niedrig sein.

---

## Offene Fragen fuer Phase B

1. Persistenz-ORM: SQLAlchemy Core vs. SQLModel - Entscheidung faellt in Phase B.
2. `country`-Parameter in `evaluate_use_case()`: Kommt aus dem Request
   (Nutzer-Standort) oder aus `UseCaseInput` (Standort der Mitarbeiter)?
   Semantisch ist Letzteres korrekt - erfordert neues Feld im Schema.
3. Idempotency-Key: UUID v4 vom Client oder Hash ueber Input?
   Implikationen fuer Retry-Verhalten und Audit-Trail.
