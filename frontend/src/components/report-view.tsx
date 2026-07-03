"use client"

import { useState } from "react"
import type {
  ReportResponse,
  TriageResponse,
  ComplianceCitation,
  BusinessSummary,
  ReviewerDecision,
} from "@/types/api"
import { ZONE_CONFIG, formatEUR } from "@/lib/formatters"
import type { ZoneKey } from "@/lib/formatters"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { recordDecision } from "@/app/actions"
import {
  NetBenefitRationale,
  CompositeBreakdown,
  RoutingRationale,
} from "@/components/decision-rationale"
import { CheckCircle2, XCircle, AlertTriangle, Circle } from "lucide-react"

interface ReportViewProps {
  result: ReportResponse
  // Volle TriageResponse zum Durchreichen der Begruendungsdaten (Aufgabe 2) --
  // ohne Backend-Aenderung. Kann null sein, wenn kein Triage-State vorliegt.
  triage: TriageResponse | null
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return <p className="eyebrow mb-2">{children}</p>
}

function formatDecidedAt(iso: string): string {
  return new Date(iso).toLocaleString("de-DE", {
    dateStyle: "medium",
    timeStyle: "short",
  })
}

interface ReviewSectionProps {
  caseId: string
  businessSummary: BusinessSummary
}

// Human-in-the-Loop Decision-Record (ADR-0043): minimaler Freigeben/Ablehnen-
// Baustein statt vollem Reviewer-Workflow -- kein Rollen-/Notification-System.
function ReviewSection({ caseId, businessSummary }: ReviewSectionProps) {
  const [decision, setDecision] = useState<ReviewerDecision>(
    businessSummary.reviewer_decision,
  )
  const [note, setNote] = useState(businessSummary.reviewer_note ?? "")
  const [decidedAt, setDecidedAt] = useState(businessSummary.decided_at)
  const [pendingAction, setPendingAction] = useState<
    "approved" | "rejected" | null
  >(null)
  const [error, setError] = useState<string | null>(null)

  async function handleDecide(next: "approved" | "rejected"): Promise<void> {
    setError(null)
    setPendingAction(next)
    try {
      const trimmed = note.trim()
      const response = await recordDecision(
        caseId,
        next,
        trimmed.length > 0 ? trimmed : null,
      )
      setDecision(response.reviewer_decision)
      setNote(response.reviewer_note ?? "")
      setDecidedAt(response.decided_at)
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "Entscheidung konnte nicht gespeichert werden",
      )
    } finally {
      setPendingAction(null)
    }
  }

  return (
    <section className="rounded-xl border border-border bg-card p-5">
      <SectionLabel>Entscheidung</SectionLabel>

      <div className="flex items-center gap-2">
        {decision === "approved" && (
          <>
            <CheckCircle2 className="size-4 text-[var(--zone-win)]" />
            <span className="text-sm font-medium text-foreground">
              Freigegeben
            </span>
          </>
        )}
        {decision === "rejected" && (
          <>
            <XCircle className="size-4 text-destructive" />
            <span className="text-sm font-medium text-foreground">
              Abgelehnt
            </span>
          </>
        )}
        {decision === "pending" && (
          <>
            <Circle className="size-4 text-muted-foreground" />
            <span className="text-sm font-medium text-muted-foreground">
              Ausstehend
            </span>
          </>
        )}
      </div>

      {decidedAt !== null && (
        <p className="mt-1 text-xs text-muted-foreground">
          {formatDecidedAt(decidedAt)}
        </p>
      )}

      <Textarea
        className="mt-4"
        placeholder="Optionale Begründung"
        value={note}
        onChange={(e) => setNote(e.target.value)}
        maxLength={2000}
        disabled={pendingAction !== null}
      />

      {error !== null && (
        <p
          role="alert"
          className="mt-3 rounded-lg border border-destructive/25 bg-destructive/5 px-4 py-3 text-sm text-destructive"
        >
          {error}
        </p>
      )}

      <div className="mt-3 flex gap-2">
        <Button
          variant="default"
          onClick={() => handleDecide("approved")}
          disabled={pendingAction !== null}
        >
          {pendingAction === "approved" ? "Wird gespeichert …" : "Freigeben"}
        </Button>
        <Button
          variant="destructive"
          onClick={() => handleDecide("rejected")}
          disabled={pendingAction !== null}
        >
          {pendingAction === "rejected" ? "Wird gespeichert …" : "Ablehnen"}
        </Button>
      </div>
    </section>
  )
}

