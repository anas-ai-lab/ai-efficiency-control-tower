# 0042 -- Retention-Enforcement als Scheduled Job: Design, kein Deploy

**Status:** Accepted
**Datum:** 2026-07-02
**Phase:** G (Privacy-Haertung)

## Kontext

`scripts/enforce_retention.py` (A1, dieselbe Session) loescht Cases aelter
als `AECT_RETENTION_DAYS` ueber den bestehenden Art.-17-Loeschpfad
(`TriageService.delete_case()`, ADR-0038). Das Script ist fuer Cron-Betrieb
gebaut (kein interaktives Bestaetigen, Default loescht tatsaechlich) -- es
braucht aber einen Ausfuehrungsmechanismus. Analog ADR-0035 (Azure
Container Apps: Design fuer den API-Deploy, kein echtes Deployment) und
ADR-0041 (Key-Vault-Settings-Source: Design + Verifikation ohne Live-Azure)
wird hier derselbe Grundsatz angewendet: der Scheduling-Pfad wird entworfen
und dokumentiert, nicht live betrieben -- aus denselben Gruenden wie
ADR-0035 (IP-Klaerung steht aus, kein produktiver Traffic, Budget-Deckel).

## Entscheidung

Azure Container Apps **Jobs** (nicht die "App"-Ressource aus ADR-0035) mit
`triggerType: Schedule` fuehren `enforce_retention.py` periodisch aus, im
selben Container-Image wie die API (kein separates Image noetig -- der
Job ueberschreibt nur den Start-Befehl).

```bash
# Environment wiederverwendet (ADR-0035) -- kein zweites Environment noetig.
az containerapp job create \
  --name aect-retention-job --resource-group aect-rg \
  --environment aect-env \
  --trigger-type Schedule \
  --cron-expression "0 3 * * *" \
  --image aectregistry.azurecr.io/aect-api:latest \
  --command "uv" "run" "python" "scripts/enforce_retention.py" \
  --cpu 0.25 --memory 0.5Gi \
  --replica-timeout 300 \
  --replica-retry-limit 1 \
  --system-assigned

# Secrets/Config identisch zur API-App: Key-Vault-Reference statt Klartext
# (ADR-0041), AECT_RETENTION_DAYS als normale Env-Var (kein Secret).
az containerapp job secret set \
  --name aect-retention-job --resource-group aect-rg \
  --secrets "aect-api-key=keyvaultref:<vault-uri>/secrets/api-key,identityref:<mi-id>"
```

`0 3 * * *` (taeglich 03:00 UTC) ist eine Beispiel-Kadenz -- bei
`AECT_RETENTION_DAYS=90` ist taeglich deutlich haeufiger als noetig, aber
unkritisch (`find_expired_case_ids` ist ein reiner Read-Filter, ein Lauf
ohne abgelaufene Cases ist ein No-op-Log-Eintrag, keine Nebenwirkung).
Eine woechentliche Kadenz (`0 3 * * 1`) waere ebenso vertretbar; taeglich
ist konservativer bei uebersichtlichem Zusatz-Overhead.

## Begruendung

| Alternative | Warum verworfen |
|---|---|
| Azure Function (Timer-Trigger) | Zweite Compute-Plattform neben Container Apps -- fuer EIN periodisches Script unnoetiger Architektur-Bruch, wenn ACA-Jobs denselben Zweck im selben Environment/Image abdecken. |
| Cron auf einer dauerhaft laufenden VM | Widerspricht dem Budget-/Teardown-Prinzip aus ADR-0035 (kein Dauerlaeufer fuer sporadischen Bedarf) -- ein Scheduled Job startet nur zur Ausfuehrung, keine laufenden Kosten dazwischen. |
| Manuelles Ausfuehren (kein Scheduling) | Retention ist eine Compliance-Pflicht (DSGVO Art. 5(1)(e)), kein "wenn Zeit ist"-Task -- ein vergessener manueller Lauf unterlaeuft den Zweck. Das Script ist deshalb bewusst NICHT interaktiv (kein Bestaetigungs-Prompt, Default loescht). |

Kein separates Job-Image: derselbe `aectregistry.azurecr.io/aect-api`-
Container wie die API-App (ADR-0035) mit ueberschriebenem `--command` --
ein zusaetzliches Image-Build/-Registry-Ziel nur fuer ein einzelnes Script
waere unverhaeltnismaessiger CI-/Registry-Overhead.

## Konsequenzen

**Positiv:**
- Wiederverwendet Environment, Image und Key-Vault-Secret-Pfad aus
  ADR-0035/0041 vollstaendig -- kein neuer Infrastruktur-Baustein.
- `--replica-retry-limit 1`: ein fehlgeschlagener Lauf wird einmal
  wiederholt, dann eskaliert (Azure-Monitor-Alert, ausserhalb dieses
  Scopes) statt endlos zu retryen.

**Negativ / Trade-offs:**
- Ungetestet bleibt zwangslaeufig der echte Scheduled-Job-Betrieb (Cron-
  Trigger-Zuverlaessigkeit, Timeout-Verhalten bei vielen abgelaufenen
  Cases, Managed-Identity-Handshake) -- dieselbe dokumentierte Grenze wie
  ADR-0035/0041: Design verifiziert, Live-Infrastruktur nicht.
- `--replica-timeout 300` (5 Minuten) ist eine Schaetzung ohne Lastdaten --
  bei sehr vielen abgelaufenen Cases (deutlich > Portfolio-Groessenordnung)
  muesste der Wert nachjustiert werden.

**Neutral / Folgeentscheidungen:**
- Kein A2-eigener Commit: dieses Dokument ergaenzt A1 (Script + Tests)
  inhaltlich direkt und macht dessen Cron-Design-Annahme ("fuer Cron-
  Betrieb gedacht") konkret nachvollziehbar -- gleicher Commit wie A1.
