import { cookies } from "next/headers";
import { getRequestConfig } from "next-intl/server";

import { defaultLocale, isLocale, LOCALE_COOKIE } from "@/i18n/config";

// next-intl Request-Konfiguration (V4.1-S6): liest die aktive Locale aus dem
// NEXT_LOCALE-Cookie (kein URL-Prefix). Ungueltige/fehlende Werte fallen auf
// Deutsch zurueck -- fail-safe fuer die Anzeige, nie ein Crash.
export default getRequestConfig(async () => {
  const store = await cookies();
  const raw = store.get(LOCALE_COOKIE)?.value;
  const locale = isLocale(raw) ? raw : defaultLocale;

  return {
    locale,
    messages: (await import(`../../messages/${locale}.json`)).default,
  };
});
