"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { CheckCircle2, Circle, XCircle } from "lucide-react";

import type { ReviewerDecision } from "@/types/api";
import { recordDecision } from "@/app/actions";
import { hardRefresh } from "@/lib/reload";
import { ActionError } from "@/components/action-error";
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
  { icon: React.ComponentType<{ className?: string }>; tone: string }
> = {
  approved: { icon: CheckCircle2, tone: "text-[var(--zone-win)]" },
  rejected: { icon: XCircle, tone: "text-destructive" },
  pending: { icon: Circle, tone: "text-muted-foreground" },
};

export function CaseDecision({ caseId, reviewerDecision, reviewerNote }: Props) {
  const t = useTranslations("decision");
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
      setError(e instanceof Error ? e.message : t("error"));
      setBusy(null);
    }
  }

  return (
    <div className="rounded-2xl border border-border bg-muted/30 p-5">
      <div className="flex items-center gap-2">
        <Icon className={`size-4 ${view.tone}`} />
        <span className="text-sm font-medium text-foreground">{t(reviewerDecision)}</span>
      </div>
      <Textarea
        className="mt-3"
        placeholder={t("notePlaceholder")}
        value={note}
        onChange={(e) => setNote(e.target.value)}
        maxLength={2000}
        disabled={busy !== null}
        rows={2}
      />
      <ActionError message={error} className="mt-3" />
      <div className="mt-3 flex gap-2">
        <Button onClick={() => handleDecide("approved")} disabled={busy !== null}>
          {busy === "approved" ? t("saving") : t("approve")}
        </Button>
        <Button
          variant="destructive"
          onClick={() => handleDecide("rejected")}
          disabled={busy !== null}
        >
          {busy === "rejected" ? t("saving") : t("reject")}
        </Button>
      </div>
    </div>
  );
}

export default CaseDecision;
