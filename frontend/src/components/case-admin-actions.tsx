"use client"

import { useRouter } from "next/navigation"
import { useState } from "react"
import { CheckCircle2, Circle, Loader2, XCircle } from "lucide-react"

import type { ReviewerDecision, SharpenedCaseResponse } from "@/types/api"
import {
  generateComplianceHints,
  proposeSolution,
  recordDecision,
  sharpenCase,
} from "@/app/actions"
import { SharpeningReview } from "@/components/sharpening-review"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"

// Admin-Aktionsleiste der Fall-Detailseite (V4-P7). Buendelt die mutierenden
// Trigger: Schaerfen (Draft -> Diff-Review), Loesungsvorschlag, Compliance und
// die Freigabe-/Ablehnungsentscheidung. Nach jeder persistierenden Aktion
// router.refresh() -> die Server-Komponente laedt GET /cases/{id} neu und der
// Report rendert den neuen Stand. Sicherheit erzwingt das Backend
// (require_admin); diese Leiste erscheint nur fuer angemeldete Admins.

interface Props {
  caseId: string
  reviewerDecision: ReviewerDecision
  reviewerNote: string | null
  hasSolution: boolean
  hasCompliance: boolean
}

const DECISION_VIEW: Record<
  ReviewerDecision,
  { label: string; icon: React.ComponentType<{ className?: string }>; tone: string }
> = {
  approved: { label: "Freigegeben", icon: CheckCircle2, tone: "text-[var(--zone-win)]" },
  rejected: { label: "Abgelehnt", icon: XCircle, tone: "text-destructive" },
  pending: { label: "Ausstehend", icon: Circle, tone: "text-muted-foreground" },
}

export function CaseAdminActions({
  caseId,
  reviewerDecision,
  reviewerNote,
  hasSolution,
  hasCompliance,
}: Props) {
  const router = useRouter()
  const [busy, setBusy] = useState<
    "sharpen" | "solution" | "compliance" | null
  >(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [draft, setDraft] = useState<SharpenedCaseResponse | null>(null)

  // Entscheidung.
  const [note, setNote] = useState(reviewerNote ?? "")
  const [decisionBusy, setDecisionBusy] = useState<
    "approved" | "rejected" | null
  >(null)
  const [decisionError, setDecisionError] = useState<string | null>(null)
  const decisionView = DECISION_VIEW[reviewerDecision]
  const DecisionIcon = decisionView.icon

  async function handleSharpen() {
    setBusy("sharpen")
    setActionError(null)
    try {
      setDraft(await sharpenCase(caseId))
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Schärfen fehlgeschlagen.")
    } finally {
      setBusy(null)
    }
  }

  async function handleSolution() {
    setBusy("solution")
    setActionError(null)
    try {
      await proposeSolution(caseId)
      router.refresh()
    } catch (e) {
      setActionError(
        e instanceof Error ? e.message : "Lösungsvorschlag fehlgeschlagen.",
      )
    } finally {
      setBusy(null)
    }
  }

  async function handleCompliance() {
    setBusy("compliance")
    setActionError(null)
    try {
      await generateComplianceHints(caseId)
      router.refresh()
    } catch (e) {
      setActionError(
        e instanceof Error ? e.message : "Compliance-Prüfung fehlgeschlagen.",
      )
    } finally {
      setBusy(null)
    }
  }

  function handleDraftResolved() {
    setDraft(null)
    router.refresh()
  }

  async function handleDecide(decision: "approved" | "rejected") {
    setDecisionBusy(decision)
    setDecisionError(null)
    try {
      const trimmed = note.trim()
      await recordDecision(caseId, decision, trimmed.length > 0 ? trimmed : null)
      router.refresh()
    } catch (e) {
      setDecisionError(
        e instanceof Error ? e.message : "Entscheidung fehlgeschlagen.",
      )
    } finally {
      setDecisionBusy(null)
    }
  }

  return (
    <section className="mt-8 rounded-2xl border border-border bg-muted/30 p-5">
      <p className="eyebrow">Admin-Aktionen</p>

      <div className="mt-3 flex flex-wrap gap-2">
        <Button
          variant="outline"
          onClick={handleSharpen}
          disabled={busy !== null || draft !== null}
        >
          {busy === "sharpen" && <Loader2 className="size-4 animate-spin" />}
          Schärfen
        </Button>
        <Button
          variant="outline"
          onClick={handleSolution}
          disabled={busy !== null}
        >
          {busy === "solution" && <Loader2 className="size-4 animate-spin" />}
          {hasSolution ? "Lösung neu erzeugen" : "Lösungsvorschlag"}
        </Button>
        <Button
          variant="outline"
          onClick={handleCompliance}
          disabled={busy !== null}
        >
          {busy === "compliance" && <Loader2 className="size-4 animate-spin" />}
          {hasCompliance ? "Compliance neu prüfen" : "Compliance-Prüfung"}
        </Button>
      </div>
      <p className="mt-2 text-xs text-muted-foreground">
        Schärfen, Lösung und Compliance sind LLM-Aktionen · 5–30 Sekunden.
      </p>

      {actionError !== null && (
        <p
          role="alert"
          className="mt-3 rounded-lg border border-destructive/25 bg-destructive/5 px-4 py-3 text-sm text-destructive"
        >
          {actionError}
        </p>
      )}

      {draft !== null && (
        <div className="mt-5">
          <SharpeningReview sharpened={draft} onResolved={handleDraftResolved} />
        </div>
      )}

      {/* Entscheidung (Human-in-the-Loop, ADR-0043). */}
      <div className="mt-6 border-t border-border pt-5">
        <div className="flex items-center gap-2">
          <DecisionIcon className={`size-4 ${decisionView.tone}`} />
          <span className="text-sm font-medium text-foreground">
            {decisionView.label}
          </span>
        </div>
        <Textarea
          className="mt-3"
          placeholder="Optionale Begründung"
          value={note}
          onChange={(e) => setNote(e.target.value)}
          maxLength={2000}
          disabled={decisionBusy !== null}
          rows={2}
        />
        {decisionError !== null && (
          <p
            role="alert"
            className="mt-3 rounded-lg border border-destructive/25 bg-destructive/5 px-4 py-3 text-sm text-destructive"
          >
            {decisionError}
          </p>
        )}
        <div className="mt-3 flex gap-2">
          <Button
            onClick={() => handleDecide("approved")}
            disabled={decisionBusy !== null}
          >
            {decisionBusy === "approved" ? "Wird gespeichert …" : "Freigeben"}
          </Button>
          <Button
            variant="destructive"
            onClick={() => handleDecide("rejected")}
            disabled={decisionBusy !== null}
          >
            {decisionBusy === "rejected" ? "Wird gespeichert …" : "Ablehnen"}
          </Button>
        </div>
      </div>
    </section>
  )
}

export default CaseAdminActions
