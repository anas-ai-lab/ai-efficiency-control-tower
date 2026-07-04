# 0045 -- Case-Lifecycle-Status (7 Zustaende, gekoppelt an ReviewerDecision)

**Status:** Accepted
**Datum:** 2026-07-04
**Phase:** G (Post-v1-Audit)

## Kontext

ADR-0043 fuehrte einen minimalen Decision-Record ein: `reviewer_decision`
(PENDING/APPROVED/REJECTED) haelt fest, ob ein Case fachlich freigegeben oder
abgelehnt wurde. Das beantwortet die Frage "ist der Case freigegeben?", aber
nicht die Frage "wo im Bearbeitungsfluss steht der Case?". Ein freigegebener
Case kann noch in Umsetzung sein, bereits integriert, oder es stellt sich
heraus, dass die Loesung schon existiert (Dedup-Treffer, ADR-0039) -- lauter
Zustaende, die orthogonal zur reinen Freigabe-/Ablehnungs-Achse liegen.

Ohne einen Lifecycle-Status muss dieser Bearbeitungsstand extern (muendlich,
im Ticketsystem) gefuehrt werden -- die Case-Historie im System bleibt
unvollstaendig.

## Entscheidung

Wir fuehren einen `CaseStatus` (StrEnum, 7 Zustaende) als eigenes Feld auf
`SubmittedCase` ein: SUBMITTED (Default nach Einreichung), IN_REVIEW, APPROVED,
ALREADY_EXISTS, INTEGRATED, REJECTED, IMPLEMENTED. Gesetzt wird er ueber
`POST /cases/{id}/status` (`TriageService.update_status()`), authentifiziert mit
demselben API-Key wie alle anderen Routen. Ein Begleit-Zeitstempel
`status_updated_at` haelt fest, wann der Zustand zuletzt wechselte -- analog
`decided_at` zur `reviewer_decision`, persistiert ueber denselben dedizierten
UPDATE-Pfad (F-011, kein `save()` der ganzen Zeile).

**Kopplung an ReviewerDecision:** `record_decision()` setzt zusaetzlich den
Lifecycle-Status -- APPROVED bei Freigabe, REJECTED bei Ablehnung -- ueber
denselben Persistenz-Pfad (`update_status_async`, ein UPDATE-Call mehr, kein
`save()`). Der Freigabe-Akt **darf** einen zuvor manuell gesetzten Status
ueberschreiben: die fachliche Freigabe gewinnt.

**Keine Transitions-Matrix.** Jeder Zustand ist aus jedem Zustand setzbar. Es
gibt bewusst keine Regel "IN_REVIEW nur aus SUBMITTED" o. Ae. Begruendung: AECT
ist ein Single-User-Build (vgl. ADR-0040/0043); der Inhaber des API-Keys ist
die menschliche Autoritaet ueber den Bearbeitungsstand. Eine erzwungene Matrix
wuerde legitime Korrekturen (versehentlich falscher Status, zurueckspringen)
blockieren, ohne einen realen Fehler zu verhindern -- sie schuetzt vor niemandem.

## Begruendung

| Alternative | Warum verworfen |
|---|---|
| `reviewer_decision` (ADR-0043) um Lifecycle-Werte erweitern statt neues Feld | Vermischt zwei orthogonale Achsen: "freigegeben?" (Review) und "wo im Fluss?" (Lifecycle). Ein Case kann freigegeben UND noch nicht integriert sein -- das braeuchte in einem gemeinsamen Enum ein Kreuzprodukt der Werte. Getrennte Felder halten beide Achsen unabhaengig les- und setzbar. Dieser ADR **ersetzt ADR-0043 nicht**, er ergaenzt ihn um eine zweite Achse. |
| Freier String statt Enum | Ein freier Status-String unterlaeuft die projektweite StrEnum-Disziplin (kontrolliertes Vokabular, Config-Key-Invariante) und laedt Tippfehler/uneinheitliche Schreibweisen ein, die still durchrutschen. Ein StrEnum gibt genau 7 valide Werte, die die API (Literal) und die Persistenz (Rekonstruktion beim Load) gemeinsam erzwingen -- ein ungueltiger Wert liefert 422 statt eines undefinierten Zustands. |
| Transitions-Matrix (erlaubte Uebergaenge erzwingen) | Setzt ein Mehr-Rollen-/Workflow-Modell voraus, das der Single-User-Build nicht hat (ADR-0040/0043). Menschliche Autoritaet ueber den Stand ist hier ausreichend und flexibler; eine Matrix wuerde nur legitime Korrekturen blockieren. |
| Keinen Lifecycle-Status, Stand extern fuehren | Die Case-Historie im System bliebe unvollstaendig -- derselbe Nachvollziehbarkeits-Verlust wie bei "gar kein Decision-Record" in ADR-0043. |

## Konsequenzen

**Positiv:**
- Bearbeitungsstand ist am Case sichtbar und nachvollziehbar
  (`status_updated_at` + Audit-Log-Event `case_status_changed`, PII-Allowlist-
  konform ohne Freitext, analog `case_decision_recorded`).
- Kein neues Auth-/Rollen-Konzept -- `require_api_key` bleibt der einzige
  Zugriffsschutz (konsistent mit ADR-0043).
- Freigabe und Lifecycle bleiben ueber die Kopplung synchron, ohne dass der
  Nutzer zwei Endpoints aufrufen muss.

**Negativ / Trade-offs (die bewusste Deckung):**
- **Kein erzwungener Workflow.** Jeder Zustandswechsel ist erlaubt -- das System
  verhindert keine "unsinnigen" Uebergaenge (z. B. IMPLEMENTED -> SUBMITTED).
  Fuer einen Single-User-/Demo-Kontext ausreichend, fuer Mehrpersonen-Betrieb
  mit Zustaendigkeitsgrenzen nicht.
- **Kein Trigger an Zustandswechsel.** Ein Statuswechsel loest keine
  nachgelagerte Aktion aus (kein Deployment bei IMPLEMENTED) -- rein
  dokumentarisch, wie schon die Freigabe in ADR-0043.
- **Zwei Achsen, eine mit Kopplung.** APPROVED/REJECTED sind ueber zwei Wege
  setzbar (`/status` direkt und `/decision` gekoppelt). Bewusst so: die
  Freigabe gewinnt, damit der Lifecycle nie im Widerspruch zur fachlichen
  Entscheidung steht.

**Neutral / Folgeentscheidungen:**
- Migrationstrigger identisch zu ADR-0043: sobald mehr als eine Person
  regelmaessig Entscheidungen/Statuswechsel auf denselben Cases trifft, ist ein
  Rollen-/Workflow-Modell (dann inkl. Transitions-Matrix) faellig -- Ausloeser
  fuer eine neue ADR, nicht fuer eine stillschweigende Erweiterung hier.
