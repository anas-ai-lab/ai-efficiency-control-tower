import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  XCircle,
} from "lucide-react"

import type { TriageResponse } from "@/types/api"
import { formatEUR, formatNumber, ZONE_CONFIG, type ZoneKey } from "@/lib/formatters"
import { ROUTING_LABELS, CONFIDENCE_LABELS } from "@/lib/labels"
import {
  NetBenefitRationale,
  RoutingRationale,
} from "@/components/decision-rationale"

// Read-only Darstellung des beim Intake berechneten Triage-Ergebnisses (V4-P6/
// P7). Wird auf der Fall-Detailseite fuer alle Zugriffsstufen gerendert -- ohne
// Aktions-Buttons. Alle Enum-Anzeigen laufen ueber die zentrale Label-Map bzw.
// ZONE_CONFIG. Die Begruendungen kommen deterministisch aus dem Backend
// (score_breakdown, confidence_reasoning, recommendation_text) -- kein LLM.

const CONFIDENCE_TEXT: Record<string, string> = {
  hoch: "text-[var(--zone-win-fg)]",
  mittel: "text-[var(--zone-risk-fg)]",
  niedrig: "text-[var(--zone-gain-fg)]",
}

function ScoreBreakdownBlock({ triage }: { triage: TriageResponse }) {
  const sb = triage.score_breakdown
  if (sb === null) return null
  return (
    <section className="rounded-2xl border border-border bg-card px-6 py-5">
      <p className="eyebrow">Aufwand-Score — Herkunft</p>
      <ul className="mt-4 space-y-3">
        {sb.components.map((c) => (
          <li key={c.key} className="grid grid-cols-[1fr_auto] gap-x-4 gap-y-1">
            <span className="text-sm font-medium text-foreground">{c.label}</span>
            <span className="font-mono text-sm tabular-nums text-foreground/85">
              {c.wert} / {c.max}
            </span>
            <span className="col-span-2 text-[0.8125rem] leading-relaxed text-muted-foreground">
              {c.begruendung}
            </span>
          </li>
        ))}
      </ul>
      <p className="mt-4 border-t border-border pt-3 text-sm text-foreground">
        {sb.total_line}
      </p>
      <p className="mt-2 text-[0.8125rem] leading-relaxed text-muted-foreground">
        Machbarkeit {sb.feasibility_score} / {sb.max_total} — {sb.feasibility_definition}
      </p>
    </section>
  )
}

