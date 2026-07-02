# 0043 -- Human-in-the-Loop-Decision-Record statt vollem Reviewer-Workflow

**Status:** Accepted
**Datum:** 2026-07-03
**Phase:** G (Post-v1-Audit)

## Kontext

Das Phase-G-Audit hat fuer Cases ohne dokumentierte manuelle Freigabe/
Ablehnung einen vollen Reviewer-Workflow als Empfehlung vorgeschlagen:
Multi-User-Auth, Rollenmodell (z. B. Reviewer vs. Antragsteller), ein
Notification-System bei neuen/geaenderten Entscheidungen und einen
Webhook-Ausgang an nachgelagerte Systeme. Aufwandsschaetzung im Audit: L
(mehrere Tage) -- ein Rollenmodell macht ein zweites Auth-Konzept neben
dem bestehenden API-Key (ADR-006) noetig.

AECT ist zur Laufzeit ein Single-Tenant-System mit einem einzigen
API-Key-Auth-Mechanismus (ADR-006, Rotation ohne Downtime seit Phase
G/Security). ADR-0040 haelt bereits fest, dass "mehr als ein gleichzeitiger
Reviewer/Nutzer" ein offener Migrationstrigger fuer den gesamten
Persistenz-Stack ist, nicht nur fuer Auth. Ein Rollenmodell fuer
Reviewer/Antragsteller wuerde diese Grenze faktisch vorwegnehmen, ohne
dass der Rest des Systems (SQLite Single-Writer, ein API-Key) dafuer
ausgelegt ist.

## Entscheidung

Statt des vollen Reviewer-Workflows wird ein minimaler Decision-Record auf
Case-Ebene umgesetzt: `reviewer_decision` (PENDING/APPROVED/REJECTED),
`reviewer_note` (optionaler Freitext, max. 2000 Zeichen) und `decided_at`
(Zeitstempel). Freigabe/Ablehnung laufen ueber `POST /cases/{id}/decision`,
authentifiziert mit demselben API-Key wie alle anderen Routen
(`require_api_key`, inkl. Rotation) -- kein zweites Auth-/Rollen-Konzept,
kein Notification-System, kein Webhook-Ausgang. Ueberschreiben einer
bestehenden Entscheidung ist ein legitimer Korrektur-Fall (kein Bug):
`decided_at` wird bei jedem Aufruf aktualisiert.

## Begruendung

| Alternative | Warum verworfen |
|---|---|
| Voller Reviewer-Workflow (Multi-User-Auth, Rollen, Notifications, Webhook-out) | Demonstriert eine Faehigkeit (Auth-/Rollen-Engineering), die nicht der Kern dieses Portfolio-Projekts ist (Rule Engine, RAG, Eval-Methodik) -- auf Kosten von Tagen statt Stunden Aufwand. Ein zweites Auth-Konzept neben dem API-Key waere zudem inkonsistent mit der in ADR-0040 dokumentierten Single-Tenant-Grenze: das System ist fuer einen Nutzer/Interview-Kontext ausgelegt, ein Rollenmodell fuer mehrere Reviewer taeuscht eine Mehrbenutzerfaehigkeit vor, die der Rest des Stacks (SQLite Single-Writer) nicht traegt. |
| Gar kein Decision-Record (Report anzeigen, Entscheidung bleibt muendlich/extern dokumentiert) | Der Kern der Anforderung -- eine Entscheidung nachvollziehbar am Case zu dokumentieren -- bliebe ungeloest; ein Report ohne Freigabe-/Ablehnungs-Spur macht Audit-Nachvollziehbarkeit (ein Staerke-Argument des Projekts, vgl. `docs/known_limitations.md`) unmoeglich. |
| Soft-Delete-artiger Status statt eigener Felder (z. B. Case in einen "archiviert"-Zustand versetzen) | Vermischt Loesch-Semantik (DSGVO Art. 17, ADR-0038 -- Cases werden ECHT geloescht) mit Review-Semantik. Ein Case kann freigegeben UND spaeter geloescht werden -- zwei unabhaengige Achsen, die getrennte Felder brauchen. |

Ein minimaler Decision-Record deckt die eigentliche Anforderung
(nachvollziehbare Freigabe/Ablehnung) vollstaendig ab, ohne eine
Systemfaehigkeit zu bauen, die der Projektkontext nicht braucht.

## Konsequenzen

**Positiv:**
- Kein neues Auth-Konzept -- `require_api_key` (inkl. Rotation) bleibt der
  einzige Zugriffsschutz im gesamten System, weiterhin in einem Satz
  erklaerbar.
- Audit-Trail vorhanden (`case_decision_recorded`, structlog, OHNE
  `reviewer_note` -- PII-Allowlist-konform, analog `case_deleted`).
- Aufwand: Stunden statt Tage, passend zur Phase-G-Scope-Disziplin.

**Negativ / Trade-offs (die bewusste Deckung):**
- **Kein Mehrbenutzer-Reviewer-Modell.** Jeder Inhaber des API-Keys kann
  jede Entscheidung setzen und ueberschreiben -- es gibt keine
  Nachvollziehbarkeit, WER genau entschieden hat, nur DASS und WANN. Fuer
  einen Demo-/Interview-Kontext mit einem Nutzer ausreichend, fuer echten
  Mehrpersonen-Betrieb nicht.
- **Keine Benachrichtigung.** Eine Entscheidung loest kein E-Mail-/
  Webhook-/Slack-Ereignis aus -- wer entscheiden soll, muss den Report
  aktiv aufrufen. Bei einem einzelnen Nutzer kein Problem, bei mehreren
  Fachbereichen ein Bottleneck.
- **Kein Freigabe-Gate.** Die Entscheidung ist rein dokumentarisch -- sie
  blockiert keine nachgelagerte Aktion (kein automatischer Trigger bei
  APPROVED). Fuer einen Portfolio-Kontext ausreichend; ein echter
  Automatisierungs-Trigger waere ein eigenes Feature.

**Neutral / Folgeentscheidungen:**
- Ergaenzt ADR-0040 (Single-Tenant-Grenze) um die Auth-/Rollen-Perspektive,
  ersetzt sie nicht.

## Migrationstrigger

Ein Wechsel auf den vollen Reviewer-Workflow (Multi-User-Auth, Rollen,
Notifications, Webhook-out) ist faellig, sobald **eine** der folgenden
konkreten Bedingungen eintritt -- nicht "irgendwann mehr Nutzer":

1. **Mehr als eine Person haelt Zugriff auf denselben API-Key** und trifft
   regelmaessig (nicht einmalig zu Demo-Zwecken) Entscheidungen auf
   denselben Cases -- der Decision-Record kann dann nicht mehr
   unterscheiden, wer entschieden hat.
2. **Echter Pilotbetrieb mit mehreren Fachbereichen**, die eigene
   Freigabe-Zustaendigkeiten haben (z. B. Fachbereich A darf nur eigene
   Cases entscheiden) -- das setzt ein Rollenmodell zwingend voraus.
3. Eine nachgelagerte Aktion soll automatisch an eine Entscheidung
   gekoppelt werden (z. B. ein Deployment-Trigger bei APPROVED) -- das
   braucht ein Ereignis-/Webhook-System, das heute bewusst fehlt.

Trifft eine dieser Bedingungen ein, ist das der Ausloeser fuer eine neue
ADR (Migrationsentscheidung minimaler Decision-Record -> voller
Reviewer-Workflow), nicht fuer eine stillschweigende Erweiterung der
bestehenden Felder.
