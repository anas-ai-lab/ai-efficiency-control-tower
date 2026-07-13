import { defineConfig, devices } from "@playwright/test";

// UI-Smoke-Tests (S3-Nachtrag). Bewusst KEIN eigener webServer: das Frontend
// (und fuer Teil b das Backend) werden extern gestartet -- siehe e2e/README.md --,
// damit exakt der Stack geprueft wird, den ein Entwickler sonst manuell
// durchklickt. Ohne laufende Server ueberspringen die Tests sauber (kein
// falscher Fehlschlag); die Skip-Bedingungen stehen in e2e/smoke.spec.ts.
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000",
    trace: "off",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
