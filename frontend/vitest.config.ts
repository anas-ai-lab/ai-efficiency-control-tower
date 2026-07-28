import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    // Nur Unit-Tests unter src/. Der vitest-Default-Glob wuerde sonst auch
    // e2e/*.spec.ts einsammeln -- die gehoeren Playwright (npm run e2e) und
    // brauchen einen laufenden Server.
    include: ["src/**/*.test.ts"],
  },
});
