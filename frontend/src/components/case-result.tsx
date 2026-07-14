"use client"

import {
  AlertTriangle,
  ArrowRight,
  ChevronDown,
  XCircle,
} from "lucide-react"
import { useTranslations } from "next-intl"

import type { TriageResponse } from "@/types/api"
import { ZONE_CONFIG, type ZoneKey } from "@/lib/formatters"
import { useFormat } from "@/lib/use-format"
import {
  NetBenefitRationale,
  RoutingRationale,
} from "@/components/decision-rationale"

// Zweischichtige Ergebnisdarstellung (V4.1-S5): Ebene 1 ist management-tauglich
// (Zone + zwei Klartext-Saetze aus dem Backend, keine internen Codes/Faktoren/
// Scores). Ebene 2 ("Wie wurde das berechnet?") klappt die Herkunft je
// Komponente auf. Alle Saetze kommen deterministisch aus management/berechnung
// (Backend), kein LLM; Zahlen unveraendert.

// Ebene 2: aufklappbare Herkunft -- die vier Berechnungs-Zeilen, das Aufwand-
// Score-Detail, der Nutzen-Rechenweg und die tragenden Routing-Signale.
function BerechnungExpander({ triage }: { triage: TriageResponse }) {
  const t = useTranslations("result")
  const te = useTranslations("enums")
  const rows = triage.berechnung
  const sb = triage.score_breakdown
  if (rows === null || rows === undefined) return null
  const routing = triage.routing
  const hasSignals =
    routing !== null &&
    (routing.automation_signals.length > 0 ||
      routing.ai_signals.length > 0 ||
      routing.risk_flags.length > 0)

  return (
    <details className="group rounded-2xl border border-border bg-card">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-2 px-6 py-4 text-sm font-medium text-foreground marker:content-none">
        {t("howCalculated")}
        <ChevronDown
          aria-hidden
          className="size-4 text-muted-foreground transition-transform group-open:rotate-180"
        />
      </summary>
      <div className="space-y-6 border-t border-border px-6 py-5">
        {/* Vier Komponenten-Zeilen: Label - Wert - ein Satz Alltagssprache. */}
        <ul className="space-y-4">
          {rows.map((r) => (
            <li key={r.label} className="grid grid-cols-[1fr_auto] gap-x-4 gap-y-1">
              <span className="text-sm font-medium text-foreground">{r.label}</span>
              <span className="text-right font-mono text-sm tabular-nums text-foreground/85">
                {r.wert}
              </span>
              <span className="col-span-2 text-[0.8125rem] leading-relaxed text-muted-foreground">
                {r.erklaerung}
              </span>
            </li>
          ))}
        </ul>

        {/* Aufwand-Score im Detail (Komplexitaet / Kosten / Datenschutz). */}
        {sb !== null && sb !== undefined && (
          <div className="border-t border-border pt-4">
            <p className="eyebrow">{t("effortScoreDetail")}</p>
            <ul className="mt-3 space-y-2.5">
              {sb.components.map((c) => (
                <li
                  key={c.key}
                  className="grid grid-cols-[1fr_auto] gap-x-4 gap-y-0.5"
                >
                  <span className="text-sm text-foreground">{c.label}</span>
                  <span className="font-mono text-sm tabular-nums text-foreground/85">
                    {c.wert} / {c.max}
                  </span>
                  <span className="col-span-2 text-[0.8125rem] leading-relaxed text-muted-foreground">
                    {c.begruendung}
                  </span>
                </li>
              ))}
            </ul>
            <p className="mt-3 border-t border-border pt-3 text-sm text-foreground">
              {sb.total_line}
            </p>
          </div>
        )}

        {/* Nutzen-Rechenweg (Faktoren) -- auf Ebene 2 zulaessig. */}
        {triage.roi !== null && (
          <div className="border-t border-border pt-4">
            <p className="eyebrow mb-2">{t("benefitCalc")}</p>
            <NetBenefitRationale roi={triage.roi} />
          </div>
        )}

        {/* Tragende Routing-Signale + Risiko-Signale. */}
        {hasSignals && routing !== null && (
          <div className="border-t border-border pt-4">
            <p className="eyebrow mb-3">{t("whatSupports")}</p>
            <RoutingRationale
              recommendation={routing.recommendation}
              automationSignals={routing.automation_signals}
              aiSignals={routing.ai_signals}
            />
            {routing.risk_flags.length > 0 && (
              <div className="mt-4">
                <p className="text-xs text-muted-foreground">{t("riskSignals")}</p>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {routing.risk_flags.map((flag, i) => (
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
          </div>
        )}

        {/* Angaben-Qualitaet: nur zeigen, wenn strukturell etwas fehlt. */}
        {triage.feasibility !== null && !triage.feasibility.is_feasible && (
          <div className="border-t border-border pt-4">
            <p className="eyebrow mb-2">{t("qualityHint")}</p>
            {triage.feasibility.recommendation !== null && (
              <p className="text-sm leading-relaxed text-foreground/85">
                {triage.feasibility.recommendation}
              </p>
            )}
            {triage.feasibility.flags.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1.5">
                {triage.feasibility.flags.map((f, i) => (
                  <span
                    key={i}
                    className="rounded-md border border-border bg-muted/50 px-2 py-0.5 text-xs text-muted-foreground"
                  >
                    {te(`feasibilityFlag.${f}`)}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </details>
  )
}

// Read-only Darstellung des beim Intake berechneten Triage-Ergebnisses (V4.1-S5).
// Wird auf der Fall-Detailseite fuer alle Zugriffsstufen gerendert -- ohne
// Aktions-Buttons. Die Klartext-Saetze (management/berechnung) kommen
// deterministisch aus dem Backend, kein LLM.
export function CaseResult({ triage }: { triage: TriageResponse }) {
  const t = useTranslations("result")
  const tz = useTranslations("zones")
  const fmt = useFormat()
  const zone = triage.zone
  const zoneConfig = zone ? ZONE_CONFIG[zone.final_zone as ZoneKey] : null
  const mgmt = triage.management ?? null

  // Vorfilter-Fail (oder unbewertet): keine Bewertung -> management/zone null.
  // Klartext-Grund + Empfehlungssatz (recommendation_text traegt hier die
  // Fail-Begruendung).
  if (mgmt === null || zone === null || zoneConfig === null) {
    return (
      <div className="space-y-5">
        <div className="rounded-xl border border-destructive/25 bg-destructive/5 px-5 py-4 text-sm">
          <div className="flex items-center gap-2.5 font-medium text-destructive">
            <XCircle className="size-4 shrink-0" />
            {t("prefilterFailed")}
          </div>
          {triage.vorfilter !== null &&
            triage.vorfilter.failed_criteria.length > 0 && (
              <ul className="mt-2.5 space-y-1 pl-6 text-foreground/80">
                {triage.vorfilter.failed_criteria.map((c, i) => (
                  <li key={i} className="list-disc">
                    {c}
                  </li>
                ))}
              </ul>
            )}
        </div>
        {triage.routing !== null && (
          <p className="max-w-prose text-[0.9375rem] leading-relaxed text-foreground/90">
            {triage.routing.recommendation_text}
          </p>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-5">
      {/* ===== Ebene 1: Management-taugliche Zusammenfassung ===== */}
      <section className={`rounded-2xl border px-6 py-6 sm:px-7 ${zoneConfig.surface}`}>
        <div className="flex items-start gap-4">
          <span
            className={`mt-2.5 size-2.5 shrink-0 rounded-full ${zoneConfig.dot}`}
            aria-hidden
          />
          <div className="min-w-0">
            <p className="eyebrow">{t("zoneLabel")}</p>
            <h2 className={`mt-1.5 text-2xl font-bold tracking-tight ${zoneConfig.text}`}>
              {tz(`${zone.final_zone}.label`)}
            </h2>
            <p className="mt-2 max-w-prose text-[0.9375rem] leading-relaxed text-foreground/90">
              {mgmt.zonen_satz}
            </p>
            {zone.handlungsdruck_elevated && (
              <span
                className={`mt-3 inline-flex items-center gap-1.5 rounded-full border border-current/25 px-2.5 py-1 text-[0.7rem] font-medium tracking-wide ${zoneConfig.text}`}
              >
                <ArrowRight className="size-3" />
                {t("elevated")}
              </span>
            )}
          </div>
        </div>
      </section>

      {/* Empfehlung als ganzer Satz (inkl. Belastbarkeit der Empfehlung). */}
      <section className="rounded-2xl border border-border bg-card px-6 py-5">
        <p className="eyebrow">{t("recommendation")}</p>
        <p className="mt-2 max-w-prose text-[0.9375rem] leading-relaxed text-foreground">
          {mgmt.empfehlung_satz}
        </p>
        {triage.routing !== null && triage.routing.requires_human_review && (
          <p className="mt-3 flex items-center gap-2 border-t border-border pt-3 text-sm font-medium text-[var(--zone-risk-fg)]">
            <AlertTriangle className="size-3.5" />
            {t("humanReviewRecommended")}
          </p>
        )}
      </section>

      {/* Headline-Kennzahlen (Zahlen, keine internen Codes). */}
      {triage.roi !== null && (
        <div className="grid grid-cols-1 gap-px overflow-hidden rounded-2xl border border-border bg-border sm:grid-cols-2">
          <div className="bg-card px-6 py-5">
            <p className="eyebrow">{t("netBenefit")}</p>
            <p className="stat-value mt-2.5 text-[1.75rem] text-foreground">
              {fmt.eur(triage.roi.net_expected_benefit_eur)}
            </p>
            <p className="mt-1.5 text-xs text-muted-foreground">{t("perYear")}</p>
          </div>
          <div className="bg-card px-6 py-5">
            <p className="eyebrow">{t("hoursSaved")}</p>
            <p className="stat-value mt-2.5 text-[1.75rem] text-foreground/80">
              {fmt.number(triage.roi.hours_per_year)}
            </p>
            <p className="mt-1.5 text-xs text-muted-foreground">{t("perYear")}</p>
          </div>
        </div>
      )}

      {/* ===== Ebene 2: Herkunft aufklappbar ===== */}
      <BerechnungExpander triage={triage} />
    </div>
  )
}

export default CaseResult
