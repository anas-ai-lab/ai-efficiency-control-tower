"use client"

import { SolutionProposalResponse } from "@/types/api"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Loader2 } from "lucide-react"

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
    <div className="space-y-4">
      <div className="rounded-lg bg-muted/40 p-4">
        <p className="text-sm leading-relaxed">{result.proposal_text}</p>
        <p className="mt-3 text-right text-xs text-muted-foreground">
          Prompt-Version: {result.prompt_version}
        </p>
      </div>

      <Separator />

      {complianceError !== null && (
        <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800">
          {complianceError}
        </div>
      )}

      <Button onClick={onCompliance} disabled={isComplianceLoading} className="w-full">
        {isComplianceLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {isComplianceLoading ? "Wird geprueft..." : "Compliance-Pruefung starten (KI)"}
      </Button>

      <p className="mt-2 text-center text-xs text-muted-foreground">
        Prueft DSGVO- und Sicherheitsanforderungen, LLM-Call
      </p>
    </div>
  )
}
export default SolutionView
