# v3 Cold-Eyes-Audit -- Findings-Status

> Statusdokument zum Cold-Eyes-Audit (Juni/Juli 2026). Phase 1 (Audit) hat
> die Findings F-001 bis F-031 erhoben; dieses Dokument protokolliert den
> Fix-Stand aus Phase 2 (2026-07-02) mit Commit-Referenzen. Findings ohne
> Eintrag in der Tabelle waren nicht Teil des Phase-2-Fix-Scopes
> (P3/v2 -- dokumentieren, nicht bauen).

## Findings-Tabelle

| ID | Thema | Status | Commit |
|---|---|---|---|
| F-001 | Vorfilter ignoriert ROIConfig (hartcodierte Modul-Defaults, Config-Edit = stiller No-op) | fixed | `daea522` |
| F-002 | Case-Mismatch in Config-Keys | fixed (Vorsession) | `501cb29` |
| F-003 | Docstring-Korrektur | fixed (Vorsession) | `c3d8b44` |
| F-005 | Docstring-Korrektur | fixed (Vorsession) | `c3d8b44` |
| F-006 | Kosten-Tiers 5.000/25.000 EUR hartcodiert in domain/pipeline.py | fixed | `62d01ee` |
| F-007 | Kommentar-Korrektur | fixed (Vorsession) | `c3d8b44` |
| F-008 | int(frequency/12)-Truncation stuft 1-11 Vorgaenge/Jahr als NOT_RECURRING ein | fixed | `1aa34d2` |
| F-010 | Idempotency-Race (get->set nicht atomar, Duplikat-Cases bei parallelen Requests) | fixed | `5916d2b` |
| F-011 | Lost-Update-Race: paralleles /sharpen + /propose-solution ueberschreibt ein Narrativ | fixed | `941bae8` |
| F-012 | SQLite-Connections nie geschlossen (Refcount-Abhaengigkeit) | fixed | `b975426` |
| F-013 | Kein WAL-Modus, kein busy_timeout | fixed | `b975426` |
| F-014 | Worst-Case-LLM-Latenz unbegrenzt (nur Per-Attempt-Timeout; Frontend-Fetch ohne AbortSignal) | fixed | `723e015` |
| F-016 | [N]-Citation-Marker ohne Gegenstueck in der Citation-Liste nicht validiert | fixed | `cc4fb90` |
| F-020 | LICENSE-Datei fehlte trotz MIT-Badge | fixed (Vorsession) | `ceb95ba` |
| F-021 | README Doc-Truth | fixed (Vorsession) | `74d394e` |
| F-022 | README Doc-Truth | fixed (Vorsession) | `74d394e` |
| F-023 | README Doc-Truth | fixed (Vorsession) | `74d394e` |
| F-025 | Englische Backend-detail-Strings roh in der deutschen UI | fixed | `a656015` |
| F-026 | Fehlende Security-Response-Header (nosniff, X-Frame-Options, CSP, Server-Header) | fixed | `6787a90` |
| F-027 | OWASP-LLM-Checklist Doc-Truth | fixed (Vorsession) | `7f91c65` |
| F-028 | OWASP-LLM-Checklist Doc-Truth | fixed (Vorsession) | `7f91c65` |
| F-029 | EU-AI-Act-Deadline veraltet (Digital Omnibus) | fixed (Vorsession) | `6f41287` |
| F-030 | Tote Config-Section | fixed (Vorsession) | `501cb29` |
| F-031 | Harte tiktoken-Netzwerkabhaengigkeit | fixed (Vorsession) | `b73e0ac` |
| Infra | Dockerfile-Basis-Images ohne Digest-Pin; kein Container-CVE-Scan in CI | fixed | `49c6ac4` |

Begleitbefund aus der Fix-Arbeit (kein Audit-Finding): der modul-globale
slowapi-Limiter teilte sein 30/min-Budget ueber alle Test-App-Instanzen der
Suite -- mit wachsender Testzahl wurde die Suite flaky (429 statt 201).
Autouse-Reset-Fixture in `tests/adapters/api/conftest.py` (Teil von `5916d2b`).

