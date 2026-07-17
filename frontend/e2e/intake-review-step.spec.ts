import { expect, test, type APIRequestContext } from "@playwright/test";

// Guard: kein Absenden ohne expliziten Bestaetigungsklick.
//
// Regression aus V4.1: der Klick auf "Weiter" im vorletzten Schritt hat den Case
// SOFORT abgesendet -- die Zusammenfassung war nie zu sehen. Ursache war der
// Wechsel desselben DOM-Buttons von type="button" auf type="submit": goNext ist
// async, React flusht den neuen Schritt im Microtask-Checkpoint, und der Browser
// fuehrt die Activation-Behavior des Klicks ERST DANACH aus -- auf dem inzwischen
// zum Absende-Button gewordenen Element. Reines Code-Lesen findet das nicht,
// darum dieser Browser-Test.
//
// Braucht NUR das Frontend: der Test stoppt vor dem Absenden, es entsteht kein
// Case. Fehlt der Prozess, wird SAUBER uebersprungen (Muster aus smoke.spec.ts).

const FRONTEND_URL = process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000";

async function serverUp(request: APIRequestContext, url: string): Promise<boolean> {
  try {
    const res = await request.get(url, { timeout: 3000 });
    return res.status() < 500;
  } catch {
    return false;
  }
}

// Radix-Select: Trigger anklicken, dann die n-te Option waehlen.
async function pickSelect(
  page: import("@playwright/test").Page,
  index: number,
  optionIdx = 0,
): Promise<void> {
  await page.locator('button[role="combobox"]').nth(index).click();
  await page.getByRole("option").nth(optionIdx).click();
}

test("Weiter im vorletzten Schritt zeigt die Zusammenfassung statt abzusenden", async ({
  page,
  request,
}) => {
  test.skip(
    !(await serverUp(request, FRONTEND_URL)),
    `Frontend unter ${FRONTEND_URL} nicht erreichbar (npm run dev).`,
  );

  await page.goto("/einreichen");

  // --- Schritt 1: Idee ---
  await page.locator('[name="title"]').fill("Rechnungspruefung mit KI beschleunigen");
  await page.locator('[name="submitter"]').fill("A. Tester");
  await page.locator('[name="department"]').fill("Finanzbuchhaltung");
  await page
    .locator('[name="current_state"]')
    .fill("Rechnungen werden heute von Hand geprueft, sortiert und im System erfasst.");
  await page
    .locator('[name="desired_state"]')
    .fill("Rechnungen werden automatisch vorgeprueft, nur Abweichungen landen manuell.");
  await page
    .locator('[name="example_process"]')
    .fill("Eine Rechnung kommt per Mail, wird geoeffnet, geprueft und abgetippt.");
  await page.getByRole("button", { name: "Weiter" }).click();

  // --- Schritt 2: Zeit & Haeufigkeit ---
  await pickSelect(page, 0); // Land
  await pickSelect(page, 1); // Mitarbeiterlevel
  await page.locator('[name="time_per_case_hours_current"]').fill("0.5");
  await page.locator('[name="time_per_case_hours_with_ai"]').fill("0.1");
  await page.locator('[name="occurrences_per_employee_per_year"]').fill("500");
  await page.locator('[name="affected_employees_count"]').fill("20");
  await page.getByRole("button", { name: "Weiter" }).click();

  // --- Schritt 3: Umsetzung (Ansatz bleibt leer -- optional, ADR-0050) ---
  await page.locator('[name="implementation_cost_eur"]').fill("5000");
  await page.locator('[name="estimated_license_cost_eur"]').fill("0");
  await page.getByRole("button", { name: "Weiter" }).click();

  // --- Schritt 4: Daten & Verbindlichkeit ---
  await pickSelect(page, 0); // Datenschutzklasse
  await pickSelect(page, 1); // Verbindlichkeit
  await pickSelect(page, 2); // Evidenzlevel

  // Der eigentliche Guard: dieser Klick darf NICHT absenden.
  await page.getByRole("button", { name: "Weiter" }).click();

  // Zusammenfassung sichtbar -- nach Abschnitten gruppiert. Die Namen stehen
  // hier in der DOM-Schreibweise: .eyebrow zeigt sie via text-transform in
  // Grossbuchstaben, der Accessible Name bleibt der Text im Markup.
  await expect(page.getByRole("button", { name: "Use Case einreichen" })).toBeVisible();
  for (const heading of ["Idee", "Zeit & Häufigkeit", "Umsetzung", "Daten & Verbindlichkeit"]) {
    await expect(page.getByRole("heading", { name: heading, exact: true })).toBeVisible();
  }
  // Eingaben stehen read-only in der Zusammenfassung.
  await expect(page.getByText("Rechnungspruefung mit KI beschleunigen")).toBeVisible();

  // Nicht abgesendet: keine Erfolgs-Bestaetigung.
  await expect(page.getByRole("status")).toHaveCount(0);
  await expect(page.getByText("Use Case eingereicht")).toHaveCount(0);

  // Korrigieren muss moeglich sein: zurueck in den Idee-Schritt und wieder vor.
  await page.getByRole("button", { name: "Ändern" }).first().click();
  await expect(page.locator('[name="title"]')).toHaveValue(
    "Rechnungspruefung mit KI beschleunigen",
  );
  await expect(page.getByRole("status")).toHaveCount(0);
});
