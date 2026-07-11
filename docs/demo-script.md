# Demo-Skript & Smoke-Checkliste (V4)

> Verbindliche Schrittfolge fuer die Live-Demo des AI Efficiency Control Tower
> (V4, Demo-Build fuer einen internen Vorgesetzten, SDR-0003). Zweck: eine
> reproduzierbare, vorgefuehrte Runde vom frischen Start bis zum Monitoring-
> Eintrag -- plus eine Selbsttest-Checkliste, die genau diesen Pfad einmal ohne
> Publikum durchspielt.

Dieses Dokument hat drei Teile:

1. **Frischer Start** -- die exakte Reset-/Start-Sequenz (Backend, Frontend, Seed).
2. **Live-Demo** -- die Schrittfolge im Browser mit dem, was jeweils zu zeigen ist.
3. **Smoke-Checkliste** -- derselbe Pfad als API-Selbsttest vor der Demo, plus die
   Punkte, die **manuell im Browser** gegengeprueft werden muessen.

---

## Rahmen

- V4 ist ein Demo-Build, kein Produktivbetrieb. Der DB-Reset ist ausdruecklich
  erlaubt (SDR-0003, Entscheidung 8).
- Zwei Zugriffsstufen: **anonym** (Einreichen, Ideen-Assistent, Listen-/Detail-
  Ansicht read-only) und **Admin** (alle Aktionen, Session-Login). Kein Multi-User.
- Die LLM-Schritte (Schaerfen, Loesungsvorschlag, Compliance) machen **echte
  Azure-Calls** -- fuer eine ueberzeugende Demo muessen `.env` (Azure) und der
  Chroma-Container laufen. Ohne beides degradiert das System sichtbar auf Mock/
  "Wissensbasis nicht verfuegbar" (fail loud, kein stiller Platzhalter).

---

## 1. Frischer Start

### 1.1 Voraussetzungen (einmalig)

- Python 3.12 + `uv`, Node 20+, Docker.
- `.env` im Repo-Root mit gueltiger Azure-OpenAI-Konfiguration (EU-Endpoint
  **und** `AECT_AZURE_OPENAI_REGION`, sonst greift der EU-Region-Guard).
- `frontend/.env.local` mit `AECT_API_BASE_URL=http://localhost:8000`
  (der API-Key wird vom Browser **nicht** mehr gebraucht -- Auth laeuft ueber das
  Session-Cookie).

### 1.2 Admin-Passwort setzen (einmalig pro Shell)

Der Admin-Login braucht einen scrypt-Hash in `AECT_ADMIN_PASSWORD_HASH`
(bewusst **nicht** in `.env`, damit kein Klartext-Passwort im Repo-Umfeld liegt):

```bash
# Hash aus einem selbst gewaehlten Demo-Passwort erzeugen (getpass, nichts wird geloggt)
uv run python scripts/hash_password.py
# Ausgabe (scrypt$...) exportieren -- gilt fuer die aktuelle Shell:
export AECT_ADMIN_PASSWORD_HASH='scrypt$...'
```

### 1.3 Chroma-Container + Wissensbasis

```bash
docker compose up -d                                   # ChromaDB (Port 8001)
uv run python scripts/seed_knowledge_base.py           # KB-Chunks einspielen
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8001/api/v2/heartbeat  # 200 erwartet
```

### 1.4 Demo-Datenbank frisch seeden

```bash
uv run python scripts/seed_demo.py --reset             # legt aect_demo.db neu an (9 Cases)
```

Erwartete Zonen-Verteilung (deterministisch): demo-001/002/008/009 LIKELY_WIN,
demo-003/004/007 CALCULATED_RISK, demo-005 MARGINAL_GAIN, demo-006 Vorfilter-Fail.

### 1.5 Backend starten (gegen die Demo-DB)

```bash
AECT_DB_PATH=aect_demo.db \
AECT_CHROMA_HOST=127.0.0.1 AECT_CHROMA_PORT=8001 \
AECT_ADMIN_PASSWORD_HASH="$AECT_ADMIN_PASSWORD_HASH" \
uv run uvicorn aect.adapters.api.app:app --port 8000 --no-server-header
# Bereit, wenn /health 200 liefert:  curl -s localhost:8000/health
```

### 1.6 Frontend starten (zweites Terminal)

```bash
cd frontend && npm install && npm run dev              # http://localhost:3000
```

---

## 2. Live-Demo (Browser)

