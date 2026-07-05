"use client";

import { useState } from "react";

import type { CaseStatus } from "@/types/api";
import { updateCaseStatus } from "@/app/actions";
import { STATUS_CONFIG } from "@/lib/status";
import { StatusBadge } from "@/components/status-badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";

// Reihenfolge der Status im Select -- gleiche Ordnung wie in cases-table (P5),
// STATUS_CONFIG bleibt die einzige Quelle fuer Label/Farbe.
const STATUS_ORDER: CaseStatus[] = [
  "submitted",
  "in_review",
  "approved",
  "already_exists",
  "integrated",
  "rejected",
  "implemented",
];

// Kopf-Steuerung im Case-Detail: zeigt den aktuellen Status als Badge und
// erlaubt den Wechsel via Select. Optimistisches Update mit Rollback +
// Fehlertext -- gleiches Verhalten wie die Status-Zelle in cases-table (P5).
export function CaseStatusControl({
  caseId,
  initialStatus,
}: {
  caseId: string;
  initialStatus: CaseStatus;
}) {
  const [status, setStatus] = useState<CaseStatus>(initialStatus);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleChange(next: CaseStatus) {
    if (next === status) return;
    const prev = status;

    setStatus(next);
    setPending(true);
    setError(null);

    try {
      const res = await updateCaseStatus(caseId, next);
      setStatus(res.status);
    } catch (e) {
      setStatus(prev);
      setError(
        e instanceof Error ? e.message : "Statuswechsel fehlgeschlagen.",
      );
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center gap-3">
        <StatusBadge status={status} />
        <Select
          value={status}
          disabled={pending}
          onValueChange={(v) => handleChange(v as CaseStatus)}
        >
          <SelectTrigger size="sm" className="w-[9.75rem]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {STATUS_ORDER.map((s) => (
              <SelectItem key={s} value={s}>
                <span
                  className={cn("size-1.5 rounded-full", STATUS_CONFIG[s].dot)}
                  aria-hidden
                />
                {STATUS_CONFIG[s].labelDE}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      {error !== null && (
        <p role="alert" className="text-xs text-destructive">
          {error}
        </p>
      )}
    </div>
  );
}
