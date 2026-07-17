# UI-Smoke-Tests

Playwright-Tests, die die bisher manuelle Durchklick-Pruefung reproduzierbar
machen (S3-Nachtrag, erweitert in V4.1-S8, -S10 und -S11). Sie laufen gegen **lokal
laufende Prozesse**, nicht gegen einen von Playwright selbst gestarteten Server --
so wird exakt der Stack geprueft, den man sonst von Hand bedient.

## Was geprueft wird

`smoke.spec.ts`:

- **`a) Passwort-Toggle`** -- Login-Seite: das Auge schaltet `input[type]` zwischen
  `password` und `text` und das `aria-label` zwischen "Passwort anzeigen" und
  "Passwort verbergen". *Braucht nur das Frontend.*
- **`b) Implementierungsansatz-Nachtrag`** -- legt ueber die public `/triage`-API
  einen Case ohne Ansatz an (Vor-Bewertungs-Zustand), loggt sich als Admin ein,
  oeffnet die Detailseite (Pending-Box sichtbar), ergaenzt den Ansatz und prueft,
  dass danach Zone/Bewertung erscheinen und die Ideenliste den Case **nicht mehr**
  mit dem Pending-Badge zeigt. Die Neubewertung ist deterministisch -- **kein
  Azure-/LLM-Call**. *Braucht Frontend + Backend + Admin-Passwort.*

`public-visibility.spec.ts` (Guard fuer ADR-0052):

- **`c) Anonyme Sichtbarkeit`** -- legt einen bewerteten Case an, gibt ihn als
  Admin frei (der Zustand, in dem die Vorgaenger-Version leakte) und prueft die
  Detailseite **anonym**: sichtbar sind Grunddaten, Status und die
  Board-Entscheidung mit Begruendung; **kein** Bewertungsbegriff und **kein**
  Bewertungswert dieses Falls. Die verbotenen Werte werden aus der Admin-Sicht
  desselben Falls gelesen, nicht hartkodiert -- so veraltet der Test nicht, wenn
  das Bewertungsmodell neu kalibriert wird. Die Ideenliste wird als zweiter Pfad
  derselben Zusicherung mitgeprueft. *Braucht Frontend + Backend + Admin-Passwort.*

  Der Test prueft `innerText` (den **sichtbaren** Text), nicht `page.content()`:
  der komplette i18n-Katalog steht als JSON im RSC-Payload des HTML und enthaelt
  "Zone"/"Nettonutzen" als Label-Strings -- ein `content()`-Test waere dauerhaft
  rot, ohne dass je Case-Daten geleakt waeren. Vor den Negativ-Assertions stehen
  bewusst Positiv-Kontrollen (Titel, Entscheidung, Begruendung sichtbar): ohne sie
  wuerde jede Fehler- oder Ladeseite den Test bestehen, weil auf ihr die
  verbotenen Begriffe ebenfalls fehlen.

`discontinue-dialog.spec.ts` (Guard fuer ADR-0053):

- **`d) Begruendungspflicht beim Einstellen`** -- legt einen bewerteten Case an,
  gibt ihn als Admin frei (erst dann steht er im Monitoring) und oeffnet den
  Einstellen-Dialog. Geprueft wird die **UI-Haelfte** der Zusicherung "ohne
  Begruendung UND Name kein Akt": Absenden bleibt gesperrt bei leeren Feldern,
  bei nur einem gefuellten Feld und -- der eigentliche Grund fuer den Test -- bei
  Feldern aus reinem **Whitespace** (`"   "` ist nicht leer und passiert eine
  naive `required`-Pruefung). Erst mit beiden Angaben wird der Button frei; danach
  laeuft der Akt echt durch und der Verlauf zeigt Aktion, Name und Begruendung.
  Die API-Haelfte (422) liegt in `tests/adapters/api/test_discontinue.py`.
  *Braucht Frontend + Backend + Admin-Passwort.*

  Die Freigabe laeuft ueber `page.request` **mit dem Session-Cookie** des
  eingeloggten Browser-Contexts (Cookies sind host-, nicht portgebunden) -- kein
  API-Key im Test, echter Admin-Pfad.

`intake-review-step.spec.ts` (Guard gegen die V4.1-Absende-Regression):

- **`e) Kein Absenden ohne Bestaetigung`** -- klickt den Wizard bis ans Ende durch
  und prueft, dass "Weiter" im vorletzten Schritt die **Zusammenfassung** zeigt
  (vier Abschnitte, Werte read-only) statt abzusenden -- kein Erfolgs-Screen, und
  "Ändern" springt zum Korrigieren zurueck. Der Test stoppt **vor** dem Absenden,
  legt also keinen Case an. *Braucht nur das Frontend.*

  Hintergrund: der Klick auf "Weiter" hat den Case zeitweise **sofort** abgesendet
  -- derselbe DOM-Button wechselte von `type="button"` auf `type="submit"`, waehrend
  der Klick noch im Dispatch war (`goNext` ist async -> React flusht den neuen
  Schritt im Microtask-Checkpoint, die Activation-Behavior des Browsers laeuft
  **danach** und traf den inzwischen zum Absende-Button gewordenen Knoten). Reines
  Code-Lesen findet das nicht: im Markup steht ein sauberer Bestaetigungs-Schritt.
  Darum ein Browser-Test statt einer Code-Regel.

`nav-layout.spec.ts` (Guard fuer die Kopfleiste):

