# 0041 -- Key-Vault-Referenzen statt Env-Strings: Design fuer Deployment, Verifikation ohne Live-Azure

**Status:** Accepted
**Datum:** 2026-07-02
**Phase:** G (Security-Haertung)

## Kontext

Phase G haertet die Security-Grundlagen ueber den bereits verifizierten
Audit-Floor hinaus. Secrets (API-Key, Azure-OpenAI-Key) liegen aktuell
ausschliesslich in Env-Vars/`.env` (`config/settings.py`, ADR-0010). Fuer
ein Portfolio-Projekt ist das ausreichend -- ein realer Produktiveinsatz
wuerde ueber die vorhandene Firmen-Infrastruktur laufen, typischerweise
inklusive eines zentralen Secret-Stores (aect-security-checklist v2.1,
"Was echter Produktiv-Einsatz braeuchte"). Gesucht war ein Design, das
diesen Pfad zeigt -- OHNE echte Azure-Infrastruktur zu brauchen, um es zu
bauen und zu verifizieren. Vorbild: ADR-0035 (Azure Container Apps Deploy)
loest exakt dasselbe Spannungsfeld (Deployment-Pfad entwerfen, ohne live zu
deployen).

## Entscheidung

Wir ergaenzen `Settings` (pydantic-settings) um eine eigene
`AzureKeyVaultSettingsSource`
(`src/aect/adapters/api/keyvault_settings.py`), eingehaengt ueber
`settings_customise_sources()`. Ist `AECT_AZURE_KEY_VAULT_URL` NICHT
gesetzt (Default), liefert die Quelle ein leeres dict -- Env-/`.env`-
Verhalten bleibt exakt wie bisher, kein Breaking Change. Ist die URL
gesetzt, zieht die Quelle drei benannte Secret-Felder (`api_key`,
`api_key_next`, `azure_openai_api_key`) ueber
`azure.keyvault.secrets.SecretClient` + `azure.identity.
DefaultAzureCredential`; ein im Vault fehlendes Einzel-Secret faellt auf
Env/`.env` zurueck (kein harter Fehler fuer das gesamte Settings-Objekt).

Quellen-Prioritaet: `init_settings` (Konstruktor-Kwargs) > Key Vault > Env
> `.env` > File-Secrets. Konstruktor-Kwargs bleiben damit die staerkste
Quelle -- alle bestehenden Tests, die `Settings(api_key=...)` direkt
konstruieren (Phase 1-3 dieser Haertungs-Session, plus der gesamte
bestehende Testbestand), bleiben unveraendert gruen.

## Begruendung

| Alternative | Warum verworfen |
|---|---|
| Azure App Configuration statt Key Vault | Fuer reine Secrets (API-Keys) ist Key Vault der spezifischere, engere Dienst -- App Configuration ist fuer nicht-geheime Konfiguration gedacht und haette hier eine zweite Abstraktion ohne Mehrwert eingefuehrt. |
| Alle Settings-Felder aus dem Vault | Nur `api_key`/`api_key_next`/`azure_openai_api_key` sind echte Secrets. Infrastruktur-Adressen (`chroma_host`, `kb_dir`, ...) aus dem Vault zu ziehen waere Kategorie-Vermischung (Secret-Store fuer Nicht-Secrets) ohne Sicherheitsgewinn. |
| Direkter SDK-Aufruf in `dependencies.py` statt eigener Settings-Source | pydantic-settings bietet mit `settings_customise_sources()` exakt den vorgesehenen Erweiterungspunkt fuer zusaetzliche Konfigurationsquellen -- ein Ad-hoc-Aufruf ausserhalb des Settings-Objekts haette Env/Vault/Test-Override in zwei getrennten Mechanismen dupliziert. |

