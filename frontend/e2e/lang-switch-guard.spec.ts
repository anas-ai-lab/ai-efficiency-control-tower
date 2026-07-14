import { expect, test, type APIRequestContext } from "@playwright/test";

// Sprachwechsel-Datenverlust-Schutz (V4.1-S6, Task 8): der harte Reload beim
// Sprachwechsel verwirft einen offenen Intake-Wizard. Zwei Faelle:
//
// (a) Befuellter Wizard  -> Sprachwechsel zeigt erst einen Bestaetigungsdialog.
// (b) Leerer Wizard      -> Sprachwechsel direkt, ohne Dialog.
//
// Nur das Frontend noetig (Einreichen-Seite ist public). Fehlt der Prozess,
// ueberspringt der Test SAUBER statt falsch fehlzuschlagen (Muster aus
// smoke.spec.ts).

const FRONTEND_URL = process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000";

async function serverUp(request: APIRequestContext, url: string): Promise<boolean> {
  try {
    const res = await request.get(url, { timeout: 3000 });
    return res.status() < 500;
  } catch {
    return false;
  }
}

test("Sprachwechsel bei leerem Wizard wechselt direkt ohne Dialog", async ({
  page,
  request,
}) => {
  test.skip(
    !(await serverUp(request, FRONTEND_URL)),
    `Frontend unter ${FRONTEND_URL} nicht erreichbar (npm run dev).`,
  );

  await page.goto("/einreichen");
  await expect(page.locator("html")).toHaveAttribute("lang", "de");

  // Nichts eingegeben -> Wechsel auf EN direkt, kein Bestaetigungsdialog.
  await page.getByRole("button", { name: "EN", exact: true }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
});

test("Sprachwechsel bei befuelltem Wizard zeigt Bestaetigungsdialog", async ({
  page,
  request,
}) => {
  test.skip(
    !(await serverUp(request, FRONTEND_URL)),
    `Frontend unter ${FRONTEND_URL} nicht erreichbar (npm run dev).`,
  );

  await page.goto("/einreichen");
  await expect(page.locator("html")).toHaveAttribute("lang", "de");

  // Ein Feld befuellen -> Formular ist dirty.
  await page.getByLabel("Titel").fill("Rechnungsverarbeitung mit KI");

  // Sprachwechsel -> erst Dialog, kein sofortiger Reload.
  await page.getByRole("button", { name: "EN", exact: true }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await expect(dialog.getByText("Sprache wechseln?")).toBeVisible();

  // Abbrechen -> Dialog weg, Sprache unveraendert, Eingabe bleibt erhalten.
  await dialog.getByRole("button", { name: "Abbrechen" }).click();
  await expect(dialog).toHaveCount(0);
  await expect(page.locator("html")).toHaveAttribute("lang", "de");
  await expect(page.getByLabel("Titel")).toHaveValue(
    "Rechnungsverarbeitung mit KI",
  );

  // Erneut wechseln und diesmal bestaetigen -> Reload in EN.
  await page.getByRole("button", { name: "EN", exact: true }).click();
  await expect(dialog).toBeVisible();
  await dialog.getByRole("button", { name: "Weiter" }).click();
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
});

test("Sprachwechsel nach Ideation-Prefill zeigt Dialog (isDirty=false)", async ({
  page,
  request,
}) => {
  test.skip(
    !(await serverUp(request, FRONTEND_URL)),
    `Frontend unter ${FRONTEND_URL} nicht erreichbar (npm run dev).`,
  );

  // Uebernommener Entwurf im sessionStorage -- Key/Felder gespiegelt aus
  // src/lib/ideation-prefill.ts (IDEATION_PREFILL_KEY + qualitative Felder).
  const draftTitle = "Aus Ideation uebernommener Entwurf";
  await page.goto("/einreichen");
  await page.evaluate(
    ([key, title]) => {
      sessionStorage.setItem(
        key,
        JSON.stringify({
          title,
          current_state:
            "Der aktuelle Prozess wurde im Ideen-Assistenten beschrieben.",
          desired_state:
            "Der Zielzustand wurde im Ideen-Assistenten beschrieben.",
          example_process: "Ein Beispielvorgang aus dem Assistenten.",
        }),
      );
    },
    ["aect_ideation_prefill", draftTitle],
  );
  // Der Wizard liest den Entwurf beim Mount -> Reload triggert die Uebernahme.
  await page.reload();
  await expect(page.getByLabel("Titel")).toHaveValue(draftTitle);

  // Der Nutzer hat nichts selbst getippt (isDirty=false), aber der Entwurf
  // traegt Inhalt: Sprachwechsel muss trotzdem den Bestaetigungsdialog zeigen.
  await page.getByRole("button", { name: "EN", exact: true }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await expect(dialog.getByText("Sprache wechseln?")).toBeVisible();
});
