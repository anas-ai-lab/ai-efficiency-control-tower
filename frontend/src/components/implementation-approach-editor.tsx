"use client";

import { useState } from "react";

import { setImplementationApproach } from "@/app/actions";
import { hardRefresh } from "@/lib/reload";
import { ActionError } from "@/components/action-error";
import { Button } from "@/components/ui/button";
import {
  IMPLEMENTATION_APPROACH_LABELS,
  IMPLEMENTATION_APPROACH_OPTIONS,
} from "@/lib/labels";
import type { ImplementationApproach } from "@/types/api";

// Read-only Anzeige des Implementierungsansatzes + (nur Admin) ein kleines
// Edit-Feld zum Nachtragen (V4.1, ADR-0050). Minimal-invasiv an der heutigen
// Stelle des Felds in CaseInputs. Das Nachtragen loest serverseitig eine
// vollstaendige Neubewertung aus; router.refresh() laedt den neuen Stand.
export function ImplementationApproachEditor({
  caseId,
  approach,
  isAdmin,
}: {
  caseId: string;
  approach: ImplementationApproach | null;
  isAdmin: boolean;
}) {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState<string>(approach ?? "");
  const [isPending, setIsPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const label = approach ? IMPLEMENTATION_APPROACH_LABELS[approach] : "—";

  // Harter Reload statt router.refresh() (Prod-Router-Cache, siehe lib/reload):
  // der Nachtrag loest ohnehin eine vollstaendige Neubewertung aus -> ein
  // sauberer Reload der Detailseite ist hier angemessen.
  async function save() {
    if (value === "") return;
    setError(null);
    setIsPending(true);
    try {
      await setImplementationApproach(caseId, value as ImplementationApproach);
      hardRefresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Speichern fehlgeschlagen.");
      setIsPending(false);
    }
  }

  return (
    <div className="grid grid-cols-1 gap-0.5 py-2 sm:grid-cols-[13rem_1fr] sm:gap-4">
      <dt className="text-sm text-muted-foreground">Implementierungsansatz</dt>
      <dd className="text-sm text-foreground/90">
        {!editing ? (
          <div className="flex flex-wrap items-center gap-2.5">
            <span>{label}</span>
            {isAdmin && (
              <button
                type="button"
                onClick={() => {
                  setValue(approach ?? "");
                  setEditing(true);
                }}
                className="text-xs font-medium text-[var(--ink)] underline decoration-[var(--ink)]/40 underline-offset-4 hover:decoration-[var(--ink)]"
              >
                {approach ? "ändern" : "ergänzen"}
              </button>
            )}
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            <div className="flex flex-wrap items-center gap-2">
              <select
                value={value}
                onChange={(e) => setValue(e.target.value)}
                disabled={isPending}
                aria-label="Implementierungsansatz"
                className="rounded-md border border-border bg-background px-2.5 py-1.5 text-sm text-foreground"
              >
                <option value="" disabled>
                  Bitte wählen
                </option>
                {IMPLEMENTATION_APPROACH_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
              <Button
                type="button"
                size="sm"
                onClick={save}
                disabled={isPending || value === ""}
              >
                {isPending ? "Speichern …" : "Speichern"}
              </Button>
              <Button
                type="button"
                size="sm"
                variant="ghost"
                onClick={() => {
                  setEditing(false);
                  setError(null);
                }}
                disabled={isPending}
              >
                Abbrechen
              </Button>
            </div>
            <p className="text-xs leading-relaxed text-muted-foreground">
              Ergänzen löst eine vollständige Neubewertung des Falls aus.
            </p>
            <ActionError message={error} className="mt-1" />
          </div>
        )}
      </dd>
    </div>
  );
}

export default ImplementationApproachEditor;
