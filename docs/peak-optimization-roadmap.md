# Peak-Optimization-Roadmap -- AECT als Portfolio-Asset

> Senior-Review aller Optimierungs-/Erweiterungs-Opportunitaeten mit dem Ziel
> maximaler Verteidigbarkeit + Wirkung pro Aufwand -- NICHT "alles bauen".
> Klassifiziert nach Wirkung (hoch/mittel/niedrig) x Aufwand (S/M/L) x IP-Risiko
> (none/low/med/high) x Scope-Fit (Tiefe-nicht-Breite).
>
> Stand: Tag 85 (2026-06-27), nach v1.1.0 + Vollaudit.

---

## Umgesetzt in dieser Session (be3f8aa + Closeout-Commit)

| Opportunity | Wirkung | Aufwand | IP | Beleg |
|---|---|---|---|---|
| C4-Diagramme (L1/L2/L3) + 3 Sequenzdiagramme | hoch | M | none | `architecture.md` |
| architecture.md: Woche-1-Stub raus (beschrieb n8n/Risk-Scorer -- nie gebaut) | hoch | S | none | `architecture.md` |
| ADR-Index (Architecture Decision Log, 41 ADRs) | mittel | S | none | `docs/adr/README.md` |
| Haertere Senior-Reviewer-Fragen (3) | mittel | S | none | `interview-qa.md` |
| Mutation-Spot-Check (manuell, 2/2 gefangen) | mittel | S | none | siehe unten |
| README-Links (Architektur, ADR-Index) klickbar | niedrig | S | none | `README.md` |

**Mutation-Spot-Check (Test-Qualitaet jenseits Coverage):** Zwei gezielte
Mutationen in den Domain-Kern injiziert und Tests gegengeprueft:
1. `zones._base_zone`: `composite <= max` -> `<` (Boundary) -> **1 Test rot** (gefangen).
2. `roi`: `net = expected - license` -> `+` (Arithmetik) -> **2 Tests rot** (gefangen).
Beide reverted. Beleg, dass die Domain-Tests Verhalten pruefen, nicht nur Zeilen
abhaken. Der vollstaendige `mutmut`-Lauf ist v2 (Friktion siehe unten).

---

## Verworfen (bigger, not better)

| Opportunity | Warum verworfen |
|---|---|
| openapi-typescript-Codegen JETZT | Frontend ist iCloud-build-blockiert (AUDIT-017) und nicht in CI (AUDIT-004) -- ungepruefter Codegen einzucheck en erzeugt Drift-Risiko statt es zu beseitigen. Erst nach iCloud-Move + Frontend-CI sinnvoll -> v2. |
| ADR-Doppelserie konsolidieren | G-S6-Entscheidung: Rename von 41 ADRs + Querverweise = hohe Churn, null funktionaler Gewinn (known_limitations #13). |
| Fuzzy-Zonen / Konfidenzintervalle JETZT | Die ehrlich benannte Hard-Threshold-Limitation ist das staerkere Interview-Asset als eine nachgebaute Glaettung ohne empirische Basis (n=3 Golden Cases). Default beibehalten. |
| CV-Bullets-Komplettueberarbeitung | In G-S6 bereits faktengecheckt, keine Drift -- Umschreiben waere Politur ohne Substanz. |
| Demo-Video-Skript | Niedrige Wirkung pro Aufwand fuer ein Repo-Artefakt; ein Reviewer liest README + Code, kein Skript. Optional v2. |

---

## v2 -- dokumentiert, braucht eigenen Record oder Umgebungs-Vorbedingung

| Opportunity | Wirkung | Aufwand | IP | Hinweis |
|---|---|---|---|---|
| `mutmut`-Volllauf auf Domain-Kern | hoch | M | none | Friktion: pytest-`addopts` (`--cov`) kollidiert mit mutmuts Coverage-Stats (`BadTestExecutionCommandsException`). Fix: `[tool.mutmut] runner` ohne Coverage-Flags, eigener Lauf. |
| Frontend-CI-Job (tsc/build/eslint) | hoch | M | none | AUDIT-004; Vorbedingung: Repo aus iCloud (AUDIT-017). |
| openapi-typescript aus FastAPI-Schema | hoch | M | none | Nach Frontend-CI -- ersetzt manuelle `types/api.ts`-Sync, zeigt Produktionsreife. |
| DSGVO-Loeschpfad (Art. 17, kaskadiert) | mittel | L | none | AUDIT-007, eigener ADR/SDR vor Bau. |
| async Repository (`to_thread`/async Port) | niedrig | M | none | AUDIT-001; bei Single-User unkritisch. |
| Mehr Golden-Cases mit unabh. Labels | mittel | M | none | Verbessert Agreement-Signal (aktuell n=3). |
| secret-compromise-Runbook | mittel | S | none | AUDIT-015; nach G-045 real motiviert. |
| SBOM-Generierung in CI | niedrig | S | none | AUDIT-006; haelt SBOM aktuell. |
| Docker Multi-Stage + HEALTHCHECK + .dockerignore | niedrig | S | none | AUDIT-005; nur vor echtem Deploy. |
| Retrieval-Dedup ueber source_id | niedrig | S | none | G-008; erst relevant bei groesserer KB. |

---

## Top 5 Hebel fuer Interview-/Portfolio-Wirkung (Empfehlung)

1. **IP-Entscheidung treffen (load-bearing).** Ohne sie ist NICHTS oeffentlich
   zeigbar -- kein LinkedIn, kein CV-Link, keine Live-Demo. Das ist der einzige
   Hebel, der den gesamten Portfolio-Wert freischaltet. Vorlage:
   `phase-g-review.md` SS6. *Empfehlung: zuerst, vor jeder weiteren Politur.*
2. **Repo aus iCloud + Frontend-CI.** Entgiftet die Umgebung (AUDIT-017) und
   macht das Frontend verifizierbar -- Vorbedingung fuer openapi-typescript und
   einen ehrlichen "alles gruen"-Status inkl. UI. *Empfehlung: direkt nach #1.*
3. **C4-Architektur (UMGESETZT).** Ein Solution-Architect-Reviewer liest zuerst
   die Architektur -- jetzt liegt sie als C4 + Sequenzdiagramme vor, statt eines
   falschen Woche-1-Stubs. *Erledigt diese Session.*
4. **Mutation-Testing vollstaendig (v2).** Das staerkste Test-Qualitaets-Signal
   ("ich messe Qualitaet, nicht nur 97% Coverage"). Spot-Check zeigt: die Tests
   fangen Mutationen. *Empfehlung: v2 nach iCloud-Move, mit mutmut-runner-Fix.*
5. **DSGVO-Loeschpfad (v2).** Schliesst die meistzitierte Compliance-Luecke
   (AUDIT-007) -- relevant fuer DACH-Rollen mit Datenschutz-Bezug. *Empfehlung:
   eigener ADR, vor jedem echten Datenbetrieb.*

Drei der fuenf Hebel sind KEIN Code (IP-Entscheidung, iCloud-Move, Architektur-
Doku). Das ist die ehrliche Botschaft dieser Optimierungsrunde: der groesste
Portfolio-Hebel liegt nicht in mehr Features, sondern in Entscheidung, Umgebung
und Verteidigbarkeit.
