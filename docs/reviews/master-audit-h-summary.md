# Master-Audit H — Konsolidierung, Triage & SHIP-Gate (Session 10)

**Datum:** 2026-07-06 · **Auditor-Rolle:** Externer Senior-Auditor
(AI Engineering + Security + Solution Architecture) · **Basis:** HEAD `63c6abc`,
Tag `v3.1.0`, alle Sessions H-S0…H-S9 (50 Findings H-001…H-050).
**Diese Session darf** `docs/reviews/` + `known_limitations.md` schreiben,
**kein** Produktivcode-Fix. Regression + Fresh-Clone read-only reproduziert.

---

## 0. Regression-Endlauf (read-only, gegen S0-Baseline)

| Gate | Ergebnis | vs. S0 | Kommando |
|---|---|---|---|
| pre-commit --all-files | **10/10 Passed** | = | `uv run pre-commit run --all-files` |
| pytest (CI-aequiv.) | **715 passed, 5 skipped, 95 %** | = | `AECT_AZURE_OPENAI_ENDPOINT= uv run pytest -q` |
| mypy src/ | **0 Issues, 78 files** | = | `uv run mypy src/` |
| Frontend build | **Erfolg, 7 Routen** | = | `npm run build` |
| Frontend lint | **kaputt (lintet `.next/`)** | = (H-003/H-039) | `npm run lint` |
| **Fresh-Clone Demo** | **lauffaehig < 10 Min (Mock)** | neu | s. §6 |

**Kein Regress gegenueber S0.** Die Toolchain-Gates sind stabil gruen; die einzige
rote Stelle (Frontend-Lint) ist ein bekanntes, seit S0 unveraendertes Tooling-Finding.

---

## 1. Master-Findings-Register (alle 50, Severity × Layer)

**Gesamtzahlen:** **P0: 2 · P1: 12 · P2: 27 · P3: 8 · NV: 1 (aufgeloest)** = 50.

### P0 — Blocker (2)
| ID | Layer | Kurztitel | Typ |
|---|---|---|---|
| H-001 | Doku/Interview | interview-qa nennt 97 % Coverage — Ist 95 % | Doku-Drift |
| H-046 | Docs/Security | README + interview-qa zeigen auf FALSCHE Test-Orte fuer Injection/Red-Team-Tests | Doku-Drift |

### P1 — Should-fix (12)
| ID | Layer | Kurztitel |
|---|---|---|
| H-002 | Doku/Interview | interview-qa "449 Tests" — Ist 715 |
| H-008 | Domain/Scoring | types.py-Docstring PERSONAL=1, Code =2 |
| H-009 | Domain/Zonen | Zone nutzt GROSS-Nutzen (vor Lizenz) — 5k-Netto-Case = LIKELY_WIN, widerspricht ADR-002 |
| H-010 | Domain | Handlungsdruck-Skala 1–4, Report/Docs sagen 1–5 |
| H-011 | Domain/Config | 12 Enum-Laender, 3 konfiguriert → 9 still ROI=0 (irrefuehrender Grund) |
| H-012 | Domain/Config-Doku | ROIConfig-Docstring zeigt obsolete UPPERCASE/HIGH-MEDIUM-Keys |
| H-016 | Application/Ports | LLMPort fett — Prompt-Load + Validierung in Adapter geleakt |
| H-018 | Application/Security | Delimiter als "primaere Verteidigung" deklariert, vom Input brechbar |
| H-027 | S4/Logging | "Logging-Allowlist" nur Kommentar, nicht durchgesetzt |
| H-034 | S5/Lifecycle | Decision→Status-Kopplung ueberschreibt fortgeschrittenen Lifecycle |
| H-038 | S6/CSV | CSV-Export neutralisiert Formel-Injection nicht (`= + - @`) |
| H-047 | Docs/Ehrlichkeit | known_limitations verschweigt 3 belegte Schwaechen (Injection-Bypass, Country-0, Gross-Net) |

