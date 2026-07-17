import { expect, test, type APIRequestContext } from "@playwright/test";

import de from "../messages/de.json";

// Guard fuer den Schema-Split public/admin (ADR-0052) an der gerenderten
// Oberflaeche: ein anonymer Besucher darf auf der Fall-Detailseite KEINE
// Bewertung sehen -- nur Grunddaten, Status und die Board-Entscheidung mit
// Begruendung. Der Backend-Vertrag ist separat abgesichert
// (tests/adapters/api/test_case_detail.py, rekursiv ueber das JSON); dieser Test
// prueft, was tatsaechlich im Browser steht. Er macht die frueher einmalig
// manuelle Sichtpruefung wiederholbar.
//
// Voraussetzungen + Startbefehle: e2e/README.md. Ohne laufende Prozesse bzw.
// ohne Admin-Passwort ueberspringt der Test SAUBER (test.skip mit Grund).
//
// Der Fall wird in den schaerfsten Zustand gebracht, den es gibt: bewertet UND
// vom Board freigegeben. Genau hier leakte die Vorgaenger-Version (Bewertung war
// nach der Entscheidung anonym sichtbar) -- ein unentschiedener Case wuerde die
// Regression nicht zeigen.

const FRONTEND_URL = process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000";
const BACKEND_URL = process.env.AECT_SMOKE_API_URL ?? "http://localhost:8000";
const ADMIN_PASSWORD = process.env.AECT_SMOKE_ADMIN_PASSWORD ?? "";

// Die Board-Begruendung ist auf der anonymen Seite sichtbar (sie ist der Zweck
// der Seite) -- deshalb bewusst frei von Bewertungs-Vokabular: stuende hier
// "Aufwand" oder "Report", wuerde der Negativ-Test an einem erlaubten Text
// scheitern statt an einem Leck.
const RATIONALE = "Vom Board freigegeben; Umsetzung im naechsten Quartal geplant.";

// Vollstaendiger Payload MIT implementation_approach -> der Case wird sofort
// bewertet (kein Vor-Bewertungs-Zustand). Deterministische Regel-Schicht, kein
// LLM-/Azure-Call. Feldsatz gespiegelt aus tests/adapters/api/test_case_detail.py.
function evaluatedCasePayload(title: string): Record<string, unknown> {
  return {
    title,
    submitter: "Smoke Test",
    department: "Finance",
    country: "de",
    current_state:
      "Rechnungen werden aktuell manuell gescannt und in SAP eingetragen; " +
      "pro Rechnung rund 15 Minuten.",
    desired_state:
      "Ein KI-System soll Rechnungen automatisch auslesen und in SAP " +
      "befuellen; Ziel unter 2 Minuten pro Rechnung.",
    example_process:
      "Rechnung von Lieferant X wird manuell gescannt und abgetippt.",
    time_per_case_hours_current: 0.2,
    time_per_case_hours_with_ai: 0.0,
    occurrences_per_employee_per_year: 5000,
    affected_employees_count: 10,
    employee_category: "professional",
    adoption_type: "fixed_process_step",
    evidence_level: "pure_estimate",
    implementation_approach: "development_on_existing",
    data_classification: "no_personal_data",
  };
}

async function serverUp(request: APIRequestContext, url: string): Promise<boolean> {
  try {
    const res = await request.get(url, { timeout: 3000 });
    return res.status() < 500;
  } catch {
    return false;
  }
}

// Formatiert eine Zahl so, wie die Oberflaeche sie in der de-Locale ausgeben
// wuerde (lib/format.ts: eur() -> Waehrung ohne Nachkommastellen). Gesucht wird
// die Ziffergruppe ("259.200"), nicht der komplette Waehrungsstring -- sie ist
// der Teil, der bei einem Leak sichtbar waere.
function deDigits(value: number): string {
  return new Intl.NumberFormat("de-DE", { maximumFractionDigits: 0 }).format(
    value,
  );
}