export function ReportView({ result, triage }: ReportViewProps) {
  const bs = result.business_summary
  const td = result.technical_detail
  const zoneConf = bs.zone !== null ? ZONE_CONFIG[bs.zone as ZoneKey] : null
  const zoneReason = triage?.zone?.reason ?? null

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

      {/* --- Entscheider-Sicht: 5-Sekunden-Lesbarkeit, Verdikt zuerst. --- */}
      <TabsContent value="entscheider">
        <div className="space-y-6 pt-6">
          {/* 1. VERDIKT: Zone als Headline, Begruendung als eine Zeile. */}
          {zoneConf !== null && (
            <section
              className={`flex items-start gap-3 rounded-2xl border px-6 py-5 ${zoneConf.surface}`}
            >
              <span
                className={`mt-2 size-2.5 shrink-0 rounded-full ${zoneConf.dot}`}
                aria-hidden
              />
              <div className="min-w-0">
                <p className="eyebrow">Bewertungszone</p>
                <p
                  className={`mt-1 text-2xl font-bold tracking-tight ${zoneConf.text}`}
                >
                  {zoneConf.labelDE}
                </p>
                {zoneReason !== null && (
                  <p className="mt-2 max-w-prose text-[0.9375rem] leading-relaxed text-foreground/90">
                    {zoneReason}
                  </p>
                )}
              </div>
            </section>
          )}

          {/* 2. FREIGABE-EMPFEHLUNG. */}
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
            <p className="mt-2 text-[0.9375rem] leading-relaxed text-foreground/90">
              {bs.recommendation}
            </p>
          </section>

          {/* 3. NETTONUTZEN: grosse Zahl plus Erklaerung und Rechenweg. */}
          {bs.expected_benefit_eur !== null && (
            <section className="rounded-xl border border-border bg-card px-6 py-5">
              <SectionLabel>Erwarteter Nettonutzen</SectionLabel>
              <p className="stat-value text-[2.25rem] text-foreground">
                {formatEUR(bs.expected_benefit_eur)}
              </p>
              <p className="mt-1.5 text-xs text-muted-foreground">pro Jahr</p>
              {triage?.roi != null && (
                <div className="mt-4 border-t border-border pt-4">
                  <NetBenefitRationale roi={triage.roi} />
                </div>
              )}
            </section>
          )}

          {/* 4. AUFWAND: Composite-Breakdown mit gelabelten Subscores. */}
          {triage?.composite != null && (
            <section className="rounded-xl border border-border bg-card px-6 py-5">
              <SectionLabel>Aufwand</SectionLabel>
              <CompositeBreakdown composite={triage.composite} />
            </section>
          )}

          {/* 5. ZUSAMMENFASSUNG. */}
          <section>
            <SectionLabel>Zusammenfassung</SectionLabel>
            <p className="text-sm leading-relaxed text-foreground/90">
              {bs.summary_text}
            </p>
          </section>

          {/* 6. GESCHAERFTE BESCHREIBUNG als Zitat-Block. */}
          {bs.sharpened_text !== null && (
            <section className="border-l-2 border-[var(--ink)] pl-4">
              <SectionLabel>Geschärfte Beschreibung</SectionLabel>
              <p className="text-sm leading-relaxed text-muted-foreground">
                {bs.sharpened_text}
              </p>
            </section>
          )}

          {/* 7. COMPLIANCE. */}
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

          <ReviewSection caseId={result.case_id} businessSummary={bs} />
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

          {/* Aufwand nie als blosses X/10: gelabelte Subscores aus der Triage,
              Fallback auf das Composite-Total aus dem technischen Detail. */}
          {triage?.composite != null ? (
            <section className="rounded-xl border border-border bg-card px-5 py-4">
              <SectionLabel>Aufwand-Score</SectionLabel>
              <CompositeBreakdown composite={triage.composite} />
            </section>
          ) : (
            td.composite_total !== null && (
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
            )
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
              {/* Begruendungslisten statt Komma-Strings. Ohne Triage-State keine
                  Empfehlung zum Gruppieren -- dann beide Seiten zeigen. */}
              <RoutingRationale
                recommendation={triage?.routing.recommendation ?? "BORDERLINE"}
                automationSignals={td.automation_signals}
                aiSignals={td.ai_signals}
              />
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