### P2 — Nice-to-have (27)
| ID | Layer | Kurztitel |
|---|---|---|
| H-003 | Frontend/Tooling | `npm run lint` lintet `.next/` (43k Fehler) |
| H-004 | Doku | CLAUDE.md "41 ADRs" — Ist 55 |
| H-005 | Umgebung/API | non-EU `.env` → 15 lokale Test-Failures; EU-Guard 500 (Test-Harness-Artefakt, s. S9) |
| H-006 | Fresh-Clone | Quick Start ruft uvicorn/pytest vor `.env`-Abschnitt |
| H-013 | Domain/Dead-Code | FrequencyUnit vestigial |
| H-014 | Domain/Hexagonal | domain/ macht Datei-I/O + yaml-Import |
| H-015 | Domain/Cruft | toter RESTRICTED-Kommentar + 2 unerreichbare Feasibility-Flags |
| H-017 | Application/Security | Injection-Regex trivial umgehbar (5/5 Bypass), Flag-not-Block |
| H-019 | Application/Observability | Cost-Logging dezentral, kein Chokepoint |
| H-020 | Tests | MockLLMAdapter maskiert Structured-Success-Pfad |
| H-021 | Application | parse_structured_llm_output toleriert keinen Markdown-Fence |
| H-022 | RAG/Citation | Halluzinationsschutz gilt nur fuer [N]-Marker, nicht Fliesstext |
| H-023 | RAG/Compliance | Citation-Duplikate (dokumentiert, Ist bestaetigt) |
| H-025 | RAG/KB-Hygiene | interne ADR-Referenz im retrievebaren KB-Text |
| H-028 | S4/Test-Hermetik | `uv run pytest` liest Entwickler-`.env` (= H-005) |
| H-029 | S4/Rate-Limit | Auth laeuft vor slowapi — fehlgeschlagene Auth nicht limitiert |
| H-030 | S4/Injection | detect_injection_patterns fehlt auf 2/5 LLM-Pfaden |
| H-031 | S4/Logging | `error=str(exc)` kann LLM-Output-Fragmente loggen |
| H-035 | S5/Async | GET /cases auf blockierendem Sync-Pfad |
| H-039 | S7/Tooling | `npm run lint` unbrauchbar + CI-ungated (= H-003) |
| H-041 | S7-LIVE/Board | Quadranten-Labels ueberlappen Achsen-Ticks |
| H-042 | Tests | Resilient generate_ideation/sketch NULL Tests |
| H-043 | Tests | Sketch kein 502/503-Test |
| H-044 | Packaging | pyproject 1.2.0 vs v3.1.0 — **live in `/health`** |
| H-048 | Docs | limitations.md "14 Punkte" — Ist 20 |
| H-049 | Docs/Portfolio | README-Screenshots existieren nicht |
| H-050 | Docs/Politur | Tippfehler in Kern-Dokumenten |

### P3 — Backlog (8)
| ID | Layer | Kurztitel |
|---|---|---|
| H-024 | RAG/KB | Drittland-Transfer (DSGVO Kap. V) fehlt |
| H-026 | RAG/Deployment | Default-Deployment RAG dormant (MockRetriever) |
| H-032 | S4/Headers | HSTS/Referrer-/Permissions-Policy fehlen |
| H-033 | S4/CORS | Preflight-Methoden-Enumeration |
| H-036 | S5/Determinismus | GET /cases ohne stabilen Sort-Tiebreak |
| H-037 | S5/Defense | Backend-Response ohne Cache-Control: no-store |
| H-040 | S7/Doku | frontend/CLAUDE.md nennt Next.js 15 (Ist 16) |
| H-045 | Tests/Infra | kein pytest-randomly (Order-Unabhaengigkeit NV) |

### NV — aufgeloest (1)
| ID | Status |
|---|---|
| H-007 | **AUFGELOEST in S8**: Agreement 9/24=37,5 %, Kappa 0,33 / 58,3 % exakt reproduziert |

---

## 2. Kreuz-Session-Muster (systemisch)

Einzeln sind viele Findings P1/P2. Vier Muster ziehen sich durch mehrere Sessions
und sind zusammen aussagekraeftiger als die Summe.

