import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

// Smokes fuer die beiden Monitoring-Defekte aus dem Filter-/Revalidierungs-Pass.
//
// g) Leeres Filterergebnis behaelt seinen Rueckweg -- die Toolbar bleibt
//    stehen, der Empty-State liegt IM Ergebnisbereich und traegt einen Reset,
//    der die SearchParams entfernt (statt sie auf Default-Werte zu setzen).
//    Der Defekt war ein Early-Return vor der Toolbar: bei leerem Ergebnis
//    verschwand jede Bedienung, und weil kein Filter-State in der URL lag, half
//    auch ein Reload nicht.
//
// h) Ein Statuswechsel aus der Ideenliste ist im Monitoring sichtbar --
//    Verhaltens-Guard, KEIN Regressions-Anker fuer die Revalidierung.
//    Gemessen (Production-Build, reine Client-Navigation): der Durchgriff
//    funktioniert auch dann, wenn man saemtliche revalidatePath-Aufrufe aus
//    updateCaseStatus entfernt. /cases und /monitoring sind force-dynamic und
//    holen ihre Daten mit cache: "no-store"; Next 16 reicht dynamische Segmente
//    ohnehin nicht aus dem Client-Router-Cache weiter (staleTimes.dynamic = 0).
//    Der Test haelt also die ZUSAGE fest, nicht die Ursache -- er wuerde
//    anschlagen, wenn eine dieser Voraussetzungen kippt (jemand nimmt
//    force-dynamic weg, setzt staleTimes oder cached listCases).
//
// Beide Tests gehoeren gegen den PRODUCTION-Build (npm run build &&
// npm run start): im dev-Server sind die Caches aus, die hier gemeint sind.
//
// Voraussetzungen + Startbefehle: e2e/README.md.

const FRONTEND_URL = process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000";
const BACKEND_URL = process.env.AECT_SMOKE_API_URL ?? "http://localhost:8000";
const ADMIN_PASSWORD = process.env.AECT_SMOKE_ADMIN_PASSWORD ?? "";

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

async function requirements(
  request: APIRequestContext,
): Promise<void> {
  test.skip(
    !(await serverUp(request, `${BACKEND_URL}/health`)),
    `Backend unter ${BACKEND_URL} nicht erreichbar (uvicorn).`,
  );
  test.skip(
    !(await serverUp(request, FRONTEND_URL)),
    `Frontend unter ${FRONTEND_URL} nicht erreichbar (npm run start).`,
  );
  test.skip(
    ADMIN_PASSWORD === "",
    "AECT_SMOKE_ADMIN_PASSWORD nicht gesetzt (muss zum Backend-Hash passen).",
  );
}

