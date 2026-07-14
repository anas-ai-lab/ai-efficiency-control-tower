"use client";

import { useFormatter } from "next-intl";

import { bindFormat, type AppFormat } from "@/lib/format";

// Client-Hook: an die aktive Locale gebundene Formatierer (V4.1-S6). Server-
// Komponenten nutzen stattdessen bindFormat(await getFormatter()) direkt.
export function useFormat(): AppFormat {
  return bindFormat(useFormatter());
}
