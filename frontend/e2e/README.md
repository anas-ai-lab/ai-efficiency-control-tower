# UI-Smoke-Tests

Vier Playwright-Tests, die die bisher manuelle Durchklick-Pruefung reproduzierbar
machen (S3-Nachtrag, erweitert in V4.1-S8 und -S10). Sie laufen gegen **lokal
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
