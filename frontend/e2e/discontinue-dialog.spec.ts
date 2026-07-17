import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

// Smoke fuer die Begruendungspflicht beim Einstellen (V4.1-S10, ADR-0053).
//
// Geprueft wird die UI-Haelfte der Zusicherung "ohne Begruendung UND Name keine
// Ausfuehrung": das Absenden bleibt gesperrt, solange eines der beiden Felder
// leer ODER nur Whitespace ist. Die API-Haelfte (422) deckt
// tests/adapters/api/test_discontinue.py ab -- beide Haelften sind noetig: die
// 422 schuetzt die Daten, die Sperre schuetzt den Nutzer vor einem Klick, der
// nur in einer Fehlermeldung enden kann.
//
// Der Whitespace-Fall ist der eigentliche Grund fuer diesen Test: "   " ist
// nicht leer und passiert eine naive required-Pruefung -- die Sperre muss auf
// dem getrimmten Wert stehen.
//
// Voraussetzungen + Startbefehle: e2e/README.md.

const FRONTEND_URL = process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000";
const BACKEND_URL = process.env.AECT_SMOKE_API_URL ?? "http://localhost:8000";
const ADMIN_PASSWORD = process.env.AECT_SMOKE_ADMIN_PASSWORD ?? "";

// Vollstaendiger Payload MIT implementation_approach -> der Case wird bewertet
// (kein Vor-Bewertungs-Zustand) und kann nach der Freigabe im Monitoring stehen.
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

async function loginAsAdmin(page: Page): Promise<void> {
  await page.goto("/login");
  await page.locator("#admin-password").fill(ADMIN_PASSWORD);
  await page.getByRole("button", { name: "Anmelden" }).click();
  await page.waitForURL((u) => !u.pathname.startsWith("/login"), {
    timeout: 15000,
  });
}

test("Einstellen-Dialog bleibt gesperrt ohne Begruendung und Name", async ({
  page,
  request,
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

  // 1. Bewerteten Case ueber die public /triage-API anlegen.
  const title = `Smoke Einstellen ${Date.now()}`;
  const created = await request.post(`${BACKEND_URL}/triage`, {
    data: evaluatedCasePayload(title),
  });
  expect(created.ok()).toBeTruthy();
  const caseId = (await created.json()).id as string;

  // 2. Admin-Login (setzt aect_session im Browser-Context).
  await loginAsAdmin(page);

  // 3. Freigeben -- erst dann steht der Case im Monitoring. Ueber page.request:
  //    der Session-Cookie gilt host-, nicht portgebunden und traegt damit auch
  //    zum Backend (kein API-Key im Test noetig, echter Admin-Pfad).
  const approved = await page.request.post(
    `${BACKEND_URL}/cases/${caseId}/status`,
    { data: { status: "approved" } },
  );
  expect(approved.ok()).toBeTruthy();

  // 4. Monitoring: Dialog der Zeile dieses Case oeffnen.
  await page.goto("/monitoring");
  // Zeilen-Wurzel (MonitoringRow) statt einer beliebigen verschachtelten div:
  // .filter({hasText}) allein trifft auch die innerste Titel-Zelle, in der der
  // Button gar nicht liegt. Der Titel ist je Lauf eindeutig (Zeitstempel).
  const row = page.locator("div.border-b").filter({ hasText: title });
  await row.getByRole("button", { name: "Use Case einstellen" }).click();

  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  const submit = dialog.getByRole("button", { name: "Einstellen", exact: true });
  const reason = dialog.getByLabel(/Begründung/);
  const actor = dialog.getByLabel(/Name der ausführenden Person/);

  // 5. Leer -> gesperrt.
  await expect(submit).toBeDisabled();

  // 6. Nur Begruendung -> weiterhin gesperrt.
  await reason.fill("Pilot ohne messbaren Nutzen beendet.");
  await expect(submit).toBeDisabled();

  // 7. Nur Name -> weiterhin gesperrt.
  await reason.fill("");
  await actor.fill("Maria Muster");
  await expect(submit).toBeDisabled();

  // 8. Beide Felder NUR Whitespace -> gesperrt. Der Kern des Tests: nicht-leer
  //    ist nicht dasselbe wie ausgefuellt.
  await reason.fill("   ");
  await actor.fill("   ");
  await expect(submit).toBeDisabled();

  // 9. Begruendung echt, Name Whitespace -> gesperrt (jede Haelfte zaehlt).
  await reason.fill("Pilot ohne messbaren Nutzen beendet.");
  await actor.fill("  ");
  await expect(submit).toBeDisabled();

  // 10. Beide gefuellt -> frei.
  await actor.fill("Maria Muster");
  await expect(submit).toBeEnabled();

  // 11. Ausfuehren: Dialog schliesst, Zustands-Badge erscheint, und der Verlauf
  //     traegt das Ereignis mit Aktion, Name und Begruendung.
  await submit.click();
  await expect(dialog).toHaveCount(0);
  await expect(row.getByText("Eingestellt", { exact: true })).toBeVisible();

  await row.getByRole("button", { name: "Verlauf" }).click();
  const entry = page.locator("li", { hasText: "Pilot ohne messbaren Nutzen beendet." });
  await expect(entry).toBeVisible();
  await expect(entry.getByText("durch Maria Muster")).toBeVisible();
});