### S-1 · Doku-Drift ohne Sync-Mechanismus — **das systemische Kern-Problem**
**Findings:** H-001, H-002, H-004, H-008, H-010, H-012, H-040, H-044, H-046, H-048, H-050 (11).
Die Doku-Zahlen und Pointer werden frei getippt und driften vom Code: Coverage
(97/95), Test-Count (449/715), ADR-Zahl (41/55), Enum-Doku (PERSONAL, 1-5-Skala,
UPPERCASE-Keys), Next-Version, Paketversion, Test-Orte, Limitations-Zahl.
**Beide P0 (H-001, H-046) sind Instanzen genau dieses Musters.** Fuer ein Projekt,
dessen Kern-These "jede Aussage aus dem Repo verteidigbar" ist, ist das die
gefaehrlichste Schwaeche: nicht ein einzelner falscher Wert, sondern ein fehlender
Mechanismus, der Doku an Code bindet. **Root-Cause-Fix > Einzelfixes.**
**Richtung:** portfolio-facing Zahlen aus der Toolchain generieren (Coverage-Badge,
Test-Count, ADR-Count per Skript in CI erzeugen statt in README/interview-qa/CLAUDE.md
frei zu pflegen); Test-Ort-Verweise aus einer Quelle.

### S-2 · Security-by-Convention statt strukturell
**Findings:** H-017, H-018, H-027, H-030, H-031, H-047 (6).
Mehrere als "Schutz" praesentierte Mechanismen sind Konvention/Kommentar, nicht
erzwungen: Injection-Regex trivial umgehbar (5/5) und nur Flag-not-Block (H-017);
Delimiter vom Input brechbar, aber als "primaer" deklariert (H-018); "Logging-
Allowlist" existiert nur als Kommentar (H-027); Injection-Check fehlt auf 2/5
LLM-Pfaden (H-030); `error=str(exc)` kann Output leaken (H-031). Der beworbene
"4-lagige Injection-Schutz" + "Allowlist" ist schwaecher als dargestellt.
**Blast-Radius real begrenzt** (kein Secret im System-Prompt, Single-User, Advisory-
Output) → **kein Live-Exploit, kein neuer P0** — aber eine Security-Interview-
Haftung. Guenstigste Minderung: H-047 (ehrliche Limitation, in dieser Session
umgesetzt) + die kleinen Struktur-Fixes H-027/H-030/H-031.

### S-3 · Single-Source-of-Truth-Verletzungen im Code
**Findings:** H-009, H-011, H-014, H-016, H-019 (5) + historisch known #14 (F-001, behoben).
Wiederkehrend zwei Quellen fuer eine Wahrheit: Zone rechnet Gross- vs. Net-Benefit
(H-009, widerspricht ADR-002); Country-Enum vs. Config (H-011); Cost-Logging an 7
Stellen statt Chokepoint (H-019); Prompt-Orchestrierung mal Service, mal Adapter
(H-016). Das Projekt hat EINEN solchen Fall bereits gefixt (Vorfilter-Schwellen,
F-001) — das Muster besteht anderswo fort.

### S-4 · Generative v3.1-Features duenn getestet/abgesichert
**Findings:** H-020, H-042, H-043 (3).
Der reale Parse-/Retry-/502-Pfad der zwei Vorzeige-Features (Ideation, Skizze) laeuft
im CI nur gegen den bypassenden Mock; der Azure-/Resilient-Pfad ist nur in
`_live`-Tests (skipped). Portfolio-Kante an den neuesten Features.

---

## 3. P0-Fixplan (mit Aufwand)

| P0 | Fix-Richtung | Aufwand | Reklassifizierung? |
|---|---|---|---|
| **H-001** | In `docs/interview-qa.md` beide "97%"-Vorkommen (Z.274, 281) → "95%". | **≤ 1 Tag** (Minuten) | Nein — bleibt P0 (Interview-Blamage, aber trivial). |
| **H-046** | In `README.md:396` und `interview-qa.md:107` den Test-Ort auf `tests/application/test_sanitization.py` (Primaer) + API-Tests korrigieren. | **≤ 1 Tag** (Minuten) | Nein — bleibt P0. |

**Beide P0 sind reine Doku-Edits, je < 1 Tag, kein Code-Blocker.** Im selben Pass
mitzunehmen (gleiche Dateien): **H-002** (449→715, interview-qa) und **H-047**
(Limitations, hier bereits ergaenzt). Kein P0 ist >1 Tag → keine Backlog-
Reklassifizierung noetig.

---

## 4. Limitations-Triage (alle 20 known + neue)

