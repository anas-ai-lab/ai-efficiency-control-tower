import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

// Header-Layout-Guard (v4.2). Die Kopfleiste kollidierte unter 768px: die Nav
// behielt ihre Inhaltsbreite und lief sichtbar UEBER Abmelden/Sprache/Theme.
//
// Der Test prueft ZWEI Zusicherungen, weil eine allein den Fehler durchlaesst:
//
//  1. KEINE UEBERLAPPUNG zwischen Nav-Links und den rechten Steuerelementen.
//  2. KEIN CLIPPING der Nav (scrollWidth <= clientWidth).
//
// Warum beide: (1) allein war gruen fuer eine Zwischenfassung, die die Nav per
// overflow-x-auto abschnitt -- Labels standen dann als "Ideenli"/"Id" da.
// getBoundingClientRect liefert die LAYOUT-Position, nicht den sichtbar
// geclippten Bereich; ein reiner Rect-Test sieht abgeschnittene Labels nie.
// (2) allein wiederum wuerde eine ueberlappende, aber ungeclippte Nav durchlassen
// -- also genau den Ausgangsfehler.
//
// Nur das Frontend noetig (/cases ist public). Der Admin-Zustand hat eine
// andere Link-Menge (Board/Monitoring statt Einreichen/Ideen-Assistent) und
// war der urspruenglich gemeldete Fall -- er laeuft nur mit Passwort.

const FRONTEND_URL = process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000";
const ADMIN_PW = process.env.AECT_SMOKE_ADMIN_PASSWORD ?? "";

// Die Breiten, an denen die Leiste umbricht bzw. wieder einreiht.
const WIDTHS = [375, 640, 768, 1024, 1280, 1440];

async function serverUp(request: APIRequestContext, url: string): Promise<boolean> {
  try {
    const res = await request.get(url, { timeout: 3000 });
    return res.status() < 500;
  } catch {
    return false;
  }
}

async function assertHeaderIntact(page: Page, width: number) {
  await page.setViewportSize({ width, height: 900 });
  // Layout nach dem Viewport-Wechsel settlen lassen.
  await page.waitForTimeout(200);

  const result = await page.evaluate(() => {
    const bar = document.querySelector("header > div") as HTMLElement | null;
    const nav = bar?.querySelector("nav") as HTMLElement | null;
    if (!bar || !nav) return null;

    // Die rechte Gruppe ist der Container, der die Nav NICHT enthaelt.
    const controls = Array.from(bar.children).find(
      (el) => el !== nav && !el.contains(nav) && el.querySelector("button"),
    ) as HTMLElement | undefined;
    if (!controls) return null;

    const rect = (el: Element) => {
      const r = el.getBoundingClientRect();
      return { x: r.x, right: r.right, y: r.y, bottom: r.bottom };
    };

    const links = Array.from(nav.querySelectorAll("a")).map((a) => ({
      text: (a as HTMLElement).innerText.trim(),
      ...rect(a),
    }));

    return {
      links,
      controls: rect(controls),
      navScrollWidth: nav.scrollWidth,
      navClientWidth: nav.clientWidth,
    };
  });

  expect(result, "Header/Nav/Steuerelemente im DOM gefunden").not.toBeNull();
  const { links, controls, navScrollWidth, navClientWidth } = result!;

  // Positiv-Kontrolle: ohne sie bestuende der Test auch auf einer Fehlerseite,
  // auf der es schlicht keine Links zum Ueberlappen gibt.
  expect(links.length, `@${width}px: Nav-Links vorhanden`).toBeGreaterThan(1);

  // (1) Keine Ueberlappung mit den rechten Steuerelementen.
  for (const link of links) {
    const overlapX = Math.min(link.right, controls.right) - Math.max(link.x, controls.x);
    const overlapY = Math.min(link.bottom, controls.bottom) - Math.max(link.y, controls.y);
    const overlaps = overlapX > 0 && overlapY > 0;
    expect(
      overlaps,
      `@${width}px: Nav-Link "${link.text}" ueberlappt die rechten Steuerelemente ` +
        `(x ${Math.round(overlapX)}px, y ${Math.round(overlapY)}px)`,
    ).toBe(false);
  }

  // (2) Kein abgeschnittenes Label.
  expect(
    navScrollWidth,
    `@${width}px: Nav ist geclippt (scrollWidth ${navScrollWidth} > clientWidth ` +
      `${navClientWidth}) -- Labels stehen abgeschnitten`,
  ).toBeLessThanOrEqual(navClientWidth);
}

test("Kopfleiste kollidiert und clippt in keiner Breite (anonym)", async ({
  page,
  request,
}) => {
  test.skip(
    !(await serverUp(request, FRONTEND_URL)),
    `Frontend unter ${FRONTEND_URL} nicht erreichbar (npm run dev).`,
  );

  await page.goto("/cases");
  for (const width of WIDTHS) await assertHeaderIntact(page, width);
});

test("Kopfleiste kollidiert und clippt in keiner Breite (angemeldet)", async ({
  page,
  request,
}) => {
  test.skip(
    !(await serverUp(request, FRONTEND_URL)),
    `Frontend unter ${FRONTEND_URL} nicht erreichbar (npm run dev).`,
  );
  test.skip(
    ADMIN_PW === "",
    "AECT_SMOKE_ADMIN_PASSWORD nicht gesetzt -- Admin-Nav nicht pruefbar.",
  );

  await page.goto("/login");
  await page.getByLabel(/Passwort/i).first().fill(ADMIN_PW);
  await page.getByRole("button", { name: /Anmelden/i }).click();
  await page.waitForURL((u) => !u.pathname.includes("/login"), { timeout: 10000 });

  await page.goto("/cases");
  // Positiv-Kontrolle: der angemeldete Zustand zeigt die Admin-Links.
  await expect(page.getByRole("link", { name: "Monitoring" })).toBeVisible();

  for (const width of WIDTHS) await assertHeaderIntact(page, width);
});