Testbarkeit ohne Live-Azure: `SecretClientProtocol` (struktureller Typ,
analog `ChromaCollection` in `adapters/rag/retriever.py`) plus eine
austauschbare `secret_client_factory` machen die Quelle mit einem
Test-Fake pruefbar -- Vorbild ADR-0035s Grundprinzip, dass ein
Deployment-Pfad entworfen UND verifiziert werden kann, ohne die echte
Infrastruktur zu betreiben. `azure-keyvault-secrets`/`azure-identity`
werden nur bei tatsaechlich gesetzter Vault-URL importiert (lokaler
Import in `_build_default_secret_client`, analog `chromadb`/
`sentence_transformers` in `dependencies.py`) -- der Mock-/Lokal-Pfad zieht
diese Pakete nie.

## Konsequenzen

**Positiv:**
- Zeigt den Produktiv-Migrationspfad konkret (Code, nicht nur Doku) --
  ohne Azure-Kosten oder -Setup fuer dieses Portfolio-Projekt zu brauchen.
- Kein Breaking Change: Default-Verhalten (Env/`.env`) bleibt unangetastet,
  9 neue Tests beweisen das explizit (leere Vault-URL -> leeres dict,
  Konstruktor-Kwargs schlagen Vault, fehlendes Einzel-Secret faellt auf
  Env zurueck).
- Einzelnes fehlendes Secret im Vault bricht nicht das gesamte
  Settings-Objekt -- Graceful Degradation pro Feld.

**Negativ / Trade-offs:**
- Ungetestet bleibt zwangslaeufig die echte Azure-Verbindung
  (`DefaultAzureCredential`-Ablauf, Netzwerk-Latenz, Berechtigungsfehler,
  Vault-Firewall-Regeln) -- das deckt nur ein echter Azure-Vault ab.
  Dokumentierte Grenze, analog ADR-0035.
- `except Exception` in `_fetch_secret()` faengt bewusst breit (fehlendes
  Secret, Netzwerkfehler, Berechtigungsfehler ununterschieden) -- fuer den
  Zweck (Einzel-Secret-Fallback auf Env) ausreichend, verschleiert aber im
  Fehlerfall die genaue Ursache. Fuer einen echten Produktiv-Einsatz waere
  granulareres Exception-Handling (z. B. `ResourceNotFoundError` vs.
  Auth-Fehler unterscheiden + strukturiertes Logging) ein sinnvoller
  Folgepunkt.

**Neutral / Folgeentscheidungen:**
- ADR-0035 bleibt das Referenzmuster fuer "Design + Verifikation ohne
  Live-Infrastruktur" in diesem Projekt -- diese ADR ist die zweite
  Anwendung desselben Prinzips.

## Anhang: HMAC-signierte Requests (bewusst zurueckgestellt)

Im Rahmen derselben Haertungs-Session wurde HMAC-Signing fuer API-Requests
geprueft und bewusst NICHT umgesetzt (Stop-Gate, keine Implementierung ohne
explizite Bestaetigung). Begruendung: Der API-Key verlaesst in dieser
Architektur nie den Server -- `frontend/src/app/actions.ts` ruft
ausschliesslich serverseitig (Next.js Server Actions), kein
Client-/Browser-Exposure des Keys. Der Hauptnutzen von HMAC-Signing (Schutz
gegen abgefangene oder wiederverwendete Requests) ist bei TLS plus
serverseitig gehaltenem Key bereits weitgehend abgedeckt, und die
Key-Rotation (Phase 2 dieser Session, `key_fingerprint`/`AECT_API_KEY_NEXT`)
deckt das verbleibende Hauptrisiko ab -- einen dauerhaft gueltigen,
gestohlenen Key ohne Rotationsmoeglichkeit. Trigger fuer eine
Neubewertung: sobald der API-Key in einer zukuenftigen
Architekturaenderung client-/browserseitig exponiert wuerde (z. B. direkte
Browser-Calls gegen die API unter Umgehung der Server-Action-Schicht), faellt
diese Begruendung weg und HMAC-Signing waere neu zu pruefen.
