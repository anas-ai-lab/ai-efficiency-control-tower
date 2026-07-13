# UI-Smoke-Tests

Zwei Playwright-Tests, die die bisher manuelle Durchklick-Pruefung reproduzierbar
machen (S3-Nachtrag). Sie laufen gegen **lokal laufende Prozesse**, nicht gegen
einen von Playwright selbst gestarteten Server -- so wird exakt der Stack
geprueft, den man sonst von Hand bedient.

## Was geprueft wird

- **`a) Passwort-Toggle`** -- Login-Seite: das Auge schaltet `input[type]` zwischen
  `password` und `text` und das `aria-label` zwischen "Passwort anzeigen" und
  "Passwort verbergen". *Braucht nur das Frontend.*
- **`b) Implementierungsansatz-Nachtrag`** -- legt ueber die public `/triage`-API
  einen Case ohne Ansatz an (Vor-Bewertungs-Zustand), loggt sich als Admin ein,
  oeffnet die Detailseite (Pending-Box sichtbar), ergaenzt den Ansatz und prueft,
  dass danach Zone/Bewertung erscheinen und die Ideenliste den Case **nicht mehr**
  mit dem Pending-Badge zeigt. Die Neubewertung ist deterministisch -- **kein
  Azure-/LLM-Call**. *Braucht Frontend + Backend + Admin-Passwort.*

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
AECT_CHROMA_HOST= \
  uv run uvicorn aect.adapters.api.app:app --no-server-header
```

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
| `AECT_SMOKE_ADMIN_PASSWORD` | *(leer -> Test b skip)* | Klartext-Passwort passend zum Backend   |

## CI-Einbindung (Vorschlag, hier NICHT umgesetzt)

Der Test braucht ein laufendes Backend+Frontend; die aktuelle CI startet keins.
Moeglich waere ein eigener Job, der beide Prozesse als Services hochfaehrt (Backend
im Mock-Modus wie oben, `AECT_ADMIN_PASSWORD_HASH` als Secret), auf `/health` und
`:3000` wartet und dann `npm run e2e` laeuft. Bis dahin bleibt der Test ein
lokaler Guard vor Release/Demo.
