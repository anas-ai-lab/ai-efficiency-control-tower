"use server";

import { cookies } from "next/headers";

import { LOCALE_COOKIE, type Locale } from "@/i18n/config";

// Setzt die aktive Sprache (V4.1-S6). httpOnly bewusst NICHT gesetzt: next-intl
// liest das Cookie serverseitig, aber der Wert ist keine Geheimnis-Information --
// ein Jahr Lebensdauer, damit die Wahl persistiert.
export async function setLocale(locale: Locale): Promise<void> {
  (await cookies()).set(LOCALE_COOKIE, locale, {
    path: "/",
    maxAge: 60 * 60 * 24 * 365,
    sameSite: "lax",
  });
}
