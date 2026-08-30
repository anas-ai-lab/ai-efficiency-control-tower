"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { CheckCircle2, Circle, Loader2, XCircle } from "lucide-react";

import type { CaseStatus, ReviewerDecision } from "@/types/api";
import { updateCaseStatus } from "@/app/actions";
import { hardRefresh } from "@/lib/reload";
import { STATUS_CONFIG } from "@/lib/status";
import { ActionError } from "@/components/action-error";
import { useLlmBusy } from "@/components/llm-busy";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

// Status und Entscheidung werden gemeinsam gespeichert, weil getrennte Pfade vor C1 case.status und case.reviewer_decision auseinanderlaufen liessen.

interface Props {
  caseId: string;
  initialStatus: CaseStatus;
  reviewerDecision: ReviewerDecision;
  reviewerNote: string | null;
}

const STATUS_ORDER: CaseStatus[] = [
  "submitted",
  "in_review",
  "approved",
  "already_exists",
  "rejected",
  "implemented",
];

const DECISION_VIEW: Record<
  ReviewerDecision,
  { icon: React.ComponentType<{ className?: string }>; tone: string }
> = {
  approved: { icon: CheckCircle2, tone: "text-[var(--zone-win)]" },
  rejected: { icon: XCircle, tone: "text-destructive" },
  pending: { icon: Circle, tone: "text-muted-foreground" },
};

export function CaseDecision({
  caseId,
  initialStatus,
  reviewerDecision,
  reviewerNote,
}: Props) {
  const t = useTranslations("decision");
  const ts = useTranslations("status");
  const [selectedStatus, setSelectedStatus] = useState<CaseStatus>(initialStatus);
  const [note, setNote] = useState(reviewerNote ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const analysisRunning = useLlmBusy();
  const waiting = analysisRunning && !busy;

  const view = DECISION_VIEW[reviewerDecision];
  const Icon = view.icon;

  async function handleSubmit() {
    setBusy(true);
    setError(null);
    try {
      const trimmed = note.trim();
      const res = await updateCaseStatus(
        caseId, selectedStatus, trimmed.length > 0 ? trimmed : null,
      );
      hardRefresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : t("error"));
      setBusy(false);
    }
  }

  return (
    <div className="rounded-2xl border border-border bg-muted/30 p-5">
      <div className="flex items-center gap-2">
        <StatusBadge status={selectedStatus} />
        <Select
          value={selectedStatus}
          disabled={busy}
          onValueChange={(v) => setSelectedStatus(v as CaseStatus)}
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
                {ts(s)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="mt-3 flex items-center gap-2">
        <Icon className={`size-4 ${view.tone}`} />
        <span className="text-sm font-medium text-foreground">{t(reviewerDecision)}</span>
      </div>
      <Textarea
        className="mt-3"
        placeholder={t("notePlaceholder")}
        value={note}
        onChange={(e) => setNote(e.target.value)}
        maxLength={2000}
        disabled={busy}
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
          onClick={handleSubmit}
          disabled={busy || analysisRunning}
        >
          {busy ? t("saving") : t("submit")}
        </Button>
      </div>
    </div>
  );
}

export default CaseDecision;
