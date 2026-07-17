# 0053 -- Begruendungspflicht beim Einstellen/Reaktivieren, protokolliert in der bestehenden Zeitleiste

**Status:** Accepted
**Datum:** 2026-07-17
**Autor:** Anas
**Phase:** V4.1 (S10)

## Kontext

Das `discontinued`-Flag (V4.1-S7) markiert einen Use Case als "wird nicht mehr
aktiv beobachtet" -- unabhaengig vom Lifecycle-Status (ADR-0045), ein
eingestellter Case behaelt z. B. weiter `approved`. Bis S10 war das ein
parameterloser Toggle: `POST /cases/{id}/discontinue` ohne Body, ein Klick, Flag
gesetzt. Damit war die folgenreichste Monitoring-Handlung -- das Beenden der
aktiven Beobachtung eines freigegebenen Use Case -- die einzige, die weder
festhielt, WARUM sie geschah, noch WER sie ausloeste. Nach zwei Wochen war
sichtbar, DASS ein Case eingestellt ist, aber nicht mehr rekonstruierbar, auf
welcher Grundlage.

Der Build kennt genau eine Admin-Identitaet (Session-Cookie ODER API-Key,
V4-Auth); das Auth-Subjekt beantwortet die Frage "wer" also nicht -- es sagt nur
"ein Admin". Wer eine Entscheidung fachlich verantwortet, ist eine andere
Information als wer sich angemeldet hat.

Parallel existiert seit ADR-0046 die append-only `monitoring_entries`-Zeitleiste
je Case (id, case_id, created_at, note, status_snapshot) fuer manuelle
Beobachtungsnotizen -- mit genau dem Audit-Charakter, den ein Einstell-Ereignis
braucht.

## Entscheidung

Wir machen **Begruendung und Name der ausfuehrenden Person zu Pflichtangaben**
fuer beide Richtungen (`discontinue` UND `reinstate`) und protokollieren das
Ereignis **als Eintrag in der bestehenden `monitoring_entries`-Zeitleiste**
statt in einer eigenen Audit-Tabelle.

Die Pflicht wird an genau einer Stelle erzwungen, die man nicht umgehen kann:
im Request-Schema (`DiscontinueEventRequest`, `reason` + `actor_name`, beide
`strip_whitespace=True, min_length=1`). Ohne beide Angaben antwortet die API
`422` und der Akt findet **nicht statt, auch nicht teilweise** -- kein Flag,
kein Eintrag. `strip_whitespace` laeuft vor der Laengenpruefung: `"   "` ist
eine leere Angabe, keine gueltige. Das UI (Dialog mit zwei Pflichtfeldern,
Absenden gesperrt bis beide getrimmt nicht-leer sind) ist die zweite Instanz,
nicht die einzige.

Die Zeitleiste bekommt dafuer zwei **nullable** Spalten: `action`
(`MonitoringAction`: `discontinued`/`reactivated`) und `actor_name`. Die
Begruendung liegt in der vorhandenen `note`-Spalte. `NULL` in beiden ist die
freie Beobachtungsnotiz -- der Regelfall und der gesamte Altbestand; gesetzt
sind sie nur bei einem der beiden Akte. Clients unterscheiden Ereignis von Notiz
an `action`, nicht an einer Heuristik ueber den `note`-Text.

Der Service schreibt zuerst das Flag, dann den Eintrag. Bricht der zweite
Schreibvorgang ab, steht ein gesetztes Flag ohne Verlaufseintrag da -- der
umgekehrte Fall (ein Eintrag ueber einen nie erfolgten Akt) waere die
schlechtere Luege. Eine Transaktion ueber beide Tabellen gibt der
`RepositoryPort` nicht her (getrennte Verbindungen je Methode).

## Begruendung

Zwei Entscheidungen, jeweils mit verworfenen Alternativen.

**(a) Ereignis in die bestehende Zeitleiste statt eigener Audit-Tabelle:**

| Alternative | Warum verworfen |
|---|---|
| Eigene Tabelle `discontinue_events` (case_id, action, reason, actor_name, created_at) | Erzeugt einen **zweiten, konkurrierenden Verlauf** zum selben Case. Die Leseansicht muesste zwei Quellen chronologisch mergen, um die Frage "was ist mit diesem Case passiert" zu beantworten -- und jede kuenftige Ereignisart braucht die Entscheidung neu, in welchen der beiden Verlaeufe sie gehoert. Die Zeitleiste ist bereits der Ort fuer "was ist wann passiert" (ADR-0046); ein Einstell-Ereignis ist genau das, nur nicht handgetippt. Zudem waeren DSGVO-Kaskade (Art. 17, ADR-0038) und Sortier-/Snapshot-Logik ein zweites Mal zu bauen und zweitens zu pflegen. |
| Felder am Case (`discontinued_reason`, `discontinued_by`) | Ueberschreibbar und damit **nur der letzte Stand**: ein Case, der eingestellt, reaktiviert und wieder eingestellt wurde, haette exakt eine Begruendung -- die letzte. Die Historie, der ganze Zweck, waere weg. Zusaetzlich das Lost-Update-Muster (F-011), das schon ADR-0046 zur eigenen Tabelle bewogen hat. |
| Nur den structlog-Audit-Trail nutzen | Logs sind fluechtig (Rotation), nicht je Case abfragbar und nicht dafuer da, fachliche Eingaben strukturiert zurueckzugeben -- dieselbe Begruendung wie in ADR-0046. Schaerfer noch: Begruendung (Freitext) und Personenname duerfen per PII-Allowlist gar nicht in die Logs. Genau die Information, um die es geht, waere die, die dort fehlen muss. |
| `note`-Text konventionell praefixen (`"[eingestellt durch X] ..."`) statt eigener Spalten | Strukturierte Information in einen Freitext kodieren heisst, sie per Parsing wieder herausholen -- und ein Nutzer, der eine Notiz zufaellig so beginnt, faelscht ein Ereignis. Zwei Spalten kosten eine Migration und sind danach eindeutig. |

