"use client"

import type { ReportResponse, ComplianceCitation } from "@/types/api"
import { ZONE_CONFIG, formatEUR } from "@/lib/formatters"
import type { ZoneKey } from "@/lib/formatters"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { CheckCircle2, XCircle, AlertTriangle } from "lucide-react"

interface ReportViewProps {
  result: ReportResponse
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return <p className="eyebrow mb-2">{children}</p>
}

export function ReportView({ result }: ReportViewProps) {
  const bs = result.business_summary
  const td = result.technical_detail
  const zoneConf = bs.zone !== null ? ZONE_CONFIG[bs.zone as ZoneKey] : null

  return (
    <Tabs defaultValue="entscheider" className="w-full">
      <TabsList className="w-full">
        <TabsTrigger value="entscheider" className="flex-1">
          Entscheider
        </TabsTrigger>
        <TabsTrigger value="technisch" className="flex-1">
          Technisch
        </TabsTrigger>
      </TabsList>

      {/* --- Entscheider-Sicht --- */}
      <TabsContent value="entscheider">
        <div className="space-y-6 pt-6">
          {zoneConf !== null && (
            <section
              className={`flex items-center gap-3 rounded-2xl border px-6 py-5 ${zoneConf.surface}`}
            >
              <span
                className={`size-2.5 shrink-0 rounded-full ${zoneConf.dot}`}
                aria-hidden
              />
              <div>
                <p className="eyebrow">Bewertungszone</p>
                <p
                  className={`mt-1 text-xl font-semibold tracking-tight ${zoneConf.text}`}
                >
                  {zoneConf.labelDE}
                </p>
              </div>
            </section>
          )}

          <section className="rounded-xl border border-border bg-card p-5">
            <div className="flex items-center gap-2">
              {bs.is_actionable ? (
                <>
                  <CheckCircle2 className="size-4 text-[var(--zone-win)]" />
                  <span className="text-sm font-medium text-foreground">
                    Empfohlen für Weiterbearbeitung
                  </span>
                </>
              ) : (
                <>
                  <XCircle className="size-4 text-destructive" />
                  <span className="text-sm font-medium text-foreground">
                    Nicht empfohlen
                  </span>
                </>
              )}
            </div>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
              {bs.recommendation}
            </p>
          </section>

          {bs.expected_benefit_eur !== null && (
            <section className="rounded-xl border border-border bg-card px-6 py-5">
              <SectionLabel>Erwarteter Nettonutzen</SectionLabel>
              <p className="stat-value text-[2.25rem] text-foreground">
                {formatEUR(bs.expected_benefit_eur)}
              </p>
              <p className="mt-1.5 text-xs text-muted-foreground">pro Jahr</p>
            </section>
          )}

          <section>
            <SectionLabel>Zusammenfassung</SectionLabel>
            <p className="text-sm leading-relaxed text-foreground/90">
              {bs.summary_text}
            </p>
          </section>

          {bs.sharpened_text !== null && (
            <section className="border-l-2 border-[var(--ink)] pl-4">
              <SectionLabel>Geschärfte Beschreibung</SectionLabel>
              <p className="text-sm leading-relaxed text-muted-foreground">
                {bs.sharpened_text}
              </p>
            </section>
          )}

          {bs.compliance_hint_text !== null && (
            <section>
              <SectionLabel>Compliance-Hinweise</SectionLabel>
              <p className="text-sm leading-relaxed text-foreground/90">
                {bs.compliance_hint_text}
              </p>
              {bs.compliance_citations.length > 0 && (
                <ul className="mt-3 space-y-1.5 border-t border-border pt-3">
                  {bs.compliance_citations.map((c: ComplianceCitation) => (
                    <li
                      key={c.number}
                      className="flex gap-2 text-xs text-muted-foreground"
                    >
                      <span className="font-mono text-foreground/60 tnum">
                        [{c.number}]
                      </span>
                      <span className="leading-relaxed">{c.citation}</span>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          )}
        </div>
      </TabsContent>

      {/* --- Technische Sicht --- */}
      <TabsContent value="technisch">
        <div className="space-y-5 pt-6">
          <section className="rounded-xl border border-border bg-card p-5">
            <SectionLabel>Vorfilter</SectionLabel>
            {td.passed_vorfilter ? (
              <div className="flex items-center gap-2">
                <CheckCircle2 className="size-4 text-[var(--zone-win)]" />
                <span className="text-sm text-foreground">Bestanden</span>
              </div>
            ) : (
              <>
                <div className="flex items-center gap-2">
                  <XCircle className="size-4 text-destructive" />
                  <span className="text-sm text-foreground">
                    Nicht bestanden
                  </span>
                </div>
                {td.vorfilter_failed_criteria.length > 0 && (
                  <ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-muted-foreground">
                    {td.vorfilter_failed_criteria.map((c, i) => (
                      <li key={i}>{c}</li>
                    ))}
                  </ul>
                )}
              </>
            )}
          </section>

          {td.composite_total !== null && (
            <section className="rounded-xl border border-border bg-card px-5 py-4">
              <SectionLabel>Aufwand-Score</SectionLabel>
              <div className="flex items-baseline gap-2">
                <span className="stat-value text-2xl text-foreground">
                  {td.composite_total}
                  <span className="text-base text-muted-foreground">/10</span>
                </span>
                {td.composite_effort_label !== null && (
                  <span className="text-sm text-muted-foreground">
                    {td.composite_effort_label}
                  </span>
                )}
              </div>
            </section>
          )}

          {td.feasibility_flags.length > 0 && (
            <section>
              <SectionLabel>Machbarkeits-Flags</SectionLabel>
              <ul className="list-disc space-y-1 pl-5 text-xs text-muted-foreground">
                {td.feasibility_flags.map((f, i) => (
                  <li key={i}>{f}</li>
                ))}
              </ul>
              {td.feasibility_recommendation !== null && (
                <p className="mt-2 text-sm text-foreground/85">
                  {td.feasibility_recommendation}
                </p>
              )}
            </section>
          )}

          {(td.automation_signals.length > 0 || td.ai_signals.length > 0) && (
            <section>
              <SectionLabel>Routing-Signale</SectionLabel>
              <div className="space-y-2 text-xs">
                {td.automation_signals.length > 0 && (
                  <div className="flex gap-2">
                    <span className="w-24 shrink-0 text-muted-foreground">
                      Automation
                    </span>
                    <span className="text-foreground/85">
                      {td.automation_signals.join(", ")}
                    </span>
                  </div>
                )}
                {td.ai_signals.length > 0 && (
                  <div className="flex gap-2">
                    <span className="w-24 shrink-0 text-muted-foreground">
                      KI
                    </span>
                    <span className="text-foreground/85">
                      {td.ai_signals.join(", ")}
                    </span>
                  </div>
                )}
              </div>
            </section>
          )}

          {td.risk_flags.length > 0 && (
            <section>
              <SectionLabel>Risiko-Flags</SectionLabel>
              <div className="flex flex-wrap gap-1.5">
                {td.risk_flags.map((flag, i) => (
                  <span
                    key={i}
                    className="rounded-md border border-[var(--zone-gain-border)] bg-[var(--zone-gain-surface)] px-2 py-0.5 text-xs font-medium text-[var(--zone-gain-fg)]"
                  >
                    {flag}
                  </span>
                ))}
              </div>
            </section>
          )}

          {td.requires_human_review && (
            <div className="flex items-center gap-2.5 rounded-xl border border-[var(--zone-risk-border)] bg-[var(--zone-risk-surface)] px-4 py-3">
              <AlertTriangle className="size-4 shrink-0 text-[var(--zone-risk-fg)]" />
              <span className="text-sm font-medium text-[var(--zone-risk-fg)]">
                Menschliche Prüfung empfohlen
              </span>
            </div>
          )}

          {td.roi_theoretical_potential_eur !== null && (
            <section className="rounded-xl border border-border bg-card px-5 py-4">
              <SectionLabel>ROI</SectionLabel>
              <dl className="space-y-2 text-sm">
                <div className="flex items-baseline justify-between gap-4">
                  <dt className="text-muted-foreground">Theoretisch</dt>
                  <dd className="stat-value text-foreground tnum">
                    {formatEUR(td.roi_theoretical_potential_eur)}
                  </dd>
                </div>
                {td.roi_net_expected_benefit_eur !== null && (
                  <div className="flex items-baseline justify-between gap-4 border-t border-border pt-2">
                    <dt className="text-muted-foreground">Netto erwartet</dt>
                    <dd className="stat-value font-medium text-foreground tnum">
                      {formatEUR(td.roi_net_expected_benefit_eur)}
                    </dd>
                  </div>
                )}
              </dl>
            </section>
          )}

          {td.proposal_text !== null && (
            <section>
              <SectionLabel>Lösungsvorschlag</SectionLabel>
              <p className="text-sm leading-relaxed text-muted-foreground">
                {td.proposal_text}
              </p>
            </section>
          )}
        </div>
      </TabsContent>
    </Tabs>
  )
}

export default ReportView
