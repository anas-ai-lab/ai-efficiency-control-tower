# Runbook: Incident Response — AECT

> Erkennung -> Eindaemmung -> Bewertung -> Dokumentation.
> Gilt fuer: unerwartete LLM-Exfiltration, kompromittierter API-Key,
> PII-Leak in Logs, aussergewoehnliche Azure-Kosten.

---

## 1. Erkennung (manuell -- kein automatisiertes Alerting in v1)

```bash
# Logs auf 401/403-Haeufungen pruefen
grep '"status": 401\|"status": 403' <logfile>

# Rate-Limit-Treffer (429) -- Brute-Force oder missbrauchter Key
grep '"status": 429' <logfile>

# PII in Logs -- Allowlist-Verletzung (darf nicht vorkommen)
grep -i '"use_case"\|"title"\|"current_state"' <logfile>
```

Azure Cost Alerts (Budget in Azure Portal): konfiguriert bei 10 / 20 / 28 EUR.
Unerwarteter Spike -> Key-Missbrauch pruefen.

---

## 2. Sofortmassnahmen

```bash
# Server stoppen
pkill -f uvicorn

# API-Key sofort deaktivieren (.env aendern)
# AECT_API_KEY=<neuer-zufaelliger-wert>

# ChromaDB stoppen (falls Embedding-Daten betroffen)
docker compose stop
```

---

## 3. Bewertung

| Frage | Pruefung |
|---|---|
| use_case-Inhalt in Logs? | Grep auf Logs (Schritt 1) |
| PII an Azure gesendet? | Azure-Deployment-Region pruefen (EU-Zone Pflicht) |
| Secret im Repo exponiert? | `scripts/runbooks/secret-compromise.md` ausfuehren |
| DSGVO-relevanter Datenleck? | Art. 33: 72h-Melde-Frist -- Firmen-DSB einbeziehen |

---

## 4. Dokumentation

Zeitstempel, Symptome, Massnahmen, Bewertung als `notes/incidents/YYYY-MM-DD.md`.

---

*v1 -- Juni 2026*