test("anonyme Detailseite zeigt die Board-Entscheidung, aber keine Bewertung", async ({
  page,
  request,
  context,
}) => {
  test.skip(
    !(await serverUp(request, `${BACKEND_URL}/health`)),
    `Backend unter ${BACKEND_URL} nicht erreichbar (uvicorn).`,
  );
  test.skip(
    !(await serverUp(request, FRONTEND_URL)),
    `Frontend unter ${FRONTEND_URL} nicht erreichbar (npm run dev).`,
  );
  test.skip(
    ADMIN_PASSWORD === "",
    "AECT_SMOKE_ADMIN_PASSWORD nicht gesetzt (muss zum Backend-Hash passen).",
  );

  // 1. Bewerteten Case anonym ueber die public /triage-API anlegen.
  const title = `Smoke Sichtbarkeit ${Date.now()}`;
  const created = await request.post(`${BACKEND_URL}/triage`, {
    data: evaluatedCasePayload(title),
  });
  expect(created.ok()).toBeTruthy();
  const createdBody = await created.json();
  expect(createdBody.evaluation_pending).toBe(false);
  const caseId = createdBody.id as string;

  // 2. Als Admin am Backend anmelden (Session-Cookie landet im request-Context)
  //    und den Fall freigeben -- der Zustand, in dem frueher geleakt wurde.
  const login = await request.post(`${BACKEND_URL}/auth/login`, {
    data: { password: ADMIN_PASSWORD },
  });
  expect(login.ok()).toBeTruthy();
  const decided = await request.post(`${BACKEND_URL}/cases/${caseId}/decision`, {
    data: { decision: "approved", note: RATIONALE },
  });
  expect(decided.ok()).toBeTruthy();

  // 3. Die echten Bewertungswerte dieses Falls aus der ADMIN-Sicht holen. Sie
  //    sind die Suchbegriffe fuer Schritt 5: nur was das Board sieht, kann
  //    anonym leaken -- hartkodierte Erwartungswerte wuerden bei jeder
  //    Kalibrierung des Modells veralten.
  const adminDetail = await request.get(`${BACKEND_URL}/cases/${caseId}`);
  expect(adminDetail.ok()).toBeTruthy();
  const admin = await adminDetail.json();
  expect(admin.triage).not.toBeNull(); // Admin sieht die Bewertung -> Gegenprobe
  const netBenefit = admin.triage.roi.net_expected_benefit_eur as number;
  const zoneValue = admin.triage.zone.final_zone as string;

  // 4. Anonymer Browser-Context: KEIN Session-Cookie. (Der request-Context oben
  //    ist ein eigener Cookie-Jar -- die Seite ist hier tatsaechlich anonym.)
  await context.clearCookies();
  await page.goto(`/cases/${caseId}`);

  // 5a. POSITIV-KONTROLLE ZUERST: die Seite hat wirklich den Fall gerendert.
  //     Ohne diese Zusicherung wuerde jede Fehler-/404-Seite den Negativ-Test
  //     unten bestehen -- ein gruener Test, der nichts beweist.
  await expect(
    page.getByRole("heading", { name: title, level: 1 }),
  ).toBeVisible();
  await expect(page.getByText("Erfasste Eingaben")).toBeVisible();

  // Entscheidung + Begruendung im zugehoerigen Abschnitt (nicht irgendwo):
  // "Freigegeben" steht auch als Status-Badge im Seitenkopf -- ohne die
  // Eingrenzung waere der Treffer mehrdeutig und die Zusicherung schwaecher.
  const decisionSection = page.locator("section").filter({
    has: page.getByRole("heading", {
      name: "Entscheidung des AI Board",
      level: 2,
    }),
  });
  await expect(decisionSection).toBeVisible();
  // exact: true -- getByText matcht sonst case-insensitiv als Teilstring und
  // der Begruendungstext ("Vom Board freigegeben; ...") waere ein zweiter
  // Treffer neben dem Status-Label.
  await expect(
    decisionSection.getByText("Freigegeben", { exact: true }),
  ).toBeVisible();
  await expect(decisionSection.getByText(RATIONALE)).toBeVisible();

  // 5b. NEGATIV: kein Bewertungsbegriff und kein Bewertungswert im sichtbaren
  //     Text. Bewusst innerText und NICHT page.content(): der komplette
  //     i18n-Katalog steht als JSON im RSC-Payload des HTML und enthaelt
  //     "Zone"/"Nettonutzen" als Label-Strings -- das ist keine Case-Daten-
  //     Ausgabe. Geprueft wird, was ein Besucher liest.
  const visibleText = await page.locator("body").innerText();

  // Jeder Begriff hier ist auf der ADMIN-Seite desselben Falls nachweislich
  // vorhanden -- nur dann belegt sein Fehlen auf der anonymen Seite etwas.
  // Verworfen wurden u. a. "Zone", "Nettonutzen", "Machbarkeit" und "Konfidenz":
  // sie stehen nirgends im sichtbaren Text (die Oberflaeche zeigt Zonen-LABEL und
  // Kennzahlen, nicht diese Woerter). Ein Begriff, der im UI gar nicht vorkommt,
  // kann kein Leck fangen -- er taeuscht nur Deckung vor.
  const forbiddenTerms = [
    "Analyse & Empfehlung", // Ueberschrift des Bewertungsbereichs
    "Empfehlung",
    "Aufwand",
    // "Nutzen" waere zu generisch: das Wort steht legitim in einer
    // Board-Begruendung ("klarer Nutzen bei geringem Risiko") und wuerde den Test
    // an einem erlaubten Text scheitern lassen, nicht an einem Leck.
    "Report",
    "Entscheidung & Report", // Ueberschrift des Admin-Bereichs 3
    "Lösungsvorschlag",
    "Compliance",
  ];
  for (const term of forbiddenTerms) {
    expect(visibleText, `Bewertungsbegriff "${term}" ist anonym sichtbar`).not.toContain(
      term,
    );
  }

  // Zahlen-Suchbegriffe: formatiert ("259.200", so zeigt die UI es) und roh
  // ("259200"). Kurze Zahlen werden verworfen -- eine ein- bis dreistellige Zahl
  // steht auch im Datum oder in Zaehlern und wuerde den Test falsch rot faerben,
  // ohne je ein Leck zu belegen. Der Payload oben erzeugt einen sechsstelligen
  // Nettonutzen; der Filter ist die Absicherung fuer den Fall, dass das
  // Bewertungsmodell spaeter anders kalibriert wird.
  const numericNeedles = [deDigits(netBenefit), String(Math.round(netBenefit))].filter(
    (v) => v.replace(/\D/g, "").length >= 4,
  );

  // Die Zone erscheint im UI NIE als Enum-Wert ("LIKELY_WIN"), sondern als
  // uebersetztes Label. Gesucht wird deshalb das Label -- aus demselben Katalog
  // gelesen, den die Oberflaeche nutzt, statt hier zweitgeschrieben: eine
  // Umbenennung im Katalog darf diesen Test nicht still entwaffnen.
  const zoneLabel = (de.zones as Record<string, { label: string }>)[zoneValue]?.label;
  expect(zoneLabel, `Kein Label fuer Zone "${zoneValue}" im de-Katalog`).toBeTruthy();

  const forbiddenValues = [...numericNeedles, zoneLabel];
  for (const value of forbiddenValues) {
    expect(visibleText, `Bewertungswert "${value}" ist anonym sichtbar`).not.toContain(
      value,
    );
  }

  // 6. Die Ideenliste ist der zweite Pfad derselben Zusicherung (sie unterlief
  //    frueher den Detail-Schutz): keine Bewertungsspalten, aber der Fall ist da.
  await page.goto("/cases");
  const row = page.locator("tr", { hasText: title });
  await expect(row).toBeVisible();
  const listText = await page.locator("table").innerText();
  expect(listText).not.toContain("Nettonutzen");
  expect(listText).not.toContain(deDigits(netBenefit));
});
