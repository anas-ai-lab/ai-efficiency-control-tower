// Zentrale i18n-Konstanten (V4.1-S6). Deutsch ist Default; Englisch die zweite
// Sprache. Kein Locale-URL-Prefix -- die aktive Sprache steht im Cookie.

export const locales = ["de", "en"] as const;
export type Locale = (typeof locales)[number];

export const defaultLocale: Locale = "de";

// Cookie-Name (next-intl-Konvention). Wird vom Sprachumschalter gesetzt und in
// src/i18n/request.ts gelesen; Server Actions reichen den Wert als lang-Query
// an das Backend durch.
export const LOCALE_COOKIE = "NEXT_LOCALE";

export function isLocale(value: string | undefined): value is Locale {
  return value === "de" || value === "en";
}
