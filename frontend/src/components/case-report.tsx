"use client"

import { CheckCircle2, Circle, XCircle } from "lucide-react"
import { useTranslations } from "next-intl"

import type {
  ComplianceCitation,
  ReportResponse,
  ReviewerDecision,
} from "@/types/api"
import { useFormat } from "@/lib/use-format"
import {
  ManagementSolutionView,
  TechnicalSolutionView,
} from "@/components/solution-view"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

// Read-only Report-Ansicht (V4-P6/P7) fuer die Fall-Detailseite. Rendert den
// vom Backend deterministisch zusammengesetzten Report (decision_report +
// technical_report) -- keine Aktions-Buttons, kein LLM. Die Admin-Trigger
// liegen in case-tools (Loesung/Compliance, Bereich 2) und case-decision
// (Entscheidung, Bereich 3).

function Label({ children }: { children: React.ReactNode }) {
  return <p className="eyebrow mb-2">{children}</p>
}

function TextBlock({ title, text }: { title: string; text: string }) {
  if (text.trim().length === 0) return null
  return (
    <section>
      <Label>{title}</Label>
      <p className="text-sm leading-relaxed whitespace-pre-wrap text-foreground/90">
        {text}
      </p>
    </section>
  )
}

const DECISION_VIEW: Record<
  ReviewerDecision,
  { icon: React.ComponentType<{ className?: string }>; tone: string }
> = {
  approved: { icon: CheckCircle2, tone: "text-[var(--zone-win)]" },
  rejected: { icon: XCircle, tone: "text-destructive" },
  pending: { icon: Circle, tone: "text-muted-foreground" },
}

function Citations({ citations }: { citations: ComplianceCitation[] }) {
  if (citations.length === 0) return null
  return (
    <ul className="mt-3 space-y-1.5 border-t border-border pt-3">
      {citations.map((c) => (
        <li key={c.number} className="flex gap-2 text-xs text-muted-foreground">
          <span className="font-mono tabular-nums text-foreground/60">[{c.number}]</span>
          <span className="leading-relaxed">{c.citation}</span>
        </li>
      ))}
    </ul>
  )
}

