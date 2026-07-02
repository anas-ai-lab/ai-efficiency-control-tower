# v3 Cold-Eyes-Audit -- Findings-Status

> Statusdokument zum Cold-Eyes-Audit (Juni/Juli 2026). Phase 1 (Audit) hat
> die Findings F-001 bis F-031 erhoben; dieses Dokument protokolliert den
> Fix-Stand aus Phase 2 (2026-07-02) mit Commit-Referenzen. Findings ohne
> Eintrag in der Tabelle waren nicht Teil des Phase-2-Fix-Scopes
> (P3/v2 -- dokumentieren, nicht bauen).

## Findings-Tabelle

| ID | Thema | Status | Commit |
|---|---|---|---|
| F-001 | Vorfilter ignoriert ROIConfig (hartcodierte Modul-Defaults, Config-Edit = stiller No-op) | fixed | `4e71e48` |
| F-002 | Case-Mismatch in Config-Keys | fixed (Vorsession) | `01747d8` |
| F-003 | Docstring-Korrektur | fixed (Vorsession) | `1ddb6aa` |
| F-005 | Docstring-Korrektur | fixed (Vorsession) | `1ddb6aa` |
| F-006 | Kosten-Tiers 5.000/25.000 EUR hartcodiert in domain/pipeline.py | fixed | `e67cb42` |
| F-007 | Kommentar-Korrektur | fixed (Vorsession) | `1ddb6aa` |
| F-008 | int(frequency/12)-Truncation stuft 1-11 Vorgaenge/Jahr als NOT_RECURRING ein | fixed | `156be2b` |
| F-010 | Idempotency-Race (get->set nicht atomar, Duplikat-Cases bei parallelen Requests) | fixed | `1acd972` |
| F-011 | Lost-Update-Race: paralleles /sharpen + /propose-solution ueberschreibt ein Narrativ | fixed | `530f62f` |
| F-012 | SQLite-Connections nie geschlossen (Refcount-Abhaengigkeit) | fixed | `5ffe5f6` |
| F-013 | Kein WAL-Modus, kein busy_timeout | fixed | `5ffe5f6` |
| F-014 | Worst-Case-LLM-Latenz unbegrenzt (nur Per-Attempt-Timeout; Frontend-Fetch ohne AbortSignal) | fixed | `3103ef9` |
| F-016 | [N]-Citation-Marker ohne Gegenstueck in der Citation-Liste nicht validiert | fixed | `121fc62` |
| F-020 | LICENSE-Datei fehlte trotz MIT-Badge | fixed (Vorsession) | `56b5e9a` |
| F-021 | README Doc-Truth | fixed (Vorsession) | `9c5a68a` |
| F-022 | README Doc-Truth | fixed (Vorsession) | `9c5a68a` |
| F-023 | README Doc-Truth | fixed (Vorsession) | `9c5a68a` |
| F-025 | Englische Backend-detail-Strings roh in der deutschen UI | fixed | `7299870` |
| F-026 | Fehlende Security-Response-Header (nosniff, X-Frame-Options, CSP, Server-Header) | fixed | `e605b3a` |
| F-027 | OWASP-LLM-Checklist Doc-Truth | fixed (Vorsession) | `4814b3d` |
| F-028 | OWASP-LLM-Checklist Doc-Truth | fixed (Vorsession) | `4814b3d` |
| F-029 | EU-AI-Act-Deadline veraltet (Digital Omnibus) | fixed (Vorsession) | `da18ca9` |
| F-030 | Tote Config-Section | fixed (Vorsession) | `01747d8` |
| F-031 | Harte tiktoken-Netzwerkabhaengigkeit | fixed (Vorsession) | `c855e9e` |
| Infra | Dockerfile-Basis-Images ohne Digest-Pin; kein Container-CVE-Scan in CI | fixed | `4bde671` |

Begleitbefund aus der Fix-Arbeit (kein Audit-Finding): der modul-globale
slowapi-Limiter teilte sein 30/min-Budget ueber alle Test-App-Instanzen der
Suite -- mit wachsender Testzahl wurde die Suite flaky (429 statt 201).
Autouse-Reset-Fixture in `tests/adapters/api/conftest.py` (Teil von `1acd972`).

## IP-Sweep (2026-07-02, Commit `e901fe5`)

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
  "AI-Governance-Gremium" (ergaenzt den frueheren Sweep in `92554af`).
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

**Als ambivalent geflaggt (Menschen-Entscheid):**

1. `config/stack_options.toml` (AUDIT-011) -- die konkrete Kombination der
   gelisteten Plattform-Produkte war ein Enterprise-Stack-Signal.
   ENTSCHIEDEN + UMGESETZT (2026-07-02): nach dem roi_config-Muster
   genericisiert -- committete Datei enthaelt nur noch Plattform-KATEGORIEN,
   konkrete Namen gehoeren in die gitignorte `stack_options.local.toml`,
   `lookup_stack_options()` bevorzugt die local-Datei mit Fallback auf die
   Platzhalter (Fresh Clone bleibt funktionsfaehig). Vendor-Nennungen der
   alten Kombination auch aus README/ADR-0008/known_limitations/Reviews/
   Notes entfernt.
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
