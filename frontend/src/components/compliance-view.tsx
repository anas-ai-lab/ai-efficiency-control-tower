"use client"

import { ComplianceHintsResponse, ComplianceCitation } from "@/types/api"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Loader2 } from "lucide-react"

interface ComplianceViewProps {
  result: ComplianceHintsResponse
  onReport: () => void
  isReportLoading: boolean
  reportError: string | null
}

export function ComplianceView({
  result,
  onReport,
  isReportLoading,
  reportError,
}: ComplianceViewProps) {
  const hasHint = result.hint_text !== null
  const hasCitations = result.citations.length > 0

  return (
    <div className="space-y-4">
      {!hasHint && !hasCitations && (
        <div className="rounded-md border border-blue-200 bg-blue-50 p-3 text-sm text-blue-800">
          Keine Compliance-Hinweise fuer diesen Use Case identifiziert.
          Kein Handlungsbedarf aus Datenschutzsicht erkannt.
        </div>
      )}

      {hasHint && (
        <p className="text-sm leading-relaxed">{result.hint_text}</p>
      )}

      {hasCitations && (
        <>
          <Separator />
          <p className="text-xs uppercase tracking-widest text-muted-foreground">
            QUELLENANGABEN
          </p>
          <Accordion type="multiple" className="w-full">
            {result.citations.map((citation: ComplianceCitation) => (
              <AccordionItem
                key={citation.number}
                value={`citation-${citation.number}`}
              >
                <AccordionTrigger className="text-sm font-normal">
                  [{citation.number}] {citation.citation}
                </AccordionTrigger>
                <AccordionContent>
                  <p className="text-xs text-muted-foreground">
                    Quelle-ID: {citation.source_id}
                  </p>
                  {citation.url !== null && (
                    <a
                      href={citation.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-1 block text-xs text-blue-600 underline"
                    >
                      Quelle oeffnen
                    </a>
                  )}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </>
      )}

      <Separator />

      {reportError !== null && (
        <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800">
          {reportError}
        </div>
      )}

      <Button onClick={onReport} disabled={isReportLoading} className="w-full">
        {isReportLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {isReportLoading ? "Wird generiert..." : "Vollstaendigen Report generieren (KI)"}
      </Button>
    </div>
  )
}
export default ComplianceView
