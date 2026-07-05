import type { CaseStatus, TriageZone } from "@/types/api";
import { STATUS_CONFIG } from "@/lib/status";
import { ZONE_CONFIG, type ZoneKey } from "@/lib/formatters";
import { cn } from "@/lib/utils";

// Server-sichere Badges (kein "use client"): nutzbar in Server- und Client-
// Komponenten. Farbe/Label kommen ausschliesslich aus STATUS_CONFIG bzw.
// ZONE_CONFIG (einzige Quelle). Analog zur (lokalen) ZoneBadge in cases-table --
// hier als geteilte Variante fuer /cases/[id] und /monitoring.

export function StatusBadge({ status }: { status: CaseStatus }) {
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
      {c.labelDE}
    </span>
  );
}

export function ZoneBadge({ zone }: { zone: TriageZone | null }) {
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
      {c.labelDE}
    </span>
  );
}
