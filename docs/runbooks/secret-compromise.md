# Runbook: Secret Compromise — AECT

> Gilt fuer: Azure-OpenAI-Key, AECT-API-Key, DB-Pfad im Repo.

---

## Symptome

- Secret in `git log` sichtbar (auch in aelterem Commit)
- Unerwartete Azure-Kosten (Key missbraucht)
- gitleaks-Alert in CI (GitHub Actions)

---

## Rotation: Azure OpenAI API Key

```bash
# 1. Neuen Key im Azure Portal generieren
# 2. .env lokal aktualisieren:
#    AECT_AZURE_OPENAI_API_KEY=<neuer-key>
# 3. Alten Key im Azure Portal deaktivieren
# 4. Server neu starten: uv run uvicorn aect.adapters.api.app:app ...
```

---

## Rotation: AECT API Key

```bash
# .env:
# AECT_API_KEY=<neuer-zufaelliger-wert-min-32-zeichen>
# Server neu starten.
```

---

## Git-Historie bereinigen (Secret committed)

```bash
# WARNUNG: History rewrite -- nur bei privatem Repo,
# wenn kein anderer den Branch gepusht hat.
pip install git-filter-repo
git filter-repo --path .env --invert-paths
git push origin main --force
```

---

## Nach der Rotation

- [ ] Log-Review: Requests mit altem Key, die nicht von dir stammen?
- [ ] Azure Cost Check: Verbrauch im Zeitraum seit Compromise
- [ ] Incident-Response-Runbook ausfuehren (falls Datenleck moeglich)

---

*v1 -- Juni 2026*