export function CaseResult({ triage }: { triage: TriageResponse }) {
  const zone = triage.zone
  const zoneConfig = zone ? ZONE_CONFIG[zone.final_zone as ZoneKey] : null
  const routingLabel =
    ROUTING_LABELS[triage.routing.recommendation] ?? triage.routing.recommendation
  const confidenceLabel =
    CONFIDENCE_LABELS[triage.routing.confidence] ?? triage.routing.confidence

  return (
    <div className="space-y-5">
      {/* Verdikt: Zone als Headline + Begruendung + Konfidenz-Saetze (V4-P6). */}
      {zone !== null && zoneConfig !== null && (
        <section className={`rounded-2xl border px-6 py-6 sm:px-7 ${zoneConfig.surface}`}>
          <div className="flex items-start gap-4">
            <span className={`mt-2.5 size-2.5 shrink-0 rounded-full ${zoneConfig.dot}`} aria-hidden />
            <div className="min-w-0">
              <p className="eyebrow">Bewertungszone</p>
              <h2 className={`mt-1.5 text-2xl font-bold tracking-tight ${zoneConfig.text}`}>
                {zoneConfig.labelDE}
              </h2>
              <p className="mt-2 max-w-prose text-[0.9375rem] leading-relaxed text-foreground/90">
                {zone.reason}
              </p>
              <div className="mt-3 border-t border-current/10 pt-3">
                <p className="text-xs text-muted-foreground">
                  Konfidenz:{" "}
                  <span
                    className={`font-medium ${
                      CONFIDENCE_TEXT[zone.confidence_reasoning.level] ?? "text-foreground"
                    }`}
                  >
                    {zone.confidence_reasoning.level}
                  </span>
                </p>
                {zone.confidence_reasoning.gruende.length > 0 && (
                  <ul className="mt-2 space-y-1">
                    {zone.confidence_reasoning.gruende.map((g, i) => (
                      <li
                        key={i}
                        className="flex gap-2 text-[0.8125rem] leading-relaxed text-muted-foreground"
                      >
                        <span className="mt-1.5 size-1 shrink-0 rounded-full bg-current/40" aria-hidden />
                        {g}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              {zone.handlungsdruck_elevated && (
                <span
                  className={`mt-3 inline-flex items-center gap-1.5 rounded-full border border-current/25 px-2.5 py-1 text-[0.7rem] font-medium tracking-wide ${zoneConfig.text}`}
                >
                  <ArrowRight className="size-3" />
                  Hochgestuft wegen Handlungsdruck
                </span>
              )}
            </div>
          </div>
        </section>
      )}

      {/* ROI-Kennzahlen + Nutzen-Erklaerung. */}
      {triage.roi !== null && (
        <section className="overflow-hidden rounded-2xl border border-border bg-card">
          <div className="grid grid-cols-1 divide-y divide-border sm:grid-cols-[1.4fr_1fr_1fr] sm:divide-x sm:divide-y-0">
            <div className="px-6 py-5">
              <p className="eyebrow">Erwarteter Nettonutzen</p>
              <p className="stat-value mt-2.5 text-[2rem] text-foreground">
                {formatEUR(triage.roi.net_expected_benefit_eur)}
              </p>
              <p className="mt-1.5 text-xs text-muted-foreground">pro Jahr</p>
            </div>
            <div className="px-6 py-5">
              <p className="eyebrow">Theoret. Potenzial</p>
              <p className="stat-value mt-2.5 text-2xl text-foreground/80">
                {formatEUR(triage.roi.theoretical_potential_eur)}
              </p>
              <p className="mt-1.5 text-xs text-muted-foreground">Obergrenze</p>
            </div>
            <div className="px-6 py-5">
              <p className="eyebrow">Stunden / Jahr</p>
              <p className="stat-value mt-2.5 text-2xl text-foreground/80">
                {formatNumber(triage.roi.hours_per_year)}
              </p>
              <p className="mt-1.5 text-xs text-muted-foreground">eingespart</p>
            </div>
          </div>
          <div className="border-t border-border px-6 py-4">
            <NetBenefitRationale roi={triage.roi} />
          </div>
        </section>
      )}

      {/* Aufwand-Score-Herkunft (V4-P6) -- ersetzt den nackten X/10-Wert. */}
      <ScoreBreakdownBlock triage={triage} />

      {/* Vorfilter -- bei Fail die Kriterien im Klartext. */}
      {triage.passed_vorfilter ? (
        <div className="flex items-center gap-2.5 rounded-xl border border-border bg-card px-4 py-3.5 text-sm font-medium text-foreground">
          <CheckCircle2 className="size-4 shrink-0 text-[var(--zone-win)]" />
          Alle Vorfilter-Kriterien erfüllt
        </div>
      ) : (
        <div className="rounded-xl border border-destructive/25 bg-destructive/5 px-4 py-3.5 text-sm">
          <div className="flex items-center gap-2.5 font-medium text-destructive">
            <XCircle className="size-4 shrink-0" />
            Vorfilter nicht bestanden
          </div>
          {triage.vorfilter.failed_criteria.length > 0 && (
            <ul className="mt-2.5 space-y-1 pl-6 text-foreground/80">
              {triage.vorfilter.failed_criteria.map((c, i) => (
                <li key={i} className="list-disc">
                  {c}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Routing -- Badge + deutscher Empfehlungssatz + tragende Signale. */}
      <section className="rounded-xl border border-border bg-card p-5">
        <p className="eyebrow">Routing-Empfehlung</p>
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <span className="inline-flex items-center gap-2 rounded-lg border border-border bg-background px-3 py-1.5 text-sm font-medium text-foreground">
            <span className="size-2 rounded-full bg-[var(--ink)]" aria-hidden />
            {routingLabel}
          </span>
          <span className="text-xs text-muted-foreground">
            Konfidenz: <span className="font-medium text-foreground">{confidenceLabel}</span>
          </span>
        </div>
        <p className="mt-3 text-[0.9375rem] leading-relaxed text-foreground/90">
          {triage.routing.recommendation_text}
        </p>
        <div className="mt-4">
          <RoutingRationale
            recommendation={triage.routing.recommendation}
            automationSignals={triage.routing.automation_signals}
            aiSignals={triage.routing.ai_signals}
          />
        </div>
        {triage.routing.risk_flags.length > 0 && (
          <div className="mt-4 border-t border-border pt-4">
            <p className="text-xs text-muted-foreground">Risiko-Signale</p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {triage.routing.risk_flags.map((flag, i) => (
                <span
                  key={i}
                  className="rounded-md border border-[var(--zone-gain-border)] bg-[var(--zone-gain-surface)] px-2 py-0.5 text-xs font-medium text-[var(--zone-gain-fg)]"
                >
                  {flag}
                </span>
              ))}
            </div>
          </div>
        )}
        {triage.routing.requires_human_review && (
          <p className="mt-4 flex items-center gap-2 text-sm font-medium text-[var(--zone-risk-fg)]">
            <AlertTriangle className="size-3.5" />
            Menschliche Prüfung empfohlen
          </p>
        )}
      </section>

      {/* Machbarkeit. */}
      <section className="rounded-xl border border-border bg-card p-5">
        <p className="eyebrow">Machbarkeit</p>
        <div className="mt-3 flex items-center gap-2 text-sm">
          {triage.feasibility.is_feasible ? (
            <>
              <CheckCircle2 className="size-4 text-[var(--zone-win)]" />
              <span className="font-medium text-foreground">Machbar</span>
            </>
          ) : (
            <>
              <XCircle className="size-4 text-destructive" />
              <span className="font-medium text-foreground">Nicht machbar</span>
            </>
          )}
        </div>
        {triage.feasibility.recommendation !== null && (
          <p className="mt-3 text-[0.9375rem] leading-relaxed text-foreground/90">
            {triage.feasibility.recommendation}
          </p>
        )}
        {triage.feasibility.flags.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-1.5">
            {triage.feasibility.flags.map((flag, i) => (
              <span
                key={i}
                className="rounded-md border border-border bg-muted/50 px-2 py-0.5 text-xs text-muted-foreground"
              >
                {flag}
              </span>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

export default CaseResult