- **`f) Kopfleiste kollidiert und clippt in keiner Breite`** -- prueft den Header
  ueber sechs Breiten (375/640/768/1024/1280/1440), anonym und angemeldet. Der
  angemeldete Zustand hat eine andere Link-Menge (Board/Monitoring statt
  Einreichen/Ideen-Assistent) und war der gemeldete Fall; er laeuft nur mit
  Admin-Passwort, der anonyme braucht nur das Frontend.

  Zwei Zusicherungen, weil **jede allein** einen echten Defekt durchlaesst:
  (1) kein Nav-Link ueberlappt die rechten Steuerelemente -- der Ausgangsfehler
  (unter 768px behielt die Nav ihre Inhaltsbreite und lief sichtbar ueber
  Abmelden/Sprache/Theme); (2) die Nav ist nicht geclippt
  (`scrollWidth <= clientWidth`). (2) existiert, weil eine Zwischenfassung die
  Nav per `overflow-x-auto` abschnitt: Ueberlappung weg, Labels standen aber als
  "Ideenli"/"Id" da -- und (1) blieb **gruen**, denn
  `getBoundingClientRect()` liefert die **Layout**-Position, nicht den sichtbar
  geclippten Bereich. Ein reiner Rect-Test sieht abgeschnittene Labels nie.
  Beide Assertions sind gegengeprobt: (1) schlaegt gegen den Stand vor dem Fix an,
  (2) gegen die Scroll-Zwischenfassung.

## Voraussetzungen (einmalig)

```bash
cd frontend
npm install                     # @playwright/test ist devDependency
npx playwright install chromium # Browser-Binary (nicht im Repo)
```

## Prozesse starten

**Terminal 1 -- Backend** (Mock-Modus, keine Azure-/Chroma-Abhaengigkeit):

```bash
# Einmal ein Test-Passwort hashen (Ausgabe ist der Env-Wert):
export AECT_SMOKE_ADMIN_PASSWORD='smoke-pw'
export AECT_ADMIN_PASSWORD_HASH="$(uv run python -c \
  "from aect.adapters.api.password import hash_password; print(hash_password('$AECT_SMOKE_ADMIN_PASSWORD'))")"

AECT_DB_PATH=aect_smoke.db \
AECT_AZURE_OPENAI_ENDPOINT= \
  uv run uvicorn aect.adapters.api.app:app --no-server-header
```

> **`AECT_CHROMA_HOST` NICHT leer setzen.** Frueher stand hier `AECT_CHROMA_HOST=`;
> seit V4-P2 ist ein leerer Wert **fail loud** (`resolve_retriever` wirft, kein
> stiller Mock-Fallback) und `POST /triage` antwortet dann `500` -- die Tests
> scheitern beim Anlegen des Cases. Der Default `127.0.0.1` ist richtig; ein
> tatsaechlich laufendes ChromaDB brauchen die Smokes nicht (die Dedup-Pruefung im
> Intake vertraegt einen nicht erreichbaren Chroma).

**Terminal 2 -- Frontend** (auf das Smoke-Backend zeigend):

```bash
cd frontend
AECT_API_BASE_URL=http://localhost:8000 AECT_API_KEY=dev npm run dev
```

**Terminal 3 -- Tests:**

```bash
cd frontend
AECT_SMOKE_ADMIN_PASSWORD='smoke-pw' npm run e2e
```

## Bekannt rot

`lang-switch-guard.spec.ts` -> "Sprachwechsel nach Ideation-Prefill zeigt Dialog
(isDirty=false)" schlaegt fehl. **Kein neuer Regress:** der Test baut den
Ideation-Handoff synthetisch nach (sessionStorage-Key setzen, dann `reload()`)
und faellt damit in ein Rennen zwischen dem read-once-Loeschen des Entwurfs und
dem Befuellen des Formulars. Der reale Pfad (Klick "Uebernehmen" auf `/ideation`
-> Client-Navigation) ist stabil. Analyse, Messwerte und Fix-Richtung:
`docs/known_limitations.md` #34.

## Skip-Verhalten

Jeder Test prueft zuerst, ob die noetigen Prozesse erreichbar sind bzw. das
Admin-Passwort gesetzt ist. Fehlt etwas, wird der Test **uebersprungen** (mit
Grund), nicht als Fehlschlag gewertet. So bleibt `npm run e2e` ohne laufende
Server gruen-mit-Skips statt rot.

## Konfigurierbare Env-Werte

| Variable                    | Default                 | Zweck                                   |
| --------------------------- | ----------------------- | --------------------------------------- |
| `PLAYWRIGHT_BASE_URL`       | `http://localhost:3000` | Frontend-URL                            |
| `AECT_SMOKE_API_URL`        | `http://localhost:8000` | Backend-URL (Case-Anlage + Health)      |
| `AECT_SMOKE_ADMIN_PASSWORD` | *(leer -> Test b + c skip)* | Klartext-Passwort passend zum Backend |

## CI-Einbindung (Vorschlag, hier NICHT umgesetzt)

Der Test braucht ein laufendes Backend+Frontend; die aktuelle CI startet keins.
Moeglich waere ein eigener Job, der beide Prozesse als Services hochfaehrt (Backend
im Mock-Modus wie oben, `AECT_ADMIN_PASSWORD_HASH` als Secret), auf `/health` und
`:3000` wartet und dann `npm run e2e` laeuft. Bis dahin bleibt der Test ein
lokaler Guard vor Release/Demo.
