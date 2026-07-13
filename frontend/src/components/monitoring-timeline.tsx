"use client";

import { useState } from "react";

import type { MonitoringEntry } from "@/types/api";
import { addMonitoringNote } from "@/app/actions";
import { STATUS_CONFIG } from "@/lib/status";
import { ActionError } from "@/components/action-error";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

const NOTE_MAX = 2000;

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("de-DE", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

// Monitoring-Zeitleiste im Case-Detail. Die API liefert Eintraege chronologisch
// AUFSTEIGEND; hier absteigend dargestellt (neuestes oben). Neue Notizen werden
// lokal oben eingefuegt (Prepend statt router.refresh -- gleiche Optik wie das
// optimistische Muster in ReviewSection). Der status_snapshot kommt vom Backend
// und spiegelt den Case-Status zum Zeitpunkt des Eintrags: nach einem
// Statuswechsel traegt die naechste Notiz automatisch den neuen Snapshot.
export function MonitoringTimeline({
  caseId,
  initialEntries,
}: {
  caseId: string;
  initialEntries: MonitoringEntry[];
}) {
  // Anzeige absteigend: initiale (aufsteigende) Liste einmal umdrehen.
  const [entries, setEntries] = useState<MonitoringEntry[]>(() =>
    [...initialEntries].reverse(),
  );
  const [note, setNote] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAdd() {
    const trimmed = note.trim();
    if (trimmed.length === 0) return;

    setPending(true);
    setError(null);
    try {
      const entry = await addMonitoringNote(caseId, trimmed);
      setEntries((prev) => [entry, ...prev]);
      setNote("");
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "Der Eintrag konnte nicht gespeichert werden.",
      );
    } finally {
      setPending(false);
    }
  }

  return (
    <section>
      <p className="eyebrow mb-3">Monitoring-Zeitleiste</p>

      {/* Notiz hinzufuegen */}
      <div className="rounded-xl border border-border bg-card p-4 sm:p-5">
        <Textarea
          placeholder="Beobachtung, Fortschritt oder Entscheidung notieren …"
          value={note}
          onChange={(e) => setNote(e.target.value.slice(0, NOTE_MAX))}
          maxLength={NOTE_MAX}
          disabled={pending}
          rows={3}
        />
        <div className="mt-2 flex items-center justify-between gap-4">
          <span className="text-xs text-muted-foreground tabular-nums">
            {note.length} / {NOTE_MAX}
          </span>
          <Button
            onClick={handleAdd}
            disabled={pending || note.trim().length === 0}
          >
            {pending ? "Wird gespeichert …" : "Eintrag hinzufügen"}
          </Button>
        </div>
        <ActionError message={error} className="mt-3" />
      </div>

      {/* Zeitleiste */}
      {entries.length === 0 ? (
        <p className="mt-6 text-sm text-muted-foreground">
          Noch keine Monitoring-Einträge.
        </p>
      ) : (
        <ol className="relative mt-6 space-y-6 border-l border-border pl-6">
          {entries.map((e) => (
            <li key={e.id} className="relative">
              {/* Punkt auf der Zeitleiste, gefaerbt nach status_snapshot. */}
              <span
                className={cn(
                  "absolute top-1 -left-6 size-2.5 -translate-x-1/2 rounded-full border-2 border-background",
                  STATUS_CONFIG[e.status_snapshot].dot,
                )}
                aria-hidden
              />
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                <time className="text-xs text-muted-foreground tabular-nums">
                  {formatDateTime(e.created_at)}
                </time>
                <StatusBadge status={e.status_snapshot} />
              </div>
              <p className="mt-1.5 text-sm leading-relaxed whitespace-pre-wrap text-foreground/90">
                {e.note}
              </p>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
