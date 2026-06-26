"use client"

import type {
  ReportResponse,
  ComplianceCitation,
} from "@/types/api"
import { ZONE_CONFIG, formatEUR } from "@/lib/formatters"
import type { ZoneKey } from "@/lib/formatters"
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs"
import { Separator } from "@/components/ui/separator"
import { CheckCircle2, XCircle, AlertTriangle } from "lucide-react"

interface ReportViewProps {
  result: ReportResponse
}

export function ReportView({ result }: ReportViewProps) {
  const bs = result.business_summary
  const td = result.technical_detail
  const zoneConf = bs.zone !== null ? ZONE_CONFIG[bs.zone as ZoneKey] : null

  return (
    <Tabs defaultValue="entscheider" className="w-full">
      <TabsList className="w-full">
        <TabsTrigger value="entscheider" className="flex-1">Entscheider</TabsTrigger>
        <TabsTrigger value="technisch" className="flex-1">Technisch</TabsTrigger>
      </TabsList>

      <TabsContent value="entscheider">
        <div className="space-y-4 pt-4">
          {zoneConf !== null && (
            <div className={`rounded-lg px-4 py-4 ${zoneConf.badgeClass}`}>
              <p className="text-lg font-bold">{zoneConf.labelDE}</p>
            </div>
          )}

          <div>
            <div className="flex items-center gap-2">
              {bs.is_actionable ? (
                <>
                  <CheckCircle2 className="h-4 w-4 text-green-600" />
                  <span className="text-sm font-medium">
                    Empfohlen fuer Weiterbearbeitung
                  </span>
                </>
              ) : (
                <>
                  <XCircle className="h-4 w-4 text-red-600" />
                  <span className="text-sm font-medium">Nicht empfohlen</span>
                </>
              )}
            </div>
            <p className="mt-1 text-sm text-muted-foreground">
              {bs.recommendation}
            </p>
          </div>

          {bs.expected_benefit_eur !== null && (
            <>
              <Separator />
              <div>
                <p className="text-xs uppercase tracking-widest text-muted-foreground">
                  Erwarteter Nettonutzen
                </p>
                <p className="text-3xl font-bold">
                  {formatEUR(bs.expected_benefit_eur)}
                </p>
              </div>
            </>
          )}

          <Separator />
          <div>
            <p className="mb-1 text-xs uppercase tracking-widest text-muted-foreground">
              ZUSAMMENFASSUNG
            </p>
            <p className="text-sm leading-relaxed">{bs.summary_text}</p>
          </div>

          {bs.sharpened_text !== null && (
            <>
              <Separator />
              <div>
                <p className="mb-1 text-xs uppercase tracking-widest text-muted-foreground">
                  GESCHAERFTE BESCHREIBUNG
                </p>
                <p className="text-sm leading-relaxed text-muted-foreground">
                  {bs.sharpened_text}
                </p>
              </div>
            </>
          )}

          {bs.compliance_hint_text !== null && (
            <>
              <Separator />
              <div>
                <p className="mb-1 text-xs uppercase tracking-widest text-muted-foreground">
                  COMPLIANCE-HINWEISE
                </p>
                <p className="text-sm leading-relaxed">{bs.compliance_hint_text}</p>
                {bs.compliance_citations.length > 0 && (
                  <ul className="mt-2 space-y-0.5">
                    {bs.compliance_citations.map((c: ComplianceCitation) => (
                      <li key={c.number} className="text-xs text-muted-foreground">
                        [{c.number}] {c.citation}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </>
          )}
        </div>
      </TabsContent>

      <TabsContent value="technisch">
        <div className="space-y-4 pt-4">
          <div className="space-y-1">
            <p className="text-xs uppercase tracking-widest text-muted-foreground">
              VORFILTER
            </p>
            {td.passed_vorfilter ? (
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
                <span className="text-sm">Bestanden</span>
              </div>
            ) : (
              <>
                <div className="flex items-center gap-2">
                  <XCircle className="h-4 w-4 text-red-600" />
                  <span className="text-sm">Nicht bestanden</span>
                </div>
                {td.vorfilter_failed_criteria.length > 0 && (
                  <ul className="mt-1 list-disc pl-5 text-xs text-red-700">
                    {td.vorfilter_failed_criteria.map((c, i) => (
                      <li key={i}>{c}</li>
                    ))}
                  </ul>
                )}
              </>
            )}
          </div>

          {td.composite_total !== null && (
            <>
              <Separator />
              <div className="space-y-1">
                <p className="text-xs uppercase tracking-widest text-muted-foreground">
                  AUFWAND-SCORE
                </p>
                <p className="text-sm">
                  {td.composite_total}/10 — {td.composite_effort_label}
                </p>
              </div>
            </>
          )}

          {td.feasibility_flags.length > 0 && (
            <>
              <Separator />
              <div className="space-y-1">
                <p className="text-xs uppercase tracking-widest text-muted-foreground">
                  MACHBARKEITS-FLAGS
                </p>
                <ul className="list-disc pl-5 text-xs text-muted-foreground">
                  {td.feasibility_flags.map((f, i) => (
                    <li key={i}>{f}</li>
                  ))}
                </ul>
                {td.feasibility_recommendation !== null && (
                  <p className="mt-1 text-sm">{td.feasibility_recommendation}</p>
                )}
              </div>
            </>
          )}

          {(td.automation_signals.length > 0 || td.ai_signals.length > 0) && (
            <>
              <Separator />
              <div className="space-y-1">
                <p className="text-xs uppercase tracking-widest text-muted-foreground">
                  ROUTING-SIGNALE
                </p>
                {td.automation_signals.length > 0 && (
                  <p className="text-xs">
                    Automation: {td.automation_signals.join(", ")}
                  </p>
                )}
                {td.ai_signals.length > 0 && (
                  <p className="text-xs">KI: {td.ai_signals.join(", ")}</p>
                )}
              </div>
            </>
          )}

          {td.risk_flags.length > 0 && (
            <>
              <Separator />
              <div className="space-y-1">
                <p className="text-xs uppercase tracking-widest text-muted-foreground">
                  RISIKO-FLAGS
                </p>
                <p className="text-xs text-red-700">
                  {td.risk_flags.join(" · ")}
                </p>
              </div>
            </>
          )}

          {td.requires_human_review && (
            <>
              <Separator />
              <div className="flex items-center gap-2 rounded-md border border-orange-300 bg-orange-50 p-2">
                <AlertTriangle className="h-4 w-4 shrink-0 text-orange-600" />
                <span className="text-sm font-medium text-orange-800">
                  Menschliche Pruefung empfohlen
                </span>
              </div>
            </>
          )}

          {td.roi_theoretical_potential_eur !== null && (
            <>
              <Separator />
              <div className="space-y-1">
                <p className="text-xs uppercase tracking-widest text-muted-foreground">
                  ROI
                </p>
                <p className="text-sm">
                  Theoretisch: {formatEUR(td.roi_theoretical_potential_eur)}
                </p>
                {td.roi_net_expected_benefit_eur !== null && (
                  <p className="text-sm">
                    Netto erwartet: {formatEUR(td.roi_net_expected_benefit_eur)}
                  </p>
                )}
              </div>
            </>
          )}

          {td.proposal_text !== null && (
            <>
              <Separator />
              <div className="space-y-1">
                <p className="text-xs uppercase tracking-widest text-muted-foreground">
                  LÖSUNGSVORSCHLAG
                </p>
                <p className="text-sm leading-relaxed text-muted-foreground">
                  {td.proposal_text}
                </p>
              </div>
            </>
          )}
        </div>
      </TabsContent>
    </Tabs>
  )
}
export default ReportView