## IP-Sweep (2026-07-02, Commit `81add54`)

Ziel: kein direkter oder kombinierter Rueckschluss auf ein reales
Firmenumfeld im oeffentlichen Repo. Die entfernten Kennungen werden hier
bewusst NICHT wiederholt -- sie stehen im privaten Sitzungsprotokoll.

**Ersetzt:**

- Eine private Dokument-Kennung in 113 Referenzen ueber 74 Dateien
  (Code-Docstrings, ADRs, docs/, notes/, config/, openapi.json,
  api.generated.ts) durch generische, den Sinn erhaltende Begruendungen
  (vertraglich bedingte IP-Trennung, Projekt-Anforderung/-Zielbild,
  Projekt-Prinzipien, Scope-/Budget-Disziplin, Eval-Methodik,
  Projekt-Zielsetzung).
- Eine Vertrags-Klauselnummer im Learning-Log durch "vertragliche
  Verpflichtung" ohne Klauselangabe.
- Die Gremiumsbezeichnung "Internes Gremium" (4 Stellen) durch
  "AI-Governance-Gremium" (ergaenzt den frueheren Sweep in `4da6900`).
- Formulierungen neutralisiert, die den Zusammenhang "Repo-Inhalt =
  reales Firmenumfeld" explizit bestaetigten (comprehensive-audit
  AUDIT-011-Wortlaut, roadmap-v2-Bewertungsachsen, phase-g-review
  Option B, Tagesnotiz 2026-06-27).
- `config/zone_thresholds.yaml`: widerspruechlicher Header ("INTERNAL --
  This file uses generic placeholders only", Verweis auf eine interne Modellversion)
  ersetzt durch ehrliche Platzhalter-Deklaration.

**Geprueft, unauffaellig:** docs/career/ (cv-bullets, linkedin-case-study --
keine realen Namen/Zahlen/Orgdetails), Stundensaetze (als generische
Platzhalter deklariert, echte Werte gitignored), keine E-Mail-Adressen oder
Firmennamen, keine Standorte/Mitarbeiterzahlen mit Realbezug ("Mitarbeiter"
nur als Domaenenbegriff bzw. in synthetischen Testdaten).

**Als ambivalent geflaggt (Menschen-Entscheid, nicht geaendert):**

1. `config/stack_options.toml` -- die Plattform-Kombination (Open WebUI,
   Copilot Studio, Microsoft Foundry, SAP BTP) ist als "generische
   Plattformbeispiele" deklariert, entspricht aber AUDIT-011: ein
   Enterprise-Stack-Profil ist ein schwaches, breites Signal
   (tausende DACH-Unternehmen). Optionen bleiben wie in AUDIT-011:
   (a) als generisch belassen oder (b) wie roi_config splitten
   (`.example` committen, echte Datei gitignoren + Code-Fallback).
2. Die Faktor-Struktur des ROI-Modells selbst (Evidenz-/Adoptionsfaktoren,
   Zonen-Logik) koennte einem Insider bekannt vorkommen -- sie ist aber
   die zeigbare, generische Methodik und der Kern des Portfolios;
   Entfernen wuerde den Projektzweck aufheben.

## Verifikation

Jeder Commit einzeln gegen die Gates gefahren:
`uv run pytest -q` (517 passed) + `uv run mypy src/` (0 Issues) +
`uv run bandit -r src/ -ll` (0 Findings) + `uv run pre-commit run
--all-files` (alle Hooks gruen). Frontend-Aenderungen (F-014/F-025)
zusaetzlich: `npm run build` + `npm run typecheck` gruen.
Race-Fixes (F-010, F-011) wurden per `git stash` gegen den alten Codepfad
verifiziert: beide Regressionstests schlagen dort fehl.
