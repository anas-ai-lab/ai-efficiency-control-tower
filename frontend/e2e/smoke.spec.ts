import { expect, test, type APIRequestContext } from "@playwright/test";

// Zwei UI-Smoke-Tests, die die bisher manuelle Durchklick-Pruefung ersetzen
// (S3-Nachtrag). Voraussetzungen + Startbefehle: e2e/README.md.
//
// (a) Passwort-Toggle auf der Login-Seite   -> nur Frontend noetig.
// (b) Implementierungsansatz-Nachtrag hebt den Vor-Bewertungs-Zustand auf
//     -> Frontend + Backend + Admin-Passwort noetig.
//
// Fehlt ein noetiger Prozess/Env-Wert, ueberspringt der jeweilige Test SAUBER
// (test.skip mit Grund), statt falsch fehlzuschlagen.

const FRONTEND_URL = process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000";
const BACKEND_URL = process.env.AECT_SMOKE_API_URL ?? "http://localhost:8000";
const ADMIN_PASSWORD = process.env.AECT_SMOKE_ADMIN_PASSWORD ?? "";

// Minimaler, gueltiger Triage-Payload OHNE implementation_approach -> der Case
// landet im Vor-Bewertungs-Zustand (evaluation_pending). Feldsatz gespiegelt aus
// tests/adapters/api/test_implementation_approach.py (_VALID_PAYLOAD).
function pendingCasePayload(title: string): Record<string, unknown> {
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

test("Passwort-Toggle schaltet Sichtbarkeit und aria-label um", async ({
  page,
  request,
}) => {
  test.skip(
    !(await serverUp(request, FRONTEND_URL)),
    `Frontend unter ${FRONTEND_URL} nicht erreichbar (npm run dev).`,
  );

  await page.goto("/login");
  const input = page.locator("#admin-password");
  await expect(input).toHaveAttribute("type", "password");

  // Toggle ist per aria-label ansprechbar; nach dem Klick wechselt das Label.
  await page.getByRole("button", { name: "Passwort anzeigen" }).click();
  await expect(input).toHaveAttribute("type", "text");
  await expect(
    page.getByRole("button", { name: "Passwort verbergen" }),
  ).toBeVisible();

  await page.getByRole("button", { name: "Passwort verbergen" }).click();
  await expect(input).toHaveAttribute("type", "password");
  await expect(
    page.getByRole("button", { name: "Passwort anzeigen" }),
  ).toBeVisible();
});

test("Implementierungsansatz-Nachtrag hebt den Vor-Bewertungs-Zustand auf", async ({
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

  // 1. Pending-Case direkt am (public) Backend anlegen -- ohne Ansatz.
  const title = `Smoke Pending ${Date.now()}`;
  const created = await request.post(`${BACKEND_URL}/triage`, {
    data: pendingCasePayload(title),
  });
  expect(created.ok()).toBeTruthy();
  const body = await created.json();
  expect(body.evaluation_pending).toBe(true);
  const caseId = body.id as string;

  // 2. Admin-Login ueber die UI (setzt das aect_session-Cookie im Context).
  await page.goto("/login");
  await page.locator("#admin-password").fill(ADMIN_PASSWORD);
  await page.getByRole("button", { name: "Anmelden" }).click();
  await page.waitForURL((u) => !u.pathname.startsWith("/login"), {
    timeout: 15000,
  });

  // 3. Case-Detail: Pending-Box sichtbar.
  await page.goto(`/cases/${caseId}`);
  await expect(page.getByText("Bewertung ausstehend")).toBeVisible();

  // 4. Ansatz ueber den Editor ergaenzen (approach war null -> Button "ergänzen").
  await page.getByRole("button", { name: "ergänzen" }).click();
  await page
    .getByLabel("Implementierungsansatz")
    .selectOption("development_on_existing");
  await page.getByRole("button", { name: "Speichern" }).click();

  // 5. Nach Erfolg: Pending-Box weg (deterministische Neubewertung, kein
  //    LLM-Call), und der Ansatz ist gesetzt -> Editor zeigt "ändern".
  await expect(page.getByText("Bewertung ausstehend")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "ändern" })).toBeVisible();

  // 6. Ideenliste: derselbe Case ohne Pending-Badge.
  await page.goto("/cases");
  const row = page.locator("tr", { hasText: title });
  await expect(row).toBeVisible();
  await expect(row.getByText("Bewertung ausstehend")).toHaveCount(0);
});
