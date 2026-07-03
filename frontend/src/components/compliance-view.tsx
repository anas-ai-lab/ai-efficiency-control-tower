"use client"

import { ComplianceHintsResponse, ComplianceCitation } from "@/types/api"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import { LlmAction } from "@/components/llm-action"
import { ShieldCheck, ExternalLink } from "lucide-react"

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
    <div className="space-y-6">
      <div>
        <p className="eyebrow mb-1.5">Was passiert hier</p>
        <p className="text-sm leading-relaxed text-muted-foreground">
          Regelbasiert ausgelöste, RAG-belegte Datenschutz-Hinweise mit
          Quellenangabe. Immer als Prüfhinweis zu verstehen, kein
          rechtsverbindliches Urteil.
        </p>
      </div>

      {!hasHint && !hasCitations && (
        <div className="flex items-start gap-3 rounded-xl border border-[var(--zone-win-border)] bg-[var(--zone-win-surface)] px-4 py-3.5">
          <ShieldCheck className="mt-0.5 size-4 shrink-0 text-[var(--zone-win-fg)]" />
          <p className="text-sm leading-relaxed text-foreground/85">
            Keine Compliance-Hinweise für diesen Use Case identifiziert. Kein
            Handlungsbedarf aus Datenschutzsicht erkannt.
          </p>
        </div>
      )}

      {hasHint && (
        <article className="rounded-2xl border border-border bg-card p-6 sm:p-7">
          <p className="eyebrow mb-3">Hinweise</p>
          <p className="text-[0.95rem] leading-7 whitespace-pre-line text-foreground/90">
            {result.hint_text}
          </p>
        </article>
      )}

      {hasCitations && (
        <section>
          <p className="eyebrow mb-1">Quellenangaben</p>
          <Accordion type="multiple" className="w-full">
            {result.citations.map((citation: ComplianceCitation) => (
              <AccordionItem
                key={citation.number}
                value={`citation-${citation.number}`}
              >
                <AccordionTrigger className="gap-3 text-sm font-normal no-underline hover:no-underline">
                  <span className="flex items-start gap-2.5 text-left">
                    <span className="mt-px font-mono text-xs text-muted-foreground tnum">
                      [{citation.number}]
                    </span>
                    <span className="text-foreground/90">
                      {citation.citation}
                    </span>
                  </span>
                </AccordionTrigger>
                <AccordionContent>
                  <div className="pl-7">
                    <p className="text-xs text-muted-foreground">
                      Quelle-ID:{" "}
                      <span className="font-mono text-foreground/70">
                        {citation.source_id}
                      </span>
                    </p>
                    {citation.url !== null && (
                      <a
                        href={citation.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-2 inline-flex items-center gap-1.5 text-xs font-medium text-[var(--ink)] hover:underline"
                      >
                        Quelle öffnen
                        <ExternalLink className="size-3" />
                      </a>
                    )}
                  </div>
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </section>
      )}

      <div className="border-t border-border pt-6">
        <LlmAction
          onAction={onReport}
          isLoading={isReportLoading}
          idleLabel="Vollständigen Report generieren"
          loadingLabel="Report wird zusammengestellt …"
          hint="Bündelt alle Ergebnisse in einem Dokument · 5–30 Sekunden"
          error={reportError}
        />
      </div>
    </div>
  )
}

export default ComplianceView
