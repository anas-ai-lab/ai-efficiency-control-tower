"use client";

import { useState } from "react";
import { CheckCircle2, Circle, XCircle } from "lucide-react";

import type { ReviewerDecision } from "@/types/api";
import { recordDecision } from "@/app/actions";
import { hardRefresh } from "@/lib/reload";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

// Reviewer-Entscheidung (Human-in-the-Loop, ADR-0043) -- Bereich 3
// "Entscheidung & Report" der Detailseite (S4). Bewusst OHNE Werkzeug-Buttons
// (Zielgruppe: Entscheider). Aus der frueheren CaseAdminActions herausgeloest;
// Verhalten unveraendert, nur router.refresh() -> hardRefresh() (Prod-Cache).

interface Props {
  caseId: string;
  reviewerDecision: ReviewerDecision;
  reviewerNote: string | null;
}

const DECISION_VIEW: Record<
  ReviewerDecision,
  { label: string; icon: React.ComponentType<{ className?: string }>; tone: string }
> = {
  approved: { label: "Freigegeben", icon: CheckCircle2, tone: "text-[var(--zone-win)]" },
  rejected: { label: "Abgelehnt", icon: XCircle, tone: "text-destructive" },
  pending: { label: "Ausstehend", icon: Circle, tone: "text-muted-foreground" },
};

export function CaseDecision({ caseId, reviewerDecision, reviewerNote }: Props) {
  const [note, setNote] = useState(reviewerNote ?? "");
  const [busy, setBusy] = useState<"approved" | "rejected" | null>(null);
  const [error, setError] = useState<string | null>(null);

  const view = DECISION_VIEW[reviewerDecision];
  const Icon = view.icon;

  async function handleDecide(decision: "approved" | "rejected") {
    setBusy(decision);
    setError(null);
    try {
      const trimmed = note.trim();
      await recordDecision(caseId, decision, trimmed.length > 0 ? trimmed : null);
      hardRefresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Entscheidung fehlgeschlagen.");
      setBusy(null);
    }
  }

  return (
    <div className="rounded-2xl border border-border bg-muted/30 p-5">
      <div className="flex items-center gap-2">
        <Icon className={`size-4 ${view.tone}`} />
        <span className="text-sm font-medium text-foreground">{view.label}</span>
      </div>
      <Textarea
        className="mt-3"
        placeholder="Optionale Begründung"
        value={note}
        onChange={(e) => setNote(e.target.value)}
        maxLength={2000}
        disabled={busy !== null}
        rows={2}
      />
      {error !== null && (
        <p
          role="alert"
          className="mt-3 rounded-lg border border-destructive/25 bg-destructive/5 px-4 py-3 text-sm text-destructive"
        >
          {error}
        </p>
      )}
      <div className="mt-3 flex gap-2">
        <Button onClick={() => handleDecide("approved")} disabled={busy !== null}>
          {busy === "approved" ? "Wird gespeichert …" : "Freigeben"}
        </Button>
        <Button
          variant="destructive"
          onClick={() => handleDecide("rejected")}
          disabled={busy !== null}
        >
          {busy === "rejected" ? "Wird gespeichert …" : "Ablehnen"}
        </Button>
      </div>
    </div>
  );
}

export default CaseDecision;