**(b) Pflichtangaben, symmetrisch fuer beide Richtungen:**

| Alternative | Warum verworfen |
|---|---|
| Begruendung optional (Freitext, wenn man mag) | Optionale Audit-Felder bleiben in der Praxis leer -- der Toggle war bereits die bequemere Variante und hat genau deshalb nichts hinterlassen. Wenn die Begruendung den Zweck erfuellen soll, ist sie Pflicht oder sie ist Dekoration. |
| Nur beim Einstellen Pflicht, Reaktivieren frei | Dann waere jedes Einstellen belegt und jedes Zuruecknehmen anonym -- ein Verlauf, in dem man die Entscheidung, aber nicht ihre Aufhebung nachvollziehen kann. Die Rueckkehr in die aktive Beobachtung ist dieselbe Art von Entscheidung. |
| `actor_name` aus dem Auth-Subjekt ableiten statt abfragen | Der Build hat eine einzige Admin-Identitaet: das Feld saehe befuellt aus und traege doch nur "admin" -- eine plausibel aussehende Nicht-Information (fail loud: lieber fragen als erfinden). Der Preis ist Ehrlichkeit ueber die Grenze: der Name ist **selbst angegeben und nicht verifiziert** (siehe Konsequenzen). |
| Pflicht nur im UI erzwingen (required-Attribute) | Die API ist der Vertrag; ein Client, der sie direkt aufruft (curl, Skript, kuenftiges Frontend), umginge die Zusicherung vollstaendig. Die Pruefung gehoert an den Rand, der die Daten schreibt. Das UI-Gating bleibt zusaetzlich -- es erspart dem Nutzer den Klick in die Fehlermeldung. |

## Konsequenzen

**Positiv:**
- Jedes Einstellen/Reaktivieren ist im Verlauf mit Zeitpunkt, Aktion, Name und
  Begruendung belegt -- in **einer** chronologischen Ansicht gemeinsam mit den
  manuellen Notizen, ohne Merge zweier Quellen.
- Die Zusicherung "ohne Begruendung + Name kein Akt" liegt im Schema, also auf
  jedem Pfad zur API -- nicht in der UI-Schicht, die ein Client ueberspringen
  kann.
- Der Altbestand bleibt ehrlich: `action IS NULL` heisst "war eine Notiz", nicht
  "war ein Ereignis mit unbekanntem Anlass". Ein `NOT NULL DEFAULT` haette jedem
  Alteintrag ein Ereignis angedichtet, das nie stattfand.
- Loesch-Kaskade, Sortierung und Status-Snapshot gelten unveraendert weiter --
  das Ereignis erbt sie von ADR-0046, statt sie zu duplizieren.

**Negativ / Trade-offs (die bewusste Deckung):**
- **`actor_name` ist nicht verifiziert.** Es ist eine Selbstauskunft im
  Formular, kein Auth-Subjekt -- wer luegt, steht falsch im Verlauf. Fuer einen
  Single-Admin-Portfolio-Build ist das die ehrlichere Loesung als ein aus der
  Session abgeleitetes "admin"; in einem Mehrbenutzer-Build waere es ein
  Migrationstrigger (Name aus der Identitaet, Feld weg).
- **Zwei Schreibvorgaenge ohne gemeinsame Transaktion.** Flag und Eintrag
  koennen theoretisch auseinanderlaufen (Flag gesetzt, Eintrag fehlt). Die
  Reihenfolge ist so gewaehlt, dass der wahrscheinlichere Rest-Fehler die
  harmlosere Haelfte ist.
- **Der Toggle ist kein Toggle mehr.** Einstellen kostet jetzt einen Dialog und
  zwei Eingaben statt eines Klicks. Das ist beabsichtigt -- der Reibungsverlust
  ist der Punkt --, aber es ist ein realer Bedienaufwand.
- **API-Bruch:** `POST /discontinue` und `/reinstate` ohne Body antworten jetzt
  `422` statt `200`. Kein externer Konsument existiert (Single-Build), das
  Frontend ist mitgezogen; `openapi.json` + `api.generated.ts` sind neu erzeugt.

**Neutral / Folgeentscheidungen:**
- `MonitoringNoteRequest.note` bekommt dieselbe `strip_whitespace`-Behandlung:
  zuvor liess `min_length=1` eine Notiz aus reinen Leerzeichen durch -- ein
  append-only Eintrag ohne Inhalt, der per ADR-0046 nie wieder loeschbar ist.
- `case_discontinued_changed` (structlog) fuehrt weiter nur Allowlist-Felder
  (`case_id`, `discontinued`, `entry_id`) -- **ohne** `reason` (Freitext) und
  **ohne** `actor_name` (Personenname), analog `case_decision_recorded`.
- Die UI-Haelfte der Zusicherung ist als Playwright-Smoke fixiert
  (`e2e/discontinue-dialog.spec.ts`): Absenden bleibt gesperrt bei leeren UND
  bei Whitespace-Feldern.
