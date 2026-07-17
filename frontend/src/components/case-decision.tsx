"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { CheckCircle2, Circle, Loader2, XCircle } from "lucide-react";

import type { ReviewerDecision } from "@/types/api";
import { recordDecision } from "@/app/actions";
import { hardRefresh } from "@/lib/reload";
import { ActionError } from "@/components/action-error";
import { useLlmBusy } from "@/components/llm-busy";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

// Reviewer-Entscheidung (Human-in-the-Loop, ADR-0043) -- Bereich 3
// "Entscheidung & Report" der Detailseite (S4). Bewusst OHNE Werkzeug-Buttons
// (Zielgruppe: Entscheider). Aus der frueheren CaseAdminActions herausgeloest;
// router.refresh() -> hardRefresh() (Prod-Cache).
//
// Solange ein Werkzeug aus Bereich 2 einen LLM-Call offen hat (useLlmBusy),
// ist die Entscheidung gesperrt UND der Grund steht daneben. Ohne die Sperre
// landete der Klick in der serialisierten Server-Action-Warteschlange und der
// Button behauptete minutenlang "Wird gespeichert …" (s. llm-busy.tsx).

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
  // Laeuft parallel eine Analyse (Bereich 2)? Dann waere jeder Klick nur eine
  // stille Wartemarke -- lieber sperren und den Grund zeigen.
  const analysisRunning = useLlmBusy();
  const waiting = analysisRunning && busy === null;

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
      {waiting && (
        <p
          role="status"
          aria-live="polite"
          className="mt-3 flex items-center gap-2 text-sm text-muted-foreground"
        >
          <Loader2 className="size-4 animate-spin text-[var(--ink)]" />
          {t("analysisRunning")}
        </p>
      )}
      <div className="mt-3 flex gap-2">
        <Button
          onClick={() => handleDecide("approved")}
          disabled={busy !== null || analysisRunning}
        >
          {busy === "approved" ? t("saving") : t("approve")}
        </Button>
        <Button
          variant="destructive"
          onClick={() => handleDecide("rejected")}
          disabled={busy !== null || analysisRunning}
        >
          {busy === "rejected" ? t("saving") : t("reject")}
        </Button>
      </div>
    </div>
  );
}

export default CaseDecision;
