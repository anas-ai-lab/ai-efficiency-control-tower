"use client";

import { useTranslations } from "next-intl";

import type { CaseStatus, TriageZone } from "@/types/api";
import { STATUS_CONFIG } from "@/lib/status";
import { ZONE_CONFIG, type ZoneKey } from "@/lib/formatters";
import { cn } from "@/lib/utils";

// Geteilte Badges (V4.1-S6 client-only wegen useTranslations -- rendern in
// Server- UND Client-Komponenten). Farbe kommt aus STATUS_CONFIG/ZONE_CONFIG,
// das Label aus dem Sprachkatalog (status.* / zones.*.label).

export function StatusBadge({ status }: { status: CaseStatus }) {
  const t = useTranslations("status");
  const c = STATUS_CONFIG[status];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs font-medium",
        c.surface,
        c.text,
      )}
    >
      <span className={cn("size-1.5 rounded-full", c.dot)} aria-hidden />
      {t(status)}
    </span>
  );
}

export function ZoneBadge({ zone }: { zone: TriageZone | null }) {
  const t = useTranslations("zones");
  if (zone === null) {
    return <span className="text-muted-foreground">—</span>;
  }
  const c = ZONE_CONFIG[zone as ZoneKey];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs font-medium",
        c.surface,
        c.text,
      )}
    >
      <span className={cn("size-1.5 rounded-full", c.dot)} aria-hidden />
      {t(`${zone}.label`)}
    </span>
  );
}