Reihenfolge bewusst so: erst der anonyme Blick, dann die Admin-Sicht -- das
Zwei-Stufen-Modell ist selbst ein Demo-Punkt.

| # | Schritt | Was zu tun ist | Was zu zeigen / zu sagen ist |
|---|---------|----------------|------------------------------|
| 1 | **Startseite** (`/`) | Landing oeffnen | KPI-Kacheln aus `GET /stats` (Eingereicht / Bewertet / Umgesetzt / freigegebener Nettonutzen). "Das ist der Portfolio-Bestand, nicht ein Einzelfall." |
| 2 | **Anonyme Einreichung** (`/einreichen`) | 5-Schritt-Wizard mit dem vorbereiteten Beispiel-Case (Tabelle unten) ausfuellen, absenden | Nach dem Absenden **kein** Score-Preview -- nur eine Bestaetigung mit Case-Link. "Die Bewertung macht das Board sichtbar, nicht der Einreicher." |
| 3 | **Case anonym oeffnen** (`/cases/{id}`) | Den soeben erzeugten Case oeffnen | Es erscheinen nur die **rohen Eingaben** + "Wird vom AI Board geprueft". Zone/ROI/Report sind bewusst verborgen (SDR-0003). |
| 4 | **Admin-Login** (`/login`) | Mit dem Demo-Passwort einloggen | Nach Login erscheinen Board + Monitoring in der Navigation; die Aktions-Buttons am Case werden sichtbar. |
| 5 | **Board-Entscheidung** (Case-Detail, Admin) | Case freigeben ("Freigeben"/approved, kurze Notiz) | Loest `record_decision` aus. "Ab jetzt ist die Bewertung auch fuer anonyme Betrachter sichtbar." |
| 6 | **Score-Breakdown & Konfidenz** | Denselben Case ansehen | Aufwandscore-Herkunft je Komponente ("Aufwandscore N von 9 -> LABEL"), Machbarkeit, Konfidenz als **Begruendung** (nicht nur Zahl). Zwei getrennte Konfidenz-Zeilen: eine zur **Bewertungszone**, eine zur **Routing**-Empfehlung -- unterschiedliche Fragen. |
| 7 | **Schaerfen + Diff** | Button "Schaerfen" -> Draft ansehen | Der vorbereitete Case loest einen **starken Rewrite** aus -> die Ansicht schaltet automatisch auf **Nebeneinander** (Vorher \| Nachher, churn > 0,5). Umschalter Inline/Split zeigen. Vorschlaege tragen `Bezugsfeld / Vorschlag / Hebel` -- **keine erfundenen Zahlen**. |
| 8 | **Uebernehmen** | Button "Uebernehmen" (accept) | Draft wird in die regulaeren Felder uebernommen; verwerfen (reject) waere die Alternative. |
| 9 | **Loesungsvorschlag** | Button "Loesungsvorschlag" | Zwei Ebenen: **business** (technikfrei -- Vokabular-Guard verbietet OCR/API/ERP/...) und **technisch** (Stack-Sicht). |
| 10 | **Compliance** | Button "Compliance-Pruefung" | RAG-gegruendeter Hinweis mit **echten Quellen** (EU AI Act Art. 50 / DSGVO Art. 35, mit eur-lex-Link). Jeder Hinweis "zu pruefen", kein Rechtsurteil. |
| 11 | **Report** | Button "Vollstaendiger Report" | Zwei Schichten: **Entscheider** (Empfehlungssatz, Kennzahlen mit dt. Zahlenformat, "zu entscheiden", Contra-Punkte) und **Technisch** (Architektur-Kurzfassung, Datenlage, Risiken, offene Fragen). |
| 12 | **Board** (`/board`) | Board-Matrix oeffnen | Streudiagramm: x = Nettonutzen, y = Machbarkeit (1-9 invertiert -> gut = oben rechts), Blasengroesse = Stunden/Jahr, Farbe = Zone. Quadranten-Linien sind **Lese-Hilfe, keine Schwellen** (known_limitations #17). |
| 13 | **Monitoring** (`/monitoring`) | Freigegebenen Case, Notiz hinzufuegen | Append-only Zeitleiste mit Status-Snapshot je Eintrag. "Der Verlauf ist unveraenderlich -- Audit-Charakter." |
| 14 | **Logout + Anonym-Recheck** | Logout, dann den Case erneut anonym oeffnen | Der **freigegebene** Case zeigt seine Bewertung jetzt auch anonym (weil Board entschieden hat); Board/Monitoring verlangen wieder Login. |

### Vorbereiteter Beispiel-Case (fuer Schritt 2)

Bewusst knapp/holprig formuliert, damit das Schaerfen einen sichtbaren Rewrite
erzeugt. Generisch, kein Firmenbezug.

| Feld | Wert |
|------|------|
| Titel | Bewerbungen grob vorsortieren |
| Einreicher / Abteilung | Demo Einreicher / Personal |
| Land | Deutschland (de) |
| Ist-Zustand | *Die Personalabteilung liest jede eingehende Bewerbung von Hand durch und sortiert sie grob nach Passung zur Stelle.* |
| Soll-Zustand | *Ein System sortiert eingehende Bewerbungen grob vor, die Personalabteilung prueft danach nur noch die Vorauswahl.* |
| Beispielvorgang | *Eine Bewerbung wird geoeffnet, gelesen und grob einer Eignungsstufe zugeordnet.* |
| Zeit heute / mit AI (h) | 0,4 / 0,1 |
| Vorgaenge je MA/Jahr | 600 |
| Betroffene MA | 5 |
| Mitarbeiterkategorie | Professional |
| Evidenz | Analogieprojekt (similar_project) |
| Verbindlichkeit | Empfohlener Teamstandard (recommended_standard) |
| Umsetzungsansatz | API-Anbindung (api_integration) |
| Lizenzkosten p.a. | 6.000 EUR |
| Datenschutz | Personenbezogen (personal) |

Ergibt reproduzierbar: passiert den Vorfilter, Zone **CALCULATED_RISK**,
Aufwandscore **4 von 9 (MITTEL)**, Nettonutzen **18.948 EUR/Jahr**, Routing
**Automatisierung empfohlen**. Das Schaerfen erzeugt churn ~0,7-0,85 (-> Split-
Ansicht); Compliance zieht EU AI Act Art. 50.

> Hinweis: Bewerber-Vorsortierung ist ein EU-AI-Act-relevantes Feld. Die
> kuratierte Wissensbasis deckt DSGVO Art. 35 + EU AI Act Art. 50 ab (nicht
> Annex-III-Hochrisiko) -- das ehrlich ansprechen, es ist eine dokumentierte
> Grenze (known_limitations #5), kein Fehler. Alternativ ein weniger sensibles
> Feld waehlen (z. B. "Eingehende Anfragen grob nach Thema vorsortieren").

---

## 3. Smoke-Checkliste (Selbsttest vor der Demo)

Diese Sequenz spielt genau den Demo-Pfad einmal ohne Publikum durch. In der
Build-Umgebung steht **kein Browser-Treiber** (Playwright/Puppeteer) zur
Verfuegung; der Selbsttest laeuft daher ueber die API + SSR-HTML, die visuellen
Punkte werden separat markiert. Letzter vollstaendiger Durchlauf: **2026-07-11,
mit echten Azure-Calls + echtem Chroma-RAG, ohne Befund.**

### 3.1 API-Pfad (Backend laeuft gegen `aect_demo.db`)

```bash
# 1. Portfolio-Kennzahlen (anonym)
curl -s localhost:8000/stats
# 2. Anonyme Einreichung -> Case-ID merken
curl -s -X POST localhost:8000/triage -H 'Content-Type: application/json' -d @beispiel_case.json
# 3a. Anonym VOR Entscheidung: triage=null, report=null, eingaben!=null
curl -s localhost:8000/cases/<ID>
# 3b. Login -> Cookie-Jar
curl -s -c cj.txt -X POST localhost:8000/auth/login -H 'Content-Type: application/json' -d '{"password":"<demo-pw>"}'
# 3c. Admin sieht triage/report; 3d. Freigabe; 3e. Anonym danach sichtbar
curl -s -b cj.txt localhost:8000/cases/<ID>
curl -s -b cj.txt -X POST localhost:8000/cases/<ID>/decision -H 'Content-Type: application/json' -d '{"decision":"approved","note":"Demo"}'
# 4-11: sharpen -> accept -> propose-solution -> compliance-hints -> report  (alle -b cj.txt)
# 12: GET /cases (Board-Daten), 13: POST/GET monitoring, 14: POST /auth/logout
```

**Erwartete Ergebnisse (alle beim letzten Lauf erfuellt):**

- [x] `GET /stats` liefert die vier Kennzahlen.
- [x] `POST /triage` anonym -> **201**, vollstaendige Bewertung in der Antwort.
- [x] `GET /cases/{id}` **anonym vor** Board-Entscheidung: `triage`/`report`
      `null`, `eingaben` vorhanden.
- [x] `POST /auth/login` -> **200** + `aect_session`-Cookie.
- [x] `GET /cases/{id}` **als Admin** -> `triage`/`report` befuellt.
- [x] `POST /cases/{id}/decision` (approved) -> **200**.
- [x] `GET /cases/{id}` **anonym nach** Freigabe -> Bewertung jetzt sichtbar.
- [x] `POST /sharpen` -> **200**, Draft mit churn > 0,5 (Split-Ansicht),
      Vorschlaege als `bezugsfeld/vorschlag/hebel`, keine erfundenen Zahlen.
- [x] `POST /sharpen/accept` -> **200** (`status: accepted`).
- [x] `POST /propose-solution` -> **200**, `solution_business` (technikfrei) +
      `solution_technical`.
- [x] `POST /compliance-hints` -> **200**, Citations mit realen `source_id`
      (kein `mock-`-Prefix).
- [x] `POST /report` -> **200**, `business_summary.decision_report` +
      `technical_detail.technical_report` vollstaendig, dt. Zahlenformat.
- [x] `POST /monitoring` -> **201**, Eintrag mit `status_snapshot`.
- [x] `POST /auth/logout` -> **200**, danach Admin-Route **401** (Session
      serverseitig geloescht).

### 3.2 SSR-HTML (Frontend laeuft)

- [x] `/`, `/einreichen`, `/cases`, `/cases/{id}`, `/login`, `/ideation`,
      `/monitoring`, `/board` liefern **HTTP 200** ohne "Application error".
- [x] Landing zeigt die KPI-Kacheln.
- [x] Freigegebener Case zeigt anonym "Bewertungszone" + Zone + "Nettonutzen".
- [x] `/monitoring` + `/board` fuehren anonym zur Login-Aufforderung.

### 3.3 Manuell im Browser pruefen (kein Browser-Treiber in der Build-Umgebung)

Diese Punkte sind **strukturell** verifiziert (Layout-Argument bzw. Achsen-
Domain), aber **nicht** per Screenshot -- vor der echten Demo einmal mit den
Augen gegenpruefen:

- [ ] **Board-Achsen**: Achsentitel (linke Schiene / unteres Band) ueberlappen
      nicht mit den Tick-Labels; y-Skala 1-9, gut = oben rechts.
- [ ] **Board-Ecklabels** ("Quick Wins" etc.) sitzen plausibel in ihren
      Quadranten (Positionen sind Pixel-Naeherungen, nicht datengekoppelt).
- [ ] **Diff-Split** bei starkem Rewrite: zwei Spalten gut lesbar, Umschalter
      Inline/Split funktioniert.
- [ ] **Dark Mode** (Theme-Toggle) auf jeder gezeigten View.
- [ ] **Ladezustaende** (Skeletons) und der Wartezustand "Wird vom AI Board
      geprueft" (Clock-Icon) unterscheidbar.

---

## 4. Fallstricke

- **Admin-Login 503**: `AECT_ADMIN_PASSWORD_HASH` ist in der Backend-Shell nicht
  gesetzt (Abschnitt 1.2). Das Cookie kommt vom Backend; das Frontend spiegelt
  es nur.
- **Compliance zeigt "Wissensbasis nicht verfuegbar"**: Chroma laeuft nicht oder
  ist nicht geseedet -> Abschnitt 1.3. Das ist der gewollte fail-loud-Pfad
  (kein stiller Mock).
- **Compliance-Citations mit `mock-`-Prefix**: `AECT_CHROMA_HOST` zeigt nicht auf
  den laufenden Container -> Host/Port pruefen.
- **LLM-Schritte scheitern (503) / EU-Region-Fehler beim Start**: `.env` ohne
  gueltigen EU-Endpoint bzw. ohne `AECT_AZURE_OPENAI_REGION`.
- **Case-Detail zeigt anonym keine Bewertung**: erwartetes Verhalten, solange das
  Board nicht entschieden hat (Schritt 5).
- **Alte DB-Datei / Schema-Konflikt**: kein Migrations-Framework (Demo-Build) --
  `seed_demo.py --reset` bzw. die `*.db` loeschen.

## 5. Aufraeumen

```bash
# uvicorn + next dev stoppen (Ctrl-C), optional:
docker compose down
rm -f aect_demo.db                                     # gitignored, jederzeit neu seedbar
```
