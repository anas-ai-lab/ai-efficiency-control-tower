# Runbook: Secret Compromise Response

> Gilt fuer: GitHub PAT, Azure-OpenAI-API-Key, AECT-API-Key, DB-Pfade.
> Schwester-Runbook: `incident-response.md` (allgemeine Eindaemmung bei
> Datenleck/Exfiltration). Dieses Runbook fokussiert auf den Lebenszyklus
> eines kompromittierten Credentials: Identify -> Rotate -> Clean -> Audit ->
> Document.

---

## Trigger -- wann dieses Runbook gilt

Genau dann ausfuehren, wenn eines davon zutrifft:

- Ein Credential ist offengelegt (in einem Commit, Log, Screenshot, Prompt,
  Error-Message oder in `.git/config`).
- Verdacht auf unbefugten CI-Zugriff (fremde Workflow-Runs, geaenderte
  Secrets, unerklaerliche Actions-Logs).
- GitHub-Security-Alert (Secret Scanning, Dependabot, Code Scanning) meldet
  ein exponiertes Credential.

Im Zweifel ausfuehren -- Rotation ist billig, ein missbrauchter Key nicht.

---

## Phase 1 -- IDENTIFY

Bevor irgendetwas rotiert wird: feststellen, *welches* Credential, *seit wann*
sichtbar und *wo*.

- **Welches Credential?** GitHub PAT, Azure-OpenAI-API-Key, AECT-API-Key oder
  ein DB-/Pfad-Geheimnis. Jeder Typ hat eine eigene Rotationsprozedur (Phase 2).
- **Seit wann sichtbar?** Commit-Zeitpunkt bzw. Datum des Logeintrags. Bestimmt
  das Audit-Fenster in Phase 4.
- **Wo exponiert?**
  - Lokal: `git config --list --show-origin | grep -i 'url\|token'`
    (PAT landet oft in `.git/config` der Remote-URL).
  - Logs: `grep -rIn 'ghp_\|sk-\|AECT_API_KEY' . --include='*.log'`
  - CI-Umgebung: GitHub -> Settings -> Secrets and variables -> Actions.
  - Committet: `git log --all -S "ghp_"` und `git log --all -S "sk-"`.

---

## Phase 2 -- ROTATE

Zuerst neuen Key erzeugen, dann alten widerrufen -- nie umgekehrt (sonst
Service-Ausfall ohne Ersatz).

### GitHub PAT

1. GitHub -> Settings -> Developer settings -> Personal access tokens.
2. Betroffenes Token **Revoke**.
3. **Generate new token**, Scope minimal: `repo` + `workflow`.
4. Remote-URL/Credential-Helper aktualisieren (siehe Phase 3).

### Azure OpenAI API Key

1. Azure Portal -> betroffene OpenAI-Ressource -> **Keys and Endpoint**.
2. **Regenerate Key** (KEY1 oder KEY2 -- den exponierten).
3. `.env` lokal aktualisieren: `AECT_AZURE_OPENAI_API_KEY=<neuer-key>`.
4. Server neu starten, damit der alte Key nicht weiter im Speicher lebt.

### AECT API Key

1. Neuen Zufallswert erzeugen (min. 32 Zeichen).
2. `.env`: `AECT_API_KEY=<neuer-wert>`; Server neu starten.

---

## Phase 3 -- CLEAN

Exponierte Spuren lokal und in der Historie entfernen.

```bash
# Remote-URL ohne eingebetteten Token (Token gehoert in den Keychain, nie in die URL)
git remote set-url origin https://github.com/anas-ai-lab/ai-efficiency-control-tower.git

# Alten Token aus dem macOS-Keychain loeschen, dann beim naechsten push neu auth'en
git credential-osxkeychain erase
host=github.com
protocol=https
# (leere Zeile schliesst die Eingabe ab)

git push   # fragt nach neuem PAT -> Keychain speichert ihn frisch
```

Pruefen, ob das Secret in der **Historie** liegt:

```bash
git log --all -S "ghp_"
git log --all -S "sk-"
```

Wird ein Treffer gefunden: History-Rewrite noetig. Bei AECT (privates Repo,
Single-Maintainer) ist **BFG Repo Cleaner** oder `git filter-repo` vertretbar:

```bash
# Variante git-filter-repo (entfernt eine ganze Datei aus der History)
git filter-repo --path .env --invert-paths
git push origin main --force   # nur privat + alleiniger Maintainer
```

> Hard-Stop-Hinweis: force-push ist laut Engineering-Constitution normalerweise
> verboten. History-Rewrite zur Secret-Entfernung ist die dokumentierte
> Ausnahme -- bewusst, mit Backup-Branch davor.

---

## Phase 4 -- AUDIT

Schaden bewerten, Missbrauch ausschliessen.

- **GitHub Security tab** pruefen: offene Secret-Scanning-/Code-Scanning-Alerts.
- **Recent CI runs** (Actions): fremde oder unerwartete Workflow-Laeufe im
  Fenster seit dem in Phase 1 bestimmten Zeitpunkt.
- **Token-Nutzung**: Wurde das Credential irgendwo unerwartet verwendet?
  - GitHub PAT: Settings -> Personal access tokens -> "Last used".
  - Azure-Key: Azure Portal -> Metrics/Cost Analysis, Spike im Audit-Fenster?
    (Budget-Alerts liegen bei 10/20/28 EUR -- vgl. `incident-response.md`.)
- Bei Hinweis auf tatsaechlichen Missbrauch -> `incident-response.md` starten.

---

## Phase 5 -- DOCUMENT

Jeden Vorfall in `docs/runbooks/incident-log.md` festhalten (Datei anlegen,
falls nicht vorhanden). Mindestens: Datum, was passiert ist, was getan wurde.

```markdown
## YYYY-MM-DD -- <Kurztitel>

- **Was:** <welches Credential, wo exponiert, seit wann>
- **Wie entdeckt:** <Security-Alert / Log / manuell>
- **Massnahmen:** <rotiert / bereinigt / Historie umgeschrieben>
- **Audit-Ergebnis:** <Missbrauch ja/nein, Kostenwirkung>
```

---

## Referenz aus der Praxis: G-045

Phase-G-Audit, Juni 2026: Ein GitHub PAT war in `.git/config` als Teil der
Remote-URL gespeichert (Klartext, lokal). Kein Push in ein oeffentliches
Artefakt, aber Verstoss gegen die Secret-Hygiene. Behandlung exakt nach diesem
Runbook: PAT revoked + neu erzeugt (Phase 2), Remote-URL auf token-freie HTTPS-
Form gesetzt und Keychain neu befuellt (Phase 3), "Last used" geprueft -- kein
Fremdzugriff (Phase 4), Eintrag im Incident-Log (Phase 5). G-045 ist der Grund,
warum dieses Runbook von der duennen v1 auf die volle 5-Phasen-Form erweitert
wurde (AUDIT-015).

---

*v2 -- Juni 2026 (AUDIT-015, motiviert durch G-045)*