test("g) Leeres Filterergebnis behaelt Toolbar und Rueckweg", async ({
  page,
  request,
}) => {
  await requirements(request);

  const title = `Smoke Filter ${Date.now()}`;
  const created = await request.post(`${BACKEND_URL}/triage`, {
    data: evaluatedCasePayload(title),
  });
  expect(created.ok()).toBeTruthy();
  const caseId = (await created.json()).id as string;

  await loginAsAdmin(page);
  const approved = await page.request.post(
    `${BACKEND_URL}/cases/${caseId}/status`,
    { data: { status: "approved" } },
  );
  expect(approved.ok()).toBeTruthy();

  await page.goto("/monitoring");
  const statusFilter = page.getByRole("combobox", { name: "Status" });
  await expect(statusFilter).toBeVisible();
  await expect(page.getByText(title)).toBeVisible();

  // Filter, der garantiert leer laeuft: der Case ist freigegeben, nicht umgesetzt.
  await statusFilter.click();
  await page.getByRole("option", { name: "Umgesetzt" }).click();

  // 1. Das Ergebnis ist leer ...
  await expect(page.getByText(title)).toHaveCount(0);
  await expect(
    page.getByText("Kein Use Case entspricht den aktiven Filtern."),
  ).toBeVisible();
  // 2. ... die Toolbar steht trotzdem (der eigentliche Defekt) ...
  await expect(statusFilter).toBeVisible();
  // 3. ... der aktive Filter ist als entfernbarer Chip mit Trefferzahl sichtbar ...
  await expect(page.getByLabel('Filter „Status“ entfernen')).toBeVisible();
  await expect(page.getByText(/0 von \d+ angezeigt/)).toBeVisible();
  // 4. ... und der Filter-State liegt in der URL, nicht in React-State.
  expect(new URL(page.url()).searchParams.get("status")).toBe("implemented");

  // 5. Reload-fest: der Filter ueberlebt, der Rueckweg ebenfalls.
  await page.reload();
  expect(new URL(page.url()).searchParams.get("status")).toBe("implemented");
  await expect(statusFilter).toBeVisible();

  // Screenshot des Empty-States MIT sichtbarer Toolbar (Beleg im Report).
  await page.screenshot({
    path: "e2e/__screenshots__/monitoring-empty-state.png",
    fullPage: true,
  });

  // Es gibt bewusst ZWEI Reset-Knoepfe im leeren Zustand: einen in der
  // Chip-Zeile (immer da, sobald ein Filter aktiv ist) und einen im Empty-State
  // selbst (dort, wo der Blick nach dem leeren Ergebnis landet). Beide werden
  // geprueft -- ein toter Zustand entstuende schon, wenn nur einer traegt.
  const resets = page.getByRole("button", { name: "Filter zurücksetzen" });
  await expect(resets).toHaveCount(2);

  // 6. Reset aus dem Empty-State entfernt den Param, statt ihn auf einen
  //    Default-Wert zu setzen.
  await resets.nth(1).click();
  expect(new URL(page.url()).searchParams.has("status")).toBe(false);
  await expect(page.getByText(title)).toBeVisible();

  // 7. Reset aus der Chip-Zeile ebenso.
  await statusFilter.click();
  await page.getByRole("option", { name: "Umgesetzt" }).click();
  await resets.first().click();
  expect(new URL(page.url()).searchParams.has("status")).toBe(false);
  await expect(page.getByText(title)).toBeVisible();

  // 8. Auch das Entfernen ueber den Chip fuehrt zurueck.
  await statusFilter.click();
  await page.getByRole("option", { name: "Umgesetzt" }).click();
  await page.getByLabel('Filter „Status“ entfernen').click();
  expect(new URL(page.url()).searchParams.has("status")).toBe(false);
  await expect(page.getByText(title)).toBeVisible();
});

test("h) Statuswechsel aus der Ideenliste schlaegt auf Monitoring durch", async ({
  page,
  request,
}) => {
  await requirements(request);

  const title = `Smoke Durchgriff ${Date.now()}`;
  const created = await request.post(`${BACKEND_URL}/triage`, {
    data: evaluatedCasePayload(title),
  });
  expect(created.ok()).toBeTruthy();

  await loginAsAdmin(page);

  // Ab hier AUSSCHLIESSLICH Client-Navigation (Link-Klicks). page.goto() waere
  // ein Volldokument-Load und wuerde den Client-Router-Cache jedes Mal leeren --
  // ein solcher Test kann die Frische nach einer Mutation gar nicht pruefen und
  // ist gruen, egal was die Anwendung tut. Genau diese Falle hat den ersten
  // Entwurf dieses Tests wertlos gemacht.
  //
  // Ebenso wichtig: nach der Navigation auf ein SICHTBARES Element warten
  // (toBeVisible/toHaveCount mit Auto-Wait). Ein blankes .count() misst den
  // Ladezustand (loading.tsx), nicht die Seite.

  // 1. Vorzustand: der Case ist eingereicht, steht also NICHT im Monitoring.
  //    Der Besuch legt den Router-Cache-Eintrag fuer /monitoring an.
  await page.getByRole("link", { name: "Monitoring" }).click();
  await page.waitForURL(/\/monitoring/);
  await expect(page.getByRole("combobox", { name: "Status" })).toBeVisible();
  await expect(page.getByText(title)).toHaveCount(0);

  // 2. Status in der IDEENLISTE wechseln (nicht im Monitoring, nicht im Detail).
  await page.getByRole("link", { name: "Ideenliste" }).click();
  await page.waitForURL(/\/cases/);
  const row = page.locator("tr", { hasText: title });
  await row.getByRole("combobox").click();
  await page.getByRole("option", { name: "Freigegeben" }).click();
  await expect(row.getByRole("combobox")).toContainText("Freigegeben");

  // 3. Zurueck ins Monitoring -- der Case muss dort stehen.
  await page.getByRole("link", { name: "Monitoring" }).click();
  await page.waitForURL(/\/monitoring/);
  await expect(page.getByText(title)).toBeVisible();

  // 4. Und ueber den Zurueck-Knopf des Browsers ebenso (eigener Cache-Pfad).
  await page.goBack();
  await page.waitForURL(/\/cases/);
  await page.goBack();
  await page.waitForURL(/\/monitoring/);
  await expect(page.getByText(title)).toBeVisible();
});