| # | Limitation | Verdikt |
|---|---|---|
| 1 | Praediktive Validitaet nicht messbar | **bleibt** (struktureller Design-Limit, ehrlich) |
| 2 | Hard-Threshold-Brittleness | **bleibt** (teils via confidence_score gemildert) |
| 3 | Expert-Agreement kleines Sample (n=24) | **bleibt** |
| 4 | Synthetic Cases unlabeled | **bleibt** (bewusst, ADR-0029) |
| 5 | Statische Wissensbasis | **bleibt** / v2 |
| 6 | Citation-Dedup fehlt (= H-023) | **bleibt** / kleiner Fix moeglich |
| 7 | PII: Regex kein NER | **bleibt** |
| 8 | LLM-Output Graceful Degradation | **bleibt** |
| 9 | Compliance advisory | **bleibt** (Kern-Prinzip) |
| 10 | Embedding nicht domain-spezifisch | **bleibt** |
| 11 | Kein Produktivbetrieb | **bleibt** |
| 12 | Frontend lokal | **bleibt** |
| 13 | ADR-Doppelserie | **bleibt** (bewusste Schuld) |
| 14 | Vorfilter zwei Quellen | **BEHOBEN** (F-001) |
| 15 | Monitoring manuell | **bleibt** |
| 16 | Status-Historie nur Snapshots | **bleibt** / v2 |
| 17 | Board-Quadranten Platzhalter | **bleibt** (bewusst) |
| 18 | Generative Features nicht golden-eval-abgedeckt | **bleibt** (+ H-042/H-043 = Test-Fix-Kandidaten) |
| 19 | Dedup O(n^2) on-read | **bleibt** (bewusst) |
| 20 | Aehnlichkeit = Text-Naehe | **bleibt** |
| **21 (neu)** | Injection-Erkennung = Best-Effort-Observability, kein Control (H-017/H-018/H-030) | **jetzt dokumentiert** (§known_limitations) |
| **22 (neu)** | Country-Coverage 3/12 committed → still ROI=0 (H-011) | **jetzt dokumentiert** |
| **23 (neu)** | Zone rechnet Gross-Benefit vor Lizenz (H-009) | **jetzt dokumentiert** |
| **24 (neu)** | CSV-Export ohne Formel-Injection-Schutz (H-038) | **dokumentiert + Code-Fix-Kandidat** (P1, code out-of-scope hier) |

Die uebrigen P1/P2/P3-Findings sind **Fixes**, keine Limitations — sie gehoeren in
den Fix-Backlog, nicht in known_limitations (sonst wird die Ehrlichkeits-Liste zur
Bug-Ablage).

> **Folge-Drift durch diese Session (ehrlich vermerkt):** Das Hinzufuegen von
> #21-#24 hebt die Limitations-Zahl von **20 auf 24**. Damit ist `cv-bullets.md:71`
> ("20 Limitationen offen kommuniziert") jetzt **stale** und muss im Fix-Pass auf
> 24 gezogen werden -- exakt das Muster S-1. `README.md:205` ("#18-#20") bleibt
> korrekt (Bereichsverweis auf existierende Punkte). Ich fuege die Zahl bewusst
> NICHT in cv/README nach (Career-Doku ist nicht Teil der erlaubten Schreib-Menge
> dieser Session).

---

## 5. Fresh-Clone-Test (Task 6)

Frischer Clone (`git clone <repo>` → `v3.1.0`), `uv sync` (~2 s, uv-Cache),
`uvicorn` im Mock-Modus (kein Azure/Chroma):

- `GET /health` → `200 {"status":"ok","version":"1.2.0"}` **← H-044 live sichtbar**
- `POST /triage` (Mock, Beispiel-Case) → vollstaendiger deterministischer Verdict
  (`passed_vorfilter:true`, `routing: AUTOMATION_RECOMMENDED`, Signale) in < 1 s.

**Verdikt:** Der **deterministische** Demo-Pfad (Problem → Triage → Verdict) ist aus
einem frischen Clone in **< 10 Min ohne Azure/Chroma** lauffaehig. **Ehrlich:** die
LLM-/RAG-Schritte (Schaerfung, Loesungsvorschlag, Quellen) liefern im Mock-Modus
**Platzhalter** — der volle generative Demo-Pfad braucht Azure-Credentials (+ Chroma
fuer echte Citations). Der `AECT_API_KEY` muss vor dem ersten Request gesetzt sein
(H-006: im README erst nach dem Quick-Start-Block erklaert).

