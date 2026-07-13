import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const nextConfig: NextConfig = {
  /* config options here */
};

// next-intl ohne Locale-URL-Prefix (V4.1-S6): die aktive Sprache kommt aus dem
// NEXT_LOCALE-Cookie (src/i18n/request.ts), nicht aus dem Pfad -- internes Tool,
// kein SEO-/Routing-Umbau. Default bleibt Deutsch.
const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");

export default withNextIntl(nextConfig);
