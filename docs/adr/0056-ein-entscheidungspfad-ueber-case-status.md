# ADR-0056: Ein Entscheidungspfad ueber den Case-Status

**Status:** Accepted
**Datum:** 2026-08-30
**Autor:** Anas
**Ersetzt:** ADR-0043 (Decision-Record statt Reviewer-Workflow)

## Kontext

ADR-0043 fuehrte mit `POST /cases/{id}/decision` einen eigenen Schreibpfad fuer
`reviewer_decision` ein. ADR-0045 ergaenzte daneben
`POST /cases/{id}/status`. Die Kopplung in `record_decision()` aktualisierte den
Lifecycle-Status nur, solange der Case `submitted` oder `in_review` war (H-034).

Damit konnten beide Felder widerspruechlich werden: Nach
`POST /status {"status":"rejected"}` setzte ein anschliessendes
`POST /decision {"decision":"approved"}` zwar `reviewer_decision` auf
`approved`, liess `status` wegen H-034 aber auf `rejected`. Monitoring las den
Status, das Board die Reviewer-Entscheidung. Beide Ansichten zeigten ohne Fehler
unterschiedliche Wahrheiten ueber denselben Case.

## Entscheidung

`POST /cases/{id}/status` ist der einzige Schreibpfad fuer Lifecycle und
Reviewer-Entscheidung. `POST /cases/{id}/decision` entfaellt. Der Request
enthaelt einen `CaseStatus` und optional eine Notiz, aber keine separate
`ReviewerDecision`.

`reviewer_decision` wird deterministisch aus dem gesetzten Status abgeleitet:

| CaseStatus | ReviewerDecision |
|---|---|
| `approved` | `approved` |
| `rejected` | `rejected` |
| `submitted`, `in_review`, `already_exists`, `implemented` | `pending` |

Status und Entscheidung werden mit demselben Zeitstempel ueber die bestehenden
dedizierten Repository-Updates geschrieben. Es bleibt bewusst dabei, dass jeder
Status aus jedem anderen Status gesetzt werden kann; eine Transitions-Matrix
wird nicht eingefuehrt.

## Begruendung

Der Lifecycle-Status ist bereits der zentrale Zustand fuer Monitoring und
Portfolio-Auswertungen. Eine abgeleitete Reviewer-Entscheidung kann ihm nicht
widersprechen und benoetigt keinen zweiten Request-Parameter.

| Alternative | Warum verworfen |
|---|---|
| Beide Endpoints behalten und atomar koppeln | Zwei oeffentliche Schreibvertraege bleiben konkurrierend und koennen bei spaeteren Aenderungen erneut auseinanderlaufen |
| `reviewer_decision` als einzige Wahrheit verwenden | Monitoring und Lifecycle-Funktionen benoetigen weiterhin die sechs differenzierten CaseStatus-Werte |
| Eine Transitions-Matrix einfuehren | Behebt den Widerspruch nicht und wuerde die bisher erlaubten manuellen Korrekturen unnoetig einschraenken |

## Konsequenzen

**Positiv:**

- Status und Reviewer-Entscheidung koennen nicht mehr durch getrennte Requests
  widerspruechlich werden.
- Ein Statuswechsel zurueck auf `submitted` oder `in_review` setzt die
  Entscheidung wieder auf `pending`: Ein erneut zu pruefender Case traegt keine
  weiter gueltige Freigabe oder Ablehnung.
- `already_exists` und `implemented` setzen ebenfalls `pending`. Ein als
  Duplikat oder umgesetzt klassifizierter Case traegt keine aktive
  Freigabe-/Ablehnungsentscheidung mehr.
- Notiz-, Status- und Entscheidungsdaten kommen in einer Response zurueck.

**Negativ / Trade-offs:**

- Clients muessen Freigabe und Ablehnung ueber das `status`-Feld senden.
- `decided_at` wird auch bei einer auf `pending` abgeleiteten Entscheidung
  aktualisiert; es bezeichnet jetzt den Zeitpunkt der letzten gemeinsamen
  Status-/Entscheidungsaktualisierung.

**Neutral / Folgeentscheidungen:**

- H-034 und seine monotone Fruehstatus-Kopplung entfallen ersatzlos. Diese
  Kopplung war die Ursache des stillen Widerspruchs, keine zu bewahrende
  Lifecycle-Eigenschaft.
- Die bestehenden Repository-Methoden `update_status_async()` und
  `record_decision_async()` bleiben als dedizierte Per-Feld-Updates bestehen.
- ADR-0043 bleibt als historische Entscheidung erhalten, ist fuer den
  oeffentlichen Schreibpfad aber durch diese ADR ersetzt.