---

## 6. IP-Status (Task 7) — **Boundary NICHT erfuellt**

Der Auftrag bat, zu **bestaetigen**, dass die IP-Klaerung vorliegt. Der Repo-Befund
sagt das **Gegenteil**:

- `README.md:244`: "IP-Klaerung **ausstehend**".
- `docs/career/cv-bullets.md:89`: "Nach IP-Klaerung (vertraglich bedingt) **veroeffentlichen**".
- `docs/career/linkedin-case-study.md:99`: "Veroeffentlichung erst **nach** vertraglicher IP-Klaerung".
- Kein SDR-Dokument im Repo (die in known #19 / interview-qa referenzierte
  `SDR-0002` ist nicht eingecheckt — vermutlich IP-sensitiv, bewusst ausgelassen);
  der Klaerungs-Status ist damit **aus dem Repo nicht als "erfuellt" belegbar**.

**Verdikt (NV/Blocker):** Oeffentliche Sichtbarkeit und Bewerbungs-Referenzen sind
nach der **projekteigenen** Grenze **noch nicht freigegeben**. Das ist unabhaengig
von der Code-Qualitaet ein harter Publikations-Gate. Ob die Klaerung ausserhalb des
Repos inzwischen erfolgt ist, ist **in dieser Session nicht verifizierbar** — muss
extern bestaetigt und dann im Repo nachgezogen werden, bevor irgendetwas oeffentlich
referenziert wird.

---

## 7. SHIP-Urteil

**Zweigeteilt — kein Weichspuelen:**

**a) Technischer Build:** **ship-faehig.** Kein Code-P0, Regression durchgehend gruen
(715/95%/mypy 0/Build), Fresh-Clone-Demo lauffaehig, Architektur (Hexagonal,
Regeln-vor-LLM, ADR-Echtheit) traegt. Die 12 P1 sind echte, aber nicht "falsche"
Qualitaetsluecken.

**b) Portfolio-/Interview-Zweck:** **NICHT ship-faehig — 2 offene P0.**
- **H-001** (97 % statt 95 % im Uebungsdokument) und **H-046** (falsche Test-Orte in
  README + interview-qa) sind exakt die Blamage-Fallen, gegen die das Projekt antritt
  ("jede Aussage aus dem Repo verteidigbar"). Ein blind uebender Kandidat zitiert sie
  woertlich und faellt live auf. **Beide < 1 Tag fixbar.**

**c) Publikation:** **gesperrt** durch die IP-Boundary (§6), unabhaengig von a/b.

**Konsequenz:** Kein Public-Ship, keine Bewerbungs-Referenz, bis (1) die 2 P0 (+ H-002
im selben Doc) gefixt sind und (2) die IP-Klaerung extern bestaetigt und im Repo
nachgezogen ist. Danach ist der technische Stand vorzeigefertig.

---

## 8. Versions-Entscheidung (Task 9)

Die anstehenden Korrekturen (2 P0 + H-002/H-047/H-048/H-050 Doku, optional H-044
Paketversion/`/health`) sind substanziell genug fuer einen eigenen Patch-Tag:
**Empfehlung nach den Fixes: `v3.1.1`** (docs/limitations/packaging-Korrekturen,
kein Verhaltens-Change am Kern). **Jetzt NICHT taggen** — der Tag kommt nach der
Fix-Freigabe, nicht in diesem read-only/Doku-Konsolidierungs-Schritt. Ohne Fixes
bleibt es `v3.1.0`.

---

## 9. Was diese Session NICHT konnte

- **Echte LLM-/RAG-Demo im Fresh-Clone** — kein Azure-Call (Budget); nur Mock-Pfad
  verifiziert.
- **IP-Klaerungs-Status extern** — aus dem Repo nur als "ausstehend" belegbar (§6).
- **CI-Status (GitHub Actions: bandit/gitleaks/pip-audit)** — laeuft remote, lokal
  nicht sichtbar; lokale Aequivalente (ruff/mypy/pre-commit) gruen.
- **Code-Fixes** — per Auftrag read-only fuer Produktivcode; nur Doku/Limitations
  geschrieben.