export function CaseReport({ report }: { report: ReportResponse }) {
  const t = useTranslations("report")
  const td_ = useTranslations("decision")
  const te = useTranslations("enums")
  const fmt = useFormat()
  const bs = report.business_summary
  const td = report.technical_detail
  const dr = bs.decision_report
  const kz = dr.kennzahlen
  const tr = td.technical_report
  const decision = DECISION_VIEW[bs.reviewer_decision]
  const DecisionIcon = decision.icon

  return (
    <Tabs defaultValue="entscheider" className="w-full">
      <TabsList className="w-full">
        <TabsTrigger value="entscheider" className="flex-1">
          {t("tabDecision")}
        </TabsTrigger>
        <TabsTrigger value="technisch" className="flex-1">
          {t("tabTechnical")}
        </TabsTrigger>
      </TabsList>

      {/* --- Entscheider-Sicht (decision_report v2). --- */}
      <TabsContent value="entscheider">
        <div className="space-y-6 pt-6">
          {/* Empfehlungssatz prominent. */}
          <section className="rounded-2xl border border-border bg-card px-6 py-5">
            <Label>{t("recommendation")}</Label>
            <p className="text-[0.95rem] leading-relaxed text-foreground">
              {dr.empfehlung_satz}
            </p>
            <div className="mt-3 flex items-center gap-2 border-t border-border pt-3">
              <DecisionIcon className={`size-4 ${decision.tone}`} />
              <span className="text-sm font-medium text-foreground">
                {td_(bs.reviewer_decision)}
              </span>
              {bs.reviewer_note !== null && bs.reviewer_note.length > 0 && (
                <span className="text-sm text-muted-foreground">— {bs.reviewer_note}</span>
              )}
            </div>
          </section>

          {/* Kennzahlen-Leiste. */}
          <dl className="grid grid-cols-2 gap-px overflow-hidden rounded-xl border border-border bg-border sm:grid-cols-4">
            <div className="bg-card px-4 py-3.5">
              <dt className="eyebrow">{t("netPa")}</dt>
              <dd className="stat-value mt-1.5 text-lg text-foreground">
                {kz.netto_eur === null ? "—" : fmt.eur(kz.netto_eur)}
              </dd>
            </div>
            <div className="bg-card px-4 py-3.5">
              <dt className="eyebrow">{t("hoursYear")}</dt>
              <dd className="stat-value mt-1.5 text-lg text-foreground">
                {kz.stunden_pro_jahr === null ? "—" : fmt.number(kz.stunden_pro_jahr)}
              </dd>
            </div>
            <div className="bg-card px-4 py-3.5">
              <dt className="eyebrow">{t("effort")}</dt>
              <dd className="stat-value mt-1.5 text-lg text-foreground">
                {kz.aufwand === null
                  ? "—"
                  : `${kz.aufwand.wert} / ${kz.aufwand.max}`}
              </dd>
              {kz.aufwand !== null && (
                <p className="mt-0.5 text-xs text-muted-foreground">
                  {te(`effortLabel.${kz.aufwand.label}`)}
                </p>
              )}
            </div>
            <div className="bg-card px-4 py-3.5">
              <dt className="eyebrow">{t("zone")}</dt>
              <dd className="mt-1.5 text-sm font-medium text-foreground">
                {kz.zone_label ?? "—"}
              </dd>
            </div>
          </dl>

          <TextBlock title={t("toDecide")} text={dr.zu_entscheiden} />

          {dr.contra_punkte.length > 0 && (
            <section>
              <Label>{t("contra")}</Label>
              <ul className="space-y-1.5">
                {dr.contra_punkte.map((p, i) => (
                  <li
                    key={i}
                    className="flex gap-2 text-sm leading-relaxed text-foreground/90"
                  >
                    <span className="mt-1.5 size-1 shrink-0 rounded-full bg-[var(--zone-gain)]" aria-hidden />
                    {p}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {/* Loesung (Geschaeftsleitung) -- technikfrei, strukturiert (ADR-0054). */}
          {bs.solution_business !== null && (
            <section>
              <Label>{t("solutionBusiness")}</Label>
              <ManagementSolutionView solution={bs.solution_business} />
            </section>
          )}

          {/* Geschaerfte Beschreibung (akzeptierte Fassung). */}
          {bs.sharpened_text !== null && (
            <section className="border-l-2 border-[var(--ink)] pl-4">
              <Label>{t("sharpenedDescription")}</Label>
              <p className="text-sm leading-relaxed whitespace-pre-wrap text-muted-foreground">
                {bs.sharpened_text}
              </p>
            </section>
          )}

          {/* Compliance. */}
          {bs.compliance_hint_text !== null && (
            <section>
              <Label>{t("complianceHints")}</Label>
              <p className="text-sm leading-relaxed text-foreground/90">
                {bs.compliance_hint_text}
              </p>
              <Citations citations={bs.compliance_citations} />
            </section>
          )}
        </div>
      </TabsContent>

      {/* --- Technische Sicht (technical_report). --- */}
      <TabsContent value="technisch">
        <div className="space-y-6 pt-6">
          <section className="rounded-xl border border-border bg-card p-5">
            <Label>{t("prefilter")}</Label>
            {td.passed_vorfilter ? (
              <div className="flex items-center gap-2">
                <CheckCircle2 className="size-4 text-[var(--zone-win)]" />
                <span className="text-sm text-foreground">{t("passed")}</span>
              </div>
            ) : (
              <>
                <div className="flex items-center gap-2">
                  <XCircle className="size-4 text-destructive" />
                  <span className="text-sm text-foreground">{t("notPassed")}</span>
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

          <TextBlock title={t("architecture")} text={tr.architektur_kurzfassung} />
          <TextBlock title={t("dataSituation")} text={tr.datenlage} />
          <TextBlock title={t("risks")} text={tr.risiken} />
          <TextBlock title={t("openQuestions")} text={tr.offene_technische_fragen} />

          {/* Loesung (technisch) -- feste Felder statt Fliesstext (ADR-0054). */}
          {td.solution_technical !== null && (
            <section>
              <Label>{t("solutionTechnical")}</Label>
              <TechnicalSolutionView solution={td.solution_technical} />
            </section>
          )}

          {td.roi_theoretical_potential_eur !== null && (
            <section className="rounded-xl border border-border bg-card px-5 py-4">
              <Label>{t("roi")}</Label>
              <dl className="space-y-2 text-sm">
                <div className="flex items-baseline justify-between gap-4">
                  <dt className="text-muted-foreground">{t("theoretical")}</dt>
                  <dd className="stat-value text-foreground tabular-nums">
                    {fmt.eur(td.roi_theoretical_potential_eur)}
                  </dd>
                </div>
                {td.roi_net_expected_benefit_eur !== null && (
                  <div className="flex items-baseline justify-between gap-4 border-t border-border pt-2">
                    <dt className="text-muted-foreground">{t("netExpected")}</dt>
                    <dd className="stat-value font-medium text-foreground tabular-nums">
                      {fmt.eur(td.roi_net_expected_benefit_eur)}
                    </dd>
                  </div>
                )}
              </dl>
            </section>
          )}

          {td.composite_total !== null && (
            <section className="rounded-xl border border-border bg-card px-5 py-4">
              <Label>{t("effortScore")}</Label>
              <div className="flex items-baseline gap-2">
                <span className="stat-value text-2xl text-foreground">
                  {td.composite_total}
                  <span className="text-base text-muted-foreground">/9</span>
                </span>
                {td.composite_effort_label !== null && (
                  <span className="text-sm text-muted-foreground">
                    {te(`effortLabel.${td.composite_effort_label}`)}
                  </span>
                )}
              </div>
            </section>
          )}

          {td.feasibility_flags.length > 0 && (
            <section>
              <Label>{t("feasibilityFlags")}</Label>
              <ul className="list-disc space-y-1 pl-5 text-xs text-muted-foreground">
                {td.feasibility_flags.map((f, i) => (
                  <li key={i}>{te(`feasibilityFlag.${f}`)}</li>
                ))}
              </ul>
              {td.feasibility_recommendation !== null && (
                <p className="mt-2 text-sm text-foreground/85">
                  {td.feasibility_recommendation}
                </p>
              )}
            </section>
          )}

          {td.risk_flags.length > 0 && (
            <section>
              <Label>{t("riskFlags")}</Label>
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
        </div>
      </TabsContent>
    </Tabs>
  )
}

export default CaseReport
