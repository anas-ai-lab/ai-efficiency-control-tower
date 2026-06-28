"use client"

import { SolutionProposalResponse } from "@/types/api"
import { LlmAction } from "@/components/llm-action"

interface SolutionViewProps {
  result: SolutionProposalResponse
  onCompliance: () => void
  isComplianceLoading: boolean
  complianceError: string | null
}

export function SolutionView({
  result,
  onCompliance,
  isComplianceLoading,
  complianceError,
}: SolutionViewProps) {
  return (
    <div className="space-y-6">
      <article className="rounded-2xl border border-border bg-card p-6 sm:p-7">
        <p className="eyebrow mb-3">Vorschlag</p>
        <p className="text-[0.95rem] leading-7 whitespace-pre-line text-foreground/90">
          {result.proposal_text}
        </p>
        <div className="mt-5 flex items-center gap-2 border-t border-border pt-3">
          <span className="font-mono text-[0.65rem] tracking-wide text-muted-foreground/70">
            PROMPT
          </span>
          <span className="font-mono text-xs text-muted-foreground tnum">
            {result.prompt_version}
          </span>
        </div>
      </article>

      <div className="border-t border-border pt-6">
        <LlmAction
          onAction={onCompliance}
          isLoading={isComplianceLoading}
          idleLabel="Compliance-Prüfung starten"
          loadingLabel="Compliance wird geprüft …"
          hint="Prüft DSGVO- und Sicherheitsanforderungen · 5–30 Sekunden"
          error={complianceError}
        />
      </div>
    </div>
  )
}

export default SolutionView
