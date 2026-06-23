# ADR-0035 — Deployment: lokal (Docker + uvicorn) statt Azure Container Apps

**Status:** Accepted
**Datum:** Juni 2026
**Kontext:** Phase F — Dokumentation downgraded Topics (Master-Plan v3.1, interne Referenz (entfernt) §4)

---

## Kontext

AECT laeuft lokal: FastAPI via uvicorn, ChromaDB via Docker Container
(Port 8001, eingerichtet in Phase D). Kein produktiver Cloud-Deploy
in v1. Azure Container Apps (ACA) war als Zielplattform in der
Phase-F-Downsizing-Liste (interne Referenz (entfernt) §4: "Azure Container Apps Deploy:
nur ADR/Design, kein Deploy").

---

## Alternativen

**A) Lokales Deployment (umgesetzt)**

Docker fuer ChromaDB, uvicorn fuer FastAPI -- Start-Schritte in README
(Tag 71 dokumentiert).
Pros: keine Cloud-Kosten, keine Infra-Komplexitaet, kein IP-Risiko
(interne Referenz (entfernt) §5: IP-Klaerung ausstehend vor Veroeffentlichung).
Cons: kein oeffentlicher Endpoint; Demo via localhost + Bildschirmfreigabe.

**B) Azure Container Apps (Design, nicht gebaut)**

ACA bietet: serverlose Container (scale-to-zero), Managed Identity,
Key-Vault-Secret-Referenzen, Azure Container Registry, integriertes
Logging (Azure Monitor).

Architektur-Skizze (B):

    # Container Apps Environment (West Europe -- EU-Datenresidenz)
    az containerapp env create \
      --name aect-env --resource-group aect-rg --location westeurope

    # AECT FastAPI -- 0.5 vCPU / 1.0 GB RAM, min-replicas 0
    az containerapp create \
      --name aect-api --resource-group aect-rg \
      --environment aect-env \
      --image aectregistry.azurecr.io/aect-api:latest \
      --cpu 0.5 --memory 1.0Gi \
      --min-replicas 0 --max-replicas 3 \
      --system-assigned

    # ChromaDB -- min-replicas 1 (darf nicht auf 0 skalieren)
    az containerapp create \
      --name aect-chroma --resource-group aect-rg \
      --environment aect-env \
      --image chromadb/chroma:1.5.3 \
      --cpu 0.5 --memory 1.0Gi --min-replicas 1

    # Azure OpenAI API-Key aus Key Vault (kein Secret im Container)
    az containerapp secret set \
      --name aect-api --resource-group aect-rg \
      --secrets "azure-openai-key=keyvaultref:<vault-uri>,identityref:<mi-id>"

Security-Aspekte einer ACA-Instanz:
- Managed Identity statt API-Key fuer Azure OpenAI Access (AAD-Auth) --
  kein Secret im Container-Image oder in Env-Variablen.
- AECT eigener API-Key: Key-Vault-Reference in ACA-Secrets, nicht Klartext.
- ChromaDB nicht extern erreichbar (nur intra-environment via VNet).
- Ingress: nur HTTPS, TLS-Terminierung am ACA-Ingress-Layer.
- CORS: explizite Origin-Allowlist, nie "*".
- Non-root User im Dockerfile (aect-security-checklist v2.1, Phase F).

Geschaetzte Kosten (scale-to-zero, sporadische Demo-Nutzung):
- ACA vCPU/RAM: ~2-4 EUR/Monat bei unter 10 aktiven Stunden.
- Azure Container Registry (Basic): ~5 EUR/Monat.
- Azure Files fuer ChromaDB-Persistenz (1 GB): ~0.10 EUR/Monat.
- Azure Monitor Logs: ~1-2 EUR/Monat bei Demo-Nutzung.
- Summe: ~8-11 EUR/Monat (innerhalb Budget-Deckel interne Referenz (entfernt) §9).

---

## Entscheidung

A) Lokales Deployment. ACA: verstanden, Design oben skizziert,
bewusst nicht deployed.

Gruende:
1. IP-Klaerung (interne Referenz (entfernt) §5) steht aus. Ein Cloud-Deploy wuerde
   firmenspezifische Konfiguration exponieren bevor die Rechtslage
   geklaert ist -- Reihenfolge: erst IP-Klaerung, dann veroeffentlichen.
2. Kein produktiver Traffic, kein SLA, keine externe Nutzerbasis --
   scale-to-zero loest kein existierendes Problem.
3. Demo-Anforderung (Gate F: Problem -> Schaerfung -> Loesung -> Verdict)
   ist via localhost vollstaendig erfuellbar.
4. Teardown-Pflicht (interne Referenz (entfernt) §9 Punkt 2): dauerhaft laufende Cloud-
   Ressourcen erfordern aktives Cleanup nach jedem Test -- unverhältnis-
   maessig fuer ein privates Build.

---

## Konsequenzen

- Frischer-Clone-Test (Gate F) laeuft lokal -- genaue Schritte in
  README (Tag 71).
- Fuer einen internen Produktiv-Einsatz waere ACA der naechste Schritt;
  Security-Design (Managed Identity, Key Vault, VNet) ist dieser ADR.
- Interview-Position: Cloud-Architektur bekannt und dokumentiert --
  nicht deployed weil privat, nicht weil unbekannt.
